# SPDX-License-Identifier: LGPL-3.0-or-later
"""Configuration model for the CSV/TXT fingerprint workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .fingerprints import FingerprintType, MorganFingerprintProfile


class MolraptorConfig(BaseModel):
    """Inputs and outputs for one file-based fingerprint execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_path: Path
    smiles_column: str = "SMILES"
    output_dir: Path = Path("artifacts")
    fingerprint_type: FingerprintType = "morgan"
    profile: MorganFingerprintProfile | None = None

    @model_validator(mode="before")
    @classmethod
    def _apply_profile_default(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        fingerprint_type = data.get("fingerprint_type", "morgan")
        if "profile" not in data and fingerprint_type == "morgan":
            data["profile"] = MorganFingerprintProfile()
        return data

    @model_validator(mode="after")
    def _validate_profile_scope(self) -> "MolraptorConfig":
        if self.fingerprint_type == "morgan" and self.profile is None:
            raise ValueError("Morgan fingerprint execution requires a profile")
        if self.fingerprint_type != "morgan" and self.profile is not None:
            raise ValueError(
                "MorganFingerprintProfile is only valid with fingerprint_type='morgan'"
            )
        return self

    @field_validator("input_path", "output_dir", mode="before")
    @classmethod
    def _expand_user_paths(cls, value: str | Path) -> Path:
        return Path(value).expanduser()


__all__ = ["MolraptorConfig"]
