"""Step 4: Check fingerprint integrity."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..config import MolraptorConfig
from ..utils.log_print import LogErrors
from .base import BaseStep


class FingerprintIntegrityStep(BaseStep):
    """Verify fingerprints have expected dimensions and no NaNs."""

    def __init__(self, cfg: MolraptorConfig, results: LogErrors) -> None:
        super().__init__(cfg, results, logging.getLogger("molraptor.fp_integrity"))

    def run(self, fp_csv: Path | str) -> Path:
        fp_csv = Path(fp_csv)

        if not fp_csv.exists():
            msg = f"Fingerprint CSV file not found: {fp_csv}"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        df = pd.read_csv(fp_csv)
        self._check_integrity(df)

        self.logger.info("✓ Fingerprint integrity check passed: %s", fp_csv)
        return fp_csv

    def _check_integrity(self, df: pd.DataFrame) -> None:
        """Raise error if shape or content are invalid."""
        expected_bits = self.cfg.fingerprint.size
        actual_bits = df.shape[1]

        if actual_bits != expected_bits:
            raise ValueError(f"Expected {expected_bits} bits, but got {actual_bits}")

        if df.isna().any().any():
            raise ValueError("Fingerprint file contains NaN values")

        self.logger.debug("Shape: %s | Expected bits: %d", df.shape, expected_bits)
