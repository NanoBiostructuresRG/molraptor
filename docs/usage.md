# Usage

This guide covers installation, CSV/TXT inputs, fingerprint selection, the
command-line interface, Python workflows, output artifacts, and failure
handling. For detailed public contracts, see the
[API Reference](api.md).

## Installation

MOLRAPTOR supports Python 3.11 and 3.12.

Install the latest published version from PyPI:

```bash
python -m pip install molraptor
```

Install the current repository in editable mode for local development:

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e .
```

Install optional development or documentation tools only when needed:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[docs]"
```

A conda environment is also provided:

```bash
conda env create -f environment.yml
conda activate molraptor_env
python -m pip install -e .
```

Verify the installation:

```bash
molraptor --help
molraptor run --help
molraptor --version
```

## Choose an Interface

MOLRAPTOR provides two interfaces backed by the same in-memory scientific
encoder:

* Use the **command-line or Python file workflow** when SMILES are stored in a
  CSV or UTF-8 TXT file and you need persisted NumPy, CSV, and JSON artifacts.
* Use the **in-memory Python API** when SMILES are already available as an
  ordered sequence and no file I/O is required.

Both interfaces preserve input order and duplicates. Invalid individual SMILES
remain traceable without preventing valid inputs from being encoded.

Each execution calculates one fingerprint type.

## Supported Fingerprints

MOLRAPTOR supports these public fingerprint identifiers:

| Identifier   | Fingerprint         | Width                       |
| ------------ | ------------------- | --------------------------- |
| `morgan`     | Morgan              | Configurable; default: 2048 |
| `featmorgan` | Feature Morgan      | 2048                        |
| `atompair`   | Atom Pair           | 2048                        |
| `rdk`        | RDKit topological   | 2048                        |
| `torsion`    | Topological Torsion | 2048                        |
| `layered`    | Layered             | 2048                        |
| `maccs`      | MACCS keys          | 167                         |

Morgan is the default fingerprint and accepts configurable settings. The other
fingerprint types use fixed effective profiles.

## Command-Line Quick Start

### CSV input

For a CSV containing a `SMILES` column:

```bash
molraptor run \
  --input molecules.csv \
  --output-dir artifacts
```

Select another column explicitly with `--smiles-column`:

```bash
molraptor run \
  --input molecules.csv \
  --smiles-column SMILES_Harmonized \
  --output-dir artifacts
```

MOLRAPTOR does not guess aliases or select a different SMILES column
implicitly.

### TXT input

For a UTF-8 TXT file containing one SMILES per line:

```bash
molraptor run \
  --input molecules.txt \
  --output-dir artifacts
```

### Fingerprint selection

Select a fingerprint with `--fingerprint`:

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

### Morgan settings

The default Morgan profile uses radius 2, 2048 bits, and chirality disabled.

```bash
molraptor run \
  --input molecules.csv \
  --smiles-column SMILES \
  --fingerprint morgan \
  --output-dir artifacts \
  --radius 3 \
  --fp-size 1024 \
  --include-chirality
```

`--radius`, `--fp-size`, and `--include-chirality` are valid only with
`--fingerprint morgan`. MOLRAPTOR rejects these options for other fingerprint
types rather than silently ignoring them.

## Command-Line Interface

Display command help or the installed package version:

```bash
molraptor --help
molraptor run --help
molraptor --version
```

The `molraptor run` command accepts:

| Option                 | Purpose                                             |
| ---------------------- | --------------------------------------------------- |
| `--input PATH`         | Source CSV or UTF-8 TXT file                        |
| `--smiles-column NAME` | CSV column containing SMILES; default: `SMILES`     |
| `--fingerprint TYPE`   | Fingerprint type; default: `morgan`                 |
| `--output-dir PATH`    | Destination directory for the four output artifacts |
| `--radius INTEGER`     | Morgan neighborhood radius; default: `2`            |
| `--fp-size INTEGER`    | Morgan bit-vector size; default: `2048`             |
| `--include-chirality`  | Include chirality in Morgan fingerprint generation  |

The input format is selected from the source-file extension. YAML
configuration and `--config` are not part of the current interface.

## Input Formats

### CSV

A CSV input must contain the explicitly configured SMILES column.

```csv
SMILES
CCO
c1ccccc1
not-a-smiles
CCO
```

The default column name is `SMILES`. Input order, duplicates, and empty cells
are preserved for validation and traceability.

Only the selected column is used for encoding. MOLRAPTOR does not retrieve
records, infer labels, curate unrelated columns, or replace the supplied
molecular representations.

### TXT

A TXT input must be UTF-8 encoded and contain one SMILES record per line.

```text
CCO
c1ccccc1
not-a-smiles
CCO
```

MOLRAPTOR removes only the trailing `CRLF`, `CR`, or `LF` line ending from each
record. All other content is preserved, including order, duplicates,
whitespace, and empty lines.

## Python File Workflow

Configure and execute a Morgan CSV/TXT workflow directly from Python:

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

Select another fingerprint through `fingerprint_type` and omit the Morgan
profile:

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig(
    input_path="molecules.csv",
    smiles_column="SMILES",
    output_dir="artifacts",
    fingerprint_type="maccs",
)

