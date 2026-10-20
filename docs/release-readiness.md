# Source-only release boundary

Private staging repository: mqar96/BioG-Reliability. The candidate has a
fresh Git root derived from a reviewed source ZIP, with no old parents, alternates,
copied .git directory or connection to the original research history. Its origin
is the approved private staging repository. Never push the research repository history.

Include original source, research scripts, tests, dependency locks, CI, documentation,
original synthetic fixtures and a screenshot of only that synthetic demonstration.
Exclude datasets, sequence-level outputs, upstream code, research reports/decks/
screenshots, environments, caches, builds and old Git metadata.

scripts/check_release.py reviews every tracked file and rejects forbidden directories,
generated egg-info, oversized/unreviewed binaries, common credential patterns,
workstation paths and literal long DNA sequences. It exports a clean committed tree
with per-file hashes. This bounded scan complements human review and is not legal clearance.

The ZIP is built from committed Git blobs, not checkout bytes. Windows newline
conversion cannot change the archived source or its manifest hashes.

Original code/fixtures are MIT; dependencies and external data retain their terms.
Nothing third-party is vendored. See THIRD_PARTY_NOTICES.md and dependency-licenses.json.

Owner/source review and private staging creation/push were authorized and completed.
Inspect Actions for the hosted run attached to the exact proposed release commit.
The private approval preview records that commit and run together with asset hashes.
The remaining publication gate is separate explicit approval for the exact public
commit, assets, visibility change, tag and release. No public release or announcement
is authorized by private staging approval. Research-data rights remain separate.
