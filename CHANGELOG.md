# Changelog

All notable changes to MOLRAPTOR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2026-07-25

### Added

- Added unified support for Morgan, Feature Morgan, Atom Pair, RDKit
  topological, Topological Torsion, Layered, and MACCS fingerprints.
- Added fingerprint selection through the CLI `--fingerprint` option and
  the Python `fingerprint_type` configuration.
- Added fixed, serializable effective profiles for non-Morgan fingerprints
  while preserving configurable Morgan settings.
- Added focused coverage for fingerprint dispatch, profiles, CLI selection,
  output dimensions, configuration validation, and removed module routes.

### Changed

- Replaced the Morgan-only scientific implementation with the unified
  `molraptor/fingerprints.py` core.
- Kept Morgan as the default fingerprint and preserved compatibility with
  the existing positional `MorganFingerprintProfile` contract.
- Renamed the CSV/TXT and artifact-writing implementation from
  `fingerprint.py` to `workflow.py`.
- Standardized one fingerprint type per execution with binary
  `numpy.uint8` matrices and natural fingerprint widths.
- Made Morgan-only CLI and configuration settings fail explicitly when
  supplied for another fingerprint type.
- Updated the project identity to
  `MOLRAPTOR: Molecular Fingerprint Rapid Generator`.
- Updated the README, API reference, usage guide, documentation homepage,
  citation metadata, and package description for multi-fingerprint support.

### Removed

- Removed the historical `molraptor.morgan` module route.
- Removed the historical `molraptor.fingerprint` module route.

## [0.3.0] - 2026-07-20

### Added

- Added a SMILES-only file workflow for CSV and UTF-8 TXT inputs.
- Added direct CLI configuration through `--input`, `--smiles-column`,
  `--output-dir`, `--radius`, `--fp-size`, and `--include-chirality`.
- Added the stable output artifact set:
  `fingerprints.npy`, `fingerprints.csv`, `input_statuses.csv`, and
  `encoding_metadata.json`.
- Added per-input validation status with explicit mapping between original
  `input_index` values and valid fingerprint matrix rows.
- Added workflow metadata for source format, source filename, effective Morgan
  profile, matrix shape and dtype, runtime versions, and deterministic ordered
  input and profile hashes.
- Added CLI coverage and expanded tests for CSV/TXT parsing, output publication,
  invalid-input isolation, metadata, and the public API.

### Changed

- Reoriented MOLRAPTOR as a SMILES-first scientific library and command-line
  tool for reproducible Morgan fingerprint generation.
- Unified the command-line interface and file workflow around the public
  in-memory `encode_fingerprints` scientific core.
- Preserved exact input order and duplicates while allowing invalid individual
  SMILES to be excluded without discarding valid fingerprint rows.
- Standardized binary fingerprint matrices as `numpy.uint8` with shape
  `(N_valid, fp_size)`.
- Updated the default Morgan profile to radius 2, 2048 bits, and chirality
  disabled unless explicitly requested.
- Updated the NumPy requirement to `numpy>=2.4`.
- Rewrote the README and MkDocs documentation for the v0.3.0 architecture,
  CLI, public API, input contract, outputs, failure handling, and scientific
  boundary.
- Updated public API docstrings and release metadata for v0.3.0.

### Removed

- Removed PubChem retrieval and CID-driven workflows.
- Removed YAML configuration and the legacy fetch, curate, integrity,
  result-management, and multi-stage pipeline components.
- Removed activity-label handling and legacy outputs such as `labels.npy`,
  `morgan_fp.csv`, `morgan_db_*.npy`, and `summary.txt`.
- Removed `rdkit_canonical_smiles` from the public and internal status
  contracts.
- Removed deleted legacy modules including `fetch.py`, `pubchem.py`,
  `curate.py`, `fp_integrity.py`, and `result_manager.py`.

### Fixed

- Replaced the obsolete CLI pipeline import path with the current SMILES-only
  workflow, resolving the startup failure reported in issue #2.

---

## [0.2.0] - 2026-07-16

### Added

- Added a public, in-memory API for generating binary Morgan fingerprints from ordered SMILES.
- Added `MorganFingerprintProfile`, `FingerprintEncodingResult`,
  `FingerprintInputStatus`, and `encode_fingerprints` to the public API.
- Added explicit profile serialization, deterministic input and profile hashes,
  RDKit and MOLRAPTOR version metadata, and traceable valid/invalid input status.
- Added focused tests for in-memory fingerprint encoding and the file-based
  fingerprint step.

### Changed

- Refactored the file-based fingerprint pipeline to reuse the public Morgan
  encoder instead of maintaining a separate implementation.
- Preserved CSV and NPY outputs for valid datasets.
- Made the file-based pipeline reject invalid SMILES before writing fingerprint
  or label artifacts.
- Documented the distinction between the in-memory library API and the
  file-based pipeline.
- Updated CI public-API checks for the new exported symbols.

---

## [0.1.1] - 2026-05-28

### Added
- `CITATION.cff` for software citation metadata.
- `CHANGELOG.md` to track project history.

### Changed
- License changed from MIT to GNU LGPL v3 or later (`LGPL-3.0-or-later`).
- `pyproject.toml`: version updated to `0.1.0` and Python requirement lowered to `>=3.11`.

---

## [0.1.0] - 2025-06-12

### Added
- Initial pre-release of MOLRAPTOR (formerly tagged as `v1.0.0`).
- Modular pipeline architecture: fetch → curate → fingerprint → validate.
- PubChem REST API integration via `PubChemService`.
- Morgan fingerprint generation using RDKit (`GetMorganGenerator`).
- YAML-based configuration schema via Pydantic v2 (`MolraptorConfig`).
- CLI entry point via Typer (`molraptor run`, `molraptor version`).
- Abstract base class `BaseStep` for pipeline step contract.
- Utility modules: `chunks`, `log_print`, `validators`, `reporter`, `result_manager`.
- Initial `configs/default.yaml` with PPARγ dataset configuration.
- MIT License (superseded in v0.1.1).

---

[0.3.0]: https://github.com/NanoBiostructuresRG/molraptor/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/NanoBiostructuresRG/molraptor/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/NanoBiostructuresRG/molraptor/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/NanoBiostructuresRG/molraptor/releases/tag/v0.1.0
