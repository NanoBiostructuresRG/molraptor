# Usage

This guide covers installation, the file-based pipeline, the command-line
interface, and YAML configuration. For the zero-file-I/O Morgan encoder, see
the [API Reference](api.md#in-memory-morgan-fingerprinting).

## Installation

MOLRAPTOR supports Python 3.11 and 3.12. Clone the repository and install the
package in editable mode:

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e .
```

This installs both the `molraptor` Python package and console command.

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
molraptor --version
```

## Choose an Interface

MOLRAPTOR provides two distinct workflows:

- Use the public in-memory Morgan API when SMILES are already available and
  you need NumPy fingerprints and metadata without files, labels, or pipeline
  configuration. Invalid inputs are reported while valid results are retained.
- Use the file-based pipeline when you need PubChem fetching, curation,
  fingerprint generation, integrity validation, and configured CSV/NPY
  artifacts. Its fingerprint stage is strict: an invalid SMILES aborts
  fingerprint and label output.

## File-based Quick Start

The pipeline expects a CSV containing at least `PubChem CID` and `Label`:

```text
PubChem CID,Label
2244,1
3672,0
5090,1
```

Point `examples/example_config.yaml` at the input file, then run:

```bash
molraptor run --config examples/example_config.yaml
```

The same pipeline is available from Python:

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig.load("examples/example_config.yaml")
run(config)
```

The complete workflow is:

```text
CSV (CIDs + labels) -> fetch -> curate -> fingerprint -> validate -> NPY / CSV
```

After a successful run, configured outputs include:

```text
artifacts/
|-- morgan_fp.csv       # Human-readable fingerprint matrix
|-- morgan_db_*.npy     # NumPy fingerprint matrix
|-- labels.npy          # Labels aligned with fingerprint rows
`-- summary.txt         # Pipeline report
```

## Command-line Interface

Display command help or package version:

```bash
molraptor --help
molraptor run --help
molraptor --version
```

Run with the bundled configuration, a custom configuration, verbose logging,
or both:

```bash
molraptor run
molraptor run --config path/to/config.yaml
molraptor run --verbose
molraptor run --config path/to/config.yaml --verbose
```

The `--config` flag defaults to `examples/example_config.yaml`. The `--verbose`
flag enables `INFO`-level progress messages; otherwise logging begins at
`WARNING`.

## Configuration

MOLRAPTOR loads one YAML file through `MolraptorConfig`. A complete example is:

```yaml
paths:
  raw_input_file: data/dataset.csv
  raw_output_file: data/properties.csv
  curated_output_file: data/properties_curated.csv
  error_log_file: logs/error_cids.txt
  fingerprint_output_file: artifacts/morgan_fp.csv
  fingerprint_array_file: artifacts/morgan_db.npy
  labels_output_file: artifacts/labels.npy

pubchem:
  properties:
    - MolecularWeight
    - XLogP
    - HBondDonorCount
    - HBondAcceptorCount
    - RotatableBondCount
    - TPSA
    - Complexity
    - SMILES
  timeout: 5
  max_retries: 3
  sleep_seconds: 0.2
  chunk_size: 400

fingerprint:
  radius: 2
  size: 1024

curate:
  required_columns:
    - PubChem CID
    - Label
    - MolecularWeight
    - Complexity
    - SMILES
  dtype_map:
    Label: int64
```

### `paths`

| Key | Purpose |
|-----|---------|
| `raw_input_file` | Input dataset containing PubChem CIDs and labels |
| `raw_output_file` | Dataset merged with fetched PubChem properties |
| `curated_output_file` | Filtered and type-normalized dataset |
| `error_log_file` | CIDs that failed during PubChem fetching |
| `fingerprint_output_file` | Morgan fingerprints as CSV |
| `fingerprint_array_file` | Morgan fingerprints as a NumPy array |
| `labels_output_file` | Labels aligned with fingerprint rows |

### `pubchem`

| Key | Default | Purpose |
|-----|---------|---------|
| `properties` | Required | PubChem properties to fetch |
| `timeout` | `5` | Request timeout in seconds |
| `max_retries` | `3` | Maximum request attempts |
| `sleep_seconds` | `0.2` | Delay between chunk requests |
| `chunk_size` | `400` | CIDs requested per chunk |

### `fingerprint`

| Key | Purpose |
|-----|---------|
| `radius` | Morgan fingerprint radius |
| `size` | Fingerprint bit-vector size |

The file-based step maps these values to the public Morgan profile. It rejects
the complete fingerprint operation if any input SMILES is invalid and reports
the affected zero-based input row indices before writing fingerprint or label
artifacts.

### `curate`

| Key | Purpose |
|-----|---------|
| `required_columns` | Columns that must exist and contain non-null values |
| `dtype_map` | Output dtype enforcement, such as `Label: int64` |
