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
from rdkit.Chem.rdMHFPFingerprint import MHFPEncoder  # type: ignore
from rdkit.Chem.rdFingerprintGenerator import (  # type: ignore
    GetAtomPairGenerator,
    GetMorganFeatureAtomInvGen,
    GetMorganGenerator,
    GetTopologicalTorsionGenerator,
)

from molraptor._klekota_roth import (
    KLEKOTA_ROTH_PATTERN_SET,
    KLEKOTA_ROTH_PATTERN_SET_SHA256,
    _get_klekota_roth_fingerprint,
)
from molraptor._map4 import _get_map4_shingles
from molraptor.version import __version__


FingerprintAlgorithm = Literal[
    "morgan",
    "featmorgan",
    "atompair",
    "rdk",
    "torsion",
    "layered",
    "maccs",
    "klekotaroth",
    "mhfp6",
    "map4",
]
FingerprintRepresentation = Literal["binary", "count", "minhash"]

FINGERPRINT_ALGORITHMS: tuple[FingerprintAlgorithm, ...] = (
    "morgan",
    "featmorgan",
    "atompair",
    "rdk",
    "torsion",
    "layered",
    "maccs",
    "klekotaroth",
    "mhfp6",
    "map4",
)
FINGERPRINT_REPRESENTATIONS: tuple[FingerprintRepresentation, ...] = (
    "binary",
    "count",
    "minhash",
)
ALGORITHM_REPRESENTATIONS: Mapping[FingerprintAlgorithm, FingerprintRepresentation] = (
    MappingProxyType(
        {
            "morgan": "binary",
            "featmorgan": "binary",
            "atompair": "count",
            "rdk": "binary",
            "torsion": "count",
            "layered": "binary",
            "maccs": "binary",
            "klekotaroth": "binary",
            "mhfp6": "minhash",
            "map4": "minhash",
        }
    )
)

# v0.4 compatibility names are aliases, not independent semantic registries.
FingerprintType = FingerprintAlgorithm
FINGERPRINT_TYPES = FINGERPRINT_ALGORITHMS

_REPRESENTATION_SEMANTICS: Mapping[FingerprintRepresentation, Mapping[str, str]] = (
    MappingProxyType(
        {
            "binary": MappingProxyType(
                {"output_type": "binary-bit-vector", "dtype": "uint8"}
            ),
            "count": MappingProxyType(
                {"output_type": "count-vector", "dtype": "uint32"}
            ),
            "minhash": MappingProxyType(
                {"output_type": "minhash-sketch", "dtype": "uint32"}
            ),
        }
    )
)
FingerprintParameterValue = str | int | bool
SerializedProfile = dict[str, FingerprintParameterValue]

FINGERPRINT_PARAMETERS: Mapping[
    FingerprintAlgorithm, Mapping[str, FingerprintParameterValue]
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
        "klekotaroth": MappingProxyType(
            {
                "fp_size": 4860,
                "pattern_set": KLEKOTA_ROTH_PATTERN_SET,
                "pattern_set_sha256": KLEKOTA_ROTH_PATTERN_SET_SHA256,
                "matching_policy": "rdkit-has-substruct-match",
            }
        ),
        "mhfp6": MappingProxyType(
            {
                "fp_size": 2048,
                "radius": 3,
                "min_radius": 1,
                "rings": True,
                "isomeric": False,
                "kekulize": False,
                "seed": 42,
                "implementation": ("rdkit.Chem.rdMHFPFingerprint.MHFPEncoder"),
            }
        ),
        "map4": MappingProxyType(
            {
                "fp_size": 1024,
                "radius": 2,
                "include_chirality": False,
                "include_duplicate_shingles": False,
                "seed": 42,
                "shingle_policy": ("map4-atom-pair-circular-environment"),
                "minhash_backend": ("rdkit.Chem.rdMHFPFingerprint.MHFPEncoder"),
            }
        ),
    }
)


