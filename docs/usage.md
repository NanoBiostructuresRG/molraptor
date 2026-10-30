# Usage

This guide covers installation, supported fingerprint algorithms, command-line
use, Python workflows, input formats, output artifacts, and failure behavior.

For the public Python contracts and encoding metadata, see the
[API Reference](api.md).

## Installation

MOLRAPTOR requires Python 3.11 or later.

Install the current published version from PyPI:

```bash
python -m pip install molraptor
```

Verify the installation:

```bash
molraptor --help
molraptor run --help
molraptor --version
```

For development and contribution instructions, see
[CONTRIBUTING.md](https://github.com/NanoBiostructuresRG/molraptor/blob/main/CONTRIBUTING.md).

## Choose an Interface

MOLRAPTOR provides two user interfaces backed by the same in-memory fingerprint
encoder.

Use the **command-line interface or Python file workflow** when SMILES are
stored in CSV or UTF-8 TXT files and you want persisted output artifacts.

Use the **in-memory Python API** when SMILES are already available as an
ordered Python sequence and file I/O is not required.

Both interfaces preserve input order and duplicates. Invalid individual SMILES
remain traceable without preventing valid inputs from being encoded.

Each execution uses one fingerprint algorithm.

## Supported Fingerprint Algorithms

MOLRAPTOR v0.5.0 supports 10 fingerprint algorithms:

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

The selected algorithm determines the representation class.

Morgan is the default algorithm and exposes configurable settings. The other
nine algorithms use fixed effective profiles.

The representation classes have different numerical meanings:

- **Binary** coordinates encode presence or absence according to the selected
  algorithm. Hashed fingerprints may map more than one molecular feature to
  the same bit.
- **Count** coordinates store multiplicities in fixed-width hashed bins.
  Different molecular features may contribute to the same bin through
  collisions.
- **MinHash** coordinates are sketch values summarizing an encoded shingle set.
  They are not molecular feature-presence bits or feature counts.

## Command-Line Interface

### CSV input

For a CSV file containing a `SMILES` column:

```bash
molraptor run \
  --input molecules.csv \
  --output-dir artifacts
```

When the source column has another name, select it explicitly:

```bash
molraptor run \
  --input molecules.csv \
  --smiles-column SMILES_Harmonized \
  --output-dir artifacts
```

MOLRAPTOR does not guess column aliases or select another SMILES column
implicitly.

### TXT input

For a UTF-8 TXT file containing one SMILES record per line:

```bash
molraptor run \
  --input molecules.txt \
  --output-dir artifacts
```

### Select a fingerprint algorithm

Use `--fingerprint` to select another algorithm:

```bash
molraptor run \
  --input molecules.csv \
  --fingerprint map4 \
  --output-dir artifacts
```

Supported identifiers are:

```text
morgan
featmorgan
atompair
rdk
torsion
layered
maccs
klekotaroth
mhfp6
map4
```

### Configure Morgan

The default Morgan profile uses:

```text
radius = 2
width = 2048
chirality = disabled
```

Configure these settings through the command line:

```bash
molraptor run \
  --input molecules.csv \
  --fingerprint morgan \
  --radius 3 \
  --fp-size 1024 \
  --include-chirality \
  --output-dir artifacts
```

`--radius`, `--fp-size`, and `--include-chirality` are valid only for Morgan.
MOLRAPTOR rejects these options for the other fingerprint algorithms rather
than silently ignoring them.

### Command reference

The `molraptor run` command accepts:

| Option | Purpose |
|---|---|
| `--input PATH` | Source CSV or UTF-8 TXT file |
| `--smiles-column NAME` | CSV column containing SMILES; default: `SMILES` |
| `--fingerprint TYPE` | Fingerprint algorithm identifier; default: `morgan` |
| `--output-dir PATH` | Destination directory for output artifacts |
| `--radius INTEGER` | Morgan neighborhood radius; default: `2` |
| `--fp-size INTEGER` | Morgan fingerprint width; default: `2048` |
| `--include-chirality` | Include chirality in Morgan fingerprint generation |

Display the complete command help with:

```bash
molraptor --help
molraptor run --help
```

## Input Formats

### CSV

A CSV input must contain the configured SMILES column.

```csv
SMILES
CCO
c1ccccc1
not-a-smiles
CCO
```

The default column name is `SMILES`.

Only the selected column is used for fingerprint encoding. Input order,
duplicates, and empty cells are preserved for validation and correspondence.

MOLRAPTOR does not retrieve molecular records or infer labels from the input.

It also does not curate, harmonize, canonicalize, or replace user-supplied
SMILES as an input-preprocessing step.

### TXT

A TXT input must be UTF-8 encoded and contain one SMILES record per line.

```text
CCO
c1ccccc1
not-a-smiles
CCO
```

MOLRAPTOR removes only the trailing `CRLF`, `CR`, or `LF` line ending from each
record.

All other content is preserved, including:

- order;
- duplicates;
- whitespace;
- empty lines.

The supplied strings are parsed with RDKit to construct the molecular graph
required for fingerprint calculation.

The source-input boundary described here does not constrain
algorithm-internal transformations used to construct a fingerprint
representation.

## Python File Workflow

The file workflow can also be executed directly from Python.

### Morgan

```python
from molraptor import (
    MolraptorConfig,
    MorganFingerprintProfile,
    run,
)

config = MolraptorConfig(
    input_path="molecules.csv",
    smiles_column="SMILES",
    output_dir="artifacts",
    fingerprint_type="morgan",
    profile=MorganFingerprintProfile(
        radius=2,
        fp_size=2048,
        include_chirality=False,
    ),
)

result = run(config)

print(result.fingerprints.shape)
print(result.valid_indices)
```

### Another fingerprint algorithm

For another algorithm, set `fingerprint_type` and omit the Morgan profile:

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig(
    input_path="molecules.csv",
    smiles_column="SMILES",
    output_dir="artifacts",
    fingerprint_type="map4",
)

result = run(config)

print(result.fingerprints.shape)
# (N_valid, 1024)
```

The API name `fingerprint_type` is retained for compatibility. Conceptually,
it selects a fingerprint algorithm; the representation is determined by that
algorithm.

For TXT input, `smiles_column` is not used:

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig(
    input_path="molecules.txt",
    output_dir="artifacts",
    fingerprint_type="rdk",
)

result = run(config)
```

`run()` reads the ordered input records, delegates encoding to the in-memory
API, validates the workflow result, and publishes the output artifacts.

## In-Memory Encoding

Use `encode_fingerprints()` when the SMILES are already available as an ordered
Python sequence.

### Morgan

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
```

The positional `MorganFingerprintProfile` form remains supported for
compatibility.

### Another fingerprint algorithm

Use the keyword-only `fingerprint_type` argument:

```python
from molraptor import encode_fingerprints

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1", "CCO"],
    fingerprint_type="map4",
)

