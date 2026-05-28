# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unified CLI entry point for MOLRAPTOR.

This module provides the ``molraptor`` command registered in ``pyproject.toml``
under ``[project.scripts]``. It exposes one subcommand:

- ``molraptor run`` — execute the full molecular pipeline.

Global flags (``--verbose``, ``--config``, ``--version``) are available to
all subcommands via argparse parent parsers.
"""

import argparse
import logging
import sys
from pathlib import Path

from .version import __version__

__all__ = ["main"]

logger = logging.getLogger(__name__)


def _global_parser() -> argparse.ArgumentParser:
    """Return a parent parser with shared flags for all subcommands."""
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--verbose",
        action="store_true",
        help="Enable progress logging (INFO level).",
    )
    parent.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default.yaml"),
        metavar="PATH",
        help="Path to YAML configuration file. Defaults to configs/default.yaml.",
    )
    return parent


def _build_parser() -> argparse.ArgumentParser:
    global_parent = _global_parser()

    parser = argparse.ArgumentParser(
        prog="molraptor",
        description="MOLRAPTOR — modular pipeline for fetching, curating, and encoding molecular datasets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[global_parent],
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"MOLRAPTOR {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # ------------------------------------------------------------------ #
    # molraptor run
    # ------------------------------------------------------------------ #
    subparsers.add_parser(
        "run",
        help="Run the full molecular pipeline.",
        description="Fetch, curate, and encode molecular datasets from PubChem.",
        parents=[global_parent],
    )

    return parser


def _configure_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s:%(name)s:%(message)s",
    )


def _run(args: argparse.Namespace) -> None:
    from .config import MolraptorConfig
    from .pipeline import MolraptorPipeline

    cfg = MolraptorConfig.load(args.config)
    MolraptorPipeline(cfg).run()


def main() -> None:
    """Entry point for the ``molraptor`` CLI command.

    Registered in ``pyproject.toml`` as::

        [project.scripts]
        molraptor = "molraptor.cli:main"

    Parses arguments, configures logging, and dispatches to the appropriate
    subcommand handler.

    Notes
    -----
    The ``--verbose`` flag sets the root logger to ``INFO`` level, which
    exposes progress messages from all ``molraptor.*`` modules. Without it,
    only ``WARNING`` and above are shown.
    """
    parser = _build_parser()
    args = parser.parse_args()
    _configure_logging(args.verbose)

    if args.command == "run":
        _run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()