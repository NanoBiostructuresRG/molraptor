"""Step 3: Generate Morgan fingerprints and legacy NPY artefacts.

Outputs created in `artifacts/`:
    - morgan_fp.csv            (CSV, 1024-bit fingerprints, human-readable)
    - morgan_db_pparg.npy      (NumPy array, shape=N×1024)
    - labels.npy               (NumPy array, shape=N,)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem  # type: ignore
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator  # type: ignore

from ..config import MolraptorConfig
from ..utils.log_print import LogErrors
from .base import BaseStep


class FingerprintStep(BaseStep):
    """Generate Morgan fingerprints and save CSV + NPY as per YAML."""

    def __init__(self, cfg: MolraptorConfig, results: LogErrors) -> None:
        super().__init__(cfg, results, logging.getLogger("molraptor.fingerprint"))
        self._gen = GetMorganGenerator(radius=cfg.fingerprint.radius,
                                       fpSize=cfg.fingerprint.size)

    def run(self, curated_csv: Path | str) -> Path:
        curated_csv = Path(curated_csv)
        self.logger.info("Generating fingerprints from: %s", curated_csv)
        df = pd.read_csv(curated_csv)

        for col in ["SMILES", "Label"]:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in input CSV.")

        fps_array = self._generate_fingerprints(df["SMILES"].tolist())
        labels_array = df["Label"].to_numpy()

        if fps_array.shape[0] != labels_array.shape[0]:
            raise ValueError("Mismatch between fingerprints and labels count.")

        # Save CSV
        csv_path = self.results.save_dataframe(pd.DataFrame(fps_array),
                                               Path(self.cfg.paths.fingerprint_output_file).name)

        # Save NPY
        np.save(self.cfg.paths.fingerprint_array_file, fps_array)
        np.save(self.cfg.paths.labels_output_file, labels_array)

        self.logger.info("Saved CSV  → %s", csv_path)
        self.logger.info("Saved NPY  → %s", self.cfg.paths.fingerprint_array_file)
        return csv_path

    def _generate_fingerprints(self, smiles_list: list[str]) -> np.ndarray:
        """Convert SMILES to Morgan fingerprints with fallback for invalid ones."""
        fp_size = self.cfg.fingerprint.size
        fps = []
        invalid_count = 0

        for smiles in smiles_list:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                self.logger.warning("Invalid SMILES skipped: %s", smiles)
                fps.append(np.zeros(fp_size, dtype=int))
                invalid_count += 1
                continue
            fp = self._gen.GetFingerprint(mol)
            arr = np.zeros(fp_size, dtype=int)
            Chem.DataStructs.ConvertToNumpyArray(fp, arr)
            fps.append(arr)

        self.logger.info("Generated %d fingerprints (%d invalid SMILES)",
                         len(fps), invalid_count)
        return np.vstack(fps)
