# SPDX-License-Identifier: LGPL-3.0-or-later
"""Command-line entry point for the CSV/TXT fingerprint workflow."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from .config import MolraptorConfig
from .morgan import MorganFingerprintProfile
from .pipeline import run
from .version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molraptor",
        description="Calculate traceable Morgan fingerprints from SMILES.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"MOLRAPTOR {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True
    run_parser = subparsers.add_parser(
        "run",
        help="Encode SMILES from a CSV or TXT file.",
    )
    run_parser.add_argument("--input", type=Path, required=True, metavar="PATH")
    run_parser.add_argument(
        "--smiles-column",
        default="SMILES",
        metavar="NAME",
        help="CSV column containing SMILES (default: SMILES).",
    )
    run_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
        metavar="PATH",
    )
    run_parser.add_argument("--radius", type=int, default=2, metavar="INTEGER")
    run_parser.add_argument(
        "--fp-size",
        type=int,
        default=2048,
        metavar="INTEGER",
    )
    run_parser.add_argument(
        "--include-chirality",
        action="store_true",
    )
    return parser


def _run(args: argparse.Namespace) -> None:
    profile = MorganFingerprintProfile(
        radius=args.radius,
        fp_size=args.fp_size,
        include_chirality=args.include_chirality,
    )
    config = MolraptorConfig(
        input_path=args.input,
        smiles_column=args.smiles_column,
        output_dir=args.output_dir,
        profile=profile,
    )
    result = run(config)
    print(
        f"Encoded {result.valid_count} valid SMILES; "
        f"{result.invalid_count} invalid. Outputs: {config.output_dir}"
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Parse command-line arguments and execute the file workflow.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Arguments to parse without the executable name. If ``None``, arguments
        are read from :data:`sys.argv` by :mod:`argparse`.

    Raises
    ------
    SystemExit
        If argument parsing fails or workflow validation reports a global
        failure.

    Notes
    -----
    The ``run`` command delegates to the same file workflow and in-memory
    encoder exposed by the Python API.
    """

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            _run(args)
    except (OSError, ValueError, ValidationError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()


__all__ = ["main"]
