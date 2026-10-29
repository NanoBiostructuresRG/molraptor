# SPDX-License-Identifier: LGPL-3.0-or-later
"""Original MAP4 molecular-shingle generation."""

from __future__ import annotations

from itertools import combinations

from rdkit import Chem  # type: ignore
from rdkit.Chem import rdmolops  # type: ignore


def _find_atom_environment(
    molecule: Chem.Mol,
    atom_index: int,
    radius: int,
) -> str:
    environment = rdmolops.FindAtomEnvironmentOfRadiusN(
        molecule,
        radius,
        atom_index,
    )
    atom_map: dict[int, int] = {}
    submolecule = Chem.PathToSubmol(
        molecule,
        environment,
        atomMap=atom_map,
    )
    if atom_index not in atom_map:
        return ""
    return Chem.MolToSmiles(
        submolecule,
        rootedAtAtom=atom_map[atom_index],
        canonical=True,
        isomericSmiles=False,
    )


def _get_map4_shingles(molecule: Chem.Mol, radius: int = 2) -> list[str]:
    """Return deduplicated original-MAP4 atom-pair shingles."""

    atom_environments = {
        atom.GetIdx(): tuple(
            _find_atom_environment(
                molecule,
                atom.GetIdx(),
                environment_radius,
            )
            for environment_radius in range(1, radius + 1)
        )
        for atom in molecule.GetAtoms()
    }
    distance_matrix = rdmolops.GetDistanceMatrix(molecule)
    shingles: set[str] = set()

    for first, second in combinations(range(molecule.GetNumAtoms()), 2):
        distance = str(int(distance_matrix[first][second]))
        for radius_index in range(radius):
            environments = sorted(
                (
                    atom_environments[first][radius_index],
                    atom_environments[second][radius_index],
                )
            )
            shingles.add(
                f"{environments[0]}|{distance}|{environments[1]}"
            )

    return sorted(shingles)
