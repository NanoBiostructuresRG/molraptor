# Configuration

MOLRAPTOR reads all settings from a single YAML file passed via `--config`.
The bundled example is `examples/example_config.yaml`.

## Example Configuration

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

Use the file from the CLI:

```bash
molraptor run --config examples/example_config.yaml
```

## Input Layout

MOLRAPTOR expects a CSV file with at least a `PubChem CID` and `Label` column:

```text
data/
└── dataset.csv      <- input file with PubChem CIDs and labels
```

Minimum required columns:

| Column | Description |
|--------|-------------|
| `PubChem CID` | PubChem compound identifier |
| `Label` | Binary class label (0 or 1) |

## Configuration Sections

### `paths`

| Key | Description |
|-----|-------------|
| `raw_input_file` | Input CSV with CIDs and labels |
| `raw_output_file` | Merged CSV after PubChem fetch |
| `curated_output_file` | Filtered CSV after curation |
| `error_log_file` | Log of failed CIDs during fetch |
| `fingerprint_output_file` | Morgan fingerprints as CSV |
| `fingerprint_array_file` | Morgan fingerprints as NumPy array |
| `labels_output_file` | Target labels as NumPy array |

### `pubchem`

| Key | Default | Description |
|-----|---------|-------------|
| `properties` | — | List of PubChem properties to fetch |
| `timeout` | `5` | HTTP request timeout in seconds |
| `max_retries` | `3` | Maximum retry attempts per request |
| `sleep_seconds` | `0.2` | Delay between chunk requests |
| `chunk_size` | `400` | Number of CIDs per API request |

### `fingerprint`

| Key | Default | Description |
|-----|---------|-------------|
| `radius` | `2` | Morgan fingerprint radius |
| `size` | `1024` | Fingerprint bit vector size |

### `curate`

| Key | Description |
|-----|-------------|
| `required_columns` | Columns that must be present and non-null |
| `dtype_map` | Column type enforcement (e.g. `Label: int64`) |

## Outputs

MOLRAPTOR writes all artifacts to `artifacts/`:

```text
artifacts/
├── morgan_fp.csv      # Morgan fingerprints (human-readable)
├── morgan_db_*.npy    # Morgan fingerprints (NumPy array, shape: N×size)
├── labels.npy         # Target labels (NumPy array, shape: N,)
└── summary.txt        # Execution report
```

| Output | Purpose |
|--------|---------|
| `morgan_fp.csv` | Human-readable fingerprint matrix |
| `morgan_db_*.npy` | ML-ready fingerprint array for downstream models |
| `labels.npy` | Target label vector aligned with fingerprints |
| `summary.txt` | Pipeline execution report with dataset statistics |