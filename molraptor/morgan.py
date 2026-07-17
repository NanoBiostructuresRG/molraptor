# SPDX-License-Identifier: LGPL-3.0-or-later
"""Public, in-memory Morgan fingerprint encoding API."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rdkit import Chem, DataStructs, __version__ as rdkit_version  # type: ignore
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator  # type: ignore

from .version import __version__


SerializedProfile = dict[str, str | int | bool]


class MorganFingerprintProfile(BaseModel):
    """Complete, serializable settings for a Morgan bit fingerprint.

    All effective defaults are model fields, so regular Pydantic serialization
    retains them even when the caller constructs the profile with no arguments.
    The invariant policy is explicit and intentionally limited to RDKit's
    built-in Morgan atom and bond invariants in this schema version.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_schema_version: Literal["1.0"] = "1.0"
    algorithm: Literal["morgan"] = "morgan"
    output_type: Literal["binary-bit-vector"] = "binary-bit-vector"
    radius: int = Field(default=2, ge=0)
    fp_size: int = Field(default=2048, gt=0)
    include_chirality: bool = False
    use_bond_types: bool = True
    include_ring_membership: bool = True
    include_redundant_environments: bool = False
    invariant_policy: Literal["rdkit-default"] = "rdkit-default"

    def serialize(self) -> SerializedProfile:
        """Return the complete effective profile as JSON-compatible values."""

        return self.model_dump(mode="json")


class FingerprintInputStatus(BaseModel):
    """Encoding status and row alignment for one original SMILES input."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_index: int = Field(ge=0)
    input_smiles: str
    status: Literal["valid", "invalid"]
    rdkit_canonical_smiles: str | None
    fingerprint_index: int | None = Field(ge=0)
    invalid_reason: Literal["parse_failure", "empty_molecule"] | None = None

    @model_validator(mode="after")
    def validate_status_contract(self) -> "FingerprintInputStatus":
        """Keep status-specific metadata complete and mutually exclusive."""

        if self.status == "valid":
            if self.rdkit_canonical_smiles is None:
                raise ValueError(
                    "valid input status requires rdkit_canonical_smiles"
                )
            if self.fingerprint_index is None:
                raise ValueError("valid input status requires fingerprint_index")
            if self.invalid_reason is not None:
                raise ValueError(
                    "valid input status cannot include an invalid_reason"
                )
        else:
            if self.invalid_reason is None:
                raise ValueError("invalid input status requires an invalid_reason")
            if self.rdkit_canonical_smiles is not None:
                raise ValueError(
                    "invalid input status cannot include rdkit_canonical_smiles"
                )
            if self.fingerprint_index is not None:
                raise ValueError(
                    "invalid input status cannot include fingerprint_index"
                )
        return self

    @property
    def original_index(self) -> int:
        """Alias emphasizing that ``input_index`` refers to the caller's input."""

        return self.input_index


@dataclass(frozen=True, slots=True)
class FingerprintEncodingResult:
    """In-memory fingerprints plus reproducibility and alignment metadata."""

    fingerprints: np.ndarray
    profile: SerializedProfile
    valid_indices: tuple[int, ...]
    input_statuses: tuple[FingerprintInputStatus, ...]
    valid_count: int
    invalid_count: int
    matrix_shape: tuple[int, int]
    matrix_dtype: str
    molraptor_version: str
    rdkit_version: str
    ordered_input_hash: str
    profile_hash: str

    @property
    def effective_profile(self) -> SerializedProfile:
        """Alias for the effective serialized profile used for encoding."""

        return self.profile

    @property
    def input_hash(self) -> str:
        """Short alias for :attr:`ordered_input_hash`."""

        return self.ordered_input_hash

    def serialize_metadata(self) -> dict[str, object]:
        """Return JSON-compatible result metadata without the NumPy matrix."""

        return {
            "profile": dict(self.profile),
            "valid_indices": list(self.valid_indices),
            "input_statuses": [
                status.model_dump(mode="json") for status in self.input_statuses
            ],
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "matrix_shape": list(self.matrix_shape),
            "matrix_dtype": self.matrix_dtype,
            "molraptor_version": self.molraptor_version,
            "rdkit_version": self.rdkit_version,
            "ordered_input_hash": self.ordered_input_hash,
            "profile_hash": self.profile_hash,
        }


