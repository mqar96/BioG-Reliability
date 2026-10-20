from pathlib import Path

import pandas as pd
import pytest

from biog_reliability.benchmark import prepare_truth

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.realdata
def test_published_cohort():
    path = ROOT / "research/upstream/data/manuscript/manuscript_primary.csv"
    if not path.exists():
        pytest.skip("Download pinned public data with scripts/fetch_data.py")
    raw = pd.read_csv(path)
    full, info = prepare_truth(raw)
    nobulge, _ = prepare_truth(raw, no_bulge=True)
    assert len(raw) == 3827 and len(full) == 1806
    assert full.status.eq("positive").sum() == 118
    assert len(nobulge) == 1768 and nobulge.status.eq("positive").sum() == 114
    assert info["conflicting_site_ids"] == 76


@pytest.mark.realdata
def test_recomputed_published_ml_recall():
    path = ROOT / "results/experiment/reproduction.csv"
    if not path.exists():
        pytest.skip("Run scripts/run_experiments.py first")
    frame = pd.read_csv(path)
    ml = frame[frame.model.isin(["CRISPert", "CRISPR-IP"])]
    assert len(ml) == 10
    assert ml.matches_1e_12.all()
