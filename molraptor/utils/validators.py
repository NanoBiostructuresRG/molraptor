"""Data validation helpers used across steps."""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd

try:
    from rdkit import Chem  # type: ignore
except ImportError:  # pragma: no cover
    Chem = None  # fallback for envs without rdkit

logger = logging.getLogger("molraptor.validators")


class DataValidator:
    """Static validation utilities."""

    @staticmethod
    def ensure_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @staticmethod
    def is_valid_smiles(smiles: str) -> bool:
        if Chem is None:
            logger.warning("RDKit not installed; skipping SMILES validation")
            return True
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
