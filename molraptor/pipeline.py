# SPDX-License-Identifier: LGPL-3.0-or-later
"""Public execution functions for the CSV/TXT fingerprint workflow."""

from __future__ import annotations

from .config import MolraptorConfig
from .workflow import FingerprintStep
from .fingerprints import FingerprintEncodingResult


def validate_config(config: MolraptorConfig) -> MolraptorConfig:
    """Validate the workflow configuration type.

    Parameters
    ----------
    config : MolraptorConfig
        Configuration to validate.

    Returns
    -------
    MolraptorConfig
        The same validated configuration instance.

    Raises
    ------
    ValueError
        If ``config`` is not a :class:`MolraptorConfig` instance.
    """

    if not isinstance(config, MolraptorConfig):
        raise ValueError(f"Expected MolraptorConfig, got {type(config)}")
    return config


def run(config: MolraptorConfig) -> FingerprintEncodingResult:
    """Encode a configured CSV or TXT file and persist its artifacts.

    Parameters
    ----------
    config : MolraptorConfig
        Input file, output directory, CSV column, and fingerprint settings.

    Returns
    -------
    FingerprintEncodingResult
        The single in-memory result used to create all output artifacts.

    Raises
    ------
    ValueError
        If the configuration object has the wrong type, the configured CSV
        SMILES column is missing, or the input contains zero valid SMILES.
    OSError
        If the input or output cannot be accessed through the file system.

    Notes
    -----
    Individual invalid SMILES do not stop a batch when another input is valid.
    A batch with zero valid SMILES is a global file-workflow failure and writes
    no artifacts.

    A successful execution writes ``fingerprints.npy``, ``fingerprints.csv``,
    ``input_statuses.csv``, and ``encoding_metadata.json``. Encoding data derive
    from one :class:`FingerprintEncodingResult`; source-identification metadata
    derive from the validated configuration.

    Examples
    --------
    >>> config = MolraptorConfig(input_path="molecules.csv")
    >>> result = run(config)  # doctest: +SKIP
    """

    return FingerprintStep(validate_config(config)).run()


__all__ = ["validate_config", "run"]
