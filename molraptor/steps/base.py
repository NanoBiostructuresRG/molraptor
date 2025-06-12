"""Abstract base class for pipeline steps."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..config import MolraptorConfig
from ..utils.log_print import LogErrors


class BaseStep(ABC):
    """Pipeline step contract."""    

    def __init__(
        self,
        cfg: MolraptorConfig,
        results: LogErrors,
        logger: logging.Logger | None = None,
    ) -> None:
        self.cfg = cfg
        self.results = results
        self.logger = logger or logging.getLogger(self.__class__.__name__.lower())

    @abstractmethod
    def run(self, data: Any) -> Any: ...
    """
    Execute the step logic with the given input.

    Args:
        data: Input data (file path or DataFrame), passed from previous step.

    Returns:
        Output data to be passed to the next pipeline step.
    """
