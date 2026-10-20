# v0.1.0 — draft, not published

BioG-Reliability evaluates existing CRISPR off-target prediction outputs. It combines
strict validation, cohort/coverage auditing, classification and ranking metrics,
exact-budget tie analysis, uncertainty, a CLI and a local Streamlit dashboard.

This first source release includes a synthetic demonstration and data-free CI.
Research datasets, sequence-level derived outputs, upstream code, environments,
research reports/presentation and previous Git history are excluded. Optional
acquisition requires reviewing original terms and obtaining applicable rights.

Historical research findings: 20/25 primary comparisons reproduce; five CCTop
differences remain. The strict TrueOT cohort contains 911 observations/93 positives/
15 guides/seven studies, with incomplete training provenance. Engineering tests
reached one million records; these workloads do not imply biological accuracy.

Original code/fixtures are MIT. Other data/dependencies retain their terms.
Python 3.13 on Windows is the supported target. No new predictor, methodological
novelty, improved biological accuracy or clinical validation is claimed.
Remote CI awaits staging authorization. Local validation is reported separately.
No public release, release date or tag is asserted before publication approval.

Local validation: 74/74 with separately acquired research inputs; 69 data-free tests
with five research cases explicitly deselected. A full no-data run has 69 passed and
five documented skips. Ruff, dependency checks and builds pass locally. Remote CI
has not run. Source-archive provenance cannot inherit an unrelated parent Git history.
