# SPDX-License-Identifier: LGPL-3.0-or-later
"""RED contract tests for v0.5.0 algorithm/representation separation."""

from __future__ import annotations

import inspect

import molraptor
import pytest

from molraptor import fingerprints


EXPECTED_ALGORITHMS = (
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
EXPECTED_REPRESENTATIONS = ("binary", "count", "minhash")
EXPECTED_ALGORITHM_REPRESENTATIONS = {
    "morgan": "binary",
    "featmorgan": "binary",
    "atompair": "count",
    "rdk": "binary",
    "torsion": "count",
    "layered": "binary",
    "maccs": "binary",
    "klekotaroth": "binary",
    "mhfp6": "minhash",
    "map4": "minhash",
}
EXPECTED_RESOLVED_CONTRACTS = (
    ("morgan", "binary", 2048),
    ("featmorgan", "binary", 2048),
    ("atompair", "count", 2048),
    ("rdk", "binary", 2048),
    ("torsion", "count", 2048),
    ("layered", "binary", 2048),
    ("maccs", "binary", 167),
    ("klekotaroth", "binary", 4860),
    ("mhfp6", "minhash", 2048),
    ("map4", "minhash", 1024),
)
EXPECTED_REPRESENTATION_SEMANTICS = {
    "binary": ("binary-bit-vector", "uint8"),
    "count": ("count-vector", "uint32"),
    "minhash": ("minhash-sketch", "uint32"),
}
def test_v050_contract_names_are_public():
    required_names = {
        "FingerprintAlgorithm",
        "FingerprintRepresentation",
        "FINGERPRINT_ALGORITHMS",
        "FINGERPRINT_REPRESENTATIONS",
        "ALGORITHM_REPRESENTATIONS",
    }

    assert required_names <= set(molraptor.__all__)
    for name in required_names:
        assert getattr(molraptor, name) is getattr(fingerprints, name)


def test_unreleased_combinatorial_representation_names_are_not_public():
    for name in ("ALLOWED_REPRESENTATIONS", "DEFAULT_REPRESENTATIONS"):
        assert name not in molraptor.__all__
        assert not hasattr(molraptor, name)
        assert not hasattr(fingerprints, name)


def test_algorithm_and_representation_registries_are_independent():
    assert fingerprints.FINGERPRINT_ALGORITHMS == EXPECTED_ALGORITHMS
    assert fingerprints.FINGERPRINT_REPRESENTATIONS == EXPECTED_REPRESENTATIONS

    assert tuple(fingerprints.ALGORITHM_REPRESENTATIONS) == EXPECTED_ALGORITHMS
    assert dict(fingerprints.ALGORITHM_REPRESENTATIONS) == (
        EXPECTED_ALGORITHM_REPRESENTATIONS
    )


def test_legacy_fingerprint_type_names_are_compatibility_aliases():
    assert fingerprints.FingerprintType is fingerprints.FingerprintAlgorithm
    assert fingerprints.FINGERPRINT_TYPES is fingerprints.FINGERPRINT_ALGORITHMS
    assert molraptor.FingerprintType is molraptor.FingerprintAlgorithm
    assert molraptor.FINGERPRINT_TYPES is molraptor.FINGERPRINT_ALGORITHMS


@pytest.mark.parametrize(
    ("algorithm", "representation", "width"),
    EXPECTED_RESOLVED_CONTRACTS,
)
def test_approved_algorithm_representation_contract_resolves(
    algorithm,
    representation,
    width,
):
    resolved = fingerprints.resolve_fingerprint_profile(
        algorithm,
    )

    assert resolved.profile["algorithm"] == algorithm
    assert resolved.profile["representation"] == representation
    assert resolved.width == width


@pytest.mark.parametrize(
    ("algorithm", "representation"),
    EXPECTED_ALGORITHM_REPRESENTATIONS.items(),
)
def test_algorithm_resolves_to_its_single_representation(
    algorithm,
    representation,
):
    resolved = fingerprints.resolve_fingerprint_profile(algorithm)

    assert resolved.representation == representation
    assert resolved.profile["representation"] == representation


def test_representation_is_not_a_public_function_parameter():
    assert "representation" not in inspect.signature(
        fingerprints.resolve_fingerprint_profile
    ).parameters
    assert "representation" not in inspect.signature(
        fingerprints.encode_fingerprints
    ).parameters


@pytest.mark.parametrize(
    ("representation", "expected_output_type", "expected_dtype"),
    (
        (representation, *semantics)
        for representation, semantics in EXPECTED_REPRESENTATION_SEMANTICS.items()
    ),
)
def test_resolved_profile_declares_representation_semantics(
    representation,
    expected_output_type,
    expected_dtype,
):
    representative_algorithm = {
        "binary": "morgan",
        "count": "atompair",
        "minhash": "mhfp6",
    }[representation]

    resolved = fingerprints.resolve_fingerprint_profile(
        representative_algorithm,
    )

    assert resolved.profile["output_type"] == expected_output_type
    assert resolved.profile["dtype"] == expected_dtype


def test_representation_aware_profiles_use_schema_version_2():
    for algorithm, representation, _width in EXPECTED_RESOLVED_CONTRACTS:
        resolved = fingerprints.resolve_fingerprint_profile(
            algorithm,
        )

        assert resolved.profile["profile_schema_version"] == "2.0"


@pytest.mark.parametrize(
    ("algorithm", "representation"),
    (
        ("map4", "minhash"),
    ),
)
def test_metadata_only_contract_fails_explicitly_at_encoding_boundary(
    algorithm,
    representation,
):
    with pytest.raises(
        NotImplementedError,
        match=rf"{algorithm}/{representation}",
    ):
        fingerprints.encode_fingerprints(
            ["CCO"],
            fingerprint_type=algorithm,
        )
