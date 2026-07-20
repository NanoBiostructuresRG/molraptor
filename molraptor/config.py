# SPDX-License-Identifier: LGPL-3.0-or-later
"""Runtime configuration for the SMILES-to-fingerprint workflow."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .morgan import MorganFingerprintProfile


class MolraptorConfig(BaseModel):
    """Validated inputs for one file-based fingerprinting execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_path: Path
    smiles_column: str = "SMILES"
    output_dir: Path = Path("artifacts")
    profile: MorganFingerprintProfile = Field(
        default_factory=MorganFingerprintProfile
    )

    @field_validator("input_path", "output_dir", mode="before")
    @classmethod
    def _expand_user_paths(cls, value: str | Path) -> Path:
        return Path(value).expanduser()


__all__ = ["MolraptorConfig"]
