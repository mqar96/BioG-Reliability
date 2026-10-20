import json

import numpy as np
import pandas as pd
import pytest

from biog_reliability.cli import run
from biog_reliability.metrics import (
    classification_metrics,
    compare_models,
    recall_at_k,
    summarize_recall,
    threshold_curve,
)
from biog_reliability.reporting import sha256, write_json
from biog_reliability.uncertainty import bootstrap_ap, paired_recall_difference
from biog_reliability.validation import (
    Provenance,
    ValidationError,
    audit_table,
    overlap_audit,
    validate_predictions,
    validate_truth,
)


def test_exact_budget_uniform_tie(truth, predictions):
    from biog_reliability.metrics import exact_budget_recall

    predictions["rank"] = 1
    row = exact_budget_recall(truth, predictions, (1,)).query("guide_id == 'g1'").iloc[0]
    assert row.selected == 1
    assert row.expected_recall == pytest.approx(1 / 3)
    assert row.worst_recall == 0 and row.best_recall == 1


def test_strict_inputs(truth, predictions, provenance):
    assert len(validate_truth(truth, provenance)) == 5
    assert len(validate_predictions(predictions, truth)) == 5


@pytest.mark.parametrize(
    "column,value",
    [
        ("status", "negative"),
        ("assembly", "hg19"),
        ("assay", "other"),
        ("context", "other"),
        ("guide_id", ""),
        ("measurement", float("inf")),
    ],
)
def test_invalid_truth(truth, provenance, column, value):
    truth.loc[0, column] = value
    with pytest.raises((ValidationError, ValueError)):
        validate_truth(truth, provenance)


@pytest.mark.parametrize(
    "column,value",
    [
        ("score", float("inf")),
        ("score", None),
        ("rank", 0),
        ("rank", 1.2),
        ("assembly", "hg19"),
        ("guide_id", "different"),
    ],
)
def test_invalid_predictions(truth, predictions, column, value):
    if column == "rank":
        predictions[column] = predictions[column].astype(float)
    predictions.loc[0, column] = value
    with pytest.raises((ValidationError, ValueError)):
        validate_predictions(predictions, truth)


def test_duplicates_rejected(truth, predictions, provenance):
    with pytest.raises(ValidationError):
        validate_truth(pd.concat([truth, truth.iloc[:1]]), provenance)
    with pytest.raises(ValidationError):
        validate_predictions(pd.concat([predictions, predictions.iloc[:1]]), truth)


def test_unknown_is_not_negative(truth, predictions):
    result = compare_models(truth, predictions).iloc[0]
    assert (
        result.n == 4
        and result.average_precision == 1
        and result.unlabeled_in_cohort_predictions == 1
    )


def test_ranking_budget_counts_unknown(truth, predictions):
    result = summarize_recall(recall_at_k(truth, predictions, (1,))).iloc[0]
    assert result.macro_recall == 0.5 and result.hits == 1


def test_missing_predictions_are_misses(truth, predictions):
    result = summarize_recall(recall_at_k(truth, predictions.iloc[:2], (2,))).iloc[0]
    assert result.macro_recall == 0.5 and result.positives == 2


@pytest.mark.parametrize(
    "labels,reason",
    [
        ([], "no_scored_measured_sites"),
        ([0, 0], "single_class_cohort"),
        ([1], "single_class_cohort"),
    ],
)
def test_undefined_metrics(labels, reason):
    result = classification_metrics(labels, [0.5] * len(labels))
    assert (
        result["auroc"] is None
        and result["average_precision"] is None
        and result["reason"] == reason
    )


def test_ties_and_ap_definition():
    stats = classification_metrics([1, 0], [0.5, 0.5])
    assert stats["auroc"] == 0.5 and stats["average_precision"] == 0.5
    assert stats["auprc_trapezoid"] == 0.75


def test_invalid_labels():
    with pytest.raises(ValidationError):
        classification_metrics([2], [0.5])


def test_fixed_common_cohort(truth, predictions):
    second = predictions.iloc[1:].assign(model="B")
    both = pd.concat([predictions, second])
    assert compare_models(truth, both, common=True).n.tolist() == [3, 3]
    assert compare_models(truth, both).n.tolist() == [4, 3]


def test_no_predictions_selected_precision_undefined(truth, predictions):
    row = threshold_curve(truth, predictions, [2]).iloc[0]
    assert np.isnan(row.precision) and row.recall == 0 and row.fn == 2


def test_untested_measurement_rejected(truth, provenance):
    truth.loc[4, "measurement"] = 0
    with pytest.raises(ValidationError):
        validate_truth(truth, provenance)


def test_coordinates(truth, provenance):
    truth = truth.assign(start=2, end=1)
    with pytest.raises(ValidationError):
        validate_truth(truth, provenance)


def test_coordinate_strings_compare_numerically(truth, provenance):
    valid = truth.assign(start="9", end="10")
    assert validate_truth(valid, provenance).end.eq(10).all()
    with pytest.raises(ValidationError, match="end precedes start"):
        validate_truth(truth.assign(start="10", end="9"), provenance)


def test_audit_and_overlap(truth):
    assert audit_table(truth)["missing_by_column"]["measurement"] == 1
    assert overlap_audit(truth, truth)["shared_guide_id"] == 2


def test_provenance_required():
    with pytest.raises(ValidationError):
        Provenance.from_dict({})


def test_bootstrap_reproducible(truth, predictions):
    joined = truth[truth.status.ne("untested")].merge(predictions[["site_id", "score"]])
    a = bootstrap_ap(joined, reps=25, seed=7)
    assert a == bootstrap_ap(joined, reps=25, seed=7)
    assert a["valid_reps"] == 25 and a["low"] == 1


def test_bootstrap_empty():
    result = bootstrap_ap(pd.DataFrame(), reps=10)
    assert result["low"] is None and result["valid_reps"] == 0


def test_paired_comparison(truth, predictions):
    both = pd.concat([predictions, predictions.assign(model="B")])
    result = paired_recall_difference(recall_at_k(truth, both), "A", "B", reps=50)
    assert result["difference"] == 0 and result["high"] == 0


def test_cli_export(tmp_path, truth, predictions, provenance):
    tt, pp, mm = [tmp_path / name for name in ("truth.csv", "pred.csv", "meta.json")]
    truth.to_csv(tt, index=False)
    predictions.to_csv(pp, index=False)
    write_json(mm, provenance.__dict__)
    result = run(tt, pp, mm, tmp_path / "out")
    assert result["common_scored"].iloc[0].auroc == 1
    manifest = json.loads((tmp_path / "out/manifest.json").read_text())
    assert manifest["files_sha256"]["recall.csv"] == sha256(tmp_path / "out/recall.csv")


def test_json_null(tmp_path):
    path = tmp_path / "metrics.json"
    write_json(path, {"x": np.nan, "y": np.int64(2)})
    assert json.loads(path.read_text()) == {"x": None, "y": 2}


def test_rank_tie_budget_disclosed(truth, predictions):
    predictions["rank"] = 1
    rows = recall_at_k(truth, predictions, (1,))
    assert rows.tie_budget_exceeded.all()


@pytest.mark.parametrize("ks", [(), (0,), (-1,), (1.5,)])
def test_bad_k(truth, predictions, ks):
    with pytest.raises(ValidationError):
        recall_at_k(truth, predictions, ks)
