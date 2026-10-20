"""Seeded percentile intervals, preserving repeated clusters during sampling."""

import numpy as np

from .metrics import classification_metrics
from .validation import ValidationError


def bootstrap_ap(joined, reps=1000, seed=20261019, unit="guide"):
    if unit not in {"guide", "row"} or reps < 1:
        raise ValidationError("Bootstrap needs reps >= 1 and unit guide or row")
    if joined.empty:
        return {
            "low": None,
            "high": None,
            "valid_reps": 0,
            "requested_reps": reps,
            "unit": unit,
            "seed": seed,
            "reason": "empty_cohort",
        }
    y = joined.status.eq("positive").astype(int).to_numpy()
    score = joined.score.to_numpy()
    groups = list(joined.reset_index(drop=True).groupby("guide_id").indices.values())
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(reps):
        if unit == "guide":
            idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        else:
            idx = rng.integers(0, len(y), len(y))
        value = classification_metrics(y[idx], score[idx])["average_precision"]
        if value is not None:
            values.append(value)
    low, high = np.percentile(values, [2.5, 97.5]) if values else (None, None)
    return {
        "low": float(low) if low is not None else None,
        "high": float(high) if high is not None else None,
        "valid_reps": len(values),
        "requested_reps": reps,
        "seed": seed,
        "unit": unit,
        "reason": None if values else "all_replicates_undefined",
    }


def paired_recall_difference(rows, model_a, model_b, k=50, reps=2000, seed=20261019):
    if reps < 1 or model_a == model_b:
        raise ValidationError("Need two different models and positive resample count")
    table = rows[rows.k.eq(k)].pivot(index="guide_id", columns="model", values="recall")
    if model_a not in table or model_b not in table:
        raise ValidationError("Requested model is absent")
    pair = table[[model_a, model_b]].dropna()
    if pair.empty:
        return {"difference": None, "low": None, "high": None, "n_guides": 0}
    delta = (pair[model_a] - pair[model_b]).to_numpy()
    rng = np.random.default_rng(seed)
    samples = delta[rng.integers(0, len(delta), (reps, len(delta)))].mean(axis=1)
    low, high = np.percentile(samples, [2.5, 97.5])
    return {
        "difference": float(delta.mean()),
        "low": float(low),
        "high": float(high),
        "n_guides": len(delta),
        "model_a": model_a,
        "model_b": model_b,
        "k": k,
        "reps": reps,
        "seed": seed,
    }
