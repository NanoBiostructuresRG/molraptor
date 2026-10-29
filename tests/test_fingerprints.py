# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the multi-fingerprint in-memory scientific core."""

import numpy as np
import pytest

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
}
EXISTING_BINARY_ALGORITHMS = tuple(EXPECTED_WIDTHS)

EXPECTED_PROFILE_HASHES = {
    "morgan": "17669bc488012071ce9586dd5f07aefd61aa6aeade17f21d939b6165a9500379",
    "featmorgan": "3060d22e79d0641e755b2ba785a29f882d6574e99b08d47cc75cdc8cac7440fe",
    "atompair": "f138470b9482cf4bc20f7e011f4a9e8b5ebb5b17bb4ab79b435c8023874f7a95",
    "rdk": "d792039b93db7a2e058bf2c493c55b11a7f3f8ab52822bc3e4a6e8b841da88ac",
    "torsion": "39c5a2b2ad9318edf19e7e9add7696bad40833547a7af368d176717cc8691550",
    "layered": "ae084c047f65c267995a1483db1605b22701608b0c5b3545029e777fe2dd0a6f",
    "maccs": "fd662cb09e38c85089670d3c7bca885261c04936a326d4b0b7807a9ba104488d",
}

EXPECTED_ACTIVE_BITS = {
    "morgan": [80, 294, 640, 794, 1057],
    "featmorgan": [0, 539, 792, 1085],
    "atompair": [880, 1144, 1145, 1336, 1404, 1405],
    "rdk": [709, 875, 1308, 1772, 1813, 1927],
    "torsion": [60],
    "layered": [
        311, 333, 354, 360, 596, 610, 611, 674, 867, 993,
        1044, 1111, 1493, 1742, 1783,
    ],
    "maccs": [114, 115, 118, 147, 149, 155, 160],
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
        "map4",
    )
    assert tuple(FINGERPRINT_PARAMETERS) == FINGERPRINT_TYPES


def test_declared_parameters_are_read_only():
    with pytest.raises(TypeError):
        FINGERPRINT_PARAMETERS["morgan"]["radius"] = 3


@pytest.mark.parametrize("fingerprint_type", EXISTING_BINARY_ALGORITHMS)
def test_resolve_each_fingerprint_profile_without_encoding(fingerprint_type):
    resolved = resolve_fingerprint_profile(fingerprint_type)

    assert isinstance(resolved, ResolvedFingerprintProfile)
    assert resolved.fingerprint_type == fingerprint_type
    assert resolved.profile["algorithm"] == fingerprint_type
    assert resolved.profile["representation"] == "binary"
    assert resolved.profile["output_type"] == "binary-bit-vector"
    assert resolved.profile["dtype"] == "uint8"
    assert resolved.width == EXPECTED_WIDTHS[fingerprint_type]
    assert resolved.fp_size == resolved.width


@pytest.mark.parametrize("fingerprint_type", EXISTING_BINARY_ALGORITHMS)
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


@pytest.mark.parametrize("fingerprint_type", EXISTING_BINARY_ALGORITHMS)
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


@pytest.mark.parametrize("fingerprint_type", EXISTING_BINARY_ALGORITHMS)
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
    assert result.profile["output_type"] == "binary-bit-vector"
    assert result.profile["fp_size"] == EXPECTED_WIDTHS[fingerprint_type]
    assert isinstance(result.profile, dict)

@pytest.mark.parametrize("fingerprint_type", EXISTING_BINARY_ALGORITHMS)
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
