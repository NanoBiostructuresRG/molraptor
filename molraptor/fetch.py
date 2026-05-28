"""Step 1 - Fetch properties with YAML-driven output path.

Compatible with PubChemService(cfg) signature (single argument).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..config import MolraptorConfig
from ..services.pubchem import PubChemService
from ..utils.log_print import LogErrors
from .base import BaseStep


class FetchStep(BaseStep):
    """Retrieve PubChem properties and merge with the input dataset."""

    def __init__(self, cfg: MolraptorConfig, results: LogErrors) -> None:
        super().__init__(cfg, results, logging.getLogger("molraptor.fetch"))
        self.service = PubChemService(cfg.pubchem)

    def run(self, dataset_path: Path | str) -> Path:
        dataset_path = Path(dataset_path)
        self.logger.info("Reading dataset from %s", dataset_path)
        df = pd.read_excel(dataset_path)

        if "PubChem CID" not in df.columns:
            msg = "Missing required column: 'PubChem CID'"
            self.logger.error(msg)
            raise ValueError(msg)

        cids = df["PubChem CID"].tolist()
        self.logger.info("Fetching properties for %d CIDs", len(cids))

        props_df = self.service.fetch(cids)
        out_path = self._merge_and_save(df, props_df)

        self.results.log_errors(self.service.failed_cids(), step="fetch")
        self.logger.info("Fetched file saved to %s", out_path)
        return out_path

    def _merge_and_save(self, df: pd.DataFrame, props_df: pd.DataFrame) -> Path:
        """Merge original dataset with fetched properties and save to disk."""
        merged = df.merge(props_df, how="left", left_on="PubChem CID", right_on="CID")
        out_path = self.cfg.paths.raw_output_file
        merged.to_csv(out_path, index=False)
        return out_path
