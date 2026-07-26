# MOLRAPTOR: Molecular Fingerprint Rapid Generator


[![Version](https://img.shields.io/badge/version-v0.4.1-blue.svg)](https://pypi.org/project/molraptor/)
[![PyPI](https://img.shields.io/pypi/v/molraptor.svg)](https://pypi.org/project/molraptor/)
[![Python](https://img.shields.io/pypi/pyversions/molraptor.svg)](https://pypi.org/project/molraptor/)
[![License: LGPL v3+](https://img.shields.io/badge/License-LGPL_v3%2B-blue.svg)](LICENSE)
[![CI](https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml/badge.svg)](https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-teal.svg)](https://nanobiostructuresrg.github.io/molraptor/)


**MOLRAPTOR** is an open-source cheminformatics software package with a Python API and command-line interface for reproducible, SMILES-first generation of binary molecular fingerprints.

**MOLRAPTOR** provides:

- an in-memory Python API for direct SMILES encoding;
- a command-line workflow for CSV and TXT inputs;
- Morgan, Feature Morgan, Atom Pair, RDKit topological, Topological Torsion, Layered, and MACCS fingerprints;
- fixed and serializable effective profiles, with configurable Morgan settings;
- deterministic input and profile hashes;
- traceable handling of valid and invalid inputs;
- NumPy and CSV fingerprint outputs.

**MOLRAPTOR** does not retrieve, curate, harmonize, canonicalize, or replace supplied SMILES. Each input string is parsed by RDKit only to construct the molecular graph required for the selected fingerprint calculation.

## Project Identity

```text
Project: MOLRAPTOR
PyPI distribution: molraptor
Python package: molraptor
Command-line interface: molraptor
License: LGPL-3.0-or-later
Development status: alpha / pre-stable
```

MOLRAPTOR uses a SMILES-only workflow and does not include the legacy PubChem-oriented pipeline.

## Documentation

The documentation is published at:

https://nanobiostructuresrg.github.io/molraptor/

Main pages:

- [Usage](https://nanobiostructuresrg.github.io/molraptor/usage/)
- [API Reference](https://nanobiostructuresrg.github.io/molraptor/api/)
- [Changelog](https://nanobiostructuresrg.github.io/molraptor/changelog/)

## Installation

Install the latest published version from PyPI:

```bash
python -m pip install molraptor
```

Install the current repository for local development:

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e .
```

Install development or documentation dependencies:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[docs]"
```

## Command-Line Quick Start

### CSV input

For a CSV containing a `SMILES` column:

```bash
molraptor run \
  --input molecules.csv \
  --output-dir artifacts
```

Use `--smiles-column` when the source column has another name:

```bash
molraptor run \
  --input molecules.csv \
  --smiles-column SMILES_Harmonized \
  --output-dir artifacts
```

### TXT input

A TXT input must contain one SMILES per line:

```bash
molraptor run \
  --input molecules.txt \
  --output-dir artifacts
```

### Fingerprint selection

Morgan is the default fingerprint. Select another supported fingerprint with `--fingerprint`:

```bash
molraptor run \
  --input molecules.csv \
  --fingerprint maccs \
  --output-dir artifacts
```

Supported values are:

```text
morgan
featmorgan
atompair
rdk
torsion
layered
maccs
```

Each execution calculates one fingerprint type.

### Morgan settings

The default profile uses radius 2, 2048 bits, and chirality disabled.

```bash
molraptor run \
  --input molecules.csv \
  --smiles-column SMILES \
  --output-dir artifacts \
  --radius 3 \
  --fp-size 1024 \
  --include-chirality
```

View the complete CLI help:

```bash
molraptor --help
molraptor run --help
molraptor --version
```

## Python Quick Start

### In-memory encoding

```python
from molraptor import MorganFingerprintProfile, encode_fingerprints

profile = MorganFingerprintProfile(
    radius=2,
    fp_size=2048,
    include_chirality=False,
)

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1", "CCO"],
    profile,
)

print(result.fingerprints.shape)
# (3, 2048)

print(result.valid_indices)
# (0, 2, 3)

for status in result.input_statuses:
    print(status)
```

### Selecting another fingerprint

Use the keyword-only `fingerprint_type` argument to select another supported fingerprint:

```python
from molraptor import encode_fingerprints

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1"],
    fingerprint_type="maccs",
)

print(result.fingerprints.shape)
# (2, 167)

print(result.profile["algorithm"])
# maccs
```

Morgan remains the default and accepts a configurable `MorganFingerprintProfile`. The other fingerprint types use their fixed effective profiles.

The returned fingerprint matrix:

- contains one row per valid input;
- has shape `(N_valid, fp_size)`;
- uses the `numpy.uint8` dtype;
- preserves the order and duplicates of valid inputs.

Invalid inputs remain traceable through `result.input_statuses` and are never represented by artificial zero vectors.

### File workflow

```python
from molraptor import (
    MolraptorConfig,
    MorganFingerprintProfile,
    run,
)

config = MolraptorConfig(
    input_path="molecules.csv",
    smiles_column="SMILES_Harmonized",
    output_dir="artifacts",
    profile=MorganFingerprintProfile(
        radius=2,
        fp_size=2048,
        include_chirality=False,
    ),
)

result = run(config)
```

The file workflow and command-line interface use the same in-memory scientific encoder.

## Inputs

MOLRAPTOR accepts:

### CSV

A CSV file with an explicitly selected SMILES column.

```csv
SMILES_Harmonized
CCO
c1ccccc1
not-a-smiles
```

The default column name is `SMILES`. MOLRAPTOR does not guess aliases or choose a column implicitly.

### TXT

A UTF-8 text file containing one SMILES per line.

```text
CCO
c1ccccc1
not-a-smiles
```

Input order, duplicates, and empty input records are preserved for validation and traceability.

## Outputs

A successful file workflow writes exactly four artifacts:

```text
artifacts/
├── fingerprints.npy
├── fingerprints.csv
├── input_statuses.csv
└── encoding_metadata.json
```

### `fingerprints.npy`

Binary fingerprint matrix for the selected fingerprint type, stored as a NumPy array.

- shape: `(N_valid, fp_size)`
- dtype: `numpy.uint8`
- rows: valid inputs only

### `fingerprints.csv`

The same binary fingerprint matrix in tabular CSV form.

### `input_statuses.csv`

One record for every original input:

```text
input_index
input_smiles
status
fingerprint_index
invalid_reason
```

- `input_index` is the zero-based position in the original input sequence.
- `input_smiles` is the exact string supplied to MOLRAPTOR.
- `status` is `valid` or `invalid`.
- `fingerprint_index` identifies the corresponding matrix row for a valid input.
- `invalid_reason` records `parse_failure` or `empty_molecule` for invalid inputs.

MOLRAPTOR does not add a canonicalized or alternative SMILES representation.

### `encoding_metadata.json`

Encoding-level metadata containing:

- source filename and input format;
- configured CSV SMILES column, when applicable;
- total, valid, and invalid input counts;
- complete effective fingerprint profile;
- matrix shape and dtype;
- valid-input alignment;
- MOLRAPTOR and RDKit versions;
- deterministic ordered-input and profile hashes.

The metadata stores the source filename but not its local filesystem path.

## Failure Isolation

MOLRAPTOR separates row-level failures from global workflow failures.

An invalid individual SMILES:

- receives an entry in `input_statuses.csv`;
- does not produce a fingerprint matrix row;
- does not prevent valid inputs from being processed.

The file workflow stops without producing final artifacts when:

- the input configuration is invalid;
- the CSV SMILES column is missing;
- the input file cannot be accessed;
- no valid SMILES remain.

## Public API

The public package exports are:

```python
from molraptor import (
    DataValidator,
    FingerprintEncodingResult,
    FingerprintInputStatus,
    MolraptorConfig,
    MorganFingerprintProfile,
    encode_fingerprints,
    run,
    validate_config,
    __version__,
)
```

The main scientific contracts are:

- `MorganFingerprintProfile`: complete effective Morgan settings;
- `encode_fingerprints`: deterministic in-memory SMILES encoding;
- `FingerprintEncodingResult`: fingerprint matrix and reproducibility metadata;
- `FingerprintInputStatus`: per-input validity and matrix-row alignment;
- `MolraptorConfig`: validated CSV/TXT workflow configuration;
- `run`: file workflow execution.

Modules and objects not exported from `molraptor.__all__` are internal implementation details and may change before version 1.0.

## Scientific and Architectural Scope

| MOLRAPTOR does | MOLRAPTOR does not |
|---|---|
| Accept user-provided SMILES from Python, CSV, or TXT. | Retrieve molecular records from PubChem or other databases. |
| Parse SMILES with RDKit for fingerprint calculation. | Curate, harmonize, canonicalize, or replace SMILES. |
| Generate supported binary molecular fingerprints. | Generate labels or activity classes. |
| Record profiles, hashes, versions, and row alignment. | Select or recommend a scientifically preferred fingerprint. |
| Preserve order and duplicates. | Train or evaluate machine-learning models. |
| Isolate invalid individual inputs. | Calculate molecular descriptors or 3D conformations. |

MOLRAPTOR uses a lightweight modular boundary:

```text
Python API / CSV / TXT / CLI
              ↓
     in-memory fingerprint core
              ↓
      NumPy / CSV / JSON
```

Input readers, workflow orchestration, and output writers depend on the scientific core. The core performs no file I/O and has no dependency on the command-line interface or external applications.

## Reproducibility

Each encoding result records:

- `ordered_input_hash`: SHA-256 digest of the exact ordered input strings, including duplicates and empty strings;
- `profile_hash`: SHA-256 digest of the complete effective fingerprint profile;
- MOLRAPTOR version;
- RDKit version;
- fingerprint matrix shape and dtype.

These values allow consumers to identify the input sequence, scientific configuration, and runtime used for an encoding result.

## Development Validation

Run the test suite:

```bash
python -m pytest tests -q
```

Validate documentation and package artifacts:

```bash
mkdocs build --strict
python -m build --no-isolation
python -m twine check dist/*
```

Check the command-line entry points:

```bash
molraptor --help
molraptor run --help
molraptor --version
```

## Citation

If you use MOLRAPTOR in your research, please cite it using the metadata in
[CITATION.cff](CITATION.cff).

```text
Contreras-Torres, F. F. (2026). MOLRAPTOR: Molecular Fingerprint Rapid Generator. Zenodo. https://doi.org/10.5281/zenodo.20434420
```


## Author

Developed by **Flavio F. Contreras-Torres**
Tecnológico de Monterrey

## License

MOLRAPTOR is licensed under the [GNU Lesser General Public License version 3 or later](LICENSE).

SPDX identifier: `LGPL-3.0-or-later`
