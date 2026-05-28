"""HTTP client for PubChem PUG REST."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List

import pandas as pd
from io import StringIO
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import PubChemCfg
from ..utils.chunks import chunked

logger = logging.getLogger("molraptor.pubchem")


class PubChemService:
    """Query PubChem REST API for molecular properties."""

    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def __init__(self, cfg: PubChemCfg) -> None:
        self.cfg = cfg
        self._failed: set[int] = set()

        self.session = requests.Session()
        retries = Retry(
            total=cfg.max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def fetch(self, cids: List[int]) -> pd.DataFrame:
        """
        Fetch molecular properties for a list of PubChem CIDs.

        Args:
            cids: List of compound IDs

        Returns:
            DataFrame with retrieved properties or empty DataFrame if all fail.
        """
        if not cids:
            logger.warning("Empty CID list received. Nothing to fetch.")
            return pd.DataFrame()

        frames = []
        total = len(cids)
        for i, chunk in enumerate(chunked(cids, self.cfg.chunk_size)):
            logger.debug("Fetching chunk %d/%d", i + 1, (total // self.cfg.chunk_size) + 1)
            try:
                frame = self._fetch_chunk(chunk)
                frames.append(frame)
            except Exception as exc:  # noqa:BLE001
                logger.error("Failed chunk %s: %s", chunk[:10], exc)
                self._failed.update(chunk)
            time.sleep(self.cfg.sleep_seconds)

        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def failed_cids(self) -> list[int]:
        """Return list of failed CIDs."""
        return list(self._failed)

    def _fetch_chunk(self, cids: List[int]) -> pd.DataFrame:
        """Fetch a chunk of CIDs and parse the CSV response."""
        url = self._build_url(cids)
        logger.debug("Requesting %s", url)
        csv_text = self._request(url)
        return pd.read_csv(StringIO(csv_text))

    def _build_url(self, cids: List[int]) -> str:
        cid_str = ",".join(map(str, cids))
        prop_str = ",".join(self.cfg.properties)
        return f"{self.BASE_URL}/compound/cid/{cid_str}/property/{prop_str}/CSV"

    def _request(self, url: str) -> str:
        resp = self.session.get(url, timeout=self.cfg.timeout)
        resp.raise_for_status()
        return resp.text
