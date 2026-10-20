"""Generate a research report, scientific plots and presentation data from real results."""

import html
import json
import re
from pathlib import Path
from xml.etree import ElementTree

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from biog_reliability.reporting import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/experiment"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
FIGURES = REPORTS / "figures"
FIGURES.mkdir(exist_ok=True)


def md_table(frame):
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in frame.itertuples(index=False, name=None):
        cells = [f"{v:.6f}" if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def html_block(paragraph):
    """Render our report prose and reference table without executing embedded HTML."""

    def inline(value):
        escaped = html.escape(value)
        return re.sub(
            r"\[([^\]]+)\]\((https://[^\s)]+)\)",
            r'<a href="\2">\1</a>',
            escaped,
        )

    if paragraph.startswith("{"):
        return "<pre>" + html.escape(paragraph) + "</pre>"
    if paragraph.startswith("# "):
        return "<h3>" + inline(paragraph[2:]) + "</h3>"
    if paragraph.startswith("| "):
        rows = paragraph.splitlines()
        rendered = []
        for index, row in enumerate(rows):
            if index == 1:
                continue
            tag = "th" if index == 0 else "td"
            cells = row.strip("|").split("|")
            rendered.append(
                "<tr>"
                + "".join(f"<{tag}>{inline(cell.strip())}</{tag}>" for cell in cells)
                + "</tr>"
            )
        return "<table>" + "".join(rendered) + "</table>"
    return "<p>" + inline(paragraph).replace("\n", "<br>") + "</p>"


def main():
    from biog_reliability.provenance import source_snapshot

    names = [
        "reproduction",
        "recall_summary",
        "classification_model_scored",
        "classification_common_scored",
        "uncertainty",
        "duplicate_policy_sensitivity",
        "indel_threshold_sensitivity",
        "exact_budget_comparison",
        "prediction_qc",
    ]
    tables = {name: pd.read_csv(RESULTS / f"{name}.csv") for name in names}
    meta = json.loads((RESULTS / "summary.json").read_text())
    verification = json.loads((ROOT / "results/validation/verification.json").read_text())
    if verification["source_sha256"] != source_snapshot(ROOT):
        raise ValueError("Stale test evidence: source changed. Run scripts/verify.py again.")
    if verification["test_report_sha256"] != sha256(ROOT / "results/test-results.xml"):
        raise ValueError("JUnit report changed after verification")
    if any(c["exit_code"] for c in verification["checks"]):
        raise ValueError("Quality gate failed; report cannot claim successful verification")
    for folder in ["experiment", "external", "large-data", "stress", "cctop-investigation"]:
        directory = ROOT / "results" / folder
        manifest = json.loads((directory / "manifest.json").read_text())
        if manifest["metadata"]["source_sha256"] != source_snapshot(ROOT):
            raise ValueError(f"Stale experiment source snapshot: {folder}")
        for name, digest in manifest["files_sha256"].items():
            if sha256(directory / name) != digest:
                raise ValueError(f"Result checksum changed: {folder}/{name}")
    suite = ElementTree.parse(ROOT / "results/test-results.xml").getroot().find("testsuite")
    tested = {key: suite.attrib.get(key) for key in ("tests", "failures", "errors", "skipped")}
    coverage = json.loads((ROOT / "results/coverage.json").read_text())["totals"]
    external = pd.read_csv(ROOT / "results/external/classification.csv")
    external_ci = pd.read_csv(ROOT / "results/external/uncertainty.csv")
    external_qc = json.loads((ROOT / "results/external/summary.json").read_text())
    large = pd.read_csv(ROOT / "results/large-data/assay_inventory.csv")
    stress = pd.read_csv(ROOT / "results/stress/measurements.csv")
    cctop = json.loads((ROOT / "results/cctop-investigation/summary.json").read_text())
    matched = int(tables["reproduction"].matches_1e_12.sum())
    total = len(tables["reproduction"])
    strict_name = "guide_study_disjoint_known_training_excluded"
    strict = external[external.cohort.eq(strict_name)]
    budget = tables["exact_budget_comparison"].query("k == 50").iloc[0]
    qc = meta["no_bulge_truth_qc"]
    sections = []

    def add(title, body, frame=None, figure=None):
        sections.append((title, body, frame, figure))

    add(
        "1. Executive scientific summary",
        f"""BioG-Reliability evaluates precomputed CRISPR off-target scores. It provides reusable validation, cohort auditing, ranking, classification, uncertainty, a CLI and a local Streamlit dashboard. No new predictor, training run, prospective experiment or clinical validation is claimed.

The current recomputation matches {matched}/{total} stored recall comparisons at absolute tolerance 1e-12. CCTop remains an unsuccessful reference reproduction. Direct execution of pinned upstream functions matches BioG: {cctop["upstream_rerun_matches_biog"]}. This narrows the discrepancy to the historical reference/artifact relationship without reconstructing its cause.

The additional TrueOT analysis retains {int(strict.n.iloc[0])} common scored observations, {int(strict.positives.iloc[0])} positives, {int(strict.guides.iloc[0])} guides and {int(strict.studies.iloc[0])} studies after excluding primary-benchmark guide/study overlap and known CRISPR-NET training overlap. This is an external cohort evaluation with incomplete training provenance, not a certificate of leakage-free generalization.

The large assay audit streamed {int(large.rows.sum()):,} candidate rows across two related assay collections. Engineering stress tests reached {int(stress.records.max()):,} deposited prediction records. These counts are not independent experimental sample sizes.

Fresh test evidence: {tested}; package coverage {coverage["percent_covered"]:.2f}%. Publication remains subject to founder approval, remote CI and redistribution review.""",
    )
    add(
        "2. Motivation and research problem",
        """Published off-target scores depend on candidate nomination, measurement, identity, label thresholds and ranking conventions. This project asks how those choices affect interpretation. It separates measured positives, assay-dependent measured negatives and unknown outcomes. Unknown candidates can consume a ranking budget but never enter binary classification as measured negatives. Scores are not calibrated safety probabilities.""",
    )
    add(
        "3. Existing tools and publications",
        (ROOT / "docs/dataset-catalog.md").read_text(encoding="utf-8"),
    )
    add(
        "4. Dataset provenance and rights",
        f"""Primary upstream commit: {meta["upstream_commit"]}. Zenodo deposit: DOI 10.5281/zenodo.20627722 v1.0.0, prediction archive CC BY 4.0. Exact inputs and checksums appear in each manifest. The principal cohort contains {qc["unique_sites"]} sequence/chromosome identities, {qc["positives"]} positives and {qc["guides"]} guides. The full raw source has {meta["full_truth_qc"]["raw_observations"]} observations.

TrueOT v1.1 is pinned at 4ff0ccd2493de3dc658747d05fa6bb4fe12ea2c7. Its source has {external_qc["source_rows"]} observations, and the context/locus identity policy retains {external_qc["sites_after_identity_policy"]}. Assay-specific author labels are retained; missing or qualitative editing percentages are not invented. The repository lacks a standalone reuse license. Local research results do not establish permission to redistribute raw or derived data.

The CRISPR-Bulge dataset archive is pinned at 3eddcd5bfcaff00b2bdf29425116ec9756ace870 and verified against its Git LFS SHA-256. Repository MIT terms do not automatically settle all underlying study-data rights. Source data and sequence-level results are omitted from the proposed source-only release archive. Full Git history still contains earlier sequence-level outputs and must not be publicly pushed as-is.""",
        tables["prediction_qc"],
    )
    add(
        "5. Architecture and validated import contracts",
        """Adapters feed shared validation, metrics, uncertainty and reporting modules. CSV/JSON uploads validate identifiers, assembly, provenance objects, coordinates, strands and finite scores. Canonical coordinates use 0-based half-open intervals. The published adapter validates source interval order but does not infer or convert uncertain coordinate origins; its evaluation key remains sequence/chromosome. Explicit PAR1/PAR2 strand suffixes are recorded and normalized. All other malformed strands fail.

Empty scored-measured overlap produces a controlled dashboard message. Import exports contain hashes of the actual uploaded bytes and selected models. This research application remains local and single-user; native model inference, authentication and deployment services are outside scope.""",
    )
    add(
        "6. Evaluation and statistical methods",
        f"""Recall uses original per-guide ranks, with unknown candidates consuming the budget and missing measured positives counted as misses. Macro recall excludes guides with no positives; micro recall pools hits over measured positives. The common scored classification population contains {meta["common_scored_sites"]} sites and {meta["common_scored_positives"]} positives. AP is threshold-based average precision; trapezoidal AUPRC is reported separately. Single-class metrics are deliberately suppressed with reasons.

AP uncertainty uses {meta["bootstrap_reps"]} percentile bootstrap resamples at seed {meta["seed"]}; guide sampling preserves clusters. External analyses also resample studies. The paired recall comparison uses {meta["paired_recall_difference"]["reps"]} guide resamples. Intervals are conditional on the observed selected cohort and deposited scores. No multiple-comparison superiority claims are made. A no-bulge label based on length 23 remains a proxy.""",
    )
    add(
        "7. Benchmark reproduction",
        f"""{matched}/{total} model/cutoff comparisons agree within absolute error 1e-12 for both macro and micro recall. Failed CCTop rows remain visible. Scores, training and genome-wide search were not regenerated. Source functions, deposited ranks, filtering and alternate deterministic tie orderings are inspected in results/cctop-investigation. Agreement with the current upstream implementation does not recover the historical candidate ordering.""",
        tables["reproduction"],
    )
    add(
        "8. Candidate budget sensitivity",
        f"""At K=50, CCTop inclusive macro recall is {budget.macro_recall:.9f}. Exact-budget expected recall is {budget.expected_recall:.9f}, with tie-order bounds [{budget.worst_recall:.9f}, {budget.best_recall:.9f}]. Uniform selection inside the boundary tie defines the expectation. These bounds are not confidence intervals. Changing the evaluation policy does not demonstrate a biological deterioration in a model.""",
        tables["exact_budget_comparison"],
        "tie_budget.png",
    )
    add(
        "9. Expanded independent-cohort evaluation",
        """TrueOT preserves study, genomic locus, cell context and delivery in its identity. Analyses first use all common CFD/CRISPR-NET scores, then exclude primary-benchmark guides using normalized 20-base spacers and source studies using PMID, then exclude known CRISPR-NET training guides. Two actual training tables and the authors' broader overlap flags inform exclusion. That inventory is incomplete, and CFD training overlap is not fully cleared.

The stricter cohort evaluates the two scores on identical observations. It cannot be directly ranked against the five-model primary benchmark because populations, models and label definitions differ. Missing scores restrict the common cohort; positive coverage and exclusions are reported in external/QC files. Source labels include assay detection limits and qualitative calls, so a unified percent-indel threshold sensitivity is scientifically unavailable. The primary cohort retains the quantitative threshold analysis. Study/cell strata are descriptive and cannot isolate causal cell-type effects.""",
        external,
    )
    add(
        "10. External uncertainty and assay scale",
        """Guide and study intervals preserve correlated units. Overlapping intervals do not prove equivalence, and their width does not by itself supply a paired significance test. The present external analysis makes no superiority claim. results/external/stratified.csv gives per-study and per-cell metrics, including undefined single-class cases.""",
        external_ci,
    )
    add(
        "Large experimental-source inventory",
        """CHANGE-seq and Full GUIDE-seq were profiled directly from the verified archive. Nonzero reads indicate assay detection. Zero-read computational candidates remain unknown. These related in-vitro and cellular assays are kept separate; they include on-target rows and may contain repeated locus/alignments. Candidate-table size is not the number of independent measured editing outcomes. No model accuracy is claimed from these files because compatible deposited model scores were not evaluated.""",
        large,
    )
    add(
        "11. Computational performance",
        """Each size uses real source prefixes from MOFF and then CRISOT, without generating new observations. Source duplicates and dependence remain. Each repeat runs in a fresh subprocess; peak RSS and CPU include the Windows launcher and descendants, sampled every 20 ms. OS file cache was not flushed. Ingestion and adapter/metric processing are timed separately; report timing covers a small aggregate HTML/CSV export. Total wall time includes startup and recovery validation. These are engineering workloads and their classification values are not biological findings.

Two processes per size test repeatability, not long-duration memory leakage. Peak memory grows with the in-memory sort/join workload. A streaming or external-sort adapter is a future option for larger files; the measured one-million-row workload completed without requiring it. Browser upload performance at this scale was not measured.""",
        stress,
    )
    add(
        "12. Primary uncertainty and selection sensitivity",
        f"""The paired CRISPert-minus-MOFF macro recall difference and guide interval are {json.dumps(meta["paired_recall_difference"])}. Interpret the interval before any superiority claim. Label cutoffs rebuild the conflict-excluded common cohort and therefore change both prevalence and the evaluation population.""",
        tables["uncertainty"],
        "uncertainty.png",
    )
    add(
        "Quantitative label thresholds",
        "Delta indels are percentages, not fractions. The thresholds below are sensitivity analyses, not optimized clinical cutoffs.",
        tables["indel_threshold_sensitivity"],
    )
    add(
        "Duplicate policy sensitivity",
        "First-record handling depends on source order. It is a diagnostic alternative to conflict exclusion, not an endorsed truth-resolution method.",
        tables["duplicate_policy_sensitivity"],
    )
    add(
        "13. Novelty and unsuccessful work",
        """Kaufmann et al. already provide coverage, recall budgets, unknown-outcome handling and guide bootstrap analysis. Kota et al. already curate measured TrueOT outcomes and remove training overlap. Yaish and Orenstein already examine large CHANGE/GUIDE cohorts and bulges. BioG independently reimplements established metrics and integrates validation, provenance and sensitivity analysis. Its empirical contributions are reproducible cohort/tie-policy case studies and a traceable external evaluation. No first-ever methodological or biological novelty is established.

The initial strict-strand run failed on legitimate source PAR annotations; the explicit adapter mapping resolved it. The initial stress monitor sampled the Windows launcher only; those memory measurements were invalid and were replaced by process-tree monitoring. Failed-run logs remain local. The five CCTop reference cells remain unresolved. Native prediction inference, full training-data provenance, external unified quantitative thresholds and prospective validation were not performed.""",
    )
    add(
        "14. Reproducibility and release gates",
        f"""Run scripts/reproduce.ps1 from a clean Python 3.13 Windows checkout. It creates a project-local environment, installs a hash-locked dependency set, fetches pinned inputs, computes primary/external/large-data/stress results, executes tests and builds, then generates this report. No processed-data cache is required. scripts/verify.py binds JUnit and coverage evidence to executable source hashes; this report refuses stale tests or changed output hashes.

Test counts: {tested}. Coverage: {coverage["covered_lines"]}/{coverage["num_statements"]} statements ({coverage["percent_covered"]:.2f}%). Full commands/logs are in results/validation. Manifests contain code snapshots, commit, timestamps, package versions, seeds, inputs and every output including exact-budget files. The fresh checkout receipt is maintained separately in docs/final-validation.md.

The source-only release archive excludes data, derived-result tables, reports, screenshots, presentation binaries and Git history. It is a reconstruction package for authorized local use. A public repository, remote CI and release publication have not been performed. Dependency licenses and package contents are inventoried in docs/release-readiness.md. Founder approval remains required.""",
    )
    add(
        "15. Limitations and next research milestones",
        """The selected measured cohorts contain few independent guides/studies, heterogeneous assays, nomination bias and detection limits. Incomplete training manifests prevent a general leakage-free claim. Main benchmark identity can merge loci; exclusion of conflicting labels changes the target population. Full positive coverage for a scorer in a seeded candidate universe is not genome-wide sensitivity. Read-level reanalysis and native predictor reproduction remain future work.

Before public release, use the reviewed source-only export, obtain approval and run remote CI. Before stronger scientific claims, obtain complete training manifests and clearly licensed quantitative external outcomes, preregister cohort/threshold policies, test additional studies and resolve CCTop artifact lineage. Any methodological novelty claim requires a broader literature review. The current defensible contribution is research software plus an independently recomputed evaluation case study.""",
    )
    add("Exact run settings", json.dumps(meta, indent=2))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    palette = ["#0b8994", "#776acb", "#d57a26", "#2875c4"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for color, model in zip(palette, ["CRISPert", "MOFF", "CRISOT", "CRISPR-IP"], strict=True):
        group = tables["recall_summary"].query("model == @model")
        ax.plot(group.k, group.macro_recall, "o-", label=model, color=color)
    ax.set(xlabel="Deposited rank cutoff per guide (K)", ylabel="Macro recall", ylim=(0, 1))
    ax.legend(ncol=4, loc="lower right")
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(FIGURES / "recall.png", dpi=200)
    plt.close(fig)
    t = tables["exact_budget_comparison"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t.k, t.macro_recall, "o-", label="Inclusive rank cutoff", color="#d57a26")
    ax.plot(t.k, t.expected_recall, "o-", label="Exact-budget expectation", color="#0b8994")
    ax.fill_between(
        t.k, t.worst_recall, t.best_recall, alpha=0.15, color="#0b8994", label="Tie-order bounds"
    )
    ax.set(xlabel="K candidates per guide", ylabel="Macro recall", ylim=(0, 1))
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGURES / "tie_budget.png", dpi=200)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    u = tables["uncertainty"].query("model == 'CRISPert'")
    ap = float(
        tables["classification_common_scored"]
        .query("model == 'CRISPert'")
        .average_precision.iloc[0]
    )
    for i, row in enumerate(u.itertuples()):
        ax.plot([row.low, row.high], [i, i], linewidth=8, color=palette[i])
        ax.plot(ap, i, "o", color="#111827")
    ax.set(
        yticks=[0, 1],
        yticklabels=["Row resampling", "Guide resampling"],
        xlabel="Average precision and 95% percentile interval",
        xlim=(0, 1),
        ylim=(-0.6, 1.6),
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "uncertainty.png", dpi=200)
    plt.close(fig)

    md = [
        "# BIOGIANT THERAPEUTICS - BioG-Reliability v0.1",
        f"Month 1 scientific research report | experiment date {meta['run_date']}",
        "Research use only. No clinical validation.",
    ]
    blocks = [
        f"<h1>BIOGIANT THERAPEUTICS<br>BioG-Reliability v0.1</h1><p>Month 1 research report | experiment date {html.escape(meta['run_date'])}</p>"
    ]
    for title, body, frame, figure in sections:
        md += ["## " + title, body]
        blocks.append("<h2>" + html.escape(title) + "</h2>")
        for paragraph in body.split("\n\n"):
            blocks.append(html_block(paragraph))
        if frame is not None:
            md.append(md_table(frame))
            blocks.append(frame.round(6).to_html(index=False, na_rep="Undefined", border=0))
        if figure:
            md.append(f"![{title}](figures/{figure})")
            blocks.append(f'<img alt="{html.escape(title)}" src="figures/{figure}">')
    (REPORTS / "Month1-Research-Report.md").write_text("\n\n".join(md), encoding="utf-8")
    style = "body{font:16px/1.65 Segoe UI,Arial;margin:60px auto;max-width:1140px;color:#142c40;padding:0 30px}h1,h2{color:#0b5b72}h1{font-size:36px}h2{margin-top:48px}table{font-size:12px;border-collapse:collapse;width:100%;display:block;overflow:auto}th,td{padding:8px;border-bottom:1px solid #cbd9df;text-align:left}th{background:#e7f2f5}img{max-width:100%}p{overflow-wrap:anywhere}@media print{body{margin:15mm;font-size:11pt}h2{break-after:avoid}table{font-size:8pt}img{break-inside:avoid}}"
    (REPORTS / "Month1-Research-Report.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>BioG Month 1</title><style>'
        + style
        + "</style><body>"
        + "".join(blocks)
        + "</body></html>",
        encoding="utf-8",
    )
    write_json(
        ROOT / "results/presentation-data.json",
        {
            "tables": {k: v.to_dict("records") for k, v in tables.items()},
            "metadata": meta,
            "tests": tested,
            "external": external.to_dict("records"),
            "external_ci": external_ci.to_dict("records"),
            "large_data": large.to_dict("records"),
            "stress": stress.to_dict("records"),
        },
    )
    outputs = {str(p.relative_to(ROOT)): sha256(p) for p in REPORTS.rglob("*") if p.is_file()}
    write_json(ROOT / "results/report-manifest.json", outputs)
    print(f"Generated {len(sections)} report sections and 3 scientific figures")


if __name__ == "__main__":
    main()