def _sha256_json(value: object, *, sort_keys: bool) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=sort_keys,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def encode_fingerprints(
    smiles: Sequence[str],
    profile: MorganFingerprintProfile,
) -> FingerprintEncodingResult:
    """Encode an ordered sequence of SMILES as binary Morgan fingerprints.

    Invalid and empty SMILES are represented only in ``input_statuses``; they
    do not add rows to the fingerprint matrix. This function performs no file
    I/O and does not depend on pipeline configuration or labels.
    """

    if isinstance(smiles, (str, bytes)):
        raise TypeError(
            "smiles must be an ordered sequence of strings, not a string"
        )
    if not isinstance(smiles, Sequence):
        raise TypeError("smiles must be an ordered sequence of strings")
    if not isinstance(profile, MorganFingerprintProfile):
        raise TypeError("profile must be a MorganFingerprintProfile")

    ordered_smiles = tuple(smiles)
    for index, value in enumerate(ordered_smiles):
        if not isinstance(value, str):
            raise TypeError(f"smiles[{index}] must be a string")

    effective_profile = profile.serialize()
    generator = GetMorganGenerator(
        radius=profile.radius,
        fpSize=profile.fp_size,
        includeChirality=profile.include_chirality,
        useBondTypes=profile.use_bond_types,
        includeRingMembership=profile.include_ring_membership,
        includeRedundantEnvironments=profile.include_redundant_environments,
    )

    rows: list[np.ndarray] = []
    valid_indices: list[int] = []
    statuses: list[FingerprintInputStatus] = []

    for input_index, input_smiles in enumerate(ordered_smiles):
        molecule = Chem.MolFromSmiles(input_smiles)
        if molecule is None:
            statuses.append(
                FingerprintInputStatus(
                    input_index=input_index,
                    input_smiles=input_smiles,
                    status="invalid",
                    rdkit_canonical_smiles=None,
                    fingerprint_index=None,
                    invalid_reason="parse_failure",
                )
            )
            continue
        if molecule.GetNumAtoms() == 0:
            statuses.append(
                FingerprintInputStatus(
                    input_index=input_index,
                    input_smiles=input_smiles,
                    status="invalid",
                    rdkit_canonical_smiles=None,
                    fingerprint_index=None,
                    invalid_reason="empty_molecule",
                )
            )
            continue

        fingerprint = generator.GetFingerprint(molecule)
        row = np.zeros(profile.fp_size, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(fingerprint, row)
        fingerprint_index = len(rows)
        rows.append(row)
        valid_indices.append(input_index)
        statuses.append(
            FingerprintInputStatus(
                input_index=input_index,
                input_smiles=input_smiles,
                status="valid",
                rdkit_canonical_smiles=Chem.MolToSmiles(
                    molecule,
                    canonical=True,
                    isomericSmiles=True,
                ),
                fingerprint_index=fingerprint_index,
            )
        )

    if rows:
        matrix = np.vstack(rows).astype(np.uint8, copy=False)
    else:
        matrix = np.empty((0, profile.fp_size), dtype=np.uint8)

    return FingerprintEncodingResult(
        fingerprints=matrix,
        profile=effective_profile,
        valid_indices=tuple(valid_indices),
        input_statuses=tuple(statuses),
        valid_count=len(rows),
        invalid_count=len(ordered_smiles) - len(rows),
        matrix_shape=matrix.shape,
        matrix_dtype=str(matrix.dtype),
        molraptor_version=__version__,
        rdkit_version=rdkit_version,
        ordered_input_hash=_sha256_json(ordered_smiles, sort_keys=False),
        profile_hash=_sha256_json(effective_profile, sort_keys=True),
    )


__all__ = [
    "MorganFingerprintProfile",
    "FingerprintEncodingResult",
    "FingerprintInputStatus",
    "encode_fingerprints",
]
