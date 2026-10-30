# SPDX-License-Identifier: LGPL-3.0-or-later
"""Scientific regression tests for original MAP4 with RDKit MinHash."""

import hashlib

import numpy as np
import pytest
from rdkit import Chem
from rdkit.Chem.rdMHFPFingerprint import MHFPEncoder

from molraptor import encode_fingerprints, resolve_fingerprint_profile
from molraptor._map4 import _get_map4_shingles


REFERENCE_SMILES = ("CCCC", "CCO", "c1ccccc1")
EXPECTED_SHINGLES = {
    "CCCC": [
        "C(C)CC|1|C(C)CC",
        "C(C)CC|1|CCC",
        "C(C)CC|2|CCC",
        "C(C)C|1|C(C)C",
        "C(C)C|1|CC",
        "C(C)C|2|CC",
        "CCC|3|CCC",
        "CC|3|CC",
    ],
    "CCO": [
        "C(C)O|1|CC",
        "C(C)O|1|OC",
        "CCO|2|OCC",
        "CC|2|OC",
        "|1|CCO",
        "|1|OCC",
    ],
    "c1ccccc1": [
        "c(c)c|1|c(c)c",
        "c(c)c|2|c(c)c",
        "c(c)c|3|c(c)c",
        "c(cc)cc|1|c(cc)cc",
        "c(cc)cc|2|c(cc)cc",
        "c(cc)cc|3|c(cc)cc",
    ],
}
EXPECTED_PROFILE = {
    "profile_schema_version": "2.0",
    "algorithm": "map4",
    "representation": "minhash",
    "output_type": "minhash-sketch",
    "dtype": "uint32",
    "fp_size": 1024,
    "radius": 2,
    "include_chirality": False,
    "include_duplicate_shingles": False,
    "seed": 42,
    "shingle_policy": "map4-atom-pair-circular-environment",
    "minhash_backend": "rdkit.Chem.rdMHFPFingerprint.MHFPEncoder",
}
EXPECTED_PROFILE_HASH = (
    "8d72745a4a74c7d29be383cfe3c0f331334778e7a09ee9cf08bd4a86ff57610e"
)
EXPECTED_REGRESSION_EVIDENCE = {
    "CCCC": {
        "sha256": ("41ad417032253e61c2505372b7426493aad93a9f234dc4d1ab20def24ad7edd4"),
        "first10": [
            956313146,
            599483974,
            771882154,
            154309972,
            997933113,
            10312194,
            378166198,
            17531596,
            184718955,
            233998818,
        ],
        "last10": [
            239961599,
            655209002,
            185019097,
            770147049,
            325517072,
            21068178,
            303257772,
            773214518,
            159416935,
            5800890,
        ],
    },
    "CCO": {
        "sha256": ("97fe80622307bee3951d704a2391e99e1dec0d3e84b9ea5ca1bd7d2a2534fe08"),
        "first10": [
            176029306,
            514704511,
            488611730,
            783178993,
            116878059,
            398394537,
            1140345333,
            44587852,
            36454347,
            220192114,
        ],
        "last10": [
            911311227,
            694616898,
            1005103376,
            1186494794,
            531715712,
            154374042,
            485740088,
            433706559,
            288245751,
            634613044,
        ],
    },
    "c1ccccc1": {
        "sha256": ("0af90a4119f83530fe4a0db47eb653ce207aa783d8cbb148de664b818fcb46b7"),
        "first10": [
            369947857,
            452314680,
            100182842,
            182778901,
            507807079,
            211085477,
            2104383326,
            107158308,
            108720539,
            1480331826,
        ],
        "last10": [
            513442407,
            1150004,
            40164860,
            899427234,
            417305630,
            1707956234,
            903467902,
            1182072010,
            246056887,
            874354398,
        ],
    },
}


def _direct_rdkit_rows(smiles=REFERENCE_SMILES):
    encoder = MHFPEncoder(1024, 42)
    return np.vstack(
        [
            np.asarray(
                encoder.FromStringArray(_get_map4_shingles(Chem.MolFromSmiles(value))),
                dtype=np.uint32,
            )
            for value in smiles
        ]
    )


