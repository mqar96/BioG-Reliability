# BioG-Reliability working rules

Research evaluation only, not a clinically validated safety predictor.

- Preserve experimental label provenance. Untested and excluded sites are never measured negatives.
- Never claim superiority from incompatible candidate sets or overlapping confidence intervals.
- Synthetic fixtures belong in tests. Experimental reports require traceable public observations.
- Record versions, SHA-256 hashes, denominators, seeds and metric definitions.
- Sequence/chromosome identity is specific to the published-benchmark adapter. New adapters must preserve genomic locus, assay, sample and cell context.
- Preserve failed reproductions. Do not tune results to match a headline number.
- Run Ruff and Pytest. Test scientific edge cases, not only happy paths.
- Keep raw data, reference checkouts, environments and caches out of Git.
- Publishing, payments, credentials and unrelated changes require founder approval.
- Do not generate video.

Architecture: adapters produce validated tables; metrics and uncertainty consume them; CLI and Streamlit are thin interfaces; reporting records provenance.

## Twelve-month program release gates

Apply these standards to subsequent BIOGIANT research performed in this repository
and carry them into explicitly authorized future project scaffolds.

- Scientific integrity: every scientific claim needs reproducible evidence, an explicit
  population and an appropriate interpretation. Never invent or hide failed results.
- Public-data validation: investigate suitable real observations and independent cohorts.
  Public availability is not a redistribution license. Record assay and label semantics.
- Large-scale testing: measure progressively larger inputs, runtime, peak process-tree
  memory, throughput and recovery. Separate engineering fixtures from biological evidence.
- Statistical rigor: preserve dependency, class imbalance, uncertainty, missingness and
  dataset shifts. Unknown outcomes never become experimentally measured negatives.
- Software quality: automated regressions, reproducible dependency locks, source control,
  CI, controlled errors and fresh-environment installation are release requirements.
- Reproducibility: record exact input/output hashes, source snapshots, commits, timestamps,
  seeds, settings and environments. Never reuse stale test evidence after source changes.
- Transparency: retain negative findings, limitations, unsuccessful runs and unresolved
  reference discrepancies. Describe downstream score evaluation separately from inference.
- Responsible publication: review attribution, licenses, derived-data rights and claims.
  Public releases, pushes and announcements require explicit founder approval.
- Exceptions: document scientifically infeasible experiments or unavailable resources,
  their effect on conclusions, and the evidence needed to close each exception.
