# Public-data selection and prior art

Search performed 19 October 2026 using primary publications and their repositories.
This is a suitability review, not proof that no larger dataset exists. Computational
candidate counts are separated from measured experimental outcomes.

| Dataset / persistent source | Authors, date/version | Scale and biological meaning | Assembly, scores and decision |
|---|---|---|---|
| [Kaufmann benchmark](https://doi.org/10.1177/10430342261466407), [Zenodo 20627722](https://doi.org/10.5281/zenodo.20627722) | Kaufmann et al., 2026; repository e82954897a77e95df46370923e9a5213ed7b1e19; deposit v1.0.0, 10 June 2026 | 3,827 measured delta-indel observations, 26 guides, multiple nomination assays/cell contexts. Positive >=0.1% background-corrected indels. Pooled observations are not independent replicates. | hg38; 14 deposited method contracts, five evaluated. Prediction deposit CC BY 4.0. Truth redistribution unresolved. Primary reproduction. |
| [TrueOT v1.1](https://doi.org/10.1101/2021.08.28.457846), [author repository](https://github.com/baolab-rice/CRISPR_OT_scoring) | Pavan K. Kota, Yidan Pan, Hoang-Anh Vu, Mingming Cao, Richard G. Baraniuk, Gang Bao; 2021 preprint, repository revision 4ff0ccd2493de3dc658747d05fa6bb4fe12ea2c7 | 1,903 source observations, 36 guides, 11 studies. Author binary labels from experimentally checked sites. Source-specific T7EI/NGS/detection criteria; 281 source positives. Missing quantitative efficiencies prevent common percent-indel relabeling. | hg38 stated in S2; coordinate origin not resolved, retained as source annotations. Deposited CFD and CRISPR-NET scores used on common cohorts. No standalone repository license. Exclude primary guide/study overlap and known training guides. Local-only data. |
| [CHANGE-seq](https://doi.org/10.1038/s41587-020-0555-7), PRJNA625995, GSE149295 | Cicera R. Lazzarotto et al., 2020 | Published study profiles 110 guides across 13 loci and reports 201,934 off-target detections. In-vitro cleavage and matched cellular assays differ. Non-detection is not experimentally confirmed editing inactivity. | hg38 in later reprocessed data. Original study is an important large source; current analysis uses the pinned Yaish/Orenstein reprocessing below, not raw sequencing. Primary study reuse terms require separate review. |
| [CRISPR-Bulge](https://doi.org/10.1093/nar/gkae428), [author repository](https://github.com/OrensteinLab/CRISPR-Bulge) | Ofir Yaish and Yaron Orenstein; 30 May 2024; commit 3eddcd5bfcaff00b2bdf29425116ec9756ace870 | Verified 524,400,344-byte archive. CHANGE: 4,936,278 candidate rows, 202,040 read-positive rows, 110 guides. Full GUIDE: 3,271,049 candidate rows, 2,166 read-positive rows, 78 guides. Includes on-targets and candidate alignments. These related cohorts are not independent biological studies. | hg38. Repository MIT; underlying data rights not inferred from code license. Streaming integrity, coordinates and read-count inventory performed. No compatible scores evaluated. Zero-read candidates retained as unknown. Counts are artifact observations, not a reproduction of original paper off-target counts. |
| CIRCLE-seq training table from [TrueOT repository](https://github.com/baolab-rice/CRISPR_OT_scoring/tree/4ff0ccd2493de3dc658747d05fa6bb4fe12ea2c7/Algorithms/pairwise_evaluation/training_sets/CRISPR-NET) | Tsai et al., 2017 source, supplied CRISPR-NET training representation | 584,949 candidate rows, 10 guides, 7,371 label-positive rows. Remaining computational/undetected candidates are not measured negatives. | Human assay; representation lacks complete locus/assembly provenance. Used for guide-overlap auditing only. Same repository license limitation. |
| SITE-seq training table from the same pinned repository | Cameron et al., 2017 source, supplied CRISPR-NET representation | 217,733 candidates, 9 guides, 3,767 read-positive rows. In-vitro cleavage differs from cellular indel measurements. | Coordinates present but assembly not independently established for this representation. Guide overlap only. No cross-assay accuracy claim. |

Acquisition: `scripts/fetch_data.py` and `scripts/fetch_external.py` use pinned
HTTPS URLs. SHA-256 pins for TrueOT inputs are in `docs/external-input-hashes.json`.
The large archive SHA-256 is
`f892f70ba4ac3b05b03b2171b4ad38746630de08ad630e650f355dd61203eab0`, matching the
Git LFS pointer. The acquisition manifests record exact URL, bytes and timestamp.

TrueOT study details, cell contexts and experimental label criteria remain in
the original S1/S2 workbooks. We do not silently harmonize those assay thresholds.
Deposited score availability, measured negatives and study identity made TrueOT
more suitable for external classification than millions of untested candidates.

## Prior capabilities and contribution boundaries

Kaufmann and colleagues already implement coverage, recall budgets, combinations
and guide bootstrap analyses. Kota and colleagues already curate a measured
benchmark and remove known training overlap. Yaish/Orenstein already investigate
large assay data and bulges. None of these capabilities is claimed as a BioG invention.
The [2020 NAR evaluation](https://academic.oup.com/nar/article/48/20/11370/5952209) also predates BioG's
comparison workflow. The review is focused and does not establish first-ever novelty.

BioG's integration adds strict import behavior, reproducible source/test/output
bindings, a consistent dashboard and explicit uncertainty/cohort policies. The
new empirical results are this independent implementation's tie-budget and
cohort-selection analyses, external reanalysis and measured software scalability.
Exact-budget expectation uses standard combinatorics. No novel predictor or
biological mechanism is introduced. A broader prior-art study and more independent
quantitative cohorts are required before a methodological originality claim.

The 2022 study by Yaish, Asif and Orenstein, https://doi.org/10.1093/bib/bbac157, already evaluates data processing, problem formulation and non-guide-overlapping evaluation on CHANGE/GUIDE data. This further limits any claim that cohort/dependence auditing itself is novel.

