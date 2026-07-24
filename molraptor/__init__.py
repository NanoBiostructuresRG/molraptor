# SPDX-License-Identifier: LGPL-3.0-or-later
"""Public API for in-memory and file-based molecular fingerprint encoding.

MOLRAPTOR accepts user-provided SMILES and exposes an in-memory encoder plus a
single CSV/TXT file workflow. The package does not fetch, curate, harmonize,
canonicalize, or replace supplied SMILES before fingerprint calculation.
"""

from .version import __version__
from .config import MolraptorConfig
from .pipeline import run, validate_config
from .validators import DataValidator
from .fingerprints import (
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
