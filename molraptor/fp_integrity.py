# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 4 — Fingerprint integrity validation.

Verifies that the generated fingerprint matrix has the expected
dimensions and contains no missing values.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import MolraptorConfig

logger = logging.getLogger("molraptor.fp_integrity")


class FingerprintIntegrityStep:
    """Verify fingerprints have expected dimensions and no NaNs."""

    def __init__(self, cfg: MolraptorConfig) -> None:
        self.cfg = cfg

    def run(self, fp_csv: Path | str) -> Path:
        fp_csv = Path(fp_csv)

        if not fp_csv.exists():
            msg = f"Fingerprint CSV file not found: {fp_csv}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        df = pd.read_csv(fp_csv)
        self._check_integrity(df)

        logger.info("✓ Fingerprint integrity check passed: %s", fp_csv)
        return fp_csv

    def _check_integrity(self, df: pd.DataFrame) -> None:
        """Raise error if shape or content are invalid."""
        expected_bits = self.cfg.fingerprint.size
        actual_bits = df.shape[1]

        if actual_bits != expected_bits:
            raise ValueError(f"Expected {expected_bits} bits, but got {actual_bits}")

        if df.isna().any().any():
            raise ValueError("Fingerprint file contains NaN values")

        logger.debug("Shape: %s | Expected bits: %d", df.shape, expected_bits)