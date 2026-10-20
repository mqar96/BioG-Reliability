"""Execute pinned upstream functions, compare deposited ranks and alternative order policies."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from biog_reliability.benchmark import prepare_predictions, prepare_truth
from biog_reliability.metrics import recall_at_k, summarize_recall
from biog_reliability.provenance import run_context, seal_directory
from biog_reliability.reporting import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    upstream = ROOT / "research/upstream"
    sys.path.insert(0, str(upstream / "src"))
    from offtarget_benchmark.benchmark_metrics import evaluate_tool_by_guide
    from offtarget_benchmark.benchmark_tables import prepare_prediction_table, prepare_truth_table

    out = ROOT / "results/cctop-investigation"
    out.mkdir(parents=True, exist_ok=True)
    rawpath = upstream / "data/manuscript/manuscript_primary.csv"
    path = ROOT / "data/raw/zenodo/standard_tool_predictions/prediction_contract_cctop.csv"
    raw = pd.read_csv(rawpath)
    raw = raw[raw.guide_seq.str.len().eq(23) & raw.offtarget_seq.str.len().eq(23)]
    temp = ROOT / "work/cctop-truth.csv"
    temp.parent.mkdir(exist_ok=True)
    raw.to_csv(temp, index=False)
    truth, _ = prepare_truth(raw)
    tt, _ = prepare_truth_table(temp, "hg38")
    pp, _ = prepare_prediction_table(pd.read_csv(path), "cctop", "hg38")
    pp = pp[pp.guide_key.str.len().eq(23) & pp.off_target_seq.str.len().eq(23)]
    _, by_guide, _ = evaluate_tool_by_guide(
        tool_slug="cctop",
        tool_display="CCTop",
        pred_table=pp,
        truth_sites=tt,
        k_values=[50, 100, 250, 500, 1250],
    )
    upstream_summary = (
        by_guide[by_guide.n_truth_true.gt(0)]
        .groupby("k")
        .agg(macro_recall=("recall", "mean"), hits=("hits", "sum"))
        .reset_index()
    )
    pred, _ = prepare_predictions(path, truth, no_bulge=True)
    policies = []
    for policy in ["deposited_rank", "stable_score_locus_order", "reverse_tie_site_order"]:
        candidate = pred.copy()
        if policy != "deposited_rank":
            candidate = candidate.sort_values(
                ["guide_id", "rank", "site_id"],
                ascending=[True, True, policy != "reverse_tie_site_order"],
            )
            candidate["rank"] = candidate.groupby("guide_id").cumcount() + 1
        policies.append(summarize_recall(recall_at_k(truth, candidate)).assign(policy=policy))
    result = pd.concat(policies)
    # The policy label explicitly describes site ordering; never fit it to reference values.
    result["policy"] = result.policy.replace({"stable_score_locus_order": "rank_then_site_id"})
    result.to_csv(out / "order_policies.csv", index=False)
    upstream_summary.to_csv(out / "upstream_function_rerun.csv", index=False)
    ours = result[result.policy.eq("deposited_rank")]
    context = {
        **run_context(ROOT),
        "upstream_code_sha256": {
            str(p.relative_to(upstream)): sha256(p)
            for p in [
                upstream / "src/offtarget_benchmark/benchmark_tables.py",
                upstream / "src/offtarget_benchmark/benchmark_metrics.py",
            ]
        },
        "upstream_rerun_matches_biog": bool(
            np.allclose(ours.macro_recall, upstream_summary.macro_recall, atol=1e-12, rtol=0)
        ),
        "interpretation": (
            "Pinned upstream functions also use rank <= K. "
            "Historical artifact generation remains unresolved; "
            "alternate ordering is diagnostic only."
        ),
    }
    write_json(out / "summary.json", context)
    seal_directory(out, context)
    print(upstream_summary.to_string(index=False))


if __name__ == "__main__":
    main()
