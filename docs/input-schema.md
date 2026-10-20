# Input contracts

UTF-8 CSVs use one row per experimental identity and one prediction per model/site. Missing scores are absent rows, never fabricated zeros.

Truth fields: site_id, guide_id, assembly, assay, context, status, measurement.
Status is exactly positive, measured_negative or untested. Measured rows require finite outcomes. Untested rows require blank outcomes. Document outcome units and labeling thresholds in provenance. Optional chromosome, start, end and strand enable annotation checks. Canonical coordinates are 0-based, half-open nonnegative integers with end > start. Supply + or - strand. Prediction coordinates, when supplied, receive the same checks. The published adapter checks source order without inferring coordinate origin; it uses sequence/chromosome identity. Source PAR1/PAR2 strand annotations are explicitly normalized and counted. The toolkit does not fetch a genome to verify reference sequences.

Prediction fields: site_id, guide_id, assembly, model, score, rank.
Scores must be finite and oriented so higher means greater predicted off-target activity. Ranks are positive integers from the full candidate universe per guide, including unlabeled candidates. Do not rerank after filtering to labeled sites. Tied ranks are allowed and budget exceedance is disclosed. Exact-budget evaluation needs the full candidate table, including all boundary ties.

Provenance JSON requires nonempty strings: dataset_id, version, source_url (HTTPS), license, assembly, species, nuclease, assay, context, identity_policy. License metadata is evidence, not automatic legal clearance.

Partition different assemblies, assays and cell contexts. The published adapter explicitly declares pooled_as_published and reports the limitation. Generic import does not silently pool inconsistent annotations. For new datasets, site identities should include assembly, coordinates, strand, guide, assay and sample context. Repeated measurements require an explicit preprocessing policy.

CLI example:

    .venv\Scripts\biog data/processed/truth.csv data/processed/predictions.csv data/processed/provenance.json --output results/custom

The overlap_audit(train, test) API reports shared site and guide identities. It cannot exclude leakage from undisclosed model training data.
