# MOLRAPTOR

<section class="ms-hero">
  <div class="ms-hero__content">
    <p class="ms-eyebrow">Molecular data pipeline</p>
    <div class="ms-brand" aria-label="MOLRAPTOR">
      <span class="ms-dotmark" aria-hidden="true">
        <span></span><span></span><span></span>
        <span></span><span></span><span></span>
        <span></span><span></span><span></span>
      </span>
      <span class="ms-wordmark">MOLRAPTOR</span>
    </div>
    <p class="ms-subtitle">
      Modular pipeline for fetching, curating, and encoding molecular datasets
      using PubChem data and RDKit's Morgan fingerprinting algorithm.
    </p>
    <div class="ms-actions">
      <a class="md-button md-button--primary" href="usage/">Get started</a>
      <a class="md-button" href="api/">API Reference</a>
    </div>
    <div class="ms-badges" aria-label="Project badges">
      <img alt="CI" src="https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml/badge.svg">
      <img alt="Python versions" src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue">
      <img alt="License: LGPL v3+" src="https://img.shields.io/badge/License-LGPL_v3%2B-blue.svg">
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
      <strong>CSV</strong>
      <small>PubChem CIDs + labels</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Fetch</span>
      <strong>PubChem</strong>
      <small>molecular properties</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Curate</span>
      <strong>molraptor run</strong>
      <small>filter + validate</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Encode</span>
      <strong>RDKit</strong>
      <small>Morgan fingerprints</small>
    </div>
    <div class="ms-flow__item ms-flow__item--artifact">
      <span class="ms-flow__kicker">Output</span>
      <strong>.npy / .csv</strong>
      <small>ML-ready artifacts</small>
    </div>
  </div>
</section>

<section class="ms-panel">
  <div class="ms-grid ms-grid--four">
    <article class="ms-card">
      <span class="ms-card__icon">01</span>
      <h3>Fetch</h3>
      <p>Retrieve molecular properties from PubChem REST API for a list
      of compound IDs (CIDs).</p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">02</span>
      <h3>Curate</h3>
      <p>Filter and validate the dataset according to required columns
      and data types defined in the YAML config.</p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">03</span>
      <h3>Encode</h3>
      <p>Generate Morgan fingerprints using RDKit and save ML-ready
      NumPy arrays and CSV artifacts.</p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">04</span>
      <h3>Validate</h3>
      <p>Verify fingerprint matrix integrity — expected dimensions and
      absence of missing values.</p>
    </article>
  </div>
</section>

## Scope

| MOLRAPTOR does | MOLRAPTOR does not |
|----------------|-------------------|
| Fetch molecular properties from PubChem. | Train machine learning models. |
| Curate and validate chemical datasets. | Perform dimensionality reduction. |
| Generate Morgan fingerprints via RDKit. | Support non-PubChem data sources (yet). |
| Output ML-ready `.npy` and `.csv` artifacts. | Handle 3D molecular structures. |
| Log failed CIDs for reproducibility. | Support alternative fingerprint types (yet). |

## Quick Example

```bash
pip install molraptor
molraptor run --config examples/example_config.yaml
```

```python
from molraptor import MolraptorConfig, run

config = MolraptorConfig.load("examples/example_config.yaml")
run(config)
```

## Documentation

| Page | Purpose |
|------|---------|
| [Usage](usage.md) | Installation, quick start, CLI, YAML configuration, and pipeline outputs. |
| [API Reference](api.md) | Public Python API generated from docstrings. |
| [Changelog](changelog.md) | Project history sourced from the repository changelog. |

## Citation

```text
Contreras-Torres, F. F. (2026). MOLRAPTOR: Molecular Learning via Rapid Processing of Topological Representations. Zenodo. https://doi.org/10.5281/zenodo.20434420
```

## License

This project is licensed under the terms of the
[GNU Lesser General Public License v3.0 or later](https://github.com/NanoBiostructuresRG/molraptor/blob/main/LICENSE).
SPDX identifier: `LGPL-3.0-or-later`.
