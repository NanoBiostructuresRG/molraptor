# SPDX-License-Identifier: LGPL-3.0-or-later
"""Data validation helpers used across steps."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .morgan import MorganFingerprintProfile, encode_fingerprints


class DataValidator:
    """Static validation utilities."""

    @staticmethod
    def ensure_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @staticmethod
    def is_valid_smiles(smiles: str) -> bool:
        result = encode_fingerprints([smiles], MorganFingerprintProfile())
        return result.input_statuses[0].status == "valid"
