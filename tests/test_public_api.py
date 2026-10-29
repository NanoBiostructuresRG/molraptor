# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for molraptor public API."""

import importlib.util

import molraptor


def test_version_importable():
    from molraptor import __version__
    assert isinstance(__version__, str)


def test_config_importable():
    from molraptor import MolraptorConfig
    assert MolraptorConfig is not None


def test_run_importable():
    from molraptor import run
    assert callable(run)


def test_validate_config_importable():
    from molraptor import validate_config
    assert callable(validate_config)


def test_data_validator_importable():
    from molraptor import DataValidator
    assert DataValidator is not None


def test_morgan_fingerprint_api_importable():
    from molraptor import (
        ALLOWED_REPRESENTATIONS,
        DEFAULT_REPRESENTATIONS,
        FINGERPRINT_ALGORITHMS,
        FINGERPRINT_REPRESENTATIONS,
        FINGERPRINT_TYPES,
        FingerprintAlgorithm,
        FingerprintEncodingResult,
        FingerprintInputStatus,
        FingerprintRepresentation,
        FingerprintType,
        MorganFingerprintProfile,
        ResolvedFingerprintProfile,
        encode_fingerprints,
        resolve_fingerprint_profile,
    )

    assert FingerprintType is FingerprintAlgorithm
    assert FINGERPRINT_TYPES is FINGERPRINT_ALGORITHMS
    assert len(FINGERPRINT_ALGORITHMS) == 9
    assert len(FINGERPRINT_REPRESENTATIONS) == 3
    assert len(ALLOWED_REPRESENTATIONS) == 9
    assert len(DEFAULT_REPRESENTATIONS) == 9
    assert FingerprintRepresentation is not None
    assert FingerprintEncodingResult is not None
    assert FingerprintInputStatus is not None
    assert MorganFingerprintProfile is not None
    assert ResolvedFingerprintProfile is not None
    assert callable(encode_fingerprints)
    assert callable(resolve_fingerprint_profile)


def test_dunder_all_contains_expected_symbols():
    expected = {
        "__version__",
        "MolraptorConfig",
        "run",
        "validate_config",
        "DataValidator",
        "FingerprintAlgorithm",
        "FingerprintRepresentation",
        "FINGERPRINT_ALGORITHMS",
        "FINGERPRINT_REPRESENTATIONS",
        "ALLOWED_REPRESENTATIONS",
        "DEFAULT_REPRESENTATIONS",
        "FingerprintType",
        "FINGERPRINT_TYPES",
        "MorganFingerprintProfile",
        "ResolvedFingerprintProfile",
        "FingerprintEncodingResult",
        "FingerprintInputStatus",
        "resolve_fingerprint_profile",
        "encode_fingerprints",
    }
    assert set(molraptor.__all__) == expected


def test_file_workflow_class_not_in_dunder_all():
    assert "FingerprintStep" not in molraptor.__all__


def test_legacy_scientific_modules_are_removed():
    assert importlib.util.find_spec("molraptor.morgan") is None
    assert importlib.util.find_spec("molraptor.fingerprint") is None
