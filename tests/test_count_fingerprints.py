# SPDX-License-Identifier: LGPL-3.0-or-later
"""Scientific regression tests for fixed-width count representations."""

import numpy as np
import pytest
from rdkit import Chem
from rdkit.Chem.rdFingerprintGenerator import (
    GetAtomPairGenerator,
    GetTopologicalTorsionGenerator,
)

from molraptor import encode_fingerprints, resolve_fingerprint_profile


REFERENCE_SMILES = ("CCCC", "CCO", "c1ccccc1")
EXPECTED_COUNT_GOLDENS = {
    "atompair": (
        ([1310, 1358, 1375, 1756], [2, 1, 2, 1], 6, 2),
        ([1375, 1423, 1503], [1, 1, 1], 3, 1),
        ([255, 311, 374], [3, 6, 6], 15, 6),
    ),
    "torsion": (
        ([15], [1], 1, 1),
        ([], [], 0, 0),
        ([1539], [6], 6, 6),
    ),
}


def _reference_count_generator(algorithm):
    if algorithm == "atompair":
        return GetAtomPairGenerator(
            minDistance=1,
            maxDistance=30,
            includeChirality=False,
            use2D=True,
            fpSize=2048,
        )
    return GetTopologicalTorsionGenerator(
        includeChirality=False,
        torsionAtomCount=4,
        fpSize=2048,
    )


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_count_panel_has_fixed_width_uint32_nonnegative_integer_values(
    algorithm,
):
    result = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type=algorithm,
    )

    assert result.fingerprints.shape == (3, 2048)
    assert result.fingerprints.dtype == np.uint32
    assert result.matrix_shape == (3, 2048)
    assert result.matrix_dtype == "uint32"
    assert np.issubdtype(result.fingerprints.dtype, np.integer)
    assert np.all(result.fingerprints >= 0)
    assert result.fingerprints.max() > 1


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_count_panel_matches_measured_nonzero_bin_and_count_goldens(algorithm):
    result = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type=algorithm,
    )

    for row, (indices, counts, total, maximum) in zip(
        result.fingerprints,
        EXPECTED_COUNT_GOLDENS[algorithm],
        strict=True,
    ):
        nonzero = np.flatnonzero(row)
        assert nonzero.tolist() == indices
        assert row[nonzero].tolist() == counts
        assert int(row.sum()) == total
        assert int(row.max()) == maximum


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_count_panel_exactly_matches_direct_rdkit_count_api(algorithm):
    result = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type=algorithm,
    )
    generator = _reference_count_generator(algorithm)

    expected = np.vstack(
        [
            generator.GetCountFingerprintAsNumPy(Chem.MolFromSmiles(smiles))
            for smiles in REFERENCE_SMILES
        ]
    )

    assert expected.dtype == np.uint32
    np.testing.assert_array_equal(result.fingerprints, expected)


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_empty_count_input_preserves_width_and_uint32_dtype(algorithm):
    result = encode_fingerprints(
        [],
        fingerprint_type=algorithm,
    )

    assert result.fingerprints.shape == (0, 2048)
    assert result.fingerprints.dtype == np.uint32
    assert result.matrix_shape == (0, 2048)
    assert result.matrix_dtype == "uint32"


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_invalid_smiles_are_isolated_from_count_rows(algorithm):
    ordered_smiles = ("CCCC", "not-a-smiles", "CCO", "")
    result = encode_fingerprints(
        ordered_smiles,
        fingerprint_type=algorithm,
    )
    valid_only = encode_fingerprints(
        ("CCCC", "CCO"),
        fingerprint_type=algorithm,
    )

    np.testing.assert_array_equal(result.fingerprints, valid_only.fingerprints)
    assert result.valid_indices == (0, 2)
    assert result.valid_count == 2
    assert result.invalid_count == 2
    assert [status.status for status in result.input_statuses] == [
        "valid",
        "invalid",
        "valid",
        "invalid",
    ]
    assert [status.fingerprint_index for status in result.input_statuses] == [
        0,
        None,
        1,
        None,
    ]
    assert [status.invalid_reason for status in result.input_statuses] == [
        None,
        "parse_failure",
        None,
        "empty_molecule",
    ]


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_input_hash_is_algorithm_independent_but_profile_hash_is_not(
    algorithm,
):
    morgan = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type="morgan",
    )
    count = encode_fingerprints(
        REFERENCE_SMILES,
        fingerprint_type=algorithm,
    )

    assert morgan.ordered_input_hash == count.ordered_input_hash
    assert morgan.profile_hash != count.profile_hash


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_count_profile_metadata_declares_semantics_and_width(algorithm):
    resolved = resolve_fingerprint_profile(algorithm)
    result = encode_fingerprints(
        ["CCCC"],
        fingerprint_type=algorithm,
    )

    assert resolved.width == 2048
    assert result.profile == resolved.profile
    assert result.profile["algorithm"] == algorithm
    assert result.profile["representation"] == "count"
    assert result.profile["output_type"] == "count-vector"
    assert result.profile["dtype"] == "uint32"
    assert result.profile["fp_size"] == 2048
    assert "count_simulation" not in result.profile


@pytest.mark.parametrize("algorithm", ("atompair", "torsion"))
def test_v050_algorithm_selection_intentionally_returns_count_not_binary(
    algorithm,
):
    result = encode_fingerprints(
        ["CCCC"],
        fingerprint_type=algorithm,
    )

    assert result.fingerprints.shape == (1, 2048)
    assert result.fingerprints.dtype == np.uint32
    assert result.fingerprints.dtype != np.uint8
    assert result.profile["representation"] == "count"
    assert result.profile["representation"] != "binary"
    assert result.profile["output_type"] == "count-vector"
    assert result.profile["dtype"] == "uint32"
