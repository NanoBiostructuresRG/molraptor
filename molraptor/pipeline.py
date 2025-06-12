"""Molraptor pipeline orchestrator (production-ready)."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import MolraptorConfig
from .utils.log_print import LogErrors
from .utils.result_manager import ResultManager
from .utils.reporter import ReportGenerator
from .steps.fetch import FetchStep
from .steps.curate import CurateStep
from .steps.fingerprint import FingerprintStep
from .steps.fp_integrity import FingerprintIntegrityStep


class MolraptorPipeline:
    """Run the full MOLRAPTOR workflow step by step."""

    def __init__(self, cfg: MolraptorConfig, output_root: Path | str = "artifacts") -> None:
        self.cfg = cfg
        self.results = LogErrors(Path(output_root))
        self.logger = logging.getLogger("molraptor.pipeline")

        self.steps = [
            FetchStep(cfg, self.results),
            CurateStep(cfg, self.results),
            FingerprintStep(cfg, self.results),
            FingerprintIntegrityStep(cfg, self.results),
        ]

    def _run_step(self, step, data: Path | str) -> Path | str:
        step_name = step.__class__.__name__
        self.logger.info(f"→ Starting: {step_name}")
        try:
            output = step.run(data)
            self.logger.info(f"Completed: {step_name}")
            return output
        except Exception as e:
            self.logger.error(f"Failed at step {step_name}: {e}")
            self.results.log_exception(step_name, e)
            raise

    def run(self) -> None:
        data = self.cfg.paths.raw_input_file
        for step in self.steps:
            data = self._run_step(step, data)
        self.logger.info("Pipeline completed successfully")
        
        summary = "\n".join([f"Step completed: {step.__class__.__name__}" for step in self.steps])
        result_path = self.results.output_root / "summary.txt"
        ResultManager(result_path).write_results(summary)


        # Generate summary report after all steps
        import pandas as pd
        import numpy as np
        
        curated_df = pd.read_csv(self.cfg.paths.curated_output_file)
        fingerprints = np.load(self.cfg.paths.fingerprint_array_file)

        report = ReportGenerator(curated_df, fingerprints)
        summary = report.get_statistics_block()
        result_path = self.results.output_root / "summary.txt"
        ResultManager(result_path).write_results(summary)
        
        