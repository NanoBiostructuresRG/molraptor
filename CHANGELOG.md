# Changelog

All notable changes to MOLRAPTOR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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