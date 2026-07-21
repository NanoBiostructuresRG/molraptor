# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the public workflow facade."""

from unittest.mock import MagicMock, patch

import pytest

from molraptor import MorganFingerprintProfile
from molraptor.config import MolraptorConfig
from molraptor.pipeline import run, validate_config


@pytest.fixture
def workflow_config(tmp_path):
    return MolraptorConfig(
        input_path=tmp_path / "molecules.csv",
        output_dir=tmp_path / "artifacts",
        profile=MorganFingerprintProfile(fp_size=64),
    )


def test_validate_config_returns_same_config(workflow_config):
    assert validate_config(workflow_config) is workflow_config


def test_validate_config_raises_on_wrong_type():
    with pytest.raises(ValueError, match="MolraptorConfig"):
        validate_config("not a config")


def test_run_executes_the_only_file_workflow(workflow_config):
    expected_result = MagicMock()
    step = MagicMock()
    step.run.return_value = expected_result

    with patch("molraptor.pipeline.FingerprintStep", return_value=step) as step_cls:
        result = run(workflow_config)

    step_cls.assert_called_once_with(workflow_config)
    step.run.assert_called_once_with()
    assert result is expected_result
