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

EXPECTED_PROFILE_HASHES = {
    "morgan": "67a59787be47c622ba3dec767773eff1105a92d3e7750f0e774c8a118685f001",
    "featmorgan": "6cb16696e3ed2f47eb0a24733ccbc45f628b652eda9c8f45642779fd863b01f4",
    "atompair": "ce06b3ff95e75c52bc7c782d02a779614e173f0ffff2a7bc0a20d0fad41eba35",
    "rdk": "f5c9c48b6966c7fc6c746f7f7404d9b8065e10a95bd66babd9c5e870435e37ab",
    "torsion": "74c493a4ab9092c27a9cc9a57ba50375923d7326f2bcbad5645e5c268e7d8074",
    "layered": "b07e4d68d8bd60635f37a958d49dc366b742668202b382e5ec4d7854890c3f68",
    "maccs": "a8754b05298989da2d1fb53a0fbda098b095a6dc0186a36fee469465f73b30f3",
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
    )
    assert tuple(FINGERPRINT_PARAMETERS) == FINGERPRINT_TYPES


def test_declared_parameters_are_read_only():
    with pytest.raises(TypeError):
        FINGERPRINT_PARAMETERS["morgan"]["radius"] = 3


@pytest.mark.parametrize("fingerprint_type", FINGERPRINT_TYPES)
def test_resolve_each_fingerprint_profile_without_encoding(fingerprint_type):
    resolved = resolve_fingerprint_profile(fingerprint_type)

    assert isinstance(resolved, ResolvedFingerprintProfile)
    assert resolved.fingerprint_type == fingerprint_type
    assert resolved.profile["algorithm"] == fingerprint_type
    assert resolved.profile["output_type"] == "binary-bit-vector"
    assert resolved.fp_size == EXPECTED_WIDTHS[fingerprint_type]


@pytest.mark.parametrize("fingerprint_type", FINGERPRINT_TYPES)
def test_default_profile_hash_matches_v040_golden_value(fingerprint_type):
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


@pytest.mark.parametrize("fingerprint_type", FINGERPRINT_TYPES)
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


@pytest.mark.parametrize("fingerprint_type", FINGERPRINT_TYPES)
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

@pytest.mark.parametrize("fingerprint_type", FINGERPRINT_TYPES)
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
