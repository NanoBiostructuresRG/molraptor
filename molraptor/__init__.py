"""Molraptor package root."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("molraptor")
except PackageNotFoundError:
    __version__ = "1.0.0"

from .pipeline import MolraptorPipeline  # noqa: F401
