# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for molraptor public API."""

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


def test_dunder_all_contains_expected_symbols():
    expected = {
        "__version__",
        "MolraptorConfig",
        "run",
        "validate_config",
        "DataValidator",
    }
    assert set(molraptor.__all__) == expected


def test_private_classes_not_in_dunder_all():
    assert "_MolraptorPipeline" not in molraptor.__all__
    assert "ResultManager" not in molraptor.__all__
    assert "FetchStep" not in molraptor.__all__
    assert "CurateStep" not in molraptor.__all__
    assert "FingerprintStep" not in molraptor.__all__