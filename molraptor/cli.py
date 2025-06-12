"""Typer CLI entry-point for Molraptor."""

from __future__ import annotations

import logging
from pathlib import Path

import typer

from .config import MolraptorConfig
from .pipeline import MolraptorPipeline

app = typer.Typer(add_completion=False)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@app.command()
def run(config: Path = typer.Option("configs/default.yaml", help="Path to YAML config")):
    """Run the full MOLRAPTOR pipeline."""
    try:
        cfg = MolraptorConfig.load(config)
    except FileNotFoundError as e:
        typer.echo(f"[ERROR] Config file not found: {e}", err=True)
        raise typer.Exit(code=1)

    pipeline = MolraptorPipeline(cfg)
    pipeline.run()


@app.command()
def version():
    """Show the current version of Molraptor."""
    typer.echo("MOLRAPTOR version 1.0.0")


def main():
    app()


if __name__ == "__main__":
    main()
