# Release validation record
The historical internal research run had 68 passed, zero failures/errors/skips and
350/390 package statements covered (89.74358974%). It reproduced 20/25 reference
comparisons and retained five unsuccessful CCTop comparisons. That evidence is not
reused as test evidence for the modified release source.

This source candidate has a fresh Git root and separately executed local validation.
Detailed receipts and current scope are included in the private publication preview.
Remote GitHub CI has not run; no badge or remote success is asserted.

Default CI deselects research cases. Full local Pytest reports missing external inputs
as skips; with prepared inputs, all research assertions execute. Synthetic demo tests
verify page traversal, exact input hashes, exported interpretation and unknown-label
semantics. Coverage is package statement coverage, not whole-project or branch coverage.
Final counts are recorded before staging approval.
