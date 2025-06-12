"""Centralised artifact & log writer (YAML-aware)."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence, Union, TYPE_CHECKING

import pandas as pd

# Sólo para tipado estático; no rompe la ejecución si MolraptorConfig aún
# no está disponible al momento de importar este módulo.
if TYPE_CHECKING:  # pragma: no cover
    from ..config import MolraptorConfig

logger = logging.getLogger("molraptor.results")


class LogErrors:
    """Guarda artefactos (CSV, NPY, TXT) y registra errores."""

    def __init__(
        self,
        output_root: Path | str = "artifacts",
        cfg: Optional["MolraptorConfig"] = None,
    ) -> None:
        self.cfg = cfg
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Helpers generics                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _header() -> str:
        ts = datetime.utcnow().isoformat(timespec="seconds")
        return f"Molraptor Results\nGenerated: {ts}\n\n"

    def save_dataframe(self, df: pd.DataFrame, filename: str) -> Path:
        path = self.output_root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.info("Saved DataFrame to %s", path)
        return path

    def write_text(self, content: str, filename: str) -> Path:
        path = self.output_root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(self._header())
            fh.write(content)
        logger.info("Wrote text report to %s", path)
        return path

    # ------------------------------------------------------------------ #
    # Logging de errores – usa la ruta del YAML si está definida          #
    # ------------------------------------------------------------------ #

    def log_errors(
        self,
        errors: Sequence[Union[int, str]],
        step: str,
    ) -> None:
        """
        Save `errors` on disc.

        1. Si el YAML define `paths.error_log_file`, se usa esa ruta.
        2. On the contrary: artifacts/<step>_errors.txt
        """
        # ── decidir ruta ────────────────────────────────────────────────
        if self.cfg and getattr(self.cfg.paths, "error_log_file", None):
            err_path = Path(self.cfg.paths.error_log_file)
        else:
            err_path = self.output_root / f"{step}_errors.txt"

        # ── crear directorio y escribir ─────────────────────────────────
        err_path.parent.mkdir(parents=True, exist_ok=True)
        with err_path.open("w", encoding="utf-8") as fh:
            for err in errors:
                fh.write(f"{err}\n")

        logger.warning("[%s] %d errors logged to %s", step, len(errors), err_path)
