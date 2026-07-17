# SPDX-License-Identifier: LGPL-3.0-or-later
"""MOLRAPTOR — Molecular Learning via Rapid Processing of Topological Representations.

Public API
----------
- ``MorganFingerprintProfile`` - explicit Morgan encoding settings.
- ``FingerprintEncodingResult`` - in-memory fingerprints and metadata.
- ``FingerprintInputStatus`` - per-input encoding status metadata.
- ``encode_fingerprints`` - encode SMILES without pipeline or file I/O.
- ``MolraptorConfig`` — runtime configuration object.
- ``validate_config``  — validate a configuration before execution.
- ``run``              — execute the full MOLRAPTOR pipeline.
- ``DataValidator``    — SMILES and column validation utilities.
- ``__version__``      — current package version string.
"""

from .version import __version__
from .config import MolraptorConfig
from .pipeline import run, validate_config
from .validators import DataValidator
from .morgan import (
    FingerprintEncodingResult,
    FingerprintInputStatus,
    MorganFingerprintProfile,
    encode_fingerprints,
)

__all__ = [
    "__version__",
    "MolraptorConfig",
    "run",
    "validate_config",
    "DataValidator",
    "MorganFingerprintProfile",
    "FingerprintEncodingResult",
    "FingerprintInputStatus",
    "encode_fingerprints",
]
