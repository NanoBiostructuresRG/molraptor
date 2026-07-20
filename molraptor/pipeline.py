# SPDX-License-Identifier: LGPL-3.0-or-later
"""Public execution doorway for the SMILES fingerprint workflow."""

from __future__ import annotations

from .config import MolraptorConfig
from .fingerprint import FingerprintStep
from .morgan import FingerprintEncodingResult


def validate_config(config: MolraptorConfig) -> MolraptorConfig:
    """Return a validated workflow configuration."""

    if not isinstance(config, MolraptorConfig):
        raise ValueError(f"Expected MolraptorConfig, got {type(config)}")
    return config


def run(config: MolraptorConfig) -> FingerprintEncodingResult:
    """Execute the configured SMILES-to-fingerprint workflow."""

    return FingerprintStep(validate_config(config)).run()


__all__ = ["validate_config", "run"]
