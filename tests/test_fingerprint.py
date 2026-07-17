# SPDX-License-Identifier: LGPL-3.0-or-later
"""Focused tests for the file-based fingerprint pipeline step."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from molraptor import MorganFingerprintProfile, encode_fingerprints
from molraptor.fingerprint import FingerprintStep
import molraptor.fingerprint as fingerprint_module


@pytest.fixture
def fingerprint_config(tmp_path):
    artifacts = tmp_path / "artifacts"
    return SimpleNamespace(
        fingerprint=SimpleNamespace(radius=3, size=64),
        paths=SimpleNamespace(
            fingerprint_output_file=artifacts / "fingerprints.csv",
            fingerprint_array_file=artifacts / "fingerprints.npy",
            labels_output_file=artifacts / "labels.npy",
        ),
    )


@pytest.fixture
def valid_curated_csv(tmp_path):
    path = tmp_path / "curated.csv"
    pd.DataFrame(
        {
            "SMILES": ["CCO", "CC", "C(C)O"],
            "Label": [10, 20, 30],
        }
    ).to_csv(path, index=False)
    return path


def test_fingerprint_step_uses_public_encoder_with_configured_profile(
    fingerprint_config,
    valid_curated_csv,
):
    assert fingerprint_module.encode_fingerprints is encode_fingerprints

    with patch(
        "molraptor.fingerprint.encode_fingerprints",
        wraps=encode_fingerprints,
    ) as encoder:
        FingerprintStep(fingerprint_config).run(valid_curated_csv)

    encoder.assert_called_once()
    smiles, profile = encoder.call_args.args
    assert smiles == ["CCO", "CC", "C(C)O"]
    assert isinstance(profile, MorganFingerprintProfile)
    assert profile.radius == fingerprint_config.fingerprint.radius
    assert profile.fp_size == fingerprint_config.fingerprint.size


def test_valid_inputs_preserve_fingerprint_and_label_outputs(
    fingerprint_config,
    valid_curated_csv,
):
    output_path = FingerprintStep(fingerprint_config).run(valid_curated_csv)
    expected = encode_fingerprints(
        ["CCO", "CC", "C(C)O"],
        MorganFingerprintProfile(radius=3, fp_size=64),
    ).fingerprints

    assert output_path == Path(fingerprint_config.paths.fingerprint_output_file)
    csv_fingerprints = pd.read_csv(output_path).to_numpy(dtype=np.uint8)
    npy_fingerprints = np.load(
        fingerprint_config.paths.fingerprint_array_file
    )
    labels = np.load(fingerprint_config.paths.labels_output_file)

    np.testing.assert_array_equal(csv_fingerprints, expected)
    np.testing.assert_array_equal(npy_fingerprints, expected)
    np.testing.assert_array_equal(labels, np.array([10, 20, 30]))
    assert npy_fingerprints.dtype == np.uint8


def test_invalid_smiles_fail_before_any_artifact_is_written(
    fingerprint_config,
    tmp_path,
):
    curated_csv = tmp_path / "invalid_curated.csv"
    pd.DataFrame(
        {
            "SMILES": ["CCO", "not-a-smiles", "CC", "also-invalid"],
            "Label": [10, 20, 30, 40],
        }
    ).to_csv(curated_csv, index=False)

    with pytest.raises(
        ValueError,
        match=r"Invalid SMILES at input row indices: \[1, 3\]",
    ):
        FingerprintStep(fingerprint_config).run(curated_csv)

    assert not Path(fingerprint_config.paths.fingerprint_output_file).exists()
    assert not Path(fingerprint_config.paths.fingerprint_array_file).exists()
    assert not Path(fingerprint_config.paths.labels_output_file).exists()
