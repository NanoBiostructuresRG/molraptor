# SPDX-License-Identifier: LGPL-3.0-or-later
"""In-memory molecular fingerprint encoding for user-provided SMILES."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Literal, cast

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rdkit import Chem, DataStructs, __version__ as rdkit_version  # type: ignore
from rdkit.Chem import MACCSkeys  # type: ignore
from rdkit.Chem.rdFingerprintGenerator import (  # type: ignore
    GetAtomPairGenerator,
    GetMorganFeatureAtomInvGen,
    GetMorganGenerator,
    GetTopologicalTorsionGenerator,
)

from .version import __version__


FingerprintType = Literal[
    "morgan",
    "featmorgan",
    "atompair",
    "rdk",
    "torsion",
    "layered",
    "maccs",
]
FINGERPRINT_TYPES: tuple[FingerprintType, ...] = (
    "morgan",
    "featmorgan",
    "atompair",
    "rdk",
    "torsion",
    "layered",
    "maccs",
)
FingerprintParameterValue = str | int | bool
SerializedProfile = dict[str, FingerprintParameterValue]

FINGERPRINT_PARAMETERS: Mapping[
    FingerprintType, Mapping[str, FingerprintParameterValue]
] = MappingProxyType(
    {
        "morgan": MappingProxyType(
            {
                "radius": 2,
                "fp_size": 2048,
                "include_chirality": False,
                "use_bond_types": True,
                "include_ring_membership": True,
                "include_redundant_environments": False,
                "invariant_policy": "rdkit-default",
            }
        ),
        "featmorgan": MappingProxyType(
            {
                "radius": 2,
                "fp_size": 2048,
                "include_chirality": False,
                "use_bond_types": True,
                "include_ring_membership": True,
                "include_redundant_environments": False,
                "invariant_policy": "rdkit-feature",
            }
        ),
        "atompair": MappingProxyType(
            {
                "min_distance": 1,
                "max_distance": 30,
                "fp_size": 2048,
                "include_chirality": False,
                "use_2d": True,
                "count_simulation": True,
            }
        ),
        "rdk": MappingProxyType(
            {
                "min_path": 1,
                "max_path": 7,
                "fp_size": 2048,
                "num_bits_per_feature": 2,
                "use_hs": True,
                "branched_paths": True,
                "use_bond_order": True,
            }
        ),
        "torsion": MappingProxyType(
            {
                "torsion_atom_count": 4,
                "fp_size": 2048,
                "include_chirality": False,
                "count_simulation": True,
            }
        ),
        "layered": MappingProxyType(
            {
                "layer_flags": 0xFFFFFFFF,
                "min_path": 1,
                "max_path": 7,
                "fp_size": 2048,
                "branched_paths": True,
            }
        ),
        "maccs": MappingProxyType(
            {
                "fp_size": 167,
                "implementation": "MACCSkeys.GenMACCSKeys",
            }
        ),
    }
)


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
        """Serialize the complete effective profile."""

        return self.model_dump(mode="json")


class FingerprintInputStatus(BaseModel):
    """Encoding status and alignment for one original SMILES input."""

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
        """Return the original input position."""

        return self.input_index


@dataclass(frozen=True, slots=True)
class FingerprintEncodingResult:
    """Fingerprints with alignment and reproducibility metadata."""

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
        """Return the effective profile used for encoding."""

        return self.profile

    @property
    def input_hash(self) -> str:
        """Return the ordered-input digest."""

        return self.ordered_input_hash

    def serialize_metadata(self) -> dict[str, object]:
        """Serialize encoding metadata without row-level statuses or bits."""

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


def _fixed_profile(fingerprint_type: FingerprintType) -> SerializedProfile:
    return {
        "profile_schema_version": "1.0",
        "algorithm": fingerprint_type,
        "output_type": "binary-bit-vector",
        **FINGERPRINT_PARAMETERS[fingerprint_type],
    }


def _prepare_fingerprint(
    fingerprint_type: FingerprintType,
    profile: MorganFingerprintProfile | None,
) -> tuple[SerializedProfile, int, Callable[[Chem.Mol], object]]:
    if fingerprint_type == "morgan":
        morgan_profile = profile or MorganFingerprintProfile()
        generator = GetMorganGenerator(
            radius=morgan_profile.radius,
            fpSize=morgan_profile.fp_size,
            includeChirality=morgan_profile.include_chirality,
            useBondTypes=morgan_profile.use_bond_types,
            includeRingMembership=morgan_profile.include_ring_membership,
            includeRedundantEnvironments=(
                morgan_profile.include_redundant_environments
            ),
        )
        return (
            morgan_profile.serialize(),
            morgan_profile.fp_size,
            generator.GetFingerprint,
        )

    if profile is not None:
        raise ValueError(
            "MorganFingerprintProfile is only valid with fingerprint_type='morgan'"
        )

    parameters = FINGERPRINT_PARAMETERS[fingerprint_type]
    effective_profile = _fixed_profile(fingerprint_type)

    if fingerprint_type == "featmorgan":
        generator = GetMorganGenerator(
            radius=cast(int, parameters["radius"]),
            fpSize=cast(int, parameters["fp_size"]),
            includeChirality=cast(bool, parameters["include_chirality"]),
            useBondTypes=cast(bool, parameters["use_bond_types"]),
            includeRingMembership=cast(
                bool, parameters["include_ring_membership"]
            ),
            includeRedundantEnvironments=cast(
                bool, parameters["include_redundant_environments"]
            ),
            atomInvariantsGenerator=GetMorganFeatureAtomInvGen(),
        )
        return effective_profile, cast(int, parameters["fp_size"]), generator.GetFingerprint

    if fingerprint_type == "atompair":
        generator = GetAtomPairGenerator(
            minDistance=cast(int, parameters["min_distance"]),
            maxDistance=cast(int, parameters["max_distance"]),
            includeChirality=cast(bool, parameters["include_chirality"]),
            use2D=cast(bool, parameters["use_2d"]),
            countSimulation=cast(bool, parameters["count_simulation"]),
            fpSize=cast(int, parameters["fp_size"]),
        )
        return effective_profile, cast(int, parameters["fp_size"]), generator.GetFingerprint

    if fingerprint_type == "rdk":
        fp_size = cast(int, parameters["fp_size"])

        def encode_rdk(molecule: Chem.Mol) -> object:
            return Chem.RDKFingerprint(
                molecule,
                minPath=cast(int, parameters["min_path"]),
                maxPath=cast(int, parameters["max_path"]),
                fpSize=fp_size,
                nBitsPerHash=cast(int, parameters["num_bits_per_feature"]),
                useHs=cast(bool, parameters["use_hs"]),
                branchedPaths=cast(bool, parameters["branched_paths"]),
                useBondOrder=cast(bool, parameters["use_bond_order"]),
            )

        return effective_profile, fp_size, encode_rdk

    if fingerprint_type == "torsion":
        generator = GetTopologicalTorsionGenerator(
            includeChirality=cast(bool, parameters["include_chirality"]),
            torsionAtomCount=cast(int, parameters["torsion_atom_count"]),
            countSimulation=cast(bool, parameters["count_simulation"]),
            fpSize=cast(int, parameters["fp_size"]),
        )
        return effective_profile, cast(int, parameters["fp_size"]), generator.GetFingerprint

    if fingerprint_type == "layered":
        fp_size = cast(int, parameters["fp_size"])

        def encode_layered(molecule: Chem.Mol) -> object:
            return Chem.LayeredFingerprint(
                molecule,
                layerFlags=cast(int, parameters["layer_flags"]),
                minPath=cast(int, parameters["min_path"]),
                maxPath=cast(int, parameters["max_path"]),
                fpSize=fp_size,
                branchedPaths=cast(bool, parameters["branched_paths"]),
            )

        return effective_profile, fp_size, encode_layered

    if fingerprint_type == "maccs":
        return (
            effective_profile,
            cast(int, parameters["fp_size"]),
            MACCSkeys.GenMACCSKeys,
        )

    raise AssertionError(f"Unhandled fingerprint type: {fingerprint_type}")


def _parse_molecule(input_smiles: str) -> tuple[Chem.Mol | None, str | None]:
    molecule = Chem.MolFromSmiles(input_smiles)
    if molecule is None:
        return None, "parse_failure"
    if molecule.GetNumAtoms() == 0:
        return None, "empty_molecule"
    return molecule, None


def _smiles_is_valid(smiles: str) -> bool:
    if not isinstance(smiles, str):
        raise TypeError("smiles must be a string")
    molecule, _ = _parse_molecule(smiles)
    return molecule is not None


def encode_fingerprints(
    smiles: Sequence[str],
    profile: MorganFingerprintProfile | None = None,
    *,
    fingerprint_type: FingerprintType = "morgan",
) -> FingerprintEncodingResult:
    """Encode ordered SMILES as one selected binary fingerprint type.

    Existing calls that pass a :class:`MorganFingerprintProfile` as the second
    positional argument continue to calculate Morgan fingerprints. Other
    fingerprint types use their fixed effective profiles and reject a Morgan
    profile.
    """

    if isinstance(smiles, (str, bytes)):
        raise TypeError(
            "smiles must be an ordered sequence of strings, not a string"
        )
    if not isinstance(smiles, Sequence):
        raise TypeError("smiles must be an ordered sequence of strings")
    if fingerprint_type not in FINGERPRINT_TYPES:
        raise ValueError(f"Unsupported fingerprint type: {fingerprint_type}")
    if profile is not None and not isinstance(profile, MorganFingerprintProfile):
        raise TypeError("profile must be a MorganFingerprintProfile or None")

    ordered_smiles = tuple(smiles)
    for index, value in enumerate(ordered_smiles):
        if not isinstance(value, str):
            raise TypeError(f"smiles[{index}] must be a string")

    effective_profile, fp_size, encode_molecule = _prepare_fingerprint(
        fingerprint_type,
        profile,
    )
    rows: list[np.ndarray] = []
    valid_indices: list[int] = []
    statuses: list[FingerprintInputStatus] = []

    for input_index, input_smiles in enumerate(ordered_smiles):
        molecule, invalid_reason = _parse_molecule(input_smiles)
        if molecule is None:
            statuses.append(
                FingerprintInputStatus(
                    input_index=input_index,
                    input_smiles=input_smiles,
                    status="invalid",
                    fingerprint_index=None,
                    invalid_reason=cast(
                        Literal["parse_failure", "empty_molecule"],
                        invalid_reason,
                    ),
                )
            )
            continue

        fingerprint = encode_molecule(molecule)
        row = np.zeros(fp_size, dtype=np.uint8)
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
        matrix = np.empty((0, fp_size), dtype=np.uint8)

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
    "FingerprintType",
    "FINGERPRINT_TYPES",
    "FINGERPRINT_PARAMETERS",
    "MorganFingerprintProfile",
    "FingerprintEncodingResult",
    "FingerprintInputStatus",
    "encode_fingerprints",
]
