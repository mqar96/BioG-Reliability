# Verified release validation

Two fresh Python 3.13.12 environments were created for the separate release repository
and an unpacked source ZIP. The source ZIP contains no .git metadata or research data.
Its provenance records a null commit rather than inheriting the parent research checkout.

| Local scope | Passed | Failed/errors | Skipped | Deselected |
|---|---:|---:|---:|---:|
| Data-free CI selection | 69 | 0 | 0 | 5 |
| Full suite without external inputs | 69 | 0 | 5 | 0 |
| Full suite with freshly acquired research inputs | 74 | 0 | 0 | 0 |

The final full research suite took 55.37 seconds. Package statement coverage was
358/398 (89.94974874%). Data-free coverage was 334/398 (83.91959799%). Coverage is
package statement coverage, not whole-project or branch coverage. No statements excluded.

Both scopes passed Ruff, formatting, pip check and wheel/sdist builds. The documented
software reconstruction and CLI demo ran from the archive. All demonstration pages,
export interpretation and unknown-label semantics were tested. The actual launcher
ran on localhost at port 8504; native browser overview and the synthetic-only screenshot
were inspected. CITATION.cff validates against the official 1.2.0 schema.

Primary, TrueOT/training and large-assay inputs downloaded into ignored local folders
and passed checksum/version verification. The full research workflow regenerated
primary/tie/external/assay/stress/CCTop results and the report. 20 deterministic
scientific CSVs match the prior verified analysis; new stress timing varies with load.
No previous processed table or old test report was supplied as current evidence.

Local source/test/output receipts are retained privately with the publication preview.
Research data and generated evidence remain excluded from the public source. The README
identifies historical performance separately from the current validation repeat.

Remote CI: NOT RUN. No private staging repository, public repository, visibility change,
release tag or release has been created. Those require the founder's explicit authorization.
