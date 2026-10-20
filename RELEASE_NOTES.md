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
Private staging at `mqar96/BioG-Reliability` passed hosted software CI on commit
`746a7c1f53fcaf524f9d97c21f722d39861e557e` (run 39477598404).
Inspect Actions for subsequent commits. Local validation is reported separately.
No public release, release date or tag is asserted before publication approval.

Local validation: 74/74 with separately acquired research inputs; 69 data-free tests
with five research cases explicitly deselected. A full no-data run has 69 passed and
five documented skips. Ruff, dependency checks and builds pass locally. Hosted CI also
passed software checks, CLI demo, package tests (69 passed/five deselected), and the
66-file release scan. Source-archive provenance cannot inherit an unrelated parent Git history.

Packaging verification: the installed/unpacked source distribution passes its 69
data-free tests; five research tests are explicitly deselected. Application, scripts
and synthetic fixtures accompany the source distribution. No datasets are bundled.

Final staging adds a regression for committed-byte source exports. The latest full
local suite passes 75 tests; the data-free selection contains 70 tests. ZIP source
hashes now match committed Git blobs despite checkout newline conversion. CI actions
are pinned to reviewed v6 commits using Node.js 24; actual run status remains in Actions.
