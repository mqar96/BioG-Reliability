# Third-party attribution and release boundaries

Original BioG code is independently implemented and MIT licensed. Data and publications retain their original terms.

## Prediction archive

Kaufmann, Masako Monika; Hackenberg, Maren; Pargeter, William Jobson (2026). Standardized prediction outputs for reproducible benchmarking of CRISPR-Cas9 off-target prediction tools, v1.0.0. https://doi.org/10.5281/zenodo.20627722.

Zenodo declares CC BY 4.0. Its metadata snapshot is retained. Attribution and disclosure of changes are required: https://creativecommons.org/licenses/by/4.0/.
BioG transformations: validation, deduplication, filtering and aggregate metric recomputation. No endorsement by source authors is implied.

## Canonical truth and reference code

The reference repository at e82954897a77e95df46370923e9a5213ed7b1e19 declares MIT in pyproject.toml but contains no standalone LICENSE. The compact truth table is locally analyzed under the repository's published declaration. That is not a legal conclusion about all upstream data rights.

CRISPRoffT database commercial redistribution rights are not independently established. Its article uses a noncommercial publication license, which does not alone determine the database license. Raw/processed data and reference code are excluded from Git. Clarify truth-table redistribution rights before bundling them publicly or commercially.

## Dependencies

docs/dependency-licenses.json records package versions and declared license metadata. NumPy, pandas, SciPy and scikit-learn use BSD-family licenses; Streamlit uses Apache-2.0; Plotly.py, Requests, pytest and Ruff use permissive licenses. Ruff includes MIT/Apache terms. Full notices remain in installed distributions. No environment or third-party source code is shipped in Git. Review notices before distributing an installer.

The bundled Artifact Tool used for the presentation is not vendored or relicensed. Native model executables and weights were not used; review their licenses before future integration. This inventory is not comprehensive legal clearance.

## Expanded research inputs

TrueOT v1.1: Kota, Pan, Vu, Cao, Baraniuk and Bao (2021),
https://doi.org/10.1101/2021.08.28.457846, author repository
https://github.com/baolab-rice/CRISPR_OT_scoring at
4ff0ccd2493de3dc658747d05fa6bb4fe12ea2c7. This includes author-provided
CIRCLE-seq and SITE-seq training representations. No standalone repository reuse
license was identified. These inputs and sequence-level derived outputs are local
research material and are excluded from the proposed public source export.

CRISPR-Bulge: Yaish and Orenstein (2024), https://doi.org/10.1093/nar/gkae428,
repository https://github.com/OrensteinLab/CRISPR-Bulge at
3eddcd5bfcaff00b2bdf29425116ec9756ace870, reprocessing Lazzarotto et al. (2020),
https://doi.org/10.1038/s41587-020-0555-7. Repository code is MIT; this does not
establish every primary dataset's redistribution or commercial-use terms.

The current dependency metadata inventory is docs/dependency-licenses.json.
Certifi declares MPL-2.0. The source export bundles no dependency distributions.
The original private research repository history includes earlier sequence-level outputs and must not
be publicly pushed without rights clearance; use the reviewed source-only export.

## Original demonstration assets
examples/demo and docs/assets/demo-dashboard.jpg are original synthetic software fixtures
and an authentic screenshot of those fixtures. No biological sequences or observations
are represented. They are distributed under the project MIT license.
