"""Run real-data reproduction and policy-sensitivity experiments."""

import argparse
import importlib.metadata
import json
import logging
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from biog_reliability.benchmark import (
    PROVENANCE,
    UPSTREAM_COMMIT,
    prepare_predictions,
    prepare_truth,
)
from biog_reliability.metrics import (
    compare_models,
    measured_join,
    recall_at_k,
    summarize_recall,
    threshold_curve,
)
from biog_reliability.provenance import run_context
from biog_reliability.reporting import export_analysis, sha256, write_json
from biog_reliability.uncertainty import bootstrap_ap, paired_recall_difference

ROOT = Path(__file__).resolve().parents[1]


def main(reps=1000):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    upstream = ROOT / "research/upstream"
    actual_commit = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_commit != UPSTREAM_COMMIT:
        raise ValueError("Upstream version changed. Review before accepting new inputs.")
    truth_path = upstream / "data/manuscript/manuscript_primary.csv"
    raw = pd.read_csv(truth_path)
    full, full_qc = prepare_truth(raw)
    truth, truth_qc = prepare_truth(raw, no_bulge=True)
    first, first_qc = prepare_truth(raw, policy="first_record")
    data_dir = ROOT / "data/raw/zenodo"
    tools = {
        "moff": "standard_tool_predictions",
        "crisot": "standard_tool_predictions",
        "cctop": "standard_tool_predictions",
        "crispert": "no_bulge_ml_tool_predictions",
        "crisprip": "no_bulge_ml_tool_predictions",
    }
    predictions, full_predictions, qc, inputs = (
        [],
        [],
        [],
        {str(truth_path.relative_to(ROOT)): sha256(truth_path)},
    )
    for slug, folder in tools.items():
        path = data_dir / folder / f"prediction_contract_{slug}.csv"
        logging.info("Reading %s", slug)
        pp, info = prepare_predictions(path, full)
        # Compact exports preserve all labeled keys plus rank <=1250 candidates.
        # The full candidate counts remain in QC. No rank is recalculated.
        keep = pp.site_id.isin(first.site_id) | pp["rank"].le(1250)
        compact = pp[keep].copy()
        if folder == "standard_tool_predictions":
            full_predictions.append(compact)
        parts = compact.site_id.str.split("::", expand=True)
        compact = compact[parts[0].str.len().eq(23) & parts[1].str.len().eq(23)]
        predictions.append(compact)
        qc.append(info)
        inputs[str(path.relative_to(ROOT))] = sha256(path)
    predictions = pd.concat(predictions, ignore_index=True)
    full_predictions = pd.concat(full_predictions, ignore_index=True)
    output = ROOT / "results/experiment"
    output.mkdir(parents=True, exist_ok=True)
    processed = ROOT / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    truth.to_csv(processed / "truth.csv", index=False)
    predictions.to_csv(processed / "predictions.csv", index=False)
    write_json(processed / "provenance.json", PROVENANCE)
    recalls = recall_at_k(truth, predictions)
    summary = summarize_recall(recalls)
    reference_path = (
        upstream
        / "results/benchmark_runs/no_bulge_ml_comparison/benchmark_overall_recall_curves.csv"
    )
    reference = pd.read_csv(reference_path).rename(columns={"tool": "model"})
    reproduction = summary.merge(
        reference[["model", "k", "macro_recall", "micro_recall", "hits_sum"]],
        on=["model", "k"],
        suffixes=("", "_published"),
    )
    reproduction["macro_absolute_error"] = (
        reproduction.macro_recall - reproduction.macro_recall_published
    ).abs()
    reproduction["micro_absolute_error"] = (
        reproduction.micro_recall - reproduction.micro_recall_published
    ).abs()
    reproduction["matches_1e_12"] = reproduction.macro_absolute_error.lt(
        1e-12
    ) & reproduction.micro_absolute_error.lt(1e-12)
    inputs[str(reference_path.relative_to(ROOT))] = sha256(reference_path)
    common_keys = set(truth.site_id)
    for _, group in predictions.groupby("model"):
        common_keys &= set(group.site_id)
    common_truth = truth[truth.site_id.isin(common_keys)]
    uncertainty = []
    for model, pp in predictions.groupby("model"):
        joined = measured_join(common_truth, pp)
        for unit in ("row", "guide"):
            logging.info("Bootstrap %s %s", model, unit)
            uncertainty.append({"model": model, **bootstrap_ap(joined, reps=reps, unit=unit)})
    sensitivity, threshold_tables = [], []
    for cutoff in (0.01, 0.05, 0.1, 0.5, 1.0):
        tt, info = prepare_truth(raw, threshold=cutoff, no_bulge=True)
        mm = compare_models(tt, predictions, common=True)
        mm["indel_threshold_percent"] = cutoff
        mm["conflicting_site_ids"] = info["conflicting_site_ids"]
        sensitivity.append(mm)
    for model, pp in predictions.groupby("model"):
        joined = measured_join(common_truth, pp)
        thresholds = np.unique(np.quantile(joined.score, np.linspace(0, 1, 31)))
        table = threshold_curve(common_truth, pp, thresholds)
        table["model"] = model
        threshold_tables.append(table)
    policy = pd.concat(
        [
            compare_models(full, full_predictions).assign(policy="exclude_conflicts"),
            compare_models(first, full_predictions).assign(policy="first_record"),
        ]
    )
    tables = {
        "classification_model_scored": compare_models(truth, predictions),
        "classification_common_scored": compare_models(truth, predictions, common=True),
        "recall_by_guide": recalls,
        "recall_summary": summary,
        "reproduction": reproduction,
        "uncertainty": pd.DataFrame(uncertainty),
        "indel_threshold_sensitivity": pd.concat(sensitivity),
        "score_threshold_sensitivity": pd.concat(threshold_tables),
        "duplicate_policy_sensitivity": policy,
        "prediction_qc": pd.DataFrame(qc),
    }
    paired = paired_recall_difference(recalls, "CRISPert", "MOFF", reps=2000)
    metadata = {
        **run_context(ROOT),
        "run_date": datetime.now(UTC).isoformat(),
        "upstream_commit": UPSTREAM_COMMIT,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "pandas", "scikit-learn", "streamlit", "biog-reliability")
        },
        "seed": 20261019,
        "bootstrap_reps": reps,
        "provenance": PROVENANCE,
        "full_truth_qc": full_qc,
        "no_bulge_truth_qc": truth_qc,
        "first_record_truth_qc": first_qc,
        "paired_recall_difference": paired,
        "input_sha256": inputs,
        "common_scored_sites": len(common_truth),
        "common_scored_positives": int(common_truth.status.eq("positive").sum()),
        "prediction_export_scope": (
            "all first-record truth identities plus rank <=1250; not full candidate universe"
        ),
        "limitations": [
            "pooled published assay/context",
            "sequence-chromosome identity may merge loci",
            "training data overlap unknown",
            "predictions not recomputed from model weights",
            "classification conditional on measured scored cohort",
            "length-23 is a no-bulge proxy",
        ],
    }
    export_analysis(output, tables, metadata)
    write_json(output / "summary.json", metadata)
    logging.info("Reproduction matches: %s/%s", reproduction.matches_1e_12.sum(), len(reproduction))
    print(json.dumps({"full": full_qc, "no_bulge": truth_qc, "paired": paired}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    main(parser.parse_args().bootstrap_reps)
