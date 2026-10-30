# API Reference

MOLRAPTOR exposes 18 public symbols through `molraptor.__all__`.

The public API separates four concepts that should not be treated as
interchangeable:

```text
molecular input
      ↓
fingerprint algorithm
      ↓
representation + effective profile
      ↓
numerical matrix
```

The project is currently pre-stable. Public interfaces may change before 1.0.
Objects not exported through `molraptor.__all__` are implementation details and
are not part of the supported top-level API.

## Public API

| Symbol | Purpose |
|---|---|
| `__version__` | Installed MOLRAPTOR version |
| `MolraptorConfig` | Configuration for the CSV/TXT file workflow |
| `run` | Execute the configured file workflow |
| `validate_config` | Validate the workflow configuration object type |
| `DataValidator` | Public tabular and SMILES validation utilities |
| `FingerprintAlgorithm` | Type identifying supported fingerprint algorithms |
| `FingerprintRepresentation` | Type identifying representation classes |
| `FINGERPRINT_ALGORITHMS` | Ordered registry of supported algorithms |
| `FINGERPRINT_REPRESENTATIONS` | Ordered registry of representation classes |
| `ALGORITHM_REPRESENTATIONS` | Mapping from algorithm to representation |
| `FingerprintType` | v0.4 compatibility alias for `FingerprintAlgorithm` |
| `FINGERPRINT_TYPES` | v0.4 compatibility alias for `FINGERPRINT_ALGORITHMS` |
| `MorganFingerprintProfile` | Configurable effective Morgan profile |
| `ResolvedFingerprintProfile` | Resolved algorithm, representation, width, profile, and profile hash |
| `FingerprintEncodingResult` | Numerical result with alignment and encoding metadata |
| `FingerprintInputStatus` | Per-input validity and matrix-row correspondence |
| `resolve_fingerprint_profile` | Resolve an effective profile without encoding SMILES |
| `encode_fingerprints` | Encode an ordered sequence of SMILES in memory |

The compatibility name `fingerprint_type` is retained in existing function and
configuration signatures. Conceptually, it selects a **fingerprint algorithm**.
The representation is derived from that algorithm and is not selected
independently.

## Algorithm and Representation Contract

MOLRAPTOR v0.5.0 supports 10 algorithms and three representation classes.

| Algorithm identifier | Representation | Width | Dtype |
|---|---|---:|---|
| `morgan` | binary | configurable; default 2048 | `uint8` |
| `featmorgan` | binary | 2048 | `uint8` |
| `atompair` | count | 2048 | `uint32` |
| `rdk` | binary | 2048 | `uint8` |
| `torsion` | count | 2048 | `uint32` |
| `layered` | binary | 2048 | `uint8` |
| `maccs` | binary | 167 | `uint8` |
| `klekotaroth` | binary | 4860 | `uint8` |
| `mhfp6` | MinHash | 2048 | `uint32` |
| `map4` | MinHash | 1024 | `uint32` |

The public registries expose this contract directly:

```python
from molraptor import (
    ALGORITHM_REPRESENTATIONS,
    FINGERPRINT_ALGORITHMS,
    FINGERPRINT_REPRESENTATIONS,
)

print(FINGERPRINT_ALGORITHMS)
print(FINGERPRINT_REPRESENTATIONS)
print(ALGORITHM_REPRESENTATIONS["map4"])
# minhash
```

The representation classes have different numerical semantics:

**Binary**
Coordinates encode presence or absence according to the selected algorithm.
For hashed binary fingerprints, more than one molecular feature may map to the
same bit.

**Count**
Coordinates store multiplicities in fixed-width hashed bins. Different
molecular features may contribute to the same bin through collisions.

**MinHash**
Coordinates are MinHash sketch values summarizing the encoded shingle set.
They are not molecular feature-presence bits or feature counts.

The same numerical dtype therefore does not imply the same representation
semantics. In particular, count and MinHash matrices both use `uint32`, but
their coordinates have different meanings.

## Effective Fingerprint Profiles

An effective profile records the settings used to construct a fingerprint
representation.

Morgan is the only configurable algorithm in v0.5.0. The other nine algorithms
use fixed effective profiles.

All serialized profiles include:

```text
profile_schema_version
algorithm
representation
output_type
dtype
```

and the algorithm-specific settings required by the encoder.

The representation output contract is:

```text
binary  → binary-bit-vector → uint8
count   → count-vector      → uint32
minhash → minhash-sketch    → uint32
```

### Resolve a profile without encoding

Use `resolve_fingerprint_profile()` when the effective encoding contract is
needed before any SMILES are parsed:

```python
from molraptor import resolve_fingerprint_profile

resolved = resolve_fingerprint_profile("maccs")

print(resolved.algorithm)
# maccs

print(resolved.representation)
# binary

print(resolved.width)
# 167

print(resolved.profile_hash)
```

`width` is the canonical v0.5 dimension property of
`ResolvedFingerprintProfile`.

