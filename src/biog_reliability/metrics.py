"""Explicit estimands, denominators, and undefined-statistic reasons."""

import numpy as np
import pandas as pd
from sklearn.metrics import auc, average_precision_score, precision_recall_curve, roc_auc_score

from .validation import ValidationError


def classification_metrics(y, scores) -> dict:
    y, scores = np.asarray(y), np.asarray(scores, dtype=float)
    if len(y) != len(scores) or not np.isfinite(scores).all() or not set(y).issubset({0, 1}):
        raise ValidationError("Classification requires aligned binary labels and finite scores")
    result = {
        "n": len(y),
        "positives": int(y.sum()),
        "auroc": None,
        "average_precision": None,
        "auprc_trapezoid": None,
        "reason": None,
    }
    if not len(y):
        result["reason"] = "no_scored_measured_sites"
    elif len(np.unique(y)) < 2:
        result["reason"] = "single_class_cohort"
        # AP=1 for all-positive is mathematically defined, but uninformative;
        # intentionally suppress all discrimination metrics with this reason.
    else:
        precision, recall, _ = precision_recall_curve(y, scores)
        result.update(
            auroc=float(roc_auc_score(y, scores)),
            average_precision=float(average_precision_score(y, scores)),
            auprc_trapezoid=float(auc(recall, precision)),
        )
    return result


def measured_join(truth, pred):
    return truth.loc[truth.status.ne("untested")].merge(
        pred[["site_id", "score", "rank"]], on="site_id", validate="one_to_one"
    )


def compare_models(truth, predictions, common=False):
    """Compare on measured sites only; common=True fixes the scored-site cohort."""
    models = sorted(predictions.model.unique())
    cohort = truth.loc[truth.status.ne("untested")].copy()
    if common:
        keys = set(cohort.site_id)
        for model in models:
            keys &= set(predictions.loc[predictions.model.eq(model), "site_id"])
        cohort = cohort[cohort.site_id.isin(keys)]
    rows = []
    measured = truth.status.ne("untested")
    positives = truth.status.eq("positive")
    for model in models:
        pred = predictions[predictions.model.eq(model)]
        joined = measured_join(cohort, pred)
        stats = classification_metrics(joined.status.eq("positive").astype(int), joined.score)
        present = truth.site_id.isin(pred.site_id)
        rows.append(
            {
                "model": model,
                "cohort": "common_scored" if common else "model_scored",
                **stats,
                "measured_total": int(measured.sum()),
                "candidate_coverage": float((present & measured).sum() / measured.sum())
                if measured.any()
                else None,
                "positive_coverage": float((present & positives).sum() / positives.sum())
                if positives.any()
                else None,
                "unlabeled_in_cohort_predictions": int(
                    (~pred.site_id.isin(truth.loc[measured, "site_id"])).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def recall_at_k(truth, predictions, k_values=(50, 100, 250, 500, 1250)):
    """Use deposited per-guide ranks, including untested candidates in the budget.

    Missing predictions are misses. Shared tied ranks may select more than K;
    this is reported explicitly rather than silently breaking the ties.
    """
    if not k_values or any(not isinstance(k, int) or k <= 0 for k in k_values):
        raise ValidationError("K values must be positive integers")
    rows = []
    for model, pred in predictions.groupby("model"):
        for guide, group in truth.groupby("guide_id"):
            true_ids = set(group.loc[group.status.eq("positive"), "site_id"])
            pp = pred[pred.guide_id.eq(guide)]
            for k in k_values:
                selected = set(pp.loc[pp["rank"].le(k), "site_id"])
                hits = len(selected & true_ids)
                rows.append(
                    {
                        "model": model,
                        "guide_id": guide,
                        "k": k,
                        "hits": hits,
                        "positives": len(true_ids),
                        "recall": hits / len(true_ids) if true_ids else np.nan,
                        "selected_candidates": len(selected),
                        "tie_budget_exceeded": len(selected) > k,
                    }
                )
    return pd.DataFrame(rows)


def summarize_recall(rows):
    records = []
    for (model, k), group in rows.groupby(["model", "k"]):
        eligible = group[group.positives.gt(0)]
        total = int(eligible.positives.sum())
        records.append(
            {
                "model": model,
                "k": int(k),
                "macro_recall": eligible.recall.mean(),
                "micro_recall": eligible.hits.sum() / total if total else np.nan,
                "hits": int(eligible.hits.sum()),
                "positives": total,
                "eligible_guides": len(eligible),
            }
        )
    return pd.DataFrame(records)


def threshold_curve(truth, pred, thresholds):
    joined = measured_join(truth, pred)
    positive = joined.status.eq("positive")
    rows = []
    for threshold in thresholds:
        if not np.isfinite(threshold):
            raise ValidationError("Thresholds must be finite")
        selected = joined.score.ge(threshold)
        tp = int((selected & positive).sum())
        fp = int((selected & ~positive).sum())
        fn = int((~selected & positive).sum())
        tn = int((~selected & ~positive).sum())
        rows.append(
            {
                "threshold": float(threshold),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "precision": tp / (tp + fp) if tp + fp else np.nan,
                "recall": tp / (tp + fn) if tp + fn else np.nan,
                "specificity": tn / (tn + fp) if tn + fp else np.nan,
            }
        )
    return pd.DataFrame(rows)


def exact_budget_recall(truth, predictions, k_values=(50, 100, 250, 500, 1250)):
    """Expected and extreme recall under uniform random selection within rank ties.

    Feed the full candidate table. The bounds describe unknown tie ordering,
    not a confidence interval or observed biological outcome.
    """
    if not k_values or any(not isinstance(k, int) or k <= 0 for k in k_values):
        raise ValidationError("K values must be positive integers")
    rows = []
    for model, pred in predictions.groupby("model"):
        for guide, measured in truth.groupby("guide_id"):
            positive = set(measured.loc[measured.status.eq("positive"), "site_id"])
            candidates = pred[pred.guide_id.eq(guide)].sort_values(["rank", "site_id"])
            for k in k_values:
                left = k
                expected = worst = best = 0.0
                for _, tied in candidates.groupby("rank", sort=True):
                    take = min(left, len(tied))
                    hits = int(tied.site_id.isin(positive).sum())
                    expected += take * hits / len(tied)
                    worst += max(0, take - (len(tied) - hits))
                    best += min(take, hits)
                    left -= take
                    if left == 0:
                        break
                denom = len(positive)
                rows.append(
                    {
                        "model": model,
                        "guide_id": guide,
                        "k": k,
                        "positives": denom,
                        "selected": k - left,
                        "expected_recall": expected / denom if denom else np.nan,
                        "worst_recall": worst / denom if denom else np.nan,
                        "best_recall": best / denom if denom else np.nan,
                    }
                )
    return pd.DataFrame(rows)
