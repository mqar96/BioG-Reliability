"""TrueOT validation, preserving study/context and removing known guide overlap.

Source labels are experimental author calls, not a common percent-indel threshold.
Deposited scores are evaluated without training or parameter selection.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from biog_reliability.metrics import classification_metrics
from biog_reliability.provenance import run_context, seal_directory
from biog_reliability.reporting import sha256, write_json
from biog_reliability.uncertainty import bootstrap_ap

ROOT = Path(__file__).resolve().parents[1]


def normalize(series):
    return series.str.replace("-", "", regex=False).str.replace("_", "", regex=False).str[:20]


def main():
    data = ROOT / "data/raw/external"
    out = ROOT / "results/external"
    out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_excel(data / "TrueOT_v1_1_allscores.xlsx", header=2)
    studies = pd.read_excel(data / "Table_S1_TrueOT_dataset_summary.xlsx", header=2)
    benchmark = pd.read_csv(ROOT / "research/upstream/data/manuscript/manuscript_primary.csv")
    frame["guide_id"] = normalize(frame.wildtype_seq)
    frame["status"] = np.where(frame.TrueOT.eq(1), "positive", "measured_negative")
    # Preserve study, source locus and context. No coordinate conversion is assumed.
    identity = [
        "Dataset",
        "wildtype_seq",
        "offtarget_seq",
        "chromosome",
        "start",
        "end",
        "Cell type",
        "Delivery of Cas9",
        "Delivery of gRNA",
    ]
    frame["identity"] = frame[identity].astype(str).agg("::".join, axis=1)
    conflicting = frame.groupby("identity").TrueOT.nunique().gt(1)
    repeated = int(frame.identity.duplicated().sum())
    frame = frame[~frame.identity.isin(conflicting[conflicting].index)].drop_duplicates("identity")
    benchmark_guides = set(normalize(benchmark.guide_seq))
    benchmark_pmids = set(benchmark.pmid.astype(str))
    pmids = studies.set_index("Dataset")["PUBMED ID"].astype(str)
    frame["pmid"] = frame.Dataset.map(pmids)
    frame["guide_disjoint"] = ~frame.guide_id.isin(benchmark_guides)
    frame["study_disjoint"] = ~frame.pmid.isin(benchmark_pmids)
    # Inspect two actual supplied CRISPR-NET training tables. These are a partial inventory.
    training = set()
    train_rows = []
    for filename, column, outcome in [
        ("CIRCLE_seq_10gRNA_wholeDataset.csv", "sgRNA_seq", "label"),
        ("SITE-Seq_offTarget_wholeDataset.csv", "on_seq", "reads"),
    ]:
        raw = pd.read_csv(data / filename)
        guides = set(normalize(raw[column]))
        training |= guides
        train_rows.append(
            {
                "file": filename,
                "rows": len(raw),
                "guides": len(guides),
                "detected_rows": int(raw[outcome].gt(0).sum()),
                "zero_or_undetected_rows": int(raw[outcome].eq(0).sum()),
                "shared_trueot_guides": len(guides & set(frame.guide_id)),
                "negative_interpretation": (
                    "not detected/computational candidates; not measured negatives"
                ),
            }
        )
    masks = pd.read_excel(data / "TrueOT_v1_1_gRNA_overlap.xlsx")
    masks["guide_id"] = normalize(masks["TrueOT gRNA"])
    known_net = set(masks.loc[masks["CRISPR-NET_in_TrueOT"], "guide_id"]) | training
    frame["known_training_overlap"] = frame.guide_id.isin(known_net)
    # Common population for these two high-is-risk scores. Do not compare with main cohort AP.
    models = ["CFD", "CRISPR-NET"]
    common = frame[frame[models].notna().all(axis=1)].copy()
    subsets = {
        "all_common_scored": common,
        "guide_disjoint": common[common.guide_disjoint],
        "guide_and_study_disjoint": common[common.guide_disjoint & common.study_disjoint],
        "guide_study_disjoint_known_training_excluded": common[
            common.guide_disjoint & common.study_disjoint & ~common.known_training_overlap
        ],
    }
    metrics, uncertainty, strata = [], [], []
    for cohort, subset in subsets.items():
        for model in models:
            stats = classification_metrics(subset.TrueOT, subset[model])
            metrics.append(
                {
                    "cohort": cohort,
                    "model": model,
                    "guides": subset.guide_id.nunique(),
                    "studies": subset.Dataset.nunique(),
                    **stats,
                }
            )
            if cohort == "guide_study_disjoint_known_training_excluded":
                for unit, groups in [("guide", subset.guide_id), ("study", subset.Dataset)]:
                    joined = subset.assign(score=subset[model], guide_id=groups)
                    ci = bootstrap_ap(joined, reps=1000, unit="guide")
                    uncertainty.append({"cohort": cohort, "model": model, **ci, "unit": unit})
                for dimension in ["Dataset", "Cell type"]:
                    for label, group in subset.groupby(dimension):
                        strata.append(
                            {
                                "dimension": dimension,
                                "stratum": label,
                                "model": model,
                                "guides": group.guide_id.nunique(),
                                **classification_metrics(group.TrueOT, group[model]),
                            }
                        )
    qc = {
        "source_rows": 1903,
        "sites_after_identity_policy": len(frame),
        "positive_rows_after_identity_policy": int(frame.TrueOT.sum()),
        "guides": frame.guide_id.nunique(),
        "studies": frame.Dataset.nunique(),
        "duplicate_identity_rows": repeated,
        "conflicting_identities": int(conflicting.sum()),
        "source_guides_overlapping_primary": len(set(frame.guide_id) & benchmark_guides),
        "common_scored_rows": len(common),
        "scores_missing": {m: int(frame[m].isna().sum()) for m in models},
        "known_training_overlap_guides": len(set(frame.guide_id) & known_net),
        "input_sha256": {
            p.name: sha256(p) for p in data.glob("*") if p.suffix in {".xlsx", ".csv"}
        },
        "seed": 20261019,
        "bootstrap_reps": 1000,
        "ci": "95% percentile, guide or study clusters",
        "limitations": [
            "Training inventory partial; author mask not independently complete",
            "CFD training overlap not fully cleared",
            "Assay-specific author labels; no unified quantitative relabeling",
            "Independent of primary benchmark guides/studies, not all model training",
            "Within-cohort retrospective evaluation, no inference or calibration",
        ],
    }
    pd.DataFrame(metrics).to_csv(out / "classification.csv", index=False)
    pd.DataFrame(uncertainty).to_csv(out / "uncertainty.csv", index=False)
    pd.DataFrame(strata).to_csv(out / "stratified.csv", index=False)
    pd.DataFrame(train_rows).to_csv(out / "training_inventory.csv", index=False)
    context = {**run_context(ROOT), **qc}
    write_json(out / "summary.json", context)
    seal_directory(out, context)
    print(pd.DataFrame(metrics).to_string(index=False))


if __name__ == "__main__":
    main()
