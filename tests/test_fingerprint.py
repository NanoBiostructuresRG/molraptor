# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the CSV/TXT fingerprint workflow and its artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from molraptor import MorganFingerprintProfile, encode_fingerprints
from molraptor.config import MolraptorConfig
from molraptor.fingerprint import FingerprintStep, OUTPUT_FILENAMES


def _config(
    input_path: Path,
    output_dir: Path,
    *,
    smiles_column: str = "SMILES",
    profile: MorganFingerprintProfile | None = None,
) -> MolraptorConfig:
    return MolraptorConfig(
        input_path=input_path,
        smiles_column=smiles_column,
        output_dir=output_dir,
        profile=profile or MorganFingerprintProfile(fp_size=64),
    )


def _assert_no_artifacts(output_dir: Path) -> None:
    assert not output_dir.exists() or not any(output_dir.iterdir())


@pytest.mark.parametrize(
    "column_name",
    ["SMILES", "SMILES_Harmonized", "SMILES_RDKit"],
)
def test_csv_uses_exact_configured_smiles_column(tmp_path, column_name):
    input_path = tmp_path / "molecules.csv"
    pd.DataFrame(
        {
            column_name: ["CCO", "CC", "CCO"],
            "ignored": ["invalid", "invalid", "invalid"],
        }
    ).to_csv(input_path, index=False)
    output_dir = tmp_path / "outputs"

    result = FingerprintStep(
        _config(input_path, output_dir, smiles_column=column_name)
    ).run()

    assert [status.input_smiles for status in result.input_statuses] == [
        "CCO",
        "CC",
        "CCO",
    ]
    assert result.valid_indices == (0, 1, 2)
    np.testing.assert_array_equal(result.fingerprints[0], result.fingerprints[2])


def test_csv_empty_cell_is_preserved_as_an_empty_input(tmp_path):
    input_path = tmp_path / "molecules.csv"
    input_path.write_text("SMILES\nCCO\n\nCC\n", encoding="utf-8")

    result = FingerprintStep(
        _config(input_path, tmp_path / "outputs")
    ).run()

    assert [status.input_smiles for status in result.input_statuses] == [
        "CCO",
        "",
        "CC",
    ]
    assert result.valid_indices == (0, 2)
    assert result.input_statuses[1].invalid_reason == "empty_molecule"


def test_txt_removes_only_line_endings_and_preserves_every_input(tmp_path):
    input_path = tmp_path / "molecules.txt"
    input_path.write_bytes(b"CCO\r\nCCO\n\n CCO \nnot-a-smiles")

    result = FingerprintStep(
        _config(input_path, tmp_path / "outputs")
    ).run()

    assert [status.input_smiles for status in result.input_statuses] == [
        "CCO",
        "CCO",
        "",
        " CCO ",
        "not-a-smiles",
    ]
    assert result.valid_indices[:2] == (0, 1)
    np.testing.assert_array_equal(result.fingerprints[0], result.fingerprints[1])


def test_mixed_batch_writes_exact_traceable_output_contract(tmp_path):
    input_path = tmp_path / "molecules.csv"
    input_path.write_text(
        "SMILES\nCCO\nnot-a-smiles\n\nc1ccccc1\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"
    profile = MorganFingerprintProfile(
        radius=3,
        fp_size=64,
        include_chirality=True,
    )

    result = FingerprintStep(
        _config(input_path, output_dir, profile=profile)
    ).run()

    assert {path.name for path in output_dir.iterdir()} == set(OUTPUT_FILENAMES)
    assert not (output_dir / "labels.npy").exists()

    npy_matrix = np.load(output_dir / "fingerprints.npy", allow_pickle=False)
    csv_matrix = pd.read_csv(output_dir / "fingerprints.csv").to_numpy(
        dtype=np.uint8
    )
    np.testing.assert_array_equal(npy_matrix, result.fingerprints)
    np.testing.assert_array_equal(csv_matrix, result.fingerprints)
    assert npy_matrix.dtype == np.uint8

    statuses = pd.read_csv(
        output_dir / "input_statuses.csv",
        dtype=str,
        keep_default_na=False,
    ).to_dict(orient="records")
    assert statuses == [
        {
            "input_index": "0",
            "input_smiles": "CCO",
            "status": "valid",
            "rdkit_canonical_smiles": "CCO",
            "fingerprint_index": "0",
            "invalid_reason": "",
        },
        {
            "input_index": "1",
            "input_smiles": "not-a-smiles",
            "status": "invalid",
            "rdkit_canonical_smiles": "",
            "fingerprint_index": "",
            "invalid_reason": "parse_failure",
        },
        {
            "input_index": "2",
            "input_smiles": "",
            "status": "invalid",
            "rdkit_canonical_smiles": "",
            "fingerprint_index": "",
            "invalid_reason": "empty_molecule",
        },
        {
            "input_index": "3",
            "input_smiles": "c1ccccc1",
            "status": "valid",
            "rdkit_canonical_smiles": "c1ccccc1",
            "fingerprint_index": "1",
            "invalid_reason": "",
        },
    ]

    metadata = json.loads((output_dir / "metadata.json").read_text("utf-8"))
    assert metadata == result.serialize_metadata()
    assert metadata["valid_indices"] == [0, 3]
    assert metadata["matrix_shape"] == [2, 64]
    assert metadata["matrix_dtype"] == "uint8"
    assert metadata["valid_count"] == 2
    assert metadata["invalid_count"] == 2


def test_file_workflow_matches_direct_in_memory_api(tmp_path):
    input_path = tmp_path / "molecules.txt"
    input_path.write_text("CCO\ninvalid\nCC\n", encoding="utf-8")
    profile = MorganFingerprintProfile(radius=3, fp_size=64)

    workflow_result = FingerprintStep(
        _config(input_path, tmp_path / "outputs", profile=profile)
    ).run()
    direct_result = encode_fingerprints(["CCO", "invalid", "CC"], profile)

    np.testing.assert_array_equal(
        workflow_result.fingerprints,
        direct_result.fingerprints,
    )
    assert workflow_result.serialize_metadata() == direct_result.serialize_metadata()


@pytest.mark.parametrize(
    ("filename", "contents", "message"),
    [
        ("molecules.csv", "Other\nCCO\n", "SMILES column 'SMILES'"),
        ("molecules.smi", "CCO\n", "Unsupported input format '.smi'"),
        ("molecules.txt", "invalid\n\n", "zero valid SMILES"),
    ],
)
def test_validation_failures_write_no_artifacts(
    tmp_path,
    filename,
    contents,
    message,
):
    input_path = tmp_path / filename
    input_path.write_text(contents, encoding="utf-8")
    output_dir = tmp_path / "outputs"

    with pytest.raises(ValueError, match=message):
        FingerprintStep(_config(input_path, output_dir)).run()

    _assert_no_artifacts(output_dir)


def test_unreadable_input_writes_no_artifacts(tmp_path):
    output_dir = tmp_path / "outputs"

    with pytest.raises(ValueError, match="Unable to read CSV input"):
        FingerprintStep(
            _config(tmp_path / "missing.csv", output_dir)
        ).run()

    _assert_no_artifacts(output_dir)


@pytest.mark.parametrize(
    "profile_kwargs",
    [{"radius": -1}, {"fp_size": 0}],
)
def test_invalid_profile_is_rejected_before_outputs(tmp_path, profile_kwargs):
    output_dir = tmp_path / "outputs"

    with pytest.raises(ValidationError):
        MorganFingerprintProfile(**profile_kwargs)

    _assert_no_artifacts(output_dir)
