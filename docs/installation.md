# Installation

MOLRAPTOR is developed for Python 3.11 and 3.12.

## Local Install

Clone the repository and install the package in editable mode:

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e .
```

This installs the `molraptor` command and the Python package.

## Optional Dependencies

Install development tools when running tests or building distributions:

```bash
python -m pip install -e ".[dev]"
```

Install documentation tools when building the MkDocs site:

```bash
python -m pip install -e ".[docs]"
```

## Conda Environment

A reproducible conda environment is provided:

```bash
conda env create -f environment.yml
conda activate molraptor_env
python -m pip install -e .
```

## PyPI Status

MOLRAPTOR is being prepared for publication on PyPI as `molraptor`.
After publication, install with:

```bash
python -m pip install molraptor
```

Until that package is published, install from the repository in editable mode.

## Verify Installation

```bash
molraptor --help
molraptor --version
```

Expected version for this release:

```text
MOLRAPTOR 0.1.1
```