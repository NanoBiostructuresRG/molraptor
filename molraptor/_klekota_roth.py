# SPDX-License-Identifier: LGPL-3.0-or-later
"""Internal Klekota-Roth structural-key definition and encoder."""

from __future__ import annotations

from functools import lru_cache
import hashlib
from importlib.resources import files

from rdkit import Chem, DataStructs  # type: ignore


KLEKOTA_ROTH_PATTERN_COUNT = 4860
KLEKOTA_ROTH_PATTERN_SET = "cdk-klekota-roth-4860"
KLEKOTA_ROTH_PATTERN_SET_SHA256 = (
    "73041eb6b27ebab742fc61ced6a4311eb726bba9c7b30b34dbc5eb378e4c5278"
)

# Ordered scientific definition extracted without normalization from the CDK
# public-domain source at this commit-pinned URL:
# https://github.com/cdk/cdk/blob/2fbdd2e406c51ec0e1326975e52856fc96794ee2/descriptor/fingerprint/src/main/java/org/openscience/cdk/fingerprint/KlekotaRothFingerprinter.java
_PATTERN_RESOURCE = "klekota_roth_smarts.txt"


@lru_cache(maxsize=1)
def _load_klekota_roth_patterns() -> tuple[Chem.Mol, ...]:
    """Load, identify, and compile the bundled ordered SMARTS definition."""

    pattern_text = (
        files("molraptor")
        .joinpath("_data", _PATTERN_RESOURCE)
        .read_text(encoding="utf-8")
    )
    patterns = tuple(pattern_text.splitlines())
    if len(patterns) != KLEKOTA_ROTH_PATTERN_COUNT or any(
        not pattern for pattern in patterns
    ):
        raise RuntimeError(
            "Bundled Klekota-Roth definition must contain exactly "
            f"{KLEKOTA_ROTH_PATTERN_COUNT} nonempty SMARTS patterns"
        )

    pattern_set_sha256 = hashlib.sha256("\n".join(patterns).encode("utf-8")).hexdigest()
    if pattern_set_sha256 != KLEKOTA_ROTH_PATTERN_SET_SHA256:
        raise RuntimeError(
            "Bundled Klekota-Roth definition has an unexpected ordered-pattern SHA256"
        )

    compiled_patterns: list[Chem.Mol] = []
    for index, pattern in enumerate(patterns):
        compiled = Chem.MolFromSmarts(pattern)
        if compiled is None:
            raise RuntimeError(
                "Bundled Klekota-Roth SMARTS failed to compile at feature "
                f"index {index}"
            )
        compiled_patterns.append(compiled)
    return tuple(compiled_patterns)


def _get_klekota_roth_fingerprint(molecule: Chem.Mol) -> DataStructs.ExplicitBitVect:
    """Return the 4860-bit ordered Klekota-Roth structural-key fingerprint."""

    fingerprint = DataStructs.ExplicitBitVect(KLEKOTA_ROTH_PATTERN_COUNT)
    for index, pattern in enumerate(_load_klekota_roth_patterns()):
        if molecule.HasSubstructMatch(pattern):
            fingerprint.SetBit(index)
    return fingerprint


__all__: list[str] = []