result = run(config)

print(result.fingerprints.shape)
# (N_valid, 167)
```

`run` reads the ordered input records, calls the public in-memory encoder,
validates the global workflow result, and publishes the four output artifacts.

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

## In-Memory Encoding

Use `encode_fingerprints` when the SMILES are already available in memory.

Morgan remains compatible with the existing positional profile contract:

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

Select another fingerprint with the keyword-only `fingerprint_type` argument:

```python
from molraptor import encode_fingerprints

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1", "CCO"],
    fingerprint_type="maccs",
)

print(result.fingerprints.shape)
# (3, 167)

print(result.profile["algorithm"])
# maccs
```

The fingerprint matrix:

* contains one row per valid input;
* has shape `(N_valid, fingerprint_width)`;
* uses the `numpy.uint8` dtype;
* contains binary `0` or `1` values;
* preserves the order and duplicates of valid inputs;
* does not contain artificial zero-vector rows for invalid inputs.

The encoder performs no file I/O. MOLRAPTOR parses each supplied SMILES with
RDKit to construct the molecular graph required for fingerprint calculation,
but it does not output a canonicalized or alternative SMILES representation.

## Output Contract

A successful file workflow writes exactly:

```text
artifacts/
|-- fingerprints.npy
|-- fingerprints.csv
|-- input_statuses.csv
`-- encoding_metadata.json
```

### `fingerprints.npy`

Binary fingerprint matrix for the selected fingerprint type, stored as a NumPy
array.

| Property | Value                          |
| -------- | ------------------------------ |
| Shape    | `(N_valid, fingerprint_width)` |
| Dtype    | `numpy.uint8`                  |
| Rows     | Valid inputs only              |
| Values   | Binary `0` or `1`              |

### `fingerprints.csv`

The same binary fingerprint matrix in CSV form. Its row order is identical to
`fingerprints.npy` and follows `fingerprint_index`.

### `input_statuses.csv`

One record is written for every original input.

```text
input_index
input_smiles
status
fingerprint_index
invalid_reason
```

| Column              | Meaning                                            |
| ------------------- | -------------------------------------------------- |
| `input_index`       | Zero-based position in the original input sequence |
| `input_smiles`      | Exact string supplied to MOLRAPTOR                 |
| `status`            | `valid` or `invalid`                               |
| `fingerprint_index` | Corresponding matrix row for a valid input         |
| `invalid_reason`    | Stable reason for an invalid input                 |

`input_index` and `fingerprint_index` are intentionally different:

* `input_index` refers to every original record, including invalid inputs;
* `fingerprint_index` refers only to rows in the valid fingerprint matrix.

For example, if input index 1 is invalid, input index 2 may map to fingerprint
index 1.

Current invalid reasons are:

* `parse_failure`: RDKit could not parse the supplied string;
* `empty_molecule`: parsing produced a molecule with zero atoms.

### `encoding_metadata.json`

The metadata file records execution-level provenance:

* `source_file_name`;
* `input_format`;
* `smiles_column`;
* `input_count`;
* `profile`;
* `valid_indices`;
* `valid_count`;
* `invalid_count`;
* `matrix_shape`;
* `matrix_dtype`;
* `molraptor_version`;
* `rdkit_version`;
* `ordered_input_hash`;
* `profile_hash`.

The `profile` field contains the complete effective profile for the selected
fingerprint type.

For TXT input, `smiles_column` is `null`.

The metadata stores the source filename but not its local filesystem path. It
does not duplicate the row-level records from `input_statuses.csv`.

## Failure Isolation

MOLRAPTOR separates row-level invalid inputs from global workflow failures.

An invalid individual SMILES:

* receives an entry in `input_statuses.csv`;
* does not produce a fingerprint matrix row;
* does not prevent valid inputs from being encoded.

The file workflow stops without publishing final artifacts when:

* the configuration is invalid;
* the fingerprint type is unsupported;
* Morgan-only settings are supplied for another fingerprint type;
* the input file is inaccessible or uses an unsupported format;
* the configured CSV SMILES column is missing;
* no valid SMILES remain;
* an output artifact cannot be written.

The in-memory encoder may return an empty matrix with shape
`(0, fingerprint_width)`. The zero-valid-input rule is enforced by the file
workflow because a persisted fingerprint dataset with no valid rows is not
considered a successful run.

## Reproducibility

Every encoding result records:

| Field                | Purpose                                                      |
| -------------------- | ------------------------------------------------------------ |
| `ordered_input_hash` | SHA-256 digest of the exact ordered input strings            |
| `profile_hash`       | SHA-256 digest of the complete effective fingerprint profile |
| `molraptor_version`  | MOLRAPTOR version used for encoding                          |
| `rdkit_version`      | RDKit version used for parsing and fingerprinting            |
| `matrix_shape`       | Number of valid rows and fingerprint width                   |
| `matrix_dtype`       | Persisted fingerprint matrix dtype                           |

The ordered-input hash includes order, duplicates, whitespace, and empty
strings. The profile hash covers the selected fingerprint algorithm and all
effective settings, including defaults.
