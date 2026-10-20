# BioG-Reliability v0.1.0 — proposed source-only release

Status: prepared for founder review; no public publication or version tag is implied.

BioG-Reliability evaluates existing CRISPR off-target prediction outputs. It provides
strict input and provenance checks, cohort/coverage auditing, classification and
ranking metrics, exact-budget tie analysis, uncertainty estimates, a CLI and a local
Streamlit dashboard. An explicitly labeled synthetic demonstration runs without
research datasets. This is not a newly developed biological prediction model.

The source-only candidate contains 66 reviewed files and independent clean Git
history. It excludes research datasets, sequence-level derived records, upstream
checkouts, model weights/executables, research reports/presentation, environments,
private evidence and the original research Git history. No credentials are required
for the default demonstration or software CI.

Validation: the full local suite passes 75 tests when external inputs are prepared.
The data-free selection and packaged source contain 70 passing tests with five
research tests deselected. A full no-data run passes 70 and explicitly skips five.
Ruff, formatting, dependency checks, installation, builds and the synthetic CLI demo
pass. Hosted Windows/Python 3.13.12 checks run against the exact pushed commit; the
final approval preview identifies that commit, run URL and release-asset hashes.
See [Actions](https://github.com/mqar96/BioG-Reliability/actions) and
[validation details](docs/validation-record.md).

Scientific findings and limits:

- 20/25 published comparisons reproduce; five unresolved CCTop discrepancies remain.
- The strict external TrueOT cohort contains 911 observations, 93 positives, 15 guides
  and seven studies. Incomplete training-data independence prevents a claim of fully
  independent model validation or improved biological prediction accuracy.
- Engineering tests reached one million records. Runtime and memory are host/load
  dependent; these workloads are not biological accuracy or measured-sample evidence.
- No methodological novelty, clinical validation or suitability for clinical decisions
  is claimed. Unknown or untested outcomes are never treated as measured negatives.
- Public availability does not establish redistribution rights. Underlying truth,
  TrueOT/training inputs and derived research records remain excluded; users must
  establish applicable rights before optional research acquisition.

Original software and synthetic fixtures are MIT licensed, permitting commercial
reuse, modification and resale subject to retaining the copyright and permission
notice. Third-party dependencies, datasets and publications retain their terms.
The license does not transfer BIOGIANT brand ownership or imply endorsement.
See [license](LICENSE) and [notices](THIRD_PARTY_NOTICES.md).

Supported release target: Python 3.13 on Windows. Source archives preserve committed
Git bytes and cannot inherit a parent research checkout's provenance. Optional
research reproduction requires separately acquired inputs; default software CI
does not download or require restricted research artifacts.
