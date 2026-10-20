# Source-only release boundary

Proposed repository: BioGiantTherapeutics/BioG-Reliability. The local candidate has a
fresh Git root derived from a reviewed source ZIP, with no old parents, alternates,
copied .git directory or remote. Never push the research repository history.

Include original source, research scripts, tests, dependency locks, CI, documentation,
original synthetic fixtures and a screenshot of only that synthetic demonstration.
Exclude datasets, sequence-level outputs, upstream code, research reports/decks/
screenshots, environments, caches, builds and old Git metadata.

scripts/check_release.py reviews every tracked file and rejects forbidden directories,
generated egg-info, oversized/unreviewed binaries, common credential patterns,
workstation paths and literal long DNA sequences. It exports a clean committed tree
with per-file hashes. This bounded scan complements human review and is not legal clearance.

Original code/fixtures are MIT; dependencies and external data retain their terms.
Nothing third-party is vendored. See THIRD_PARTY_NOTICES.md and dependency-licenses.json.

Gates: review owner/source inventory; authorize private staging creation/push; run
and inspect remote CI; obtain separate explicit approval for public visibility/tag/release.
Local preparation creates no remote resource, release tag or announcement.