print(result.fingerprints.shape)
# (3, 1024)

print(result.profile["algorithm"])
# map4

print(result.profile["representation"])
# minhash

print(result.valid_indices)
# (0, 2, 3)
```

The returned matrix:

- contains one row per valid input;
- has shape `(N_valid, fingerprint_width)`;
- uses a representation-dependent dtype;
- preserves the order and duplicates of valid inputs;
- does not contain artificial zero-vector rows for invalid inputs.

The dtype contract is:

```text
binary  → uint8
count   → uint32
minhash → uint32
```

For detailed Python contracts, effective profiles, and metadata fields, see
the [API Reference](api.md).

## Output Artifacts

A successful file workflow writes exactly four artifacts:

```text
artifacts/
├── fingerprints.npy
├── fingerprints.csv
├── input_statuses.csv
└── encoding_metadata.json
```

### `fingerprints.npy`

NumPy matrix containing one fingerprint representation per valid input.

| Property | Value |
|---|---|
| Shape | `(N_valid, fingerprint_width)` |
| Rows | Valid inputs only |
| Dtype | binary → `uint8`; count → `uint32`; MinHash → `uint32` |
| Values | Representation-dependent numerical coordinates |

### `fingerprints.csv`

Tabular serialization of the same matrix values.

Its row order matches `fingerprints.npy` and follows `fingerprint_index`.

### `input_statuses.csv`

Contains one record for every original input:

```text
input_index
input_smiles
status
fingerprint_index
invalid_reason
```

| Column | Meaning |
|---|---|
| `input_index` | Zero-based position in the original input sequence |
| `input_smiles` | Exact string supplied to MOLRAPTOR |
| `status` | `valid` or `invalid` |
| `fingerprint_index` | Corresponding matrix row for a valid input |
| `invalid_reason` | Reason recorded for an invalid input |

`input_index` and `fingerprint_index` represent different coordinate systems.

`input_index` refers to the complete original input sequence.

`fingerprint_index` refers only to rows in the valid fingerprint matrix.

For example, if input index `1` is invalid, input index `2` may correspond to
fingerprint index `1`.

Current invalid reasons are:

- `parse_failure` — RDKit could not parse the supplied string;
- `empty_molecule` — parsing produced a molecule with zero atoms.

### `encoding_metadata.json`

Records execution-level encoding metadata, including:

- source filename and input format;
- configured CSV SMILES column, when applicable;
- input counts;
- complete effective fingerprint profile;
- valid-input alignment;
- matrix shape and dtype;
- MOLRAPTOR version;
- RDKit version;
- ordered-input hash;
- profile hash.

The source filename is recorded without its local filesystem path.

Row-level input information remains in `input_statuses.csv` rather than being
duplicated in the metadata file.

For the exact metadata and hash contracts, see the
[API Reference](api.md).

## Failure Behavior

MOLRAPTOR distinguishes invalid individual inputs from failures of the complete
file workflow.

An invalid individual SMILES:

- receives an entry in `input_statuses.csv`;
- does not produce a fingerprint matrix row;
- does not prevent valid inputs from being encoded.

The file workflow stops without publishing final artifacts when:

- configuration validation fails;
- the fingerprint algorithm identifier is unsupported;
- Morgan-only settings are supplied for another algorithm;
- the input file is inaccessible;
- the input format is unsupported;
- the configured CSV SMILES column is missing;
- no valid SMILES remain;
- artifact publication fails.

The in-memory API behaves differently when every supplied input is invalid: it
can return an empty matrix with shape:

```text
(0, fingerprint_width)
```

The requirement for at least one valid input belongs to the file workflow, not
to `encode_fingerprints()`.

## Next Steps

For public Python objects, effective profiles, result alignment, metadata, and
hash definitions, continue to the [API Reference](api.md).

For release-specific changes, see the [Changelog](changelog.md).