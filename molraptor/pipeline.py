# SPDX-License-Identifier: LGPL-3.0-or-later
"""Public execution doorway for MOLRAPTOR.

This module exposes two public functions:

- ``validate_config`` — validate a :class:`~molraptor.config.MolraptorConfig`
  before execution.
- ``run`` — validate and execute the full MOLRAPTOR pipeline.

The internal pipeline class is private and should not be imported
or used directly.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from pathlib import Path

from .config import MolraptorConfig
from .fetch import FetchStep
from .curate import CurateStep
from .fingerprint import FingerprintStep
from .fp_integrity import FingerprintIntegrityStep
from .result_manager import ResultManager

__all__ = ["validate_config", "run"]

logger = logging.getLogger("molraptor.pipeline")


def validate_config(config: MolraptorConfig | None = None) -> MolraptorConfig:
    """Validate a MOLRAPTOR runtime configuration object.

    Parameters
    ----------
    config : MolraptorConfig, optional
        Configuration to validate. When ``None``, loads from
        ``examples/example_config.yaml``.

    Returns
    -------
    MolraptorConfig
        The validated configuration object.

    Raises
    ------
    ValueError
        If one or more validation checks fail.

    Examples
    --------
    >>> from molraptor import MolraptorConfig, validate_config
    >>> config = MolraptorConfig.load("examples/example_config.yaml")
    >>> validated = validate_config(config)  # doctest: +SKIP
    """
    if config is None:
        config = MolraptorConfig.load("examples/example_config.yaml")
    if not isinstance(config, MolraptorConfig):
        raise ValueError(f"Expected MolraptorConfig, got {type(config)}")
    return config


def run(config: MolraptorConfig | None = None) -> None:
    """Validate and execute the full MOLRAPTOR pipeline.

    Parameters
    ----------
    config : MolraptorConfig, optional
        Runtime configuration. When ``None``, loads from
        ``examples/example_config.yaml``.

    Raises
    ------
    ValueError
        If configuration validation fails before execution begins.

    Examples
    --------
    >>> from molraptor import MolraptorConfig, run
    >>> config = MolraptorConfig.load("examples/example_config.yaml")
    >>> run(config)  # doctest: +SKIP
    """
    active_config = validate_config(config)
    _MolraptorPipeline(cfg=active_config).run()


class _MolraptorPipeline:
    """Internal pipeline orchestrator. Not part of the public API."""

    def __init__(self, cfg: MolraptorConfig) -> None:
        self.cfg = cfg
        self.steps = [
            FetchStep(cfg),
            CurateStep(cfg),
            FingerprintStep(cfg),
            FingerprintIntegrityStep(cfg),
        ]

    def run(self) -> None:
        data = self.cfg.paths.raw_input_file
        for step in self.steps:
            step_name = step.__class__.__name__
            logger.info("→ Starting: %s", step_name)
            try:
                data = step.run(data)
                logger.info("✓ Completed: %s", step_name)
            except Exception as e:
                logger.error("✗ Failed at %s: %s", step_name, e)
                raise

        self._write_report()
        logger.info("Pipeline completed successfully.")

    def _write_report(self) -> None:
        """Load curated data and fingerprints, write summary report."""
        curated_df = pd.read_csv(self.cfg.paths.curated_output_file)
        fingerprints = np.load(self.cfg.paths.fingerprint_array_file)
        result_path = Path("artifacts") / "summary.txt"
        ResultManager(result_path).write_results(curated_df, fingerprints)
        logger.info("Report saved to %s", result_path)