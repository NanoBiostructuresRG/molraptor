# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 2 — Curation with YAML-driven output path.

Uses ``cfg.paths.curated_output_file`` so the filename is defined
exclusively in the YAML configuration file.
"""

from __future__ import annotations

import logging
import pandas as pd
from pathlib import Path
from .config import MolraptorConfig

logger = logging.getLogger("molraptor.curate")


class CurateStep:
    """Filter dataset according to required columns and dtypes."""

    def __init__(self, cfg: MolraptorConfig) -> None:
        self.cfg = cfg

    def run(self, fetched_csv: Path | str) -> Path:
        fetched_csv = Path(fetched_csv)
        logger.info("Curating file: %s", fetched_csv)
        df = pd.read_csv(fetched_csv)

        curated_df = self._apply_curation(df)

        out_path = self.cfg.paths.curated_output_file
        curated_df.to_csv(out_path, index=False)
        logger.info("Curated file saved to %s", out_path)
        return out_path

    def _apply_curation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter rows and enforce dtypes based on config."""
        required = self.cfg.curate.required_columns

        if not required:
            msg = "No required columns specified in config."
            logger.error(msg)
            raise ValueError(msg)

        missing_cols = [col for col in required if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns in input: {missing_cols}"
            logger.error(msg)
            raise ValueError(msg)

        filtered = df.dropna(subset=required)
        logger.info("Rows before: %d | after dropna: %d", len(df), len(filtered))

        if self.cfg.curate.dtype_map:
            filtered = filtered.astype(self.cfg.curate.dtype_map)
            logger.info("Applied dtype mapping.")

        return filtered