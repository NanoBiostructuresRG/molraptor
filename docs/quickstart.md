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

## Run from Python

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig.load("examples/example_config.yaml")
run(config)
```

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