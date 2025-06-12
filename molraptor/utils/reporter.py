# reporter.py

import pandas as pd
import numpy as np

class ReportGenerator:
    def __init__(self, dataframe: pd.DataFrame, fingerprints: np.ndarray):
        self.df = dataframe
        self.fps = fingerprints

    def get_statistics_block(self) -> str:
        total = len(self.df)
        valid_smiles = self.df["SMILES"].notna().sum()
        n_pos = (self.df["Label"] == 1).sum()
        n_neg = (self.df["Label"] == 0).sum()
        pct_pos = (n_pos / total) * 100 if total else 0
        pct_neg = (n_neg / total) * 100 if total else 0
        fp_count = len(self.fps)
        fp_dim = self.fps.shape[1] if self.fps.ndim == 2 else "N/A"

        return f'''
------------------------------
Dataset Summary:
- Total entries: {total}
- Valid SMILES: {valid_smiles}
- Labels:
  - Class 0 (inactive): {n_neg} ({pct_neg:.1f}%)
  - Class 1 (agonist):  {n_pos} ({pct_pos:.1f}%)
- Fingerprints generated: {fp_count}
- Fingerprint dimension: {fp_dim}
------------------------------
'''.strip()
