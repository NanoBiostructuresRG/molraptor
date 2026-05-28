# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for molraptor.config."""

import pytest
from pathlib import Path
import yaml

from molraptor.config import MolraptorConfig


@pytest.fixture
def minimal_yaml(tmp_path):
    """Write a minimal valid YAML config to tmp_path."""
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
        "fingerprint": {
            "radius": 2,
            "size": 1024,
        },
        "curate": {
            "required_columns": ["PubChem CID", "Label", "SMILES"],
        },
    }
    # Create the input file so FilePath validation passes
    (tmp_path / "dataset.csv").write_text("PubChem CID,Label\n1,0\n")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))
    return path


def test_config_loads_from_yaml(minimal_yaml):
    cfg = MolraptorConfig.load(minimal_yaml)
    assert isinstance(cfg, MolraptorConfig)


def test_config_fingerprint_radius(minimal_yaml):
    cfg = MolraptorConfig.load(minimal_yaml)
    assert cfg.fingerprint.radius == 2


def test_config_fingerprint_size(minimal_yaml):
    cfg = MolraptorConfig.load(minimal_yaml)
    assert cfg.fingerprint.size == 1024


def test_config_pubchem_chunk_size(minimal_yaml):
    cfg = MolraptorConfig.load(minimal_yaml)
    assert cfg.pubchem.chunk_size == 400


def test_config_curate_required_columns(minimal_yaml):
    cfg = MolraptorConfig.load(minimal_yaml)
    assert "PubChem CID" in cfg.curate.required_columns
    assert "SMILES" in cfg.curate.required_columns


def test_config_fingerprint_input_file_defaults_to_curated(minimal_yaml):
    cfg = MolraptorConfig.load(minimal_yaml)
    assert cfg.fingerprint.input_file == cfg.paths.curated_output_file


def test_config_missing_required_field_raises(tmp_path):
    """Config without fingerprint section should raise a validation error."""
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
            "properties": ["MolecularWeight"],
            "timeout": 5,
            "max_retries": 3,
            "sleep_seconds": 0.2,
            "chunk_size": 400,
        },
        "curate": {
            "required_columns": ["PubChem CID"],
        },
    }
    (tmp_path / "dataset.csv").write_text("PubChem CID,Label\n1,0\n")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))

    with pytest.raises(Exception):
        MolraptorConfig.load(path)