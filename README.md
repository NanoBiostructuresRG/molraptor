# MOLRAPTOR — Molecular Fingerprint Rapid Generator

[![Version](https://img.shields.io/badge/version-v0.5.0-blue.svg)](https://pypi.org/project/molraptor/)
[![PyPI](https://img.shields.io/pypi/v/molraptor.svg)](https://pypi.org/project/molraptor/)
[![Python](https://img.shields.io/pypi/pyversions/molraptor.svg)](https://pypi.org/project/molraptor/)
[![License: LGPL v3+](https://img.shields.io/badge/License-LGPL_v3%2B-blue.svg)](LICENSE)
[![CI](https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml/badge.svg)](https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-teal.svg)](https://nanobiostructuresrg.github.io/molraptor/)

**MOLRAPTOR** is an open-source Python package and command-line tool for generating molecular fingerprints from ordered SMILES. It preserves the relationship between the supplied molecular input, the effective encoding profile, and the resulting numerical representation.

MOLRAPTOR provides a common workflow for binary, count, and MinHash fingerprints while keeping input correspondence and encoding metadata available for inspection.

## Why MOLRAPTOR?

A fingerprint matrix alone does not identify all the information required to interpret how it was generated. The selected algorithm, representation semantics, effective parameters, source-input correspondence, and software versions are also part of the encoding context.

MOLRAPTOR keeps this information associated with the fingerprint result. Its purpose is not to select a preferred molecular representation, but to make fingerprint encoding explicit and traceable.

## Installation

Install MOLRAPTOR from PyPI:

```bash
python -m pip install molraptor
```

MOLRAPTOR requires Python 3.11 or later.

## Quick Start

### Python

```python
from molraptor import encode_fingerprints

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1"],
    fingerprint_type="map4",
)

print(result.fingerprints.shape)
# (2, 1024)

print(result.profile["algorithm"])
# map4

print(result.profile["representation"])
# minhash

print(result.valid_indices)
# (0, 2)
```

Invalid inputs remain traceable and do not produce artificial zero-vector rows.

### Command line

For a CSV file containing a `SMILES` column:

```bash
molraptor run \
  --input molecules.csv \
  --fingerprint map4 \
  --output-dir artifacts
```

For a UTF-8 TXT file containing one SMILES per line:

```bash
molraptor run \
  --input molecules.txt \
  --fingerprint klekotaroth \
  --output-dir artifacts
```

Morgan is the default fingerprint algorithm.

## Current Capabilities

MOLRAPTOR supports 10 fingerprint algorithms and three representation classes.

| Identifier | Fingerprint | Representation | Width | Dtype |
|---|---|---|---:|---|
| `morgan` | Morgan | binary | configurable; default 2048 | `uint8` |
| `featmorgan` | Feature Morgan | binary | 2048 | `uint8` |
| `atompair` | Atom Pair | count | 2048 | `uint32` |
| `rdk` | RDKit topological | binary | 2048 | `uint8` |
| `torsion` | Topological Torsion | count | 2048 | `uint32` |
| `layered` | Layered | binary | 2048 | `uint8` |
| `maccs` | MACCS keys | binary | 167 | `uint8` |
| `klekotaroth` | Klekota–Roth | binary | 4860 | `uint8` |
| `mhfp6` | MHFP6 | MinHash | 2048 | `uint32` |
| `map4` | MAP4 | MinHash | 1024 | `uint32` |

Morgan supports configurable radius, fingerprint width, and chirality through the public interface. The other nine algorithms use fixed effective profiles.

Each execution uses one fingerprint algorithm. The representation is determined by that algorithm.

The API name `fingerprint_type` is retained for compatibility; conceptually, it selects a fingerprint algorithm.

## Inputs and Outputs

MOLRAPTOR accepts user-provided SMILES through:

- the in-memory Python API;
- CSV files;
- UTF-8 TXT files.

Input order and duplicates are preserved. Invalid individual SMILES are recorded separately from valid fingerprint rows.

A successful file workflow writes four artifacts:

```text
artifacts/
├── fingerprints.npy
├── fingerprints.csv
├── input_statuses.csv
└── encoding_metadata.json
```

The numerical matrix contains valid inputs only. Its dtype depends on the selected representation:

```text
binary  → uint8
count   → uint32
minhash → uint32
```

`input_statuses.csv` preserves the correspondence between the original input sequence and matrix rows, while `encoding_metadata.json` records the effective encoding profile, matrix properties, software versions, and deterministic input and profile hashes.

See the [Usage guide](https://nanobiostructuresrg.github.io/molraptor/usage/) for the complete input and output contracts.

## Scientific Scope

| MOLRAPTOR does | MOLRAPTOR does not |
|---|---|
| Accept user-provided SMILES through Python, CSV, or TXT. | Retrieve molecular records from external databases. |
| Parse supplied SMILES for fingerprint calculation. | Curate, harmonize, canonicalize, or replace supplied SMILES as an input-preprocessing step. |
| Generate binary, count, and MinHash fingerprint representations. | Select or recommend a scientifically preferred fingerprint. |
| Preserve input order, duplicates, and row-level correspondence. | Generate labels or activity classes. |
| Record effective encoding profiles and execution metadata. | Train or evaluate machine-learning models. |
| Isolate invalid individual inputs. | Calculate molecular descriptors or 3D conformations. |

MOLRAPTOR does not modify the user-supplied SMILES as a preprocessing step. The supplied strings are parsed to construct the molecular graph required by the selected fingerprint algorithm. This source-input boundary does not constrain algorithm-internal transformations used to construct a fingerprint representation.

## Encoding Traceability

MOLRAPTOR preserves four related elements of an encoding:

```text
ordered molecular input
          ↓
fingerprint algorithm
          ↓
effective encoding profile
          ↓
numerical representation
```

Each result also records input validity and matrix-row correspondence, MOLRAPTOR and RDKit versions, matrix shape and dtype, and deterministic input and profile hashes.

This allows the numerical representation to be interpreted together with the conditions under which it was generated.

## Documentation

Full documentation is available at:

https://nanobiostructuresrg.github.io/molraptor/

- [Usage](https://nanobiostructuresrg.github.io/molraptor/usage/) — installation, CLI, Python workflows, inputs, outputs, and failure handling.
- [API Reference](https://nanobiostructuresrg.github.io/molraptor/api/) — public Python contracts, fingerprint profiles, representations, metadata, and hashes.
- [Changelog](https://nanobiostructuresrg.github.io/molraptor/changelog/) — release history.

## Help and Contributing

Questions and bug reports can be submitted through the [GitHub issue tracker](https://github.com/NanoBiostructuresRG/molraptor/issues).

Contributions are welcome. See [CONTRIBUTING.md](https://github.com/NanoBiostructuresRG/molraptor/blob/main/CONTRIBUTING.md) for development setup, testing, documentation, and contribution guidelines.

MOLRAPTOR is maintained by the [Nano and Biostructures Research Group](https://nanobiostructuresrg.github.io/).

## Citation

If you use MOLRAPTOR in your research, please cite it using the metadata in [CITATION.cff](https://github.com/NanoBiostructuresRG/molraptor/blob/main/CITATION.cff).

```text
Contreras-Torres, F. F. (2026). MOLRAPTOR: Molecular Fingerprint Rapid Generator. Zenodo. https://doi.org/10.5281/zenodo.20434420
```

## License

MOLRAPTOR is licensed under the [GNU Lesser General Public License version 3 or later](LICENSE).

SPDX identifier: `LGPL-3.0-or-later`