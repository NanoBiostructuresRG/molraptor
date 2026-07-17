# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the public in-memory Morgan fingerprint API."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest
from pydantic import ValidationError

from molraptor import (
    FingerprintEncodingResult,
    FingerprintInputStatus,
    MorganFingerprintProfile,
    encode_fingerprints,
)
from molraptor.version import __version__


def test_profile_serialization_includes_all_fixed_defaults():
    profile = MorganFingerprintProfile()

    assert profile.serialize() == {
        "profile_schema_version": "1.0",
        "algorithm": "morgan",
        "output_type": "binary-bit-vector",
        "radius": 2,
        "fp_size": 2048,
        "include_chirality": False,
        "use_bond_types": True,
        "include_ring_membership": True,
        "include_redundant_environments": False,
        "invariant_policy": "rdkit-default",
    }
    assert json.loads(profile.model_dump_json()) == profile.serialize()
    assert MorganFingerprintProfile.model_validate_json(
        profile.model_dump_json()
    ) == profile


def test_profile_validates_size_radius_and_unknown_settings():
    with pytest.raises(ValidationError):
        MorganFingerprintProfile(fp_size=0)
    with pytest.raises(ValidationError):
        MorganFingerprintProfile(radius=-1)
    with pytest.raises(ValidationError):
        MorganFingerprintProfile(unknown_setting=True)


def test_encoding_is_deterministic_and_reports_versions_and_hashes():
    smiles = ["CCO", "c1ccccc1", "CCO"]
    profile = MorganFingerprintProfile(fp_size=128)

    first = encode_fingerprints(smiles, profile)
    second = encode_fingerprints(smiles, profile)

    assert isinstance(first, FingerprintEncodingResult)
    np.testing.assert_array_equal(first.fingerprints, second.fingerprints)
    assert first.ordered_input_hash == second.ordered_input_hash
    assert first.profile_hash == second.profile_hash
    assert first.profile["output_type"] == "binary-bit-vector"
    assert first.molraptor_version == __version__
    assert first.rdkit_version
    assert len(first.ordered_input_hash) == 64
    assert len(first.profile_hash) == 64
    int(first.ordered_input_hash, 16)
    int(first.profile_hash, 16)


def test_order_duplicates_and_metadata_alignment_are_preserved():
    result = encode_fingerprints(
        ["C(C)O", "not-a-smiles", "CC", "C(C)O"],
        MorganFingerprintProfile(fp_size=64),
    )

    assert result.valid_indices == (0, 2, 3)
    assert result.valid_count == 3
    assert result.invalid_count == 1
    assert len(result.input_statuses) == 4
    assert [item.input_index for item in result.input_statuses] == [0, 1, 2, 3]
    assert [item.status for item in result.input_statuses] == [
        "valid",
        "invalid",
        "valid",
        "valid",
    ]
    assert [item.fingerprint_index for item in result.input_statuses] == [
        0,
        None,
        1,
        2,
    ]
    assert result.input_statuses[0].rdkit_canonical_smiles == "CCO"
    assert result.input_statuses[0].invalid_reason is None
    assert result.input_statuses[1].rdkit_canonical_smiles is None
    np.testing.assert_array_equal(result.fingerprints[0], result.fingerprints[2])
    assert not np.array_equal(result.fingerprints[0], result.fingerprints[1])


def test_invalid_smiles_reasons_do_not_create_zero_vectors():
    result = encode_fingerprints(
        ["invalid", ""],
        MorganFingerprintProfile(fp_size=32),
    )

    assert result.fingerprints.shape == (0, 32)
    assert result.valid_indices == ()
    assert result.valid_count == 0
    assert result.invalid_count == 2
    assert [status.invalid_reason for status in result.input_statuses] == [
        "parse_failure",
        "empty_molecule",
    ]
    assert all(status.status == "invalid" for status in result.input_statuses)
    assert all(
        status.fingerprint_index is None for status in result.input_statuses
    )


def test_invalid_input_status_requires_a_stable_reason():
    with pytest.raises(ValidationError, match="requires an invalid_reason"):
        FingerprintInputStatus(
            input_index=0,
            input_smiles="invalid",
            status="invalid",
            rdkit_canonical_smiles=None,
            fingerprint_index=None,
        )


