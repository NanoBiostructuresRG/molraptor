# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the multi-fingerprint in-memory scientific core."""

import numpy as np
import pytest

from molraptor import MorganFingerprintProfile, encode_fingerprints
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
