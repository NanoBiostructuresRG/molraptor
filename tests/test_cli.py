# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests for the v0.3 command-line workflow."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from molraptor import MorganFingerprintProfile, encode_fingerprints
from molraptor.cli import main
import molraptor.fingerprint as fingerprint_module
from molraptor.version import __version__


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"MOLRAPTOR {__version__}"


def test_cli_run_smoke_and_direct_api_equivalence(tmp_path):
    input_path = tmp_path / "molecules.csv"
    pd.DataFrame(
        {"SMILES_Harmonized": ["CCO", "invalid", "CC"]}
    ).to_csv(input_path, index=False)
    output_dir = tmp_path / "outputs"

    assert fingerprint_module.encode_fingerprints is encode_fingerprints
    with patch(
        "molraptor.fingerprint.encode_fingerprints",
        wraps=encode_fingerprints,
    ) as encoder:
        main(
            [
                "run",
                "--input",
                str(input_path),
                "--smiles-column",
                "SMILES_Harmonized",
                "--output-dir",
                str(output_dir),
                "--radius",
                "3",
                "--fp-size",
                "64",
                "--include-chirality",
            ]
        )

    encoder.assert_called_once()
    smiles, profile = encoder.call_args.args
    assert smiles == ["CCO", "invalid", "CC"]
    assert profile == MorganFingerprintProfile(
        radius=3,
        fp_size=64,
        include_chirality=True,
    )

    expected = encode_fingerprints(smiles, profile)
    actual = np.load(output_dir / "fingerprints.npy", allow_pickle=False)
    np.testing.assert_array_equal(actual, expected.fingerprints)