@pytest.mark.parametrize(
    "status_data",
    [
        {
            "status": "valid",
            "rdkit_canonical_smiles": None,
            "fingerprint_index": 0,
            "invalid_reason": None,
        },
        {
            "status": "valid",
            "rdkit_canonical_smiles": "CCO",
            "fingerprint_index": None,
            "invalid_reason": None,
        },
        {
            "status": "valid",
            "rdkit_canonical_smiles": "CCO",
            "fingerprint_index": 0,
            "invalid_reason": "parse_failure",
        },
        {
            "status": "invalid",
            "rdkit_canonical_smiles": "CCO",
            "fingerprint_index": None,
            "invalid_reason": "parse_failure",
        },
        {
            "status": "invalid",
            "rdkit_canonical_smiles": None,
            "fingerprint_index": 0,
            "invalid_reason": "parse_failure",
        },
    ],
)
def test_input_status_rejects_inconsistent_status_metadata(status_data):
    with pytest.raises(ValidationError):
        FingerprintInputStatus(
            input_index=0,
            input_smiles="CCO",
            **status_data,
        )


@pytest.mark.parametrize(
    ("input_index", "fingerprint_index"),
    [(-1, 0), (0, -1)],
)
def test_input_status_rejects_negative_indices(input_index, fingerprint_index):
    with pytest.raises(ValidationError):
        FingerprintInputStatus(
            input_index=input_index,
            input_smiles="CCO",
            status="valid",
            rdkit_canonical_smiles="CCO",
            fingerprint_index=fingerprint_index,
        )


def test_empty_input_returns_correct_uint8_matrix_and_metadata():
    result = encode_fingerprints([], MorganFingerprintProfile(fp_size=96))

    assert result.fingerprints.shape == (0, 96)
    assert result.fingerprints.dtype == np.uint8
    assert result.matrix_shape == (0, 96)
    assert result.matrix_dtype == "uint8"
    assert result.valid_indices == ()
    assert result.input_statuses == ()
    assert result.valid_count == 0
    assert result.invalid_count == 0


def test_single_string_is_rejected():
    with pytest.raises(TypeError, match="not a string"):
        encode_fingerprints("CCO", MorganFingerprintProfile())


def test_matrix_is_binary_uint8_with_reported_shape():
    result = encode_fingerprints(
        ["CCO", "CCN"],
        MorganFingerprintProfile(fp_size=80),
    )

    assert result.fingerprints.dtype == np.uint8
    assert result.fingerprints.shape == (2, 80)
    assert result.matrix_shape == result.fingerprints.shape
    assert result.matrix_dtype == str(result.fingerprints.dtype)
    assert set(np.unique(result.fingerprints)).issubset({0, 1})


def test_hashes_cover_ordered_input_and_effective_profile():
    profile = MorganFingerprintProfile(fp_size=64)
    original = encode_fingerprints(["CC", "CO"], profile)
    reordered = encode_fingerprints(["CO", "CC"], profile)
    changed_profile = encode_fingerprints(
        ["CC", "CO"],
        MorganFingerprintProfile(fp_size=64, radius=3),
    )

    expected_input_payload = json.dumps(
        ["CC", "CO"],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_profile_payload = json.dumps(
        original.profile,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    assert original.ordered_input_hash == hashlib.sha256(
        expected_input_payload
    ).hexdigest()
    assert original.profile_hash == hashlib.sha256(
        expected_profile_payload
    ).hexdigest()
    assert reordered.ordered_input_hash != original.ordered_input_hash
    assert changed_profile.profile_hash != original.profile_hash


def test_result_metadata_serialization_is_json_compatible_without_matrix():
    result = encode_fingerprints(
        ["CCO", "invalid"],
        MorganFingerprintProfile(fp_size=32),
    )

    metadata = result.serialize_metadata()

    json.dumps(metadata)
    assert "fingerprints" not in metadata
    assert metadata["profile"] == result.profile
    assert metadata["valid_indices"] == [0]
    assert metadata["valid_count"] == 1
    assert metadata["invalid_count"] == 1
    assert metadata["matrix_shape"] == [1, 32]
    assert metadata["matrix_dtype"] == "uint8"
    assert metadata["molraptor_version"] == result.molraptor_version
    assert metadata["rdkit_version"] == result.rdkit_version
    assert metadata["ordered_input_hash"] == result.ordered_input_hash
    assert metadata["profile_hash"] == result.profile_hash
    assert metadata["input_statuses"][0]["rdkit_canonical_smiles"] == "CCO"
    assert "canonical_smiles" not in metadata["input_statuses"][0]
    assert metadata["input_statuses"][1]["invalid_reason"] == "parse_failure"


def test_encoding_performs_no_file_io(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())

    encode_fingerprints(
        ["CCO", "invalid"],
        MorganFingerprintProfile(fp_size=32),
    )

    assert set(tmp_path.iterdir()) == before
