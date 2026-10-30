# Contributing to MOLRAPTOR

Thank you for your interest in contributing to MOLRAPTOR.This project is maintained by the [Nano and Biostructures Research Group](https://nanobiostructuresrg.github.io/) at Tecnológico de Monterrey.

By participating in this project, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## How to contribute

### Reporting bugs

Open an issue on [GitHub Issues](https://github.com/NanoBiostructuresRG/molraptor/issues) with:

- a clear description of the problem;
- a minimal reproducible example;
- your environment details, including operating system, Python version, MOLRAPTOR version, and RDKit version.

### Suggesting features

Open an issue describing:

- the scientific or computational use case;
- the proposed behavior;
- why it would be useful beyond a single workflow.

### Submitting a pull request

1. Fork the repository.
2. Create a branch from `main`:

   ```bash
   git switch -c dev/your-feature
   ```

3. Make your changes.
4. Run the relevant validation checks.
5. Push your branch and open a pull request against `main`.

Pull requests should pass CI before merge. User-facing changes should include appropriate documentation and, when relevant, a `CHANGELOG.md` entry.

## Development setup

Create an environment with Python 3.11 or later using the environment manager you prefer, then install MOLRAPTOR in editable mode with its development dependencies:

```bash
git clone https://github.com/NanoBiostructuresRG/molraptor.git
cd molraptor
python -m pip install -e ".[dev]"
```

RDKit and the other runtime dependencies are resolved from `pyproject.toml`.

To work on the documentation, install the documentation dependencies as well:

```bash
python -m pip install -e ".[dev,docs]"
```

## Validation

Run the test suite:

```bash
python -m pytest tests -q
```

Build the documentation in strict mode:

```bash
mkdocs build --strict
```

Build and validate the package distributions when packaging or release-related files change:

```bash
python -m build
python -m twine check dist/*
```

The GitHub Actions workflow provides the final CI validation for supported Python versions and documentation builds.

## Code style

Follow [PEP 8](https://peps.python.org/pep-0008/) and the style already used in the surrounding code.

Keep changes focused and avoid unrelated refactoring within the same pull request.

## Documentation and changelog

Update the README, documentation, examples, or API reference when user-facing behavior, interfaces, commands, or examples change.

Add an entry to `CHANGELOG.md` when the change affects users or the public scientific/software contract.

Keep documentation responsibilities separated:

- `README.md` provides the project overview, installation, quick start, scope, and links;
- `docs/usage.md` documents user workflows, inputs, outputs, and failure behavior;
- `docs/api.md` documents public Python contracts and encoding metadata;
- `CHANGELOG.md` records release history.

## Scientific and cheminformatics changes

Changes that affect fingerprint algorithms, representation semantics, encoding profiles, molecular parsing, or input-to-output correspondence require explicit scientific justification and tests.

When relevant:

- state the scientific or cheminformatics assumption being changed;
- identify the affected algorithm or representation;
- add or update tests against an appropriate reference implementation or frozen reference case;
- document RDKit-dependent behavior;
- preserve input order, duplicate handling, invalid-input traceability, and matrix-row correspondence;
- avoid introducing implicit curation, harmonization, canonicalization, or replacement of user-supplied SMILES as an input-preprocessing step.

Changes to fingerprint mathematics or representation semantics should not be introduced as incidental refactoring.

## Questions

Questions, bug reports, and feature discussions can be opened through the [GitHub issue tracker](https://github.com/NanoBiostructuresRG/molraptor/issues).
