"""Typed configuration *schema* for Molraptor (Pydantic-v2).

Only schema & validation live here - **no project-specific values**.
The user edits a single YAML file and passes it with `--config`.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, FilePath, field_validator, model_validator


# --------------------------------------------------------------------------- #
#  Block‑level models                                                         #
# --------------------------------------------------------------------------- #

class Paths(BaseModel):
    """All file paths used in the pipeline."""
    
    raw_input_file: FilePath
    raw_output_file: Path
    curated_output_file: Path
    error_log_file: Path
    fingerprint_output_file: Path
    fingerprint_array_file: Path 
    labels_output_file: Path

    # Expand tilde and convert to Path early
    @field_validator("*", mode="before")
    def _expand_user_paths(cls, v):
        return Path(v).expanduser()


class PubChemCfg(BaseModel):
    """Parameters controlling the PubChem REST calls."""

    properties: List[str]
    timeout: int = 5
    max_retries: int = 3
    sleep_seconds: float = 0.2
    chunk_size: int = 400


class FingerprintCfg(BaseModel):
    """Morgan fingerprint parameters."""

    radius: int
    size: int
    input_file: Path | None = None


class CurateCfg(BaseModel):
    """Rules for post-fetch curation."""

    required_columns: List[str]
    dtype_map: dict[str, str] = {}


# --------------------------------------------------------------------------- #
#  Root model                                                                 #
# --------------------------------------------------------------------------- #

class MolraptorConfig(BaseModel):
    paths: Paths
    pubchem: PubChemCfg
    fingerprint: FingerprintCfg
    curate: CurateCfg

    # hook post-validation
    @model_validator(mode="after")
    def set_defaults(self) -> "MolraptorConfig":
        if self.fingerprint.input_file is None:
            self.fingerprint.input_file = self.paths.curated_output_file
        return self


    # ---------------------------- helpers ---------------------------------- #

    @classmethod
    def load(cls, path: str | Path) -> "MolraptorConfig":
        """Load, parse and validate a YAML config file."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return cls.model_validate(data)
