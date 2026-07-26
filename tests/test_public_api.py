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
        FINGERPRINT_TYPES,
        FingerprintEncodingResult,
        FingerprintInputStatus,
        FingerprintType,
        MorganFingerprintProfile,
        ResolvedFingerprintProfile,
        encode_fingerprints,
        resolve_fingerprint_profile,
    )

    assert FingerprintType is not None
    assert len(FINGERPRINT_TYPES) == 7
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