class MorganFingerprintProfile(BaseModel):
    """Settings for a binary Morgan fingerprint calculation.

    Attributes
    ----------
    profile_schema_version : {"2.0"}
        Version of the serialized profile schema.
    algorithm : {"morgan"}
        Fingerprint algorithm identifier.
    output_type : {"binary-bit-vector"}
        Representation produced by the encoder.
    representation : {"binary"}
        Representation semantics selected for the algorithm.
    dtype : {"uint8"}
        Numerical storage type produced by the encoder.
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

    profile_schema_version: Literal["2.0"] = "2.0"
    algorithm: Literal["morgan"] = "morgan"
    representation: Literal["binary"] = "binary"
    output_type: Literal["binary-bit-vector"] = "binary-bit-vector"
    dtype: Literal["uint8"] = "uint8"
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


@dataclass(frozen=True, slots=True)
class ResolvedFingerprintProfile:
    """Complete effective fingerprint profile and its derived metadata."""

    algorithm: FingerprintAlgorithm
    representation: FingerprintRepresentation
    width: int
    profile: Mapping[str, FingerprintParameterValue]
    profile_hash: str

    @property
    def fingerprint_type(self) -> FingerprintAlgorithm:
        """Return the algorithm through the v0.4 compatibility name."""

        return self.algorithm

    @property
    def fp_size(self) -> int:
        """Return the width through the v0.4 compatibility name."""

        return self.width


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
                raise ValueError("valid input status cannot include an invalid_reason")
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


def _fixed_profile(algorithm: FingerprintAlgorithm) -> SerializedProfile:
    representation = ALGORITHM_REPRESENTATIONS[algorithm]
    semantics = _REPRESENTATION_SEMANTICS[representation]
    return {
        "profile_schema_version": "2.0",
        "algorithm": algorithm,
        "representation": representation,
        "output_type": semantics["output_type"],
        "dtype": semantics["dtype"],
        **FINGERPRINT_PARAMETERS[algorithm],
    }


def resolve_fingerprint_profile(
    fingerprint_type: FingerprintType = "morgan",
    profile: MorganFingerprintProfile | None = None,
) -> ResolvedFingerprintProfile:
    """Resolve a complete effective fingerprint profile without encoding."""

    if fingerprint_type not in FINGERPRINT_ALGORITHMS:
        raise ValueError(f"Unsupported fingerprint type: {fingerprint_type}")
    algorithm = cast(FingerprintAlgorithm, fingerprint_type)
    representation = ALGORITHM_REPRESENTATIONS[algorithm]
    if profile is not None and not isinstance(profile, MorganFingerprintProfile):
        raise TypeError("profile must be a MorganFingerprintProfile or None")
    if algorithm != "morgan" and profile is not None:
        raise ValueError(
            "MorganFingerprintProfile is only valid with fingerprint_type='morgan'"
        )

    if algorithm == "morgan":
        effective_profile = (profile or MorganFingerprintProfile()).serialize()
    else:
        effective_profile = _fixed_profile(algorithm)

    profile_hash = _sha256_json(effective_profile, sort_keys=True)
    read_only_profile = MappingProxyType(dict(effective_profile))

    return ResolvedFingerprintProfile(
        algorithm=algorithm,
        representation=representation,
        width=cast(int, effective_profile["fp_size"]),
        profile=read_only_profile,
        profile_hash=profile_hash,
    )


def _prepare_fingerprint(
    fingerprint_type: FingerprintType,
    profile: MorganFingerprintProfile | None,
) -> tuple[ResolvedFingerprintProfile, Callable[[Chem.Mol], object]]:
    resolved = resolve_fingerprint_profile(fingerprint_type, profile)
    algorithm = resolved.algorithm
    parameters = resolved.profile

    if algorithm == "morgan":
        generator = GetMorganGenerator(
            radius=cast(int, parameters["radius"]),
            fpSize=resolved.width,
            includeChirality=cast(bool, parameters["include_chirality"]),
            useBondTypes=cast(bool, parameters["use_bond_types"]),
            includeRingMembership=cast(bool, parameters["include_ring_membership"]),
            includeRedundantEnvironments=(
                cast(bool, parameters["include_redundant_environments"])
            ),
        )
        return resolved, generator.GetFingerprint

    if algorithm == "featmorgan":
        generator = GetMorganGenerator(
            radius=cast(int, parameters["radius"]),
            fpSize=resolved.width,
            includeChirality=cast(bool, parameters["include_chirality"]),
            useBondTypes=cast(bool, parameters["use_bond_types"]),
            includeRingMembership=cast(bool, parameters["include_ring_membership"]),
            includeRedundantEnvironments=cast(
                bool, parameters["include_redundant_environments"]
            ),
            atomInvariantsGenerator=GetMorganFeatureAtomInvGen(),
        )
        return resolved, generator.GetFingerprint

    if algorithm == "atompair":
        generator = GetAtomPairGenerator(
            minDistance=cast(int, parameters["min_distance"]),
            maxDistance=cast(int, parameters["max_distance"]),
            includeChirality=cast(bool, parameters["include_chirality"]),
            use2D=cast(bool, parameters["use_2d"]),
            fpSize=resolved.width,
        )
        return resolved, generator.GetCountFingerprintAsNumPy

    if algorithm == "rdk":

        def encode_rdk(molecule: Chem.Mol) -> object:
            return Chem.RDKFingerprint(
                molecule,
                minPath=cast(int, parameters["min_path"]),
                maxPath=cast(int, parameters["max_path"]),
                fpSize=resolved.width,
                nBitsPerHash=cast(int, parameters["num_bits_per_feature"]),
                useHs=cast(bool, parameters["use_hs"]),
                branchedPaths=cast(bool, parameters["branched_paths"]),
                useBondOrder=cast(bool, parameters["use_bond_order"]),
            )

        return resolved, encode_rdk

    if algorithm == "torsion":
        generator = GetTopologicalTorsionGenerator(
            includeChirality=cast(bool, parameters["include_chirality"]),
            torsionAtomCount=cast(int, parameters["torsion_atom_count"]),
            fpSize=resolved.width,
        )
        return resolved, generator.GetCountFingerprintAsNumPy

    if algorithm == "layered":

        def encode_layered(molecule: Chem.Mol) -> object:
            return Chem.LayeredFingerprint(
                molecule,
                layerFlags=cast(int, parameters["layer_flags"]),
                minPath=cast(int, parameters["min_path"]),
                maxPath=cast(int, parameters["max_path"]),
                fpSize=resolved.width,
                branchedPaths=cast(bool, parameters["branched_paths"]),
            )

        return resolved, encode_layered

    if algorithm == "maccs":
        return resolved, MACCSkeys.GenMACCSKeys

    if algorithm == "klekotaroth":
        return resolved, _get_klekota_roth_fingerprint

    if algorithm == "mhfp6":
        encoder = MHFPEncoder(
            resolved.width,
            cast(int, parameters["seed"]),
        )

        def encode_mhfp6(molecule: Chem.Mol) -> object:
            return encoder.EncodeMol(
                molecule,
                radius=cast(int, parameters["radius"]),
                rings=cast(bool, parameters["rings"]),
                isomeric=cast(bool, parameters["isomeric"]),
                kekulize=cast(bool, parameters["kekulize"]),
                min_radius=cast(int, parameters["min_radius"]),
            )

        return resolved, encode_mhfp6

    if algorithm == "map4":
        encoder = MHFPEncoder(
            resolved.width,
            cast(int, parameters["seed"]),
        )

        def encode_map4(molecule: Chem.Mol) -> object:
            shingles = _get_map4_shingles(
                molecule,
                radius=cast(int, parameters["radius"]),
            )
            return encoder.FromStringArray(shingles)

        return resolved, encode_map4

    raise AssertionError(f"Unhandled fingerprint algorithm: {algorithm}")


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
    """Encode ordered SMILES with a selected fingerprint algorithm.

    Existing calls that pass a :class:`MorganFingerprintProfile` as the second
    positional argument continue to calculate Morgan fingerprints. Other
    algorithms use their fixed effective profiles and reject a Morgan profile.
    Each algorithm has one fixed representation. Algorithms without an
    implemented encoder fail explicitly.
    """

    if isinstance(smiles, (str, bytes)):
        raise TypeError("smiles must be an ordered sequence of strings, not a string")
    if not isinstance(smiles, Sequence):
        raise TypeError("smiles must be an ordered sequence of strings")

    resolved_profile, encode_molecule = _prepare_fingerprint(
        fingerprint_type,
        profile,
    )
    ordered_smiles = tuple(smiles)
    for index, value in enumerate(ordered_smiles):
        if not isinstance(value, str):
            raise TypeError(f"smiles[{index}] must be a string")

    matrix_dtype = (
        np.uint8 if resolved_profile.representation == "binary" else np.uint32
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
        if resolved_profile.representation == "binary":
            row = np.zeros(resolved_profile.width, dtype=np.uint8)
            DataStructs.ConvertToNumpyArray(fingerprint, row)
        else:
            row = np.asarray(fingerprint, dtype=np.uint32)
        if row.shape != (resolved_profile.width,):
            raise RuntimeError(
                f"{resolved_profile.algorithm} produced shape {row.shape}; "
                f"expected ({resolved_profile.width},)"
            )
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
        matrix = np.vstack(rows).astype(matrix_dtype, copy=False)
    else:
        matrix = np.empty((0, resolved_profile.width), dtype=matrix_dtype)

    return FingerprintEncodingResult(
        fingerprints=matrix,
        profile=dict(resolved_profile.profile),
        valid_indices=tuple(valid_indices),
        input_statuses=tuple(statuses),
        valid_count=len(rows),
        invalid_count=len(ordered_smiles) - len(rows),
        matrix_shape=matrix.shape,
        matrix_dtype=str(matrix.dtype),
        molraptor_version=__version__,
        rdkit_version=rdkit_version,
        ordered_input_hash=_sha256_json(ordered_smiles, sort_keys=False),
        profile_hash=resolved_profile.profile_hash,
    )


__all__ = [
    "FingerprintAlgorithm",
    "FingerprintRepresentation",
    "FINGERPRINT_ALGORITHMS",
    "FINGERPRINT_REPRESENTATIONS",
    "ALGORITHM_REPRESENTATIONS",
    "FingerprintType",
    "FINGERPRINT_TYPES",
    "FINGERPRINT_PARAMETERS",
    "MorganFingerprintProfile",
    "ResolvedFingerprintProfile",
    "FingerprintEncodingResult",
    "FingerprintInputStatus",
    "resolve_fingerprint_profile",
    "encode_fingerprints",
]
