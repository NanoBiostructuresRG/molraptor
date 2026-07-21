# SPDX-License-Identifier: LGPL-3.0-or-later
"""In-memory Morgan fingerprint encoding for user-provided SMILES."""

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
    """Settings for a binary Morgan fingerprint calculation.

    Attributes
    ----------
    profile_schema_version : {"1.0"}
        Version of the serialized profile schema.
    algorithm : {"morgan"}
        Fingerprint algorithm identifier.
    output_type : {"binary-bit-vector"}
        Representation produced by the encoder.
    radius : int
        Morgan neighborhood radius. Must be non-negative.
    fp_size : int
        Number of bits in each fingerprint. Must be positive.
    include_chirality : bool
        Whether the Morgan generator includes chirality information.
    use_bond_types : bool
        Whether bond types contribute to the fingerprint.
    include_ring_membership : bool
        Whether ring membership contributes to atom invariants.
    include_redundant_environments : bool
        Whether redundant atom environments are included.
    invariant_policy : {"rdkit-default"}
        Atom and bond invariant policy used by the encoder.

    Notes
    -----
    The model is frozen and rejects unknown settings. All effective defaults
    are fields, so serialization records the complete calculation profile.
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
        """Serialize the complete effective profile.

        Returns
        -------
        dict
            JSON-compatible profile values, including effective defaults.
        """

        return self.model_dump(mode="json")


class FingerprintInputStatus(BaseModel):
    """Encoding status and alignment for one original SMILES input.

    Attributes
    ----------
    input_index : int
        Zero-based position in the original ordered input sequence.
    input_smiles : str
        Exact input string supplied by the caller.
    status : {"valid", "invalid"}
        Whether RDKit produced a non-empty molecule and a fingerprint row.
    fingerprint_index : int or None
        Zero-based row in the valid fingerprint matrix. This is ``None`` for
        invalid inputs.
    invalid_reason : {"parse_failure", "empty_molecule"} or None
        Stable failure reason for an invalid input. This is ``None`` for a
        valid input.

    Notes
    -----
    ``input_index`` aligns statuses with original inputs, while
    ``fingerprint_index`` aligns valid statuses with matrix rows. No derived
    or alternative SMILES representation is stored.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_index: int = Field(ge=0)
    input_smiles: str
    status: Literal["valid", "invalid"]
    fingerprint_index: int | None = Field(ge=0)
    invalid_reason: Literal["parse_failure", "empty_molecule"] | None = None

    @model_validator(mode="after")
    def validate_status_contract(self) -> "FingerprintInputStatus":
        """Keep status-specific metadata complete and mutually exclusive."""

        if self.status == "valid":
            if self.fingerprint_index is None:
                raise ValueError("valid input status requires fingerprint_index")
            if self.invalid_reason is not None:
                raise ValueError(
                    "valid input status cannot include an invalid_reason"
                )
        else:
            if self.invalid_reason is None:
                raise ValueError("invalid input status requires an invalid_reason")
            if self.fingerprint_index is not None:
                raise ValueError(
                    "invalid input status cannot include fingerprint_index"
                )
        return self

    @property
    def original_index(self) -> int:
        """Return the original input position.

        Returns
        -------
        int
            The same zero-based position as :attr:`input_index`.
        """

        return self.input_index


@dataclass(frozen=True, slots=True)
class FingerprintEncodingResult:
    """Fingerprints with alignment and reproducibility metadata.

    Attributes
    ----------
    fingerprints : numpy.ndarray
        Binary matrix with shape ``(N_valid, fp_size)`` and dtype
        ``numpy.uint8``.
    profile : dict
        Complete effective fingerprint profile.
    valid_indices : tuple of int
        Original input positions represented by matrix rows, in row order.
    input_statuses : tuple of FingerprintInputStatus
        One status record for every original input.
    valid_count : int
        Number of valid inputs and fingerprint matrix rows.
    invalid_count : int
        Number of inputs that did not produce fingerprint rows.
    matrix_shape : tuple of int
        Shape of ``fingerprints`` as ``(N_valid, fp_size)``.
    matrix_dtype : str
        String representation of the matrix dtype, currently ``"uint8"``.
    molraptor_version : str
        MOLRAPTOR version used for the calculation.
    rdkit_version : str
        RDKit version used for parsing and fingerprint generation.
    ordered_input_hash : str
        SHA-256 digest of the exact ordered input strings.
    profile_hash : str
        SHA-256 digest of the effective serialized profile.

    Notes
    -----
    Invalid inputs are excluded from ``fingerprints`` but retained in
    ``input_statuses``. Original order and duplicates are preserved for all
    valid matrix rows.
    """

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
        """Return the effective profile used for encoding.

        Returns
        -------
        dict
            Alias of :attr:`profile`.
        """

        return self.profile

    @property
    def input_hash(self) -> str:
        """Return the ordered-input digest.

        Returns
        -------
        str
            Alias of :attr:`ordered_input_hash`.
        """

        return self.ordered_input_hash

    def serialize_metadata(self) -> dict[str, object]:
        """Serialize encoding metadata without row-level statuses or bits.

        Returns
        -------
        dict
            JSON-compatible profile, alignment, counts, matrix properties,
            hashes, and runtime versions. The NumPy matrix and per-input
            statuses are excluded.
        """

        return {
            "profile": dict(self.profile),
            "valid_indices": list(self.valid_indices),
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
    """Encode ordered SMILES as binary Morgan fingerprints.

    Parameters
    ----------
    smiles : sequence of str
        User-provided SMILES in the exact order to encode. A single string is
        not accepted as a sequence argument.
    profile : MorganFingerprintProfile
        Complete Morgan generator settings.

    Returns
    -------
    FingerprintEncodingResult
        Valid fingerprints and per-input alignment metadata. The matrix has
        shape ``(N_valid, profile.fp_size)`` and dtype ``numpy.uint8``.

    Raises
    ------
    TypeError
        If ``smiles`` is a string, is not an ordered sequence, contains a
        non-string item, or if ``profile`` is not a
        :class:`MorganFingerprintProfile`.

    Notes
    -----
    Each exact input string is passed to RDKit to construct the molecule used
    by the Morgan generator. MOLRAPTOR does not fetch, curate, harmonize,
    canonicalize, or replace the supplied strings. Invalid and empty inputs
    receive status records but no matrix rows; valid inputs continue to be
    encoded in original order, including duplicates.

    ``ordered_input_hash`` is computed from the exact ordered input strings.
    ``profile_hash`` is computed from the complete effective profile.

    Examples
    --------
    >>> profile = MorganFingerprintProfile(radius=2, fp_size=128)
    >>> result = encode_fingerprints(["CCO", "invalid", "CCO"], profile)
    >>> result.fingerprints.shape
    (2, 128)
    >>> result.valid_indices
    (0, 2)
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
