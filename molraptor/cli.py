# SPDX-License-Identifier: LGPL-3.0-or-later
"""Command-line entry point for the CSV/TXT fingerprint workflow."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from .config import MolraptorConfig
from .fingerprints import FINGERPRINT_TYPES, MorganFingerprintProfile
from .pipeline import run
from .version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molraptor",
        description="Calculate traceable molecular fingerprints from SMILES.",
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
    run_parser.add_argument(
        "--fingerprint",
        choices=FINGERPRINT_TYPES,
        default="morgan",
        help="Fingerprint type (default: morgan).",
    )
    run_parser.add_argument(
        "--radius",
        type=int,
        default=None,
        metavar="INTEGER",
        help="Morgan radius (Morgan only).",
    )
    run_parser.add_argument(
        "--fp-size",
        type=int,
        default=None,
        metavar="INTEGER",
        help="Morgan fingerprint size (Morgan only).",
    )
    run_parser.add_argument(
        "--include-chirality",
        action="store_true",
        default=None,
        help="Include chirality in Morgan fingerprints (Morgan only).",
    )
    return parser


def _run(args: argparse.Namespace) -> None:
    morgan_option_used = any(
        value is not None
        for value in (args.radius, args.fp_size, args.include_chirality)
    )
    if args.fingerprint != "morgan" and morgan_option_used:
        raise ValueError(
            "--radius, --fp-size, and --include-chirality are only valid "
            "with --fingerprint morgan"
        )

    profile = None
    if args.fingerprint == "morgan":
        profile_kwargs: dict[str, int | bool] = {}
        if args.radius is not None:
            profile_kwargs["radius"] = args.radius
        if args.fp_size is not None:
            profile_kwargs["fp_size"] = args.fp_size
        if args.include_chirality is not None:
            profile_kwargs["include_chirality"] = args.include_chirality
        profile = MorganFingerprintProfile(**profile_kwargs)

    config = MolraptorConfig(
        input_path=args.input,
        smiles_column=args.smiles_column,
        output_dir=args.output_dir,
        fingerprint_type=args.fingerprint,
        profile=profile,
    )
    result = run(config)
    print(
        f"Encoded {result.valid_count} valid SMILES; "
        f"{result.invalid_count} invalid. Outputs: {config.output_dir}"
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Parse command-line arguments and execute the file workflow."""

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
