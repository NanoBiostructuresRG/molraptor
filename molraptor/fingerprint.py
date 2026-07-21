# SPDX-License-Identifier: LGPL-3.0-or-later
"""CSV/TXT workflow for encoding SMILES and writing traceable artifacts.

The workflow reads user-provided SMILES without curation, harmonization,
canonicalization, or replacement. It delegates all molecule parsing,
fingerprint calculation, status generation, and hashing to
:func:`molraptor.morgan.encode_fingerprints`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from .config import MolraptorConfig
from .morgan import FingerprintEncodingResult, encode_fingerprints


OUTPUT_FILENAMES = (
    "fingerprints.npy",
    "fingerprints.csv",
    "input_statuses.csv",
    "encoding_metadata.json",
)


def _read_csv_smiles(path: Path, smiles_column: str) -> list[str]:
    try:
        frame = pd.read_csv(
            path,
            dtype=str,
            encoding="utf-8",
            keep_default_na=False,
            na_filter=False,
            skip_blank_lines=False,
        )
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"CSV input '{path}' has no header") from exc
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"Unable to read CSV input '{path}': {exc}") from exc

    if smiles_column not in frame.columns:
        raise ValueError(
            f"CSV input '{path}' does not contain configured SMILES column "
            f"'{smiles_column}'"
        )
    return frame[smiles_column].tolist()


def _remove_line_ending(line: str) -> str:
    """Remove one trailing CRLF, CR, or LF without changing other characters."""

    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\r", "\n")):
        return line[:-1]
    return line


def _read_txt_smiles(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            return [_remove_line_ending(line) for line in stream]
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Unable to read TXT input '{path}': {exc}") from exc


def _read_smiles(path: Path, smiles_column: str) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv_smiles(path, smiles_column)
    if suffix == ".txt":
        return _read_txt_smiles(path)
    raise ValueError(
        f"Unsupported input format '{path.suffix or '<none>'}'; "
        "expected .csv or .txt"
    )


def _write_outputs(
    config: MolraptorConfig,
    result: FingerprintEncodingResult,
) -> None:
    status_records = [
        status.model_dump(mode="json") for status in result.input_statuses
    ]
    status_frame = pd.DataFrame.from_records(status_records)
    status_frame["input_index"] = status_frame["input_index"].astype("int64")
    status_frame["fingerprint_index"] = pd.array(
        status_frame["fingerprint_index"],
        dtype="Int64",
    )
    input_format = config.input_path.suffix.lower().removeprefix(".")
    metadata = {
        "source_file_name": config.input_path.name,
        "input_format": input_format,
        "smiles_column": (
            config.smiles_column if input_format == "csv" else None
        ),
        "input_count": len(result.input_statuses),
        **result.serialize_metadata(),
    }

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".molraptor-", dir=output_dir) as temp_name:
        staging_dir = Path(temp_name)
        np.save(
            staging_dir / "fingerprints.npy",
            result.fingerprints,
            allow_pickle=False,
        )
        pd.DataFrame(result.fingerprints).to_csv(
            staging_dir / "fingerprints.csv",
            index=False,
        )
        status_frame.to_csv(
            staging_dir / "input_statuses.csv",
            index=False,
        )
        (staging_dir / "encoding_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        for filename in OUTPUT_FILENAMES:
            os.replace(staging_dir / filename, output_dir / filename)


class FingerprintStep:
    """Execute one configured CSV/TXT fingerprint workflow.

    Parameters
    ----------
    config : MolraptorConfig
        Source, destination, and Morgan profile for the execution.

    Attributes
    ----------
    config : MolraptorConfig
        Immutable workflow configuration.
    """

    def __init__(self, config: MolraptorConfig) -> None:
        self.config = config

    def run(self) -> FingerprintEncodingResult:
        """Read, encode, validate, and persist one ordered SMILES batch.

        Returns
        -------
        FingerprintEncodingResult
            The result supplying persisted matrix content, row statuses,
            scientific metadata, hashes, and runtime provenance. Source file
            name, input format, and configured CSV column come from
            :class:`MolraptorConfig`.

        Raises
        ------
        ValueError
            If input validation fails or the batch contains zero valid SMILES.
        OSError
            If output artifacts cannot be written.

        Notes
        -----
        Invalid individual inputs remain in ``input_statuses.csv`` while valid
        fingerprints retain their original ordering. A successful run writes
        ``fingerprints.npy``, ``fingerprints.csv``, ``input_statuses.csv``, and
        ``encoding_metadata.json``.
        """

        smiles = _read_smiles(
            self.config.input_path,
            self.config.smiles_column,
        )
        result = encode_fingerprints(smiles, self.config.profile)
        if result.valid_count == 0:
            raise ValueError("Input contains zero valid SMILES")

        _write_outputs(self.config, result)
        return result


__all__ = ["FingerprintStep", "OUTPUT_FILENAMES"]
