# Quick Start

The fastest way to try MOLRAPTOR is with the bundled example configuration.

## Install

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e .
```

## Prepare Your Input

MOLRAPTOR expects a CSV file with at least a `PubChem CID` and `Label` column:

```text
PubChem CID,Label
2244,1
3672,0
5090,1
```

Edit `examples/example_config.yaml` to point to your input file and configure
the output paths and fingerprint parameters.

## Run the Pipeline

```bash
molraptor run --config examples/example_config.yaml
```

With verbose logging:

```bash
molraptor run --config examples/example_config.yaml --verbose
```

## Run the File-based Pipeline from Python

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig.load("examples/example_config.yaml")
run(config)
```

## Choose the Right Interface

Use the public in-memory Morgan API when SMILES are already available and you
need NumPy fingerprints and metadata without creating files. It requires no
labels or pipeline configuration, and reports invalid inputs while returning
rows for valid inputs.

Use `run(config)` when you need the complete file-based workflow shown below.
That pipeline fetches and curates data and writes configured artifacts. Its
fingerprint stage is strict: any invalid SMILES aborts fingerprint and label
output rather than returning a partial matrix. See the [API Reference](api.md)
for the in-memory example and full result contract.

## Expected Workflow

```text
CSV (CIDs + labels) -> fetch -> curate -> fingerprint -> validate -> .npy / .csv
```

## Output Artifacts

After a successful run, the following files are written to `artifacts/`:

```text
artifacts/
├── morgan_fp.csv          # Morgan fingerprints (human-readable)
├── morgan_db_*.npy        # Morgan fingerprints (NumPy array)
├── labels.npy             # Target labels (NumPy array)
└── summary.txt            # Execution report
```
