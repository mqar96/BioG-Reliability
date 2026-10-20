# Final publication validation

The current suite contains 75 tests. One source-export regression was added during
staging; earlier 74/69 counts belong to superseded evidence and are not current totals.

| Executed scope | Passed | Failed/errors | Skipped | Deselected |
|---|---:|---:|---:|---:|
| Full local suite with separately prepared research inputs | 75 | 0 | 0 | 0 |
| Source archive, data-free selection | 70 | 0 | 0 | 5 |
| Source archive, full suite without research inputs | 70 | 0 | 5 | 0 |
| Installed and unpacked source distribution, data-free selection | 70 | 0 | 0 | 5 |
| Hosted Windows software CI selection | 70 | 0 | 0 | 5 |

Ruff, formatting, dependency validation, installation, CLI demo and wheel/source
builds passed. The documented dashboard launcher and synthetic demonstration ran
locally with a successful HTTP health response. All synthetic demonstration pages
and exports are covered by application tests. CITATION.cff was schema-validated.

Full package statement coverage is 358/398 (89.94974874%); data-free coverage is
334/398 (83.91959799%). No statements are excluded. These figures do not describe
whole-project coverage, branch coverage, biological accuracy or clinical validity.

Fresh Python 3.13.12 environments were used for source archives without Git metadata
or research data. Their provenance records a null commit instead of inheriting an
unrelated parent checkout. The exporter archives committed Git bytes, so its ZIP
manifest matches the staged source despite Windows newline conversion.

The final publication preview retained privately binds the exact release commit,
source-file hashes, archive/package hashes, local reports and actual hosted run.
The source does not embed a supposed self-referential final commit hash or assume
that an earlier run covers a later commit. Inspect [Actions](https://github.com/mqar96/BioG-Reliability/actions)
for the run attached to the exact commit being reviewed. Default CI requires no
research dataset or configured repository secret and uses read-only contents access.

Research reconstruction was verified separately with newly acquired, pinned inputs.
Twenty deterministic scientific CSVs matched the earlier verified analysis. Those
experiments retain their original source/input/output receipts; a documentation-only
release update does not turn them into new biological validation. See README for
historical and repeated performance measurements and their host-load limitations.

The primary benchmark reproduces 20/25 comparisons. Five CCTop discrepancies remain.
The strict TrueOT cohort contains 911 observations, 93 positives, 15 guides and seven
studies; incomplete training-data independence limits interpretation. Candidate-row
counts in assay/stress work are not counts of independently measured observations.

The source ZIP, wheel and source distribution contain no research data, upstream
checkouts, environments or sequence-level derived research outputs. The source
distribution includes the app, scripts, documentation and synthetic fixtures needed
by its tests; the wheel provides the reusable package/CLI. One earlier local unpacked
package run emitted a Pytest cache-permission warning while all tests passed; this
is retained in private historical evidence rather than hidden.

Private staging is authorized. Public visibility, version tags, releases and
announcements require separate explicit founder approval.
