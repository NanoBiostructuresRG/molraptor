# API Reference

MOLRAPTOR exposes nine public symbols through `molraptor.__all__`. The project
is pre-stable, so this API may change before 1.0. Objects not listed here are
implementation details and are not part of the supported public contract.

```python
from molraptor import MolraptorConfig
from molraptor import validate_config
from molraptor import run
from molraptor import DataValidator
from molraptor import MorganFingerprintProfile
from molraptor import FingerprintEncodingResult
from molraptor import FingerprintInputStatus
from molraptor import encode_fingerprints
from molraptor import __version__
```

---

## Scientific in-memory API

The scientific API encodes an ordered sequence of user-provided SMILES without
reading or writing files.

```python
from molraptor import MorganFingerprintProfile, encode_fingerprints

profile = MorganFingerprintProfile(
    radius=2,
    fp_size=2048,
    include_chirality=False,
)

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1", "CCO"],
    profile,
)

fingerprints = result.fingerprints
print(fingerprints.shape)
# (3, 2048)

print(fingerprints.dtype)
# uint8

print(result.valid_indices)
# (0, 2, 3)
```

`encode_fingerprints`:

- performs no file I/O;
- preserves exact input strings, order, and duplicates;
- parses each supplied SMILES with RDKit;
- generates one binary Morgan fingerprint row per valid input;
- omits invalid inputs from the matrix instead of inserting zero vectors;
- records one `FingerprintInputStatus` for every original input;
- returns deterministic ordered-input and profile hashes.

The matrix has shape `(N_valid, fp_size)` and dtype `numpy.uint8`.

MOLRAPTOR uses the supplied SMILES to construct the molecular graph required
for fingerprint calculation. It does not return, canonicalize, harmonize, or
replace the caller's molecular representation.

### Result alignment

`valid_indices` maps fingerprint rows back to the zero-based positions of valid
records in the original input sequence.

Each `FingerprintInputStatus` records:

- `input_index`;
- `input_smiles`;
- `status`;
- `fingerprint_index`;
- `invalid_reason`.

For valid inputs, `fingerprint_index` identifies the corresponding matrix row.
For invalid inputs, `fingerprint_index` is absent and `invalid_reason` records
the failure.

Current invalid reasons are:

- `parse_failure`;
- `empty_molecule`.

### Metadata and hashes

`FingerprintEncodingResult` contains:

- the fingerprint matrix;
- the complete effective profile;
- per-input statuses;
- valid indices and counts;
- matrix shape and dtype;
- MOLRAPTOR and RDKit versions;
- `ordered_input_hash`;
- `profile_hash`.

`serialize_metadata()` returns a JSON-compatible dictionary and deliberately
excludes the NumPy fingerprint matrix.

The ordered-input hash covers the exact ordered sequence, including
duplicates, whitespace, and empty strings. The profile hash covers the complete
effective Morgan configuration, including defaults.

### Zero-valid behavior

The in-memory encoder can return an empty matrix with shape `(0, fp_size)` when
all supplied records are invalid.

The file workflow treats zero valid SMILES as a global failure and does not
publish final artifacts. This policy belongs to `run`, not to
`encode_fingerprints`.

### MorganFingerprintProfile

::: molraptor.morgan.MorganFingerprintProfile

### encode_fingerprints

::: molraptor.morgan.encode_fingerprints

### FingerprintEncodingResult

::: molraptor.morgan.FingerprintEncodingResult

### FingerprintInputStatus

::: molraptor.morgan.FingerprintInputStatus

---

## File workflow API

The file workflow reads SMILES from CSV or UTF-8 TXT, delegates fingerprint
generation to the same in-memory scientific API, and publishes the approved
artifact set.

```python
from molraptor import (
    MolraptorConfig,
    MorganFingerprintProfile,
    run,
)

config = MolraptorConfig(
    input_path="molecules.csv",
    smiles_column="SMILES",
    output_dir="artifacts",
    profile=MorganFingerprintProfile(
        radius=2,
        fp_size=2048,
        include_chirality=False,
    ),
)

result = run(config)

print(result.fingerprints.shape)
print(result.valid_indices)
```

A successful run writes exactly:

```text
fingerprints.npy
fingerprints.csv
input_statuses.csv
encoding_metadata.json
```

The file workflow stops without publishing final artifacts when configuration,
input access, input format, the configured CSV column, zero-valid validation, or
artifact publication fails.

### MolraptorConfig

::: molraptor.config.MolraptorConfig

### validate_config

::: molraptor.pipeline.validate_config

### run

::: molraptor.pipeline.run

---

## Validation utility

`DataValidator` remains part of the public API for explicit validation tasks.
It does not retrieve PubChem data, infer activity labels, harmonize SMILES, or
generate alternative molecular representations.

### DataValidator

::: molraptor.validators.DataValidator

---

## Version

`__version__` exposes the installed MOLRAPTOR package version.

::: molraptor.version
