# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 3 — Generate Morgan fingerprints and NPY artifacts.

Outputs created in ``artifacts/``:
    - morgan_fp.csv        (CSV, human-readable fingerprints)
    - morgan_db_*.npy      (NumPy array, shape=N×size)
    - labels.npy           (NumPy array, shape=N,)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem  # type: ignore
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator  # type: ignore

from .config import MolraptorConfig

logger = logging.getLogger("molraptor.fingerprint")


class FingerprintStep:
    """Generate Morgan fingerprints and save CSV + NPY as per YAML config."""

    def __init__(self, cfg: MolraptorConfig) -> None:
        self.cfg = cfg
        self._gen = GetMorganGenerator(
            radius=cfg.fingerprint.radius,
            fpSize=cfg.fingerprint.size,
        )

    def run(self, curated_csv: Path | str) -> Path:
        curated_csv = Path(curated_csv)
        logger.info("Generating fingerprints from: %s", curated_csv)
        df = pd.read_csv(curated_csv)

        for col in ["SMILES", "Label"]:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in input CSV.")

        fps_array = self._generate_fingerprints(df["SMILES"].tolist())
        labels_array = df["Label"].to_numpy()

        if fps_array.shape[0] != labels_array.shape[0]:
            raise ValueError("Mismatch between fingerprints and labels count.")

        csv_path = Path(self.cfg.paths.fingerprint_output_file)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(fps_array).to_csv(csv_path, index=False)

        np.save(self.cfg.paths.fingerprint_array_file, fps_array)
        np.save(self.cfg.paths.labels_output_file, labels_array)

        logger.info("Saved CSV  → %s", csv_path)
        logger.info("Saved NPY  → %s", self.cfg.paths.fingerprint_array_file)
        return csv_path

    def _generate_fingerprints(self, smiles_list: list[str]) -> np.ndarray:
        """Convert SMILES to Morgan fingerprints with fallback for invalid ones."""
        fp_size = self.cfg.fingerprint.size
        fps = []
        invalid_count = 0

        for smiles in smiles_list:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.warning("Invalid SMILES skipped: %s", smiles)
                fps.append(np.zeros(fp_size, dtype=int))
                invalid_count += 1
                continue
            fp = self._gen.GetFingerprint(mol)
            arr = np.zeros(fp_size, dtype=int)
            Chem.DataStructs.ConvertToNumpyArray(fp, arr)
            fps.append(arr)

        logger.info("Generated %d fingerprints (%d invalid SMILES)",
                    len(fps), invalid_count)
        return np.vstack(fps)