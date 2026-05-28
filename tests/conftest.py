# SPDX-License-Identifier: LGPL-3.0-or-later
"""Shared pytest fixtures for MOLRAPTOR test suite."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

N_SAMPLES = 20
FP_SIZE = 16


@pytest.fixture
def tmp_curated_csv(tmp_path):
    """Minimal curated CSV with SMILES and Label columns."""
    df = pd.DataFrame({
        "PubChem CID": range(N_SAMPLES),
        "SMILES": ["CCO"] * N_SAMPLES,
        "Label": [0, 1] * (N_SAMPLES // 2),
        "MolecularWeight": [46.07] * N_SAMPLES,
        "Complexity": [10.0] * N_SAMPLES,
    })
    path = tmp_path / "curated.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def tmp_fingerprints(tmp_path):
    """Synthetic fingerprint matrix."""
    fps = np.random.randint(0, 2, size=(N_SAMPLES, FP_SIZE))
    path = tmp_path / "morgan_fp.npy"
    np.save(path, fps)
    return path, fps