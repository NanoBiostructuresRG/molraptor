# MOLRAPTOR: Molecular Learning via Rapid Processing of Topological Representations

[![CI](https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml/badge.svg)](https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.1.1-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)]()

**MOLRAPTOR** is a pre-stable modular pipeline for fetching, curating, and
encoding molecular datasets using PubChem data and RDKit's Morgan
fingerprinting algorithm, designed for cheminformatics workflows and phase 1
machine learning applications in computational drug discovery.

## Project Structure

```text
MOLRAPTOR/
├── .github/workflows/
│   ├── ci.yml
│   ├── docs.yml
│   └── publish-to-pypi.yml
├── docs/
│   ├── stylesheets/
│   │   └── extra.css
│   ├── api.md
│   ├── cli.md
│   ├── configuration.md
│   ├── index.md
│   ├── installation.md
│   ├── quickstart.md
│   └── release.md
├── examples/
│   └── example_config.yaml
├── molraptor/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── curate.py
│   ├── fetch.py
│   ├── fingerprint.py
│   ├── fp_integrity.py
│   ├── pipeline.py
│   ├── pubchem.py
│   ├── result_manager.py
│   ├── validators.py
│   └── version.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_public_api.py
│   └── test_version.py
├── .gitignore
├── CHANGELOG.md
├── CITATION.cff
├── COPYING
├── COPYING.LESSER
├── environment.yml
├── LICENSE
├── mkdocs.yml
├── pyproject.toml
└── README.md
```

## Project Identity

```text
Project: MOLRAPTOR
PyPI distribution: molraptor
Import package: molraptor
CLI: molraptor
Version: 0.1.1
License: LGPL-3.0-or-later
Status: alpha / pre-stable
```

## Documentation

The live documentation is published at:

https://nanobiostructuresrg.github.io/molraptor/

Key pages:

- [Installation](https://nanobiostructuresrg.github.io/molraptor/installation/)
- [Quick Start](https://nanobiostructuresrg.github.io/molraptor/quickstart/)
- [CLI Reference](https://nanobiostructuresrg.github.io/molraptor/cli/)
- [Configuration](https://nanobiostructuresrg.github.io/molraptor/configuration/)
- [API Reference](https://nanobiostructuresrg.github.io/molraptor/api/)

## Installation

After PyPI publication:

```bash
python -m pip install molraptor
```

For local development:

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e .
```

For development and documentation tools:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[docs]"
```

## Quick Start

Run the pipeline with the bundled example configuration:

```bash
molraptor run --config examples/example_config.yaml
```

Run from Python:

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig.load("examples/example_config.yaml")
run(config)
```

## Scope

| MOLRAPTOR does | MOLRAPTOR does not |
|----------------|-------------------|
| Fetch molecular properties from PubChem. | Train machine learning models. |
| Curate and validate chemical datasets. | Perform dimensionality reduction. |
| Generate Morgan fingerprints via RDKit. | Support non-PubChem data sources (yet). |
| Output ML-ready `.npy` and `.csv` artifacts. | Handle 3D molecular structures. |
| Log failed CIDs for reproducibility. | Support alternative fingerprint types (yet). |

## CLI

```bash
molraptor --help
molraptor run --help
molraptor --version
```

Common commands:

```bash
molraptor run
molraptor run --config examples/example_config.yaml
molraptor run --config examples/example_config.yaml --verbose
```

## Public API

```python
from molraptor import MolraptorConfig
from molraptor import validate_config
from molraptor import run
from molraptor import DataValidator
from molraptor import __version__
```

Modules not listed above are importable directly but are not part of the public
contract and may change before 1.0.

## Input Format

```text
data/
└── dataset.csv      <- CSV with PubChem CIDs and labels
```

Minimum required columns: `PubChem CID`, `Label`.

## Outputs

```text
artifacts/
├── morgan_fp.csv          # Morgan fingerprints (human-readable)
├── morgan_db_*.npy        # Morgan fingerprints (NumPy array, shape: N×size)
├── labels.npy             # Target labels (NumPy array, shape: N,)
└── summary.txt            # Execution report
```

Local inputs and generated artifacts such as `data/`, `artifacts/`, and `logs/`
are intentionally ignored by Git.

## Validation

The current `dev/v0.1.1` branch targets:

```bash
python -m pytest tests/ -v
mkdocs build --strict
python -m build --no-isolation
python -m twine check dist/*
molraptor --help
molraptor run --help
molraptor --version
```

## Citation

If you use MOLRAPTOR in your research, please cite it using the metadata in
[CITATION.cff](CITATION.cff).

## Author

Developed by **Flavio F. Contreras-Torres**. Tecnologico de Monterrey

## License

This project is licensed under the terms of the
[GNU Lesser General Public License v3.0 or later](LICENSE).

SPDX identifier: `LGPL-3.0-or-later`