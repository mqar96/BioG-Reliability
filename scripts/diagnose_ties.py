"""Real-data extension: enforce a candidate budget under coarse ranking ties."""

import json
from pathlib import Path

import pandas as pd

from biog_reliability.benchmark import prepare_predictions, prepare_truth
from biog_reliability.metrics import exact_budget_recall
from biog_reliability.provenance import seal_directory

root = Path(__file__).resolve().parents[1]
truth, _ = prepare_truth(
    pd.read_csv(root / "research/upstream/data/manuscript/manuscript_primary.csv"), no_bulge=True
)
pred, qc = prepare_predictions(
    root / "data/raw/zenodo/standard_tool_predictions/prediction_contract_cctop.csv",
    truth,
    no_bulge=True,
)
by_guide = exact_budget_recall(truth, pred)
by_guide.to_csv(root / "results/experiment/exact_budget_by_guide.csv", index=False)
summary = (
    by_guide.groupby(["model", "k"])[["expected_recall", "worst_recall", "best_recall"]]
    .mean()
    .reset_index()
)
baseline = pd.read_csv(root / "results/experiment/recall_summary.csv")
summary = summary.merge(baseline[["model", "k", "macro_recall"]], on=["model", "k"])
summary.to_csv(root / "results/experiment/exact_budget_comparison.csv", index=False)
print(summary.to_string(index=False))
seal_directory(
    root / "results/experiment", json.loads((root / "results/experiment/summary.json").read_text())
)
