# SPDX-License-Identifier: LGPL-3.0-or-later
"""Configuration model for the CSV/TXT fingerprint workflow."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .morgan import MorganFingerprintProfile


class MolraptorConfig(BaseModel):
    """Inputs and outputs for one file-based fingerprint execution.

    Attributes
    ----------
    input_path : pathlib.Path
        Path to a user-provided ``.csv`` or UTF-8 ``.txt`` input file.
    smiles_column : str
        CSV column containing SMILES. The default is ``"SMILES"``. This value
        is ignored for TXT inputs, which contain one SMILES per line.
    output_dir : pathlib.Path
        Directory for the four workflow artifacts. The default is
        ``artifacts``.
    profile : MorganFingerprintProfile
        Effective Morgan settings. The default profile uses radius 2 and 2048
        bits.

    Notes
    -----
    The model is frozen and rejects unknown fields. Path values have ``~``
    expanded during validation; input reading occurs when :func:`molraptor.run`
    executes.
    """

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
