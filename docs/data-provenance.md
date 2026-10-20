# Dataset provenance and distribution boundary
Default software tests and the demonstration use only original artificial fixtures
in examples/demo (MIT). They contain no biological sequences or experimental records.
No private inputs are required.

Optional research scripts acquire separately published inputs. Review their terms
and establish rights for your intended use before acknowledging data terms. The
acknowledgment does not grant rights. No research dataset or third-party source is bundled.

| Input | Pin | Terms and role |
|---|---|---|
| Canonical primary truth | maren-ha/OffTargetPredictionBenchmark e82954897a77e95df46370923e9a5213ed7b1e19 | Upstream package declares MIT but lacks standalone license; underlying database rights unresolved. Separately obtained for authorized local research. |
| Prediction deposit | DOI 10.5281/zenodo.20627722, v1.0.0 | CC BY 4.0. SHA-256 42c1b1c71c77494b3ab3a4cf5a3e54c500bf2eb2985a53c76a41dc08c3e6cda9; MD5 611cb28ab0516e471c5dc59ea44a330a. |
| TrueOT/training inventories | baolab-rice/CRISPR_OT_scoring 4ff0ccd2493de3dc658747d05fa6bb4fe12ea2c7 | No standalone reuse license independently identified. Six pins in external-input-hashes.json. Local access does not clear redistribution. |
| CRISPR-Bulge assay archive | OrensteinLab/CRISPR-Bulge 3eddcd5bfcaff00b2bdf29425116ec9756ace870 | Code MIT does not settle all primary-data terms. LFS SHA-256 f892f70ba4ac3b05b03b2171b4ad38746630de08ad630e650f355dd61203eab0. |

Acquisition uses pinned HTTPS sources with checksum/version validation. Scientific
context and source publications are in dataset-catalog.md. hg38/SpCas9 is the primary
scope; TrueOT retains source-specific labels/context and does not silently convert
uncertain coordinate origins. Related CHANGE/GUIDE collections are not independent
studies. Unknown zero-read candidates are not measured negatives.

Raw/processed tables, upstream checkouts, sequence-level outputs, research reports,
research screenshots/presentation, environments and previous Git history are excluded.
Only aggregate factual summaries with attribution are included in documentation.
Public download access is not unrestricted reuse or commercial redistribution permission.
