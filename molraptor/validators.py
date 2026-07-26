# SPDX-License-Identifier: LGPL-3.0-or-later
"""Public validation utilities for tabular data and SMILES."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .fingerprints import _smiles_is_valid


class DataValidator:
    """Stateless validation utilities."""

    @staticmethod
    def ensure_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
        """Require named columns in a tabular input.

        Parameters
        ----------
        df : pandas.DataFrame
            Table whose columns are inspected.
        required : iterable of str
            Column names that must be present.

        Raises
        ------
        ValueError
            If one or more required columns are absent.
        """

        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @staticmethod
    def is_valid_smiles(smiles: str) -> bool:
        """Return whether one SMILES produces a non-empty RDKit molecule.

        Parameters
        ----------
        smiles : str
            Exact user-provided SMILES string to validate.

        Returns
        -------
        bool
            ``True`` when the in-memory encoder classifies the input as valid;
            otherwise ``False``.

        Notes
        -----
        Validation delegates to the shared RDKit parsing rule; the supplied
        string is not curated, harmonized, canonicalized, or replaced.
        """

        return _smiles_is_valid(smiles)
