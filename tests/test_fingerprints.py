# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the multi-fingerprint in-memory scientific core."""

import hashlib
from importlib.resources import files

import numpy as np
import pytest
from rdkit import Chem

from molraptor import (
    MorganFingerprintProfile,
    ResolvedFingerprintProfile,
    encode_fingerprints,
    resolve_fingerprint_profile,
)
from molraptor.fingerprints import FINGERPRINT_PARAMETERS, FINGERPRINT_TYPES


EXPECTED_WIDTHS = {
    "morgan": 2048,
    "featmorgan": 2048,
    "atompair": 2048,
    "rdk": 2048,
    "torsion": 2048,
    "layered": 2048,
    "maccs": 167,
    "klekotaroth": 4860,
    "mhfp6": 2048,
    "map4": 1024,
}
IMPLEMENTED_ALGORITHMS = tuple(EXPECTED_WIDTHS)
IMPLEMENTED_BINARY_ALGORITHMS = (
    "morgan",
    "featmorgan",
    "rdk",
    "layered",
    "maccs",
    "klekotaroth",
)

EXPECTED_PROFILE_HASHES = {
    "morgan": "17669bc488012071ce9586dd5f07aefd61aa6aeade17f21d939b6165a9500379",
    "featmorgan": "3060d22e79d0641e755b2ba785a29f882d6574e99b08d47cc75cdc8cac7440fe",
    "atompair": "8c31e4c2ae14c8585e6e35049cd4e92ca84c1f1fe55679d431ff40153835b839",
    "rdk": "d792039b93db7a2e058bf2c493c55b11a7f3f8ab52822bc3e4a6e8b841da88ac",
    "torsion": "47ce301893d8e083ca01910bb443b9b999606cd5b5dae9352d942adf479eed07",
    "layered": "ae084c047f65c267995a1483db1605b22701608b0c5b3545029e777fe2dd0a6f",
    "maccs": "fd662cb09e38c85089670d3c7bca885261c04936a326d4b0b7807a9ba104488d",
    "klekotaroth": "1b888c365a2d25e868273d8c3bf13c6e03d73434add2197a4984e1004dd99969",
    "mhfp6": "0326a002f5996daa9027c3f875c4ad4078d23fb579aa82b8bf9c30340f847ef8",
    "map4": "8d72745a4a74c7d29be383cfe3c0f331334778e7a09ee9cf08bd4a86ff57610e",
}

EXPECTED_ACTIVE_BITS = {
    "morgan": [80, 294, 640, 794, 1057],
    "featmorgan": [0, 539, 792, 1085],
    "rdk": [709, 875, 1308, 1772, 1813, 1927],
    "layered": [
        311, 333, 354, 360, 596, 610, 611, 674, 867, 993,
        1044, 1111, 1493, 1742, 1783,
    ],
    "maccs": [114, 115, 118, 147, 149, 155, 160],
    "klekotaroth": [296, 340, 381, 465, 668, 2974, 3223, 3639, 3691],
}

KLEKOTA_ROTH_PATTERN_SET_SHA256 = (
    "73041eb6b27ebab742fc61ced6a4311eb726bba9c7b30b34dbc5eb378e4c5278"
)
KLEKOTA_ROTH_ACTIVE_BITS = {
    "CCCC": [296, 340, 381, 465, 668, 2974, 3223, 3639, 3691],
    "CCO": [296, 465, 493, 668, 1147, 2948, 2974, 3223, 3787, 3955, 4330],
    "c1ccccc1": [],
}


def test_all_approved_fingerprint_names_are_declared_once():
    assert FINGERPRINT_TYPES == (
        "morgan",
        "featmorgan",
        "atompair",
        "rdk",
        "torsion",
        "layered",
        "maccs",
        "klekotaroth",
        "mhfp6",
        "map4",
    )
    assert tuple(FINGERPRINT_PARAMETERS) == FINGERPRINT_TYPES


def test_declared_parameters_are_read_only():
    with pytest.raises(TypeError):
        FINGERPRINT_PARAMETERS["morgan"]["radius"] = 3


