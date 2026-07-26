# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the direct workflow configuration."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from molraptor import MorganFingerprintProfile
from molraptor.config import MolraptorConfig


def test_config_defaults_to_smiles_column_artifacts_and_default_profile(tmp_path):
    config = MolraptorConfig(input_path=tmp_path / "molecules.csv")

    assert config.input_path == tmp_path / "molecules.csv"
    assert config.smiles_column == "SMILES"
    assert config.output_dir == Path("artifacts")
    assert config.fingerprint_type == "morgan"
    assert config.profile == MorganFingerprintProfile()


def test_config_accepts_custom_column_output_and_profile(tmp_path):
    profile = MorganFingerprintProfile(
        radius=3,
        fp_size=64,
        include_chirality=True,
    )
    config = MolraptorConfig(
        input_path=tmp_path / "molecules.txt",
        smiles_column="SMILES_RDKit",
        output_dir=tmp_path / "results",
        profile=profile,
    )

    assert config.smiles_column == "SMILES_RDKit"
    assert config.output_dir == tmp_path / "results"
    assert config.profile is profile


def test_config_rejects_unknown_fields(tmp_path):
    with pytest.raises(ValidationError):
        MolraptorConfig(
            input_path=tmp_path / "molecules.csv",
            unknown_option=True,
        )


def test_config_accepts_fixed_non_morgan_fingerprint(tmp_path):
    config = MolraptorConfig(
        input_path=tmp_path / "molecules.csv",
        fingerprint_type="maccs",
    )

    assert config.fingerprint_type == "maccs"
    assert config.profile is None


def test_config_rejects_morgan_profile_for_other_fingerprint(tmp_path):
    with pytest.raises(ValidationError, match="only valid"):
        MolraptorConfig(
            input_path=tmp_path / "molecules.csv",
            fingerprint_type="maccs",
            profile=MorganFingerprintProfile(),
        )