`fp_size` remains available on that object as a v0.4 compatibility alias for
`width`. Serialized profiles continue to use their defined `fp_size` field.

For Morgan, pass a `MorganFingerprintProfile` when a non-default profile is
required:

```python
from molraptor import (
    MorganFingerprintProfile,
    resolve_fingerprint_profile,
)

profile = MorganFingerprintProfile(
    radius=3,
    fp_size=1024,
    include_chirality=True,
)

resolved = resolve_fingerprint_profile(
    "morgan",
    profile,
)
```

A `MorganFingerprintProfile` supplied for another algorithm is rejected rather
than silently ignored.

### MorganFingerprintProfile

::: molraptor.fingerprints.MorganFingerprintProfile

### ResolvedFingerprintProfile

::: molraptor.fingerprints.ResolvedFingerprintProfile

### resolve_fingerprint_profile

::: molraptor.fingerprints.resolve_fingerprint_profile

## In-Memory Encoding

`encode_fingerprints()` is the scientific in-memory encoding interface.

Its public signature is:

```python
encode_fingerprints(
    smiles,
    profile=None,
    *,
    fingerprint_type="morgan",
)
```

`smiles` must be an ordered sequence of strings. Passing a single string or a
sequence containing non-string elements raises `TypeError`.

Each call uses one fingerprint algorithm.

The encoder:

- preserves the supplied strings, their order, and duplicates;
- parses each string with RDKit;
- records one status for every original input;
- produces one matrix row for every valid input;
- excludes invalid inputs from the matrix rather than inserting artificial
  zero vectors;
- records the complete effective profile and encoding metadata;
- returns deterministic ordered-input and profile hashes.

The matrix shape is:

```text
(N_valid, fingerprint_width)
```

Its dtype is determined by the representation:

```text
binary  → uint8
count   → uint32
minhash → uint32
```

The in-memory API performs no file I/O.

MOLRAPTOR does not retrieve, curate, harmonize, canonicalize, or replace the
user-supplied SMILES as an input-preprocessing step. The supplied strings are
parsed to construct the molecular graph required by the selected fingerprint
algorithm.

This source-input boundary does not constrain algorithm-internal
transformations used to construct a fingerprint representation.

### Compatibility behavior

Existing calls that provide a `MorganFingerprintProfile` as the second
positional argument remain valid:

```python
from molraptor import MorganFingerprintProfile, encode_fingerprints

profile = MorganFingerprintProfile(radius=2, fp_size=2048)

result = encode_fingerprints(
    ["CCO", "c1ccccc1"],
    profile,
)
```

For another algorithm, use the keyword-only compatibility parameter
`fingerprint_type` and do not provide a Morgan profile:

```python
from molraptor import encode_fingerprints

result = encode_fingerprints(
    ["CCO", "c1ccccc1"],
    fingerprint_type="map4",
)
```

### encode_fingerprints

::: molraptor.fingerprints.encode_fingerprints

## Result and Input Correspondence

`FingerprintEncodingResult` keeps the numerical representation and its
encoding context together.

Its principal fields are:

| Field | Meaning |
|---|---|
| `fingerprints` | NumPy matrix for valid inputs |
| `profile` | Complete serialized effective profile |
| `valid_indices` | Original input positions represented in the matrix |
| `input_statuses` | One status object for every original input |
| `valid_count` | Number of valid inputs |
| `invalid_count` | Number of invalid inputs |
| `matrix_shape` | Matrix dimensions |
| `matrix_dtype` | NumPy matrix dtype |
| `molraptor_version` | MOLRAPTOR version used for encoding |
| `rdkit_version` | RDKit version used for parsing and encoding |
| `ordered_input_hash` | Digest identifying the ordered source-input sequence |
| `profile_hash` | Digest identifying the complete effective profile |

`valid_indices` maps matrix rows back to positions in the original input
sequence.

For example:

```python
from molraptor import encode_fingerprints

result = encode_fingerprints(
    ["CCO", "not-a-smiles", "c1ccccc1"],
)

print(result.valid_indices)
# (0, 2)
```

The matrix contains two rows:

```text
matrix row 0 ↔ input index 0
matrix row 1 ↔ input index 2
```

The invalid record at input index `1` remains represented in
`input_statuses`.

### FingerprintInputStatus

Each `FingerprintInputStatus` records:

```text
input_index
input_smiles
status
fingerprint_index
invalid_reason
```

For a valid input:

- `status` is `valid`;
- `fingerprint_index` identifies its matrix row;
- `invalid_reason` is absent.

For an invalid input:

- `status` is `invalid`;
- `fingerprint_index` is absent;
- `invalid_reason` is recorded.

Current invalid reasons are:

- `parse_failure`;
- `empty_molecule`.

### Zero-valid behavior

The in-memory encoder may return an empty matrix when all supplied records are
invalid:

```text
(0, fingerprint_width)
```

