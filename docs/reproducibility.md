# Reproducibility scopes

Default scripts/reproduce.ps1 installs the hash-locked environment, evaluates the
original synthetic examples through the CLI, runs data-free tests, lint, formatting,
dependency checks and wheel/sdist builds. scripts/launch.ps1 runs the synthetic demo
without external data. No dataset, secret or paid service is required.

For authorized research only, review docs/data-provenance.md and run:
    .\scripts\reproduce.ps1 -Research -DataTermsAccepted

The pipeline acquires pinned primary/external sources and recomputes primary metrics,
ties, external evaluation, assay profiling, stress measurements and upstream CCTop
diagnostics, then full verification and reporting. Source versions, environments,
seeds and input/output hashes are recorded; reports reject stale evidence.

-SkipDownload accepts already verified raw inputs and a pinned reference checkout,
not previously processed tables. Preserve transfer failures and disclose raw-cache reuse.
Direct acquisition scripts require --acknowledge-data-terms.

Full Pytest retains all tests, skipping research cases only when required external
inputs are absent. Default CI explicitly deselects those cases and never downloads
research data. The README research findings are identified historical internal results;
current release checks are independently executed and recorded in the publication preview.