@pytest.mark.parametrize("fingerprint_type", IMPLEMENTED_ALGORITHMS)
def test_resolve_each_fingerprint_profile_without_encoding(fingerprint_type):
    resolved = resolve_fingerprint_profile(fingerprint_type)
    expected_representation = {
        "atompair": "count",
        "torsion": "count",
        "mhfp6": "minhash",
        "map4": "minhash",
    }.get(fingerprint_type, "binary")
    expected_output_type = {
        "binary": "binary-bit-vector",
        "count": "count-vector",
        "minhash": "minhash-sketch",
    }[expected_representation]
    expected_dtype = (
        "uint8" if expected_representation == "binary" else "uint32"
    )

    assert isinstance(resolved, ResolvedFingerprintProfile)
    assert resolved.fingerprint_type == fingerprint_type
    assert resolved.profile["algorithm"] == fingerprint_type
    assert resolved.profile["representation"] == expected_representation
    assert resolved.profile["output_type"] == expected_output_type
    assert resolved.profile["dtype"] == expected_dtype
    assert resolved.width == EXPECTED_WIDTHS[fingerprint_type]
    assert resolved.fp_size == resolved.width


@pytest.mark.parametrize("fingerprint_type", IMPLEMENTED_ALGORITHMS)
def test_default_profile_hash_matches_v050_golden_value(fingerprint_type):
    assert resolve_fingerprint_profile(fingerprint_type).profile_hash == (
        EXPECTED_PROFILE_HASHES[fingerprint_type]
    )


def test_resolved_profile_is_read_only_and_defensively_copied():
    resolved = resolve_fingerprint_profile()
    original_profile = dict(resolved.profile)
    original_hash = resolved.profile_hash

    with pytest.raises(TypeError):
        resolved.profile["fp_size"] = 999

    resolved_again = resolve_fingerprint_profile()
    assert dict(resolved_again.profile) == original_profile
    assert resolved_again.profile_hash == original_hash


@pytest.mark.parametrize("fingerprint_type", IMPLEMENTED_ALGORITHMS)
def test_resolved_profile_and_hash_match_encoding(fingerprint_type):
    resolved = resolve_fingerprint_profile(fingerprint_type)
    result = encode_fingerprints(["CCCC"], fingerprint_type=fingerprint_type)

    assert resolved.profile == result.profile
    assert resolved.profile_hash == result.profile_hash


def test_custom_morgan_profile_resolves_completely():
    profile = MorganFingerprintProfile(
        radius=3,
        fp_size=128,
        include_chirality=True,
    )

    resolved = resolve_fingerprint_profile("morgan", profile)

    assert resolved.profile == profile.serialize()
    assert resolved.fp_size == 128
    assert resolved.profile_hash == encode_fingerprints(
        ["CCO"],
        profile,
    ).profile_hash


def test_resolver_rejects_morgan_profile_for_non_morgan_fingerprint():
    with pytest.raises(ValueError, match="only valid"):
        resolve_fingerprint_profile("maccs", MorganFingerprintProfile())


def test_resolver_rejects_unknown_fingerprint_type():
    with pytest.raises(ValueError, match="Unsupported fingerprint type"):
        resolve_fingerprint_profile("unknown")


def test_resolver_rejects_invalid_profile_object_type():
    with pytest.raises(
        TypeError,
        match="profile must be a MorganFingerprintProfile or None",
    ):
        resolve_fingerprint_profile("morgan", object())


@pytest.mark.parametrize("fingerprint_type", IMPLEMENTED_BINARY_ALGORITHMS)
def test_each_fingerprint_produces_binary_uint8_with_effective_profile(
    fingerprint_type,
):
    result = encode_fingerprints(
        ["CCCC"],
        fingerprint_type=fingerprint_type,
    )

    assert result.fingerprints.shape == (
        1,
        EXPECTED_WIDTHS[fingerprint_type],
    )
    assert result.fingerprints.dtype == np.uint8
    assert set(np.unique(result.fingerprints)).issubset({0, 1})
    assert np.flatnonzero(result.fingerprints[0]).tolist() == (
        EXPECTED_ACTIVE_BITS[fingerprint_type]
    )
    assert result.profile["algorithm"] == fingerprint_type
    assert result.profile["representation"] == "binary"
    assert result.profile["output_type"] == "binary-bit-vector"
    assert result.profile["dtype"] == "uint8"
    assert result.profile["fp_size"] == EXPECTED_WIDTHS[fingerprint_type]
    assert result.matrix_dtype == "uint8"
    assert isinstance(result.profile, dict)