@pytest.mark.parametrize(
    ("smiles", "expected_shingles"),
    EXPECTED_SHINGLES.items(),
)
def test_map4_generates_exact_original_shingles(smiles, expected_shingles):
    molecule = Chem.MolFromSmiles(smiles)

    assert _get_map4_shingles(molecule) == expected_shingles


def test_map4_profile_declares_complete_fixed_semantics():
    resolved = resolve_fingerprint_profile("map4")
    result = encode_fingerprints(["CCCC"], fingerprint_type="map4")

    assert dict(resolved.profile) == EXPECTED_PROFILE
    assert resolved.width == 1024
    assert resolved.profile_hash == EXPECTED_PROFILE_HASH
    assert result.profile == EXPECTED_PROFILE
    assert result.profile_hash == EXPECTED_PROFILE_HASH
    assert result.profile["representation"] == "minhash"
    assert result.profile["output_type"] == "minhash-sketch"
    assert result.matrix_dtype == "uint32"


def test_map4_matches_complete_direct_rdkit_minhash_rows():
    result = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type="map4",
    )
    expected = _direct_rdkit_rows()

    assert expected.shape == (3, 1024)
    assert expected.dtype == np.uint32
    assert result.fingerprints.shape == (3, 1024)
    assert result.fingerprints.dtype == np.uint32
    np.testing.assert_array_equal(result.fingerprints, expected)


def test_map4_frozen_regression_evidence_matches_direct_backend():
    rows = _direct_rdkit_rows()

    for smiles, row in zip(REFERENCE_SMILES, rows, strict=True):
        evidence = EXPECTED_REGRESSION_EVIDENCE[smiles]
        assert (
            hashlib.sha256(np.ascontiguousarray(row).tobytes()).hexdigest()
            == evidence["sha256"]
        )
        assert row[:10].tolist() == evidence["first10"]
        assert row[-10:].tolist() == evidence["last10"]


def test_map4_repeated_calls_are_deterministic():
    first = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type="map4",
    )
    second = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type="map4",
    )

    np.testing.assert_array_equal(first.fingerprints, second.fingerprints)
    assert first.profile_hash == second.profile_hash
    assert first.ordered_input_hash == second.ordered_input_hash


def test_map4_isolates_invalid_input_and_preserves_duplicate_alignment():
    ordered_smiles = ("CCCC", "not-a-smiles", "CCO", "CCCC")
    result = encode_fingerprints(
        ordered_smiles,
        fingerprint_type="map4",
    )
    valid_only = encode_fingerprints(
        ("CCCC", "CCO", "CCCC"),
        fingerprint_type="map4",
    )

    np.testing.assert_array_equal(result.fingerprints, valid_only.fingerprints)
    np.testing.assert_array_equal(result.fingerprints[0], result.fingerprints[2])
    assert result.fingerprints.shape == (3, 1024)
    assert result.fingerprints.dtype == np.uint32
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


def test_all_invalid_map4_input_preserves_width_and_uint32_dtype():
    result = encode_fingerprints(
        ("not-a-smiles", ""),
        fingerprint_type="map4",
    )

    assert result.fingerprints.shape == (0, 1024)
    assert result.fingerprints.dtype == np.uint32
    assert result.matrix_shape == (0, 1024)
    assert result.matrix_dtype == "uint32"
    assert result.valid_indices == ()
    assert result.valid_count == 0
    assert result.invalid_count == 2


def test_map4_and_mhfp6_are_distinct_minhash_algorithms():
    map4 = encode_fingerprints(["CCCC"], fingerprint_type="map4")
    mhfp6 = encode_fingerprints(["CCCC"], fingerprint_type="mhfp6")

    assert map4.profile["representation"] == "minhash"
    assert mhfp6.profile["representation"] == "minhash"
    assert map4.profile["algorithm"] == "map4"
    assert mhfp6.profile["algorithm"] == "mhfp6"
    assert map4.fingerprints.shape == (1, 1024)
    assert mhfp6.fingerprints.shape == (1, 2048)
    assert map4.fingerprints.dtype == np.uint32
    assert mhfp6.fingerprints.dtype == np.uint32
    assert mhfp6.profile_hash == (
        "0326a002f5996daa9027c3f875c4ad4078d23fb579aa82b8bf9c30340f847ef8"
    )
