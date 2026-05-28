# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for molraptor.pipeline."""

import pytest
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from molraptor.config import MolraptorConfig
from molraptor.pipeline import validate_config, run


@pytest.fixture
def valid_config(tmp_path):
    """Write a minimal valid YAML config and return a loaded MolraptorConfig."""
    (tmp_path / "dataset.csv").write_text("PubChem CID,Label\n1,0\n2,1\n")
    config = {
        "paths": {
            "raw_input_file": str(tmp_path / "dataset.csv"),
            "raw_output_file": str(tmp_path / "properties.csv"),
            "curated_output_file": str(tmp_path / "curated.csv"),
            "error_log_file": str(tmp_path / "errors.txt"),
            "fingerprint_output_file": str(tmp_path / "morgan_fp.csv"),
            "fingerprint_array_file": str(tmp_path / "morgan_db.npy"),
            "labels_output_file": str(tmp_path / "labels.npy"),
        },
        "pubchem": {
            "properties": ["MolecularWeight", "SMILES"],
            "timeout": 5,
            "max_retries": 3,
            "sleep_seconds": 0.2,
            "chunk_size": 400,
        },
        "fingerprint": {"radius": 2, "size": 1024},
        "curate": {
            "required_columns": ["PubChem CID", "Label", "SMILES"],
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))
    return MolraptorConfig.load(path)


def test_validate_config_returns_config(valid_config):
    result = validate_config(valid_config)
    assert isinstance(result, MolraptorConfig)


def test_validate_config_returns_same_config(valid_config):
    result = validate_config(valid_config)
    assert result is valid_config


def test_validate_config_raises_on_wrong_type():
    with pytest.raises(ValueError, match="MolraptorConfig"):
        validate_config("not a config")


def test_validate_config_accepts_none(tmp_path, monkeypatch):
    """validate_config(None) should load from examples/example_config.yaml."""
    fake_config = MagicMock(spec=MolraptorConfig)
    with patch("molraptor.pipeline.MolraptorConfig.load", return_value=fake_config):
        result = validate_config(None)
    assert result is fake_config


def test_run_calls_pipeline(valid_config):
    """run() should instantiate and call _MolraptorPipeline.run()."""
    mock_pipeline = MagicMock()
    with patch("molraptor.pipeline._MolraptorPipeline", return_value=mock_pipeline):
        run(valid_config)
    mock_pipeline.run.assert_called_once()


def test_run_validates_config_first(valid_config):
    """run() should call validate_config before instantiating the pipeline."""
    with patch("molraptor.pipeline.validate_config", return_value=valid_config) as mock_validate, \
         patch("molraptor.pipeline._MolraptorPipeline") as mock_cls:
        mock_cls.return_value = MagicMock()
        run(valid_config)
    mock_validate.assert_called_once_with(valid_config)