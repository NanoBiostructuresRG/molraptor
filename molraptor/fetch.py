# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 1 — Fetch molecular properties from PubChem.

Uses ``cfg.paths.raw_output_file`` so the filename is defined
exclusively in the YAML configuration file.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import MolraptorConfig
from .pubchem import PubChemService

logger = logging.getLogger("molraptor.fetch")


class FetchStep:
    """Retrieve PubChem properties and merge with the input dataset."""

    def __init__(self, cfg: MolraptorConfig) -> None:
        self.cfg = cfg
        self.service = PubChemService(cfg.pubchem)

    def run(self, dataset_path: Path | str) -> Path:
        dataset_path = Path(dataset_path)
        logger.info("Reading dataset from %s", dataset_path)
        df = pd.read_csv(dataset_path)

        if "PubChem CID" not in df.columns:
            msg = "Missing required column: 'PubChem CID'"
            logger.error(msg)
            raise ValueError(msg)

        cids = df["PubChem CID"].tolist()
        logger.info("Fetching properties for %d CIDs", len(cids))

        props_df = self.service.fetch(cids)
        out_path = self._merge_and_save(df, props_df)

        self._log_fetch_errors()
        logger.info("Fetched file saved to %s", out_path)
        return out_path

    def _merge_and_save(self, df: pd.DataFrame, props_df: pd.DataFrame) -> Path:
        """Merge original dataset with fetched properties and save to disk."""
        merged = df.merge(props_df, how="left", left_on="PubChem CID", right_on="CID")
        out_path = self.cfg.paths.raw_output_file
        merged.to_csv(out_path, index=False)
        return out_path

    def _log_fetch_errors(self) -> None:
        """Log failed CIDs to the error log file."""
        failed = self.service.failed_cids()
        if not failed:
            return
        err_path = Path(self.cfg.paths.error_log_file)
        err_path.parent.mkdir(parents=True, exist_ok=True)
        with err_path.open("w", encoding="utf-8") as f:
            for cid in failed:
                f.write(f"{cid}\n")
        logger.warning("%d CIDs failed to fetch. Logged to %s", len(failed), err_path)