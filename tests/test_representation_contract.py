# SPDX-License-Identifier: LGPL-3.0-or-later
"""RED contract tests for v0.5.0 algorithm/representation separation."""

from __future__ import annotations

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
    "map4",
)
EXPECTED_REPRESENTATIONS = ("binary", "count", "minhash")
EXPECTED_ALLOWED_REPRESENTATIONS = {
    "morgan": ("binary",),
    "featmorgan": ("binary",),
    "atompair": ("binary", "count"),
    "rdk": ("binary",),
    "torsion": ("binary", "count"),
    "layered": ("binary",),
    "maccs": ("binary",),
    "klekotaroth": ("binary",),
    "map4": ("minhash",),
}
EXPECTED_DEFAULT_REPRESENTATIONS = {
    "morgan": "binary",
    "featmorgan": "binary",
    "atompair": "binary",
    "rdk": "binary",
    "torsion": "binary",
    "layered": "binary",
    "maccs": "binary",
    "klekotaroth": "binary",
    "map4": "minhash",
}
EXPECTED_RESOLVED_CONTRACTS = (
    ("morgan", "binary", 2048),
    ("featmorgan", "binary", 2048),
    ("atompair", "binary", 2048),
    ("atompair", "count", 2048),
    ("rdk", "binary", 2048),
    ("torsion", "binary", 2048),
    ("torsion", "count", 2048),
    ("layered", "binary", 2048),
    ("maccs", "binary", 167),
    ("klekotaroth", "binary", 4860),
    ("map4", "minhash", 1024),
)
EXPECTED_REPRESENTATION_SEMANTICS = {
    "binary": ("binary-bit-vector", "uint8"),
    "count": ("count-vector", "uint32"),
    "minhash": ("minhash-sketch", "uint32"),
}
REJECTED_COMBINATIONS = (
    ("morgan", "count"),
    ("morgan", "minhash"),
    ("featmorgan", "count"),
    ("maccs", "count"),
    ("klekotaroth", "count"),
    ("klekotaroth", "minhash"),
    ("map4", "binary"),
    ("map4", "count"),
    ("atompair", "minhash"),
    ("torsion", "minhash"),
    ("rdk", "count"),
    ("layered", "count"),
)


def test_v050_contract_names_are_public():
    required_names = {
        "FingerprintAlgorithm",
        "FingerprintRepresentation",
        "FINGERPRINT_ALGORITHMS",
        "FINGERPRINT_REPRESENTATIONS",
        "ALLOWED_REPRESENTATIONS",
        "DEFAULT_REPRESENTATIONS",
    }

    assert required_names <= set(molraptor.__all__)
    for name in required_names:
        assert getattr(molraptor, name) is getattr(fingerprints, name)


def test_algorithm_and_representation_registries_are_independent():
    assert fingerprints.FINGERPRINT_ALGORITHMS == EXPECTED_ALGORITHMS
    assert fingerprints.FINGERPRINT_REPRESENTATIONS == EXPECTED_REPRESENTATIONS

    allowed = fingerprints.ALLOWED_REPRESENTATIONS
    assert tuple(allowed) == EXPECTED_ALGORITHMS
    assert {
        algorithm: tuple(allowed[algorithm]) for algorithm in allowed
    } == EXPECTED_ALLOWED_REPRESENTATIONS
    assert dict(fingerprints.DEFAULT_REPRESENTATIONS) == (
        EXPECTED_DEFAULT_REPRESENTATIONS
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
        representation=representation,
    )

    assert resolved.profile["algorithm"] == algorithm
    assert resolved.profile["representation"] == representation
    assert resolved.width == width


@pytest.mark.parametrize(
    ("algorithm", "representation"),
    REJECTED_COMBINATIONS,
)
def test_unapproved_algorithm_representation_contract_is_rejected(
    algorithm,
    representation,
):
    with pytest.raises(ValueError):
        fingerprints.resolve_fingerprint_profile(
            algorithm,
            representation=representation,
        )


@pytest.mark.parametrize(
    ("algorithm", "default_representation"),
    EXPECTED_DEFAULT_REPRESENTATIONS.items(),
)
def test_omitted_representation_resolves_to_algorithm_default(
    algorithm,
    default_representation,
):
    resolved = fingerprints.resolve_fingerprint_profile(algorithm)

    assert resolved.profile["representation"] == default_representation


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
        "minhash": "map4",
    }[representation]

    resolved = fingerprints.resolve_fingerprint_profile(
        representative_algorithm,
        representation=representation,
    )

    assert resolved.profile["output_type"] == expected_output_type
    assert resolved.profile["dtype"] == expected_dtype


def test_representation_aware_profiles_use_schema_version_2():
    for algorithm, representation, _width in EXPECTED_RESOLVED_CONTRACTS:
        resolved = fingerprints.resolve_fingerprint_profile(
            algorithm,
            representation=representation,
        )

        assert resolved.profile["profile_schema_version"] == "2.0"


@pytest.mark.parametrize(
    ("algorithm", "representation"),
    (
        ("atompair", "count"),
        ("torsion", "count"),
        ("klekotaroth", "binary"),
        ("map4", "minhash"),
    ),
)
def test_metadata_only_contracts_fail_explicitly_at_encoding_boundary(
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
            representation=representation,
        )
