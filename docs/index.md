# MOLRAPTOR

<section class="ms-hero">
  <div class="ms-hero__content">
    <p class="ms-eyebrow">Traceable molecular fingerprint encoding</p>
    <div class="ms-brand" aria-label="MOLRAPTOR">
      <span class="ms-dotmark" aria-hidden="true">
        <span></span><span></span><span></span>
        <span></span><span></span><span></span>
        <span></span><span></span><span></span>
      </span>
      <span class="ms-wordmark">MOLRAPTOR</span>
    </div>
    <p class="ms-subtitle">
      Documentation for molecular fingerprint encoding from ordered,
      user-provided SMILES. MOLRAPTOR connects each numerical representation
      to its source inputs, fingerprint algorithm, effective encoding profile,
      and input-to-output correspondence.
    </p>
    <div class="ms-actions">
      <a class="md-button md-button--primary" href="usage/">Get started</a>
      <a class="md-button" href="api/">API Reference</a>
      <a class="md-button" href="changelog/">Changelog</a>
    </div>
    <div class="ms-badges" aria-label="Project badges">
      <a href="https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml"><img src="https://github.com/NanoBiostructuresRG/molraptor/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
      <a href="https://pypi.org/project/molraptor/"><img src="https://img.shields.io/pypi/v/molraptor.svg" alt="PyPI"></a>
      <a href="https://pypi.org/project/molraptor/"><img src="https://img.shields.io/pypi/pyversions/molraptor.svg" alt="Python versions"></a>
      <a href="https://github.com/NanoBiostructuresRG/molraptor/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-LGPL_v3%2B-blue.svg" alt="License: LGPL v3+"></a>
    </div>
  </div>
</section>

!!! note "Pre-stable"
    MOLRAPTOR is currently in alpha-stage development. Public APIs may change
    before 1.0.

## Conceptual Model

MOLRAPTOR treats fingerprint generation as more than a matrix transformation.
An encoding result is interpreted through the relationship between the
molecular input, the selected algorithm, its representation semantics, the
effective encoding profile, and the resulting numerical matrix.

<section class="ms-workflow" aria-label="MOLRAPTOR conceptual model">
  <div class="ms-flow">
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Input</span>
      <strong>Ordered SMILES</strong>
      <small>source identity</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Algorithm</span>
      <strong>Fingerprint</strong>
      <small>one algorithm per execution</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Representation</span>
      <strong>Binary / Count / MinHash</strong>
      <small>algorithm-defined semantics</small>
    </div>
    <div class="ms-flow__item">
      <span class="ms-flow__kicker">Profile</span>
      <strong>Effective settings</strong>
      <small>explicit encoding configuration</small>
    </div>
    <div class="ms-flow__item ms-flow__item--artifact">
      <span class="ms-flow__kicker">Result</span>
      <strong>Matrix + metadata</strong>
      <small>numerical representation and correspondence</small>
    </div>
  </div>
</section>

The fingerprint algorithm determines the representation class. MOLRAPTOR does
not expose a separate representation selector.

Morgan uses a configurable effective profile. The other nine supported
algorithms use fixed effective profiles in v0.5.0.

## What MOLRAPTOR Preserves

<section class="ms-panel">
  <div class="ms-grid ms-grid--four">
    <article class="ms-card">
      <span class="ms-card__icon">01</span>
      <h3>Input identity</h3>
      <p>
        Preserve the supplied strings, their order, duplicates, and the
        distinction between valid and invalid inputs.
      </p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">02</span>
      <h3>Encoding identity</h3>
      <p>
        Record the selected fingerprint algorithm, representation, complete
        effective profile, and deterministic profile hash.
      </p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">03</span>
      <h3>Numerical result</h3>
      <p>
        Generate a representation-dependent matrix with explicit width, shape,
        and dtype.
      </p>
    </article>
    <article class="ms-card">
      <span class="ms-card__icon">04</span>
      <h3>Correspondence</h3>
      <p>
        Preserve the mapping between original input positions and valid matrix
        rows together with MOLRAPTOR and RDKit versions.
      </p>
    </article>
  </div>
</section>

These elements are kept separate because source identity, encoding identity,
and numerical identity are not equivalent. Different input strings can produce
the same numerical fingerprint, and the same input sequence can be encoded
under different effective profiles.

## Representation Classes

MOLRAPTOR v0.5.0 supports three numerical representation classes:

**Binary**
Coordinates encode presence or absence according to the selected fingerprint
algorithm.

**Count**
Coordinates store multiplicities in fixed-width count vectors.

**MinHash**
Coordinates form a MinHash sketch of the encoded shingle set rather than
feature-presence bits or feature counts.

The detailed algorithm-to-representation mapping, widths, dtypes, and usage
examples are documented in the [Usage guide](usage.md).

## Source-Input Boundary

MOLRAPTOR operates on user-provided SMILES. It parses those strings with RDKit
to construct the molecular graph required for fingerprint calculation.

It does not retrieve molecular records from external databases or curate,
harmonize, canonicalize, or replace the supplied SMILES as an
input-preprocessing step.

This source-input boundary does not constrain algorithm-internal
transformations required to construct a fingerprint representation.

## Where to Go Next

| Page | Use it for |
|------|------------|
| [Usage](usage.md) | Installation, supported algorithms, command-line use, Python workflows, inputs, outputs, and failure handling. |
| [API Reference](api.md) | Public Python contracts, effective profiles, representation semantics, result alignment, metadata, and hashes. |
| [Changelog](changelog.md) | Release history and version-specific changes. |

For bug reports, feature requests, and questions, use the
[GitHub issue tracker](https://github.com/NanoBiostructuresRG/molraptor/issues).

For development and contribution instructions, see
[CONTRIBUTING.md](https://github.com/NanoBiostructuresRG/molraptor/blob/main/CONTRIBUTING.md).
