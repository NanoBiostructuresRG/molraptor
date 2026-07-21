# MOLRAPTOR

<section class="ms-hero">
  <div class="ms-hero__content">
    <p class="ms-eyebrow">SMILES-first fingerprinting</p>
    <div class="ms-brand" aria-label="MOLRAPTOR">
      <span class="ms-dotmark" aria-hidden="true">
        <span></span><span></span><span></span>
        <span></span><span></span><span></span>
        <span></span><span></span><span></span>
      </span>
      <span class="ms-wordmark">MOLRAPTOR</span>
    </div>
    <p class="ms-subtitle">
      Scientific library and command-line tool for generating reproducible
      Morgan fingerprints from user-provided molecular representations.
    </p>
    <div class="ms-actions">
      <a class="md-button md-button--primary" href="usage/#installation">Install</a>
      <a class="md-button" href="api/">API Reference</a>
      <a class="md-button" href="changelog/">Changelog</a>
    </div>
    <div class="ms-badges" aria-label="Project badges">
      <a href="https://github.com/NanoBiostructuresRG/molrapto/actions/workflows/ci.yml"><img src="https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
      <a href="https://pypi.org/project/molraptor/"><img src="https://img.shields.io/pypi/v/molraptor.svg" alt="PyPI"></a>
      <a href="https://pypi.org/project/molraptor/"><img src="https://img.shields.io/pypi/pyversions/molraptor.svg" alt="Python versions"></a>
      <a href="https://github.com/NanoBiostructuresRG/molraptor/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-LGPL_v3%2B-blue.svg" alt="License: LGPL v3+"></a>
    </div>
  </div>
</section>

!!! note "Pre-stable"
    MOLRAPTOR is currently in alpha-stage development. Public APIs may change
    before 1.0.

## Workflow

<section class="ms-workflow" aria-label="MOLRAPTOR workflow">
  <div class="ms-flow">
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Input</span>
      <strong>Python / CSV / TXT</strong>
      <small>user-provided SMILES</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Parse</span>
      <strong>RDKit</strong>
      <small>molecular graph construction</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Encode</span>
      <strong>Morgan</strong>
      <small>binary bit vectors</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Trace</span>
      <strong>Status + hashes</strong>
      <small>alignment and provenance</small>
    </div>
    <div class="ms-flow__item ms-flow__item--artifact">
      <span class="ms-flow__kicker">Output</span>
      <strong>NumPy / CSV / JSON</strong>
      <small>reproducible artifacts</small>
    </div>
  </div>
</section>

<section class="ms-panel">
  <div class="ms-grid ms-grid--four">
    <article class="ms-card">
      <span class="ms-card__icon">01</span>
      <h3>Supply</h3>
      <p>Provide ordered SMILES directly through Python or from a CSV or
      UTF-8 TXT file.</p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">02</span>
      <h3>Encode</h3>
      <p>Generate binary Morgan fingerprints using an explicit,
      serializable RDKit profile.</p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">03</span>
      <h3>Trace</h3>
      <p>Preserve input order and duplicates while recording validity,
      matrix-row alignment, hashes, and runtime versions.</p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">04</span>
      <h3>Export</h3>
      <p>Write fingerprint matrices, per-input statuses, and encoding
      metadata for downstream scientific workflows.</p>
    </article>
  </div>
</section>

## Scope

| MOLRAPTOR does | MOLRAPTOR does not |
|----------------|-------------------|
| Accept user-provided SMILES through Python, CSV, or TXT. | Retrieve molecular records from PubChem or other databases. |
| Parse SMILES with RDKit for fingerprint calculation. | Curate, harmonize, canonicalize, or replace supplied SMILES. |
| Generate binary Morgan fingerprints. | Generate labels or activity classes. |
| Preserve input order and duplicates. | Train or evaluate machine-learning models. |
| Isolate invalid individual inputs. | Calculate molecular descriptors or 3D conformations. |
| Record profiles, hashes, versions, and row alignment. | Provide alternative fingerprint algorithms in v0.3.0. |

## Quick Example

```bash
python -m pip install molraptor

molraptor run \
  --input molecules.csv \
  --smiles-column SMILES \
  --output-dir artifacts
```

```python
from molraptor import MorganFingerprintProfile, encode_fingerprints

profile = MorganFingerprintProfile(radius=2, fp_size=2048)

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1"],
    profile,
)

print(result.fingerprints.shape)
# (2, 2048)
```

The in-memory API, file workflow, and command-line interface use the same
scientific encoding core.

## Documentation

| Page | Purpose |
|------|---------|
| [Usage](usage.md) | Installation, CLI, CSV/TXT inputs, Python workflows, outputs, and failure handling. |
| [API Reference](api.md) | Current public Python contracts and examples. |
| [Changelog](changelog.md) | Project history sourced from the repository changelog. |

## Citation

```text
Contreras-Torres, F. F. (2026). MOLRAPTOR: Molecular Learning via Rapid Processing of Topological Representations. Zenodo. https://doi.org/10.5281/zenodo.20434420
```

## License

This project is licensed under the terms of the
[GNU Lesser General Public License v3.0 or later](https://github.com/NanoBiostructuresRG/molraptor/blob/main/LICENSE).
SPDX identifier: `LGPL-3.0-or-later`.