@pytest.mark.parametrize("fingerprint_type", IMPLEMENTED_BINARY_ALGORITHMS)
def test_empty_input_preserves_selected_fingerprint_width(fingerprint_type):
    result = encode_fingerprints([], fingerprint_type=fingerprint_type)

    assert result.fingerprints.shape == (
        0,
        EXPECTED_WIDTHS[fingerprint_type],
    )
    assert result.matrix_dtype == "uint8"
    assert result.profile["algorithm"] == fingerprint_type


def test_non_morgan_fingerprint_rejects_morgan_profile():
    with pytest.raises(ValueError, match="only valid"):
        encode_fingerprints(
            ["CCO"],
            MorganFingerprintProfile(),
            fingerprint_type="maccs",
        )


def test_unknown_fingerprint_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported fingerprint type"):
        encode_fingerprints(["CCO"], fingerprint_type="unknown")


def test_klekota_roth_ordered_scientific_definition_is_frozen_and_compilable():
    pattern_text = (
        files("molraptor")
        .joinpath("_data", "klekota_roth_smarts.txt")
        .read_text(encoding="utf-8")
    )
    patterns = tuple(pattern_text.splitlines())

    assert len(patterns) == 4860
    assert all(patterns)
    assert hashlib.sha256("\n".join(patterns).encode("utf-8")).hexdigest() == (
        KLEKOTA_ROTH_PATTERN_SET_SHA256
    )
    assert all(Chem.MolFromSmarts(pattern) is not None for pattern in patterns)


@pytest.mark.parametrize(
    ("smiles", "expected_active_bits"),
    KLEKOTA_ROTH_ACTIVE_BITS.items(),
)
def test_klekota_roth_matches_frozen_active_bit_goldens(
    smiles,
    expected_active_bits,
):
    result = encode_fingerprints([smiles], fingerprint_type="klekotaroth")

    assert np.flatnonzero(result.fingerprints[0]).tolist() == expected_active_bits


def test_klekota_roth_profile_identifies_ordered_pattern_set():
    resolved = resolve_fingerprint_profile("klekotaroth")

    assert resolved.profile == {
        "profile_schema_version": "2.0",
        "algorithm": "klekotaroth",
        "representation": "binary",
        "output_type": "binary-bit-vector",
        "dtype": "uint8",
        "fp_size": 4860,
        "pattern_set": "cdk-klekota-roth-4860",
        "pattern_set_sha256": KLEKOTA_ROTH_PATTERN_SET_SHA256,
        "matching_policy": "rdkit-has-substruct-match",
    }
    assert resolved.profile_hash == EXPECTED_PROFILE_HASHES["klekotaroth"]


def test_klekota_roth_isolates_invalid_input_and_preserves_duplicates():
    ordered_smiles = ("CCCC", "not-a-smiles", "CCO", "CCCC")
    result = encode_fingerprints(
        ordered_smiles,
        fingerprint_type="klekotaroth",
    )
    valid_only = encode_fingerprints(
        ("CCCC", "CCO", "CCCC"),
        fingerprint_type="klekotaroth",
    )

    np.testing.assert_array_equal(result.fingerprints, valid_only.fingerprints)
    np.testing.assert_array_equal(result.fingerprints[0], result.fingerprints[2])
    assert result.fingerprints.shape == (3, 4860)
    assert result.fingerprints.dtype == np.uint8
    assert result.valid_indices == (0, 2, 3)
    assert result.valid_count == 3
    assert result.invalid_count == 1
    assert [status.status for status in result.input_statuses] == [
        "valid",
        "invalid",
        "valid",
        "valid",
    ]
    assert [status.fingerprint_index for status in result.input_statuses] == [
        0,
        None,
        1,
        2,
    ]
    assert [status.invalid_reason for status in result.input_statuses] == [
        None,
        "parse_failure",
        None,
        None,
    ]
