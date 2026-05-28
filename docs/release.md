# Release Notes

MOLRAPTOR `0.1.1` establishes the professional development foundation,
migrating to hatchling, adopting a clean public API, and restructuring
the package architecture.

## 0.1.1 Highlights

- Migrated build backend from `setuptools` to `hatchling`.
- Replaced `typer` CLI with `argparse` following project conventions.
- Introduced `version.py` as single source of truth for project version.
- Flattened package structure — removed `steps/`, `services/`, `utils/` subdirectories.
- Rewrote `pipeline.py` as a public doorway with `run()` and `validate_config()`.
- Rewrote `result_manager.py` — imports version metadata, integrates dataset statistics.
- Replaced MIT license with GNU LGPL v3 or later.
- Added `CITATION.cff`, `CHANGELOG.md`, `environment.yml`, `mkdocs.yml`.
- Added initial test suite (13 tests passing).

## Validation Targets

Before release, validate:

```bash
mkdocs build --strict
python -m pytest tests/ -v
python -m build --no-isolation
python -m twine check dist/*
molraptor --help
molraptor run --help
molraptor --version
```

## Full Changelog

The complete release history is maintained in the repository changelog:

--8<-- "CHANGELOG.md"