This is a valid in-memory result.

The file workflow applies a stricter policy and treats zero valid SMILES as a
global workflow failure.

### FingerprintEncodingResult

::: molraptor.fingerprints.FingerprintEncodingResult

### FingerprintInputStatus

::: molraptor.fingerprints.FingerprintInputStatus

## Encoding Metadata

`FingerprintEncodingResult.serialize_metadata()` returns a JSON-compatible
dictionary containing encoding-level metadata without embedding either the
fingerprint matrix or the row-level `input_statuses`.

It contains:

```text
profile
valid_indices
valid_count
invalid_count
matrix_shape
matrix_dtype
molraptor_version
rdkit_version
ordered_input_hash
profile_hash
```

The file workflow extends this encoding metadata with source-file information
and `input_count` before writing `encoding_metadata.json`.

Source-file metadata added by the file workflow are:

```text
source_file_name
input_format
smiles_column
input_count
```

For TXT input, `smiles_column` is `null`.

The local filesystem path is not persisted in the metadata.

## Hash Definitions

MOLRAPTOR uses two SHA-256 hashes to distinguish source-input identity from
effective-profile identity.

Neither hash is a hash of the fingerprint matrix.

### `ordered_input_hash`

`ordered_input_hash` is calculated from the complete ordered sequence of input
strings.

The sequence preserves:

- input order;
- duplicate strings;
- whitespace;
- empty strings.

The sequence is serialized as compact JSON using:

```python
json.dumps(
    value,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=False,
)
```

The UTF-8 encoded JSON bytes are then hashed with SHA-256.

Conceptually:

```python
payload = json.dumps(
    ordered_smiles,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=False,
).encode("utf-8")

ordered_input_hash = hashlib.sha256(payload).hexdigest()
```

The hash therefore identifies the exact ordered source-input sequence used by
the encoder. It does not identify chemical equivalence.

Different SMILES strings may produce the same numerical fingerprint while
retaining different `ordered_input_hash` values.

### `profile_hash`

`profile_hash` is calculated from the complete effective profile.

The profile is serialized as compact JSON using:

```python
json.dumps(
    value,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
)
```

The UTF-8 encoded JSON bytes are then hashed with SHA-256.

Conceptually:

```python
payload = json.dumps(
    effective_profile,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("utf-8")

profile_hash = hashlib.sha256(payload).hexdigest()
```

Sorting the object keys makes the digest independent of dictionary key
insertion order.

The hash identifies the effective encoding profile. It does not identify the
source input or the resulting numerical matrix.

The two hashes therefore represent different identities:

```text
ordered_input_hash → source-input identity
profile_hash       → effective-profile identity
```

MOLRAPTOR does not claim that these hashes capture the complete computational
environment. Environment details such as operating system, Python version, and
NumPy version are not included in either hash.

## File Workflow API

The file workflow reads ordered SMILES from CSV or UTF-8 TXT, delegates
fingerprint calculation to `encode_fingerprints()`, applies workflow-level
validation, and writes the defined four-artifact output set.

### MolraptorConfig

`MolraptorConfig` defines:

| Field | Meaning |
|---|---|
| `input_path` | Input CSV or TXT path |
| `smiles_column` | CSV column containing SMILES; default `SMILES` |
| `output_dir` | Artifact destination; default `artifacts` |
| `fingerprint_type` | Compatibility name selecting the fingerprint algorithm |
| `profile` | `MorganFingerprintProfile` for Morgan; otherwise `None` |

Morgan receives its default `MorganFingerprintProfile` when no explicit
profile is supplied.

Non-Morgan algorithms reject a Morgan profile.

::: molraptor.config.MolraptorConfig

### validate_config

`validate_config()` checks that the supplied object is a
`MolraptorConfig` instance and returns that same validated instance.

Configuration-field validation itself is performed by `MolraptorConfig`.

::: molraptor.pipeline.validate_config

### run

`run()` executes the file workflow and returns the same
`FingerprintEncodingResult` used to create the persisted artifacts.

A successful execution writes:

```text
fingerprints.npy
fingerprints.csv
input_statuses.csv
encoding_metadata.json
```

Individual invalid SMILES do not stop a batch when at least one input is valid.
A batch containing zero valid SMILES is a global file-workflow failure and
publishes no final artifacts.

For input formats, CLI operation, output schemas, and failure behavior, see the
[Usage guide](usage.md).

::: molraptor.pipeline.run

## Validation Utility

`DataValidator` provides public stateless validation helpers.

`ensure_required_columns()` verifies that specified columns exist in a pandas
DataFrame.

`is_valid_smiles()` applies the same RDKit parsing rule used by the in-memory
encoder and returns whether the supplied string produces a non-empty molecule.

Validation does not curate, harmonize, canonicalize, or replace the supplied
SMILES.

::: molraptor.validators.DataValidator

## Version

`__version__` exposes the installed MOLRAPTOR package version.

::: molraptor.version
