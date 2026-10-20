"""Local Streamlit dashboard. Run with streamlit run app.py."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from biog_reliability.metrics import compare_models, recall_at_k, summarize_recall, threshold_curve
from biog_reliability.reporting import clean_json
from biog_reliability.validation import (
    Provenance,
    audit_table,
    validate_predictions,
    validate_truth,
)

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="BioG-Reliability", page_icon="🧬", layout="wide")
st.markdown(
    """<style>
.stApp {background:#081624;color:#e9f3fa}
h1,h2,h3 {font-family:'Segoe UI',sans-serif}
[data-testid='stMetricValue'] {color:#42dce4}
[data-testid='stSidebar'] {background:#0d2234}
[data-testid='stMainBlockContainer'] {padding-top:2rem;padding-left:2rem;padding-right:2rem}
h3 {font-size:1.15rem !important}
div[data-testid='stMetric'] {border-top:2px solid #36cbd6;padding-top:15px}
</style>""",
    unsafe_allow_html=True,
)
st.sidebar.markdown("### BIOGIANT\nTHERAPEUTICS")
st.sidebar.caption("BioG-Reliability v0.1")
mode = st.sidebar.radio(
    "Data source",
    ["Public benchmark", "Import CSV files", "Synthetic demonstration"],
    index=0 if (ROOT / "data/processed/truth.csv").exists() else 2,
)
page = st.sidebar.radio(
    "Workspace", ["Overview", "Model comparison", "Sensitivity", "Data audit", "Export"]
)
st.sidebar.divider()
st.sidebar.caption("Research evaluation tool. No clinical safety validation.")


@st.cache_data
def bundled():
    truth = pd.read_csv(ROOT / "data/processed/truth.csv")
    predictions = pd.read_csv(ROOT / "data/processed/predictions.csv")
    provenance = json.loads((ROOT / "data/processed/provenance.json").read_text())
    meta = json.loads((ROOT / "results/experiment/summary.json").read_text())
    return truth, predictions, provenance, meta


if mode == "Synthetic demonstration":
    demo_dir = ROOT / "examples/demo"
    provenance = json.loads((demo_dir / "provenance.json").read_text())
    truth = validate_truth(pd.read_csv(demo_dir / "truth.csv"), Provenance.from_dict(provenance))
    predictions = validate_predictions(pd.read_csv(demo_dir / "predictions.csv"), truth)
    metadata = {
        "provenance": provenance,
        "synthetic_demonstration": True,
        "input_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(demo_dir.glob("*"))
        },
    }
elif mode == "Import CSV files":
    st.title("Import an evaluation cohort")
    st.caption("Canonical CSV schema and provenance fields: docs/input-schema.md")
    a, b, c = st.columns(3)
    tt = a.file_uploader("Experimental sites CSV", type="csv")
    pp = b.file_uploader("Precomputed predictions CSV", type="csv")
    mm = c.file_uploader("Provenance JSON", type="json")
    if not (tt and pp and mm):
        st.info("Upload all three files to validate and evaluate your cohort.")
        st.stop()
    try:
        contents = {
            "truth.csv": tt.getvalue(),
            "predictions.csv": pp.getvalue(),
            "provenance.json": mm.getvalue(),
        }
        provenance = json.loads(contents["provenance.json"])
        truth = validate_truth(
            pd.read_csv(io.BytesIO(contents["truth.csv"])), Provenance.from_dict(provenance)
        )
        predictions = validate_predictions(
            pd.read_csv(io.BytesIO(contents["predictions.csv"])), truth
        )
        metadata = {
            "provenance": provenance,
            "imported": True,
            "input_sha256": {k: hashlib.sha256(v).hexdigest() for k, v in contents.items()},
        }
    except (ValueError, KeyError, TypeError) as error:
        st.error(f"Input validation failed: {error}")
        st.stop()
else:
    try:
        truth, predictions, provenance, metadata = bundled()
    except FileNotFoundError:
        st.error(
            "Public data are not prepared. Run scripts/fetch_data.py "
            "and scripts/run_experiments.py."
        )
        st.stop()

st.title("BioG-Reliability")
st.caption("CRISPR off-target benchmarking · evidence, coverage and reproducibility")
if mode == "Synthetic demonstration":
    st.warning(
        "SYNTHETIC SOFTWARE DEMONSTRATION: artificial labels and scores. "
        "No biological measurements, predictor performance or safety evidence."
    )
if mode == "Public benchmark":
    st.caption(
        "Kaufmann et al. 2026 · hg38 / human SpCas9 · length-23 cohort · 0.1% indel threshold"
    )
models = st.sidebar.multiselect(
    "Models", sorted(predictions.model.unique()), default=sorted(predictions.model.unique())
)
if not models:
    st.info("Select at least one model.")
    st.stop()
predictions = predictions[predictions.model.isin(models)]
metadata = {**metadata, "selected_models": list(models)}
individual = compare_models(truth, predictions)
common = compare_models(truth, predictions, common=True)
recalls = summarize_recall(
    recall_at_k(truth, predictions, (1, 2, 3))
    if mode == "Synthetic demonstration"
    else recall_at_k(truth, predictions)
)
palette = ["#43dce4", "#7d9dff", "#f3bb66", "#df85c8", "#82dcb2"]


def plot(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#081624",
        plot_bgcolor="#081624",
        font=dict(family="Segoe UI", size=15),
        margin=dict(t=55, b=70),
        legend_title_text="",
        height=360,
        legend=dict(orientation="h", y=1.18, x=0, font=dict(size=12)),
    )
    if fig.layout.yaxis.title.text == "Fraction of measured positives scored":
        fig.update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, width="stretch")


if page == "Overview":
    cols = st.columns(4)
    cols[0].metric("Measured sites", int(truth.status.ne("untested").sum()))
    cols[1].metric("Positive sites", int(truth.status.eq("positive").sum()))
    cols[2].metric("Guides", truth.guide_id.nunique())
    cols[3].metric("Models", len(models))
    left, right = st.columns([1.55, 1])
    with left:
        st.subheader(
            "Recovery across artificial rank cutoffs"
            if mode == "Synthetic demonstration"
            else "Recovery across deposited rank cutoffs"
        )
        plot(
            px.line(
                recalls,
                x="k",
                y="macro_recall",
                color="model",
                markers=True,
                color_discrete_sequence=palette,
                range_y=[0, 1],
                labels={"k": "Deposited rank cutoff (K)", "macro_recall": "Macro recall"},
            )
        )
    with right:
        st.subheader("Coverage before classification")
        plot(
            px.bar(
                individual,
                x="model",
                y="positive_coverage",
                color="model",
                color_discrete_sequence=palette,
                range_y=[0, 1.05],
                labels={"positive_coverage": "Fraction of measured positives scored"},
            )
        )
    st.info(
        "Untested candidates consume ranking budget but never count as measured negatives. "
        "Missing scores reduce coverage. Scores are not calibrated safety probabilities."
    )
    if mode == "Public benchmark":
        st.warning(
            "CCTop has coarse tied ranks. Its rank cutoff can exceed K candidates. "
            "Use the exact-budget sensitivity results for budget comparisons."
        )
        st.caption(
            "Published baseline: DOI 10.1177/10430342261466407. "
            "Predictions: Zenodo 20627722 (CC BY 4.0). "
            "Compact candidate export retains original ranks through K=1,250."
        )

elif page == "Model comparison":
    st.subheader("Comparable classification cohorts")
    cohort = st.radio(
        "Scored sites",
        ["Common to selected models", "Each model's available sites"],
        horizontal=True,
    )
    table = common if cohort.startswith("Common") else individual
    st.caption(
        "Average precision (step-weighted) and trapezoidal AUPRC are distinct statistics. "
        "Only experimentally measured sites with scores enter classification."
    )
    show = table.melt(
        id_vars=["model"],
        value_vars=["auroc", "average_precision", "auprc_trapezoid"],
        var_name="Metric",
        value_name="Value",
    )
    plot(
        px.bar(
            show,
            x="model",
            y="Value",
            color="Metric",
            barmode="group",
            range_y=[0, 1.05],
            color_discrete_sequence=palette,
        )
    )
    st.dataframe(table, hide_index=True, width="stretch")
    if mode == "Public benchmark":
        st.caption("Saved uncertainty comparison below uses all five models' fixed common cohort.")
        st.dataframe(pd.read_csv(ROOT / "results/experiment/uncertainty.csv"), hide_index=True)

elif page == "Sensitivity":
    st.subheader("Decision threshold sensitivity")
    model = st.selectbox("Model", models)
    selected = predictions[predictions.model.eq(model)]
    scored = selected[selected.site_id.isin(truth.loc[truth.status.ne("untested"), "site_id"])]
    if scored.empty:
        st.info(
            "Empty comparable cohort: this model has no scored, measured sites. "
            "Check site identifiers and cohort selection. No sensitivity metrics are defined."
        )
        st.stop()
    thresholds = scored.score.quantile([i / 30 for i in range(31)]).unique()
    curve = threshold_curve(truth, selected, thresholds)
    plot(
        px.line(
            curve.melt(
                id_vars="threshold",
                value_vars=["precision", "recall", "specificity"],
                var_name="Metric",
                value_name="Value",
            ),
            x="threshold",
            y="Value",
            color="Metric",
            color_discrete_sequence=palette,
        )
    )
    st.caption(
        "Descriptive sensitivity only. These data were not used to select a deployment threshold."
    )
    if mode == "Public benchmark":
        st.subheader("CCTop: exact budget under rank ties")
        st.dataframe(
            pd.read_csv(ROOT / "results/experiment/exact_budget_comparison.csv"), hide_index=True
        )
        st.caption(
            "Expected recall assumes uniform selection within the boundary tie. "
            "Worst/best values are tie-order bounds, not confidence intervals."
        )
        st.subheader("Experimental label threshold")
        sensitivity = pd.read_csv(ROOT / "results/experiment/indel_threshold_sensitivity.csv")
        plot(
            px.line(
                sensitivity[sensitivity.model.isin(models)],
                x="indel_threshold_percent",
                y="average_precision",
                color="model",
                markers=True,
                color_discrete_sequence=palette,
            )
        )
        st.caption(
            "Re-labels each measured observation, excludes discordant repeated sites, "
            "then rebuilds the common scored cohort at each threshold."
        )

elif page == "Data audit":
    st.subheader("Provenance and annotation audit")
    st.json(provenance)
    st.json(audit_table(truth))
    if mode == "Public benchmark":
        st.warning(
            "Published sequence/chromosome identity pools repeated measurements. "
            "The full cohort contains 76 identities with discordant labels, "
            "excluded by the runner. "
            "A first-record policy produces a different cohort."
        )
        st.dataframe(
            pd.read_csv(ROOT / "results/experiment/duplicate_policy_sensitivity.csv"),
            hide_index=True,
        )
        st.json(metadata["full_truth_qc"])
    st.dataframe(truth.head(100), hide_index=True)

else:
    st.subheader("Reproducible analysis export")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, table in {
            "model_scored": individual,
            "common_scored": common,
            "recall": recalls,
        }.items():
            archive.writestr(name + ".csv", table.to_csv(index=False))
        archive.writestr("provenance.json", json.dumps(clean_json(metadata), indent=2))
    st.download_button(
        "Download current analysis", buffer.getvalue(), "biog-analysis.zip", "application/zip"
    )
    st.caption(
        "Exports include model selection, denominators and source metadata. "
        "See the saved research report for interpretation and limitations."
    )
    st.json(metadata)
