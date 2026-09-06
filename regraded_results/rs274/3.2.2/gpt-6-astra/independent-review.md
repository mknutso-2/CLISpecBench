# Independent final review: RS274 3.2.2 Astra cohort

**Approved for committing the separate regrade records. No blocking correctness, fairness, provenance, or packaging findings remain.** The approval covers unchanged saved submissions graded by commit `0c7e3d9b10b2b48619e5304dacd5b49f3cc34d67`, eval 3.2.2, test SHA `3d096665fab1578444b0c0a0f7bfa1975e389a9398a34e265820305b300eca11`.

## Verified final scores

| Language | Max | High | Low |
|---|---:|---:|---:|
| C++ | 555/555 | 555/555 | 549/555 |
| Python | 555/555 | 550/555 | 549/555 |
| JavaScript | 550/555 | 555/555 | 554/555 |
| Rust | 555/555 | 555/555 | 553/555 |

All 6,660 test executions completed: **6,635 passed, 25 failed**, with no skipped tests or pytest infrastructure errors. Six submissions pass every test. No new failure IDs appeared relative to the preliminary 3.2.1 cohort.

## Independent preservation and packaging audit

- All twelve archived generation UIDs are distinct and unchanged; all twelve regrade UIDs are distinct and differ from the preliminary regrades.
- Every run records the same clean committed grader revision, test hash, harness hash, and pinned Docker image. Snapshot tests were independently hashed; raw pytest outcomes reproduce each summary and score.
- Original result bytes/hashes, full source hashes, generation metadata, original scores, token usage and costs are preserved. Complete source snapshots match the originals with no exclusions. Each original prompt hash matches the unchanged current model-visible corpus.
- All twelve portable JSON summaries match their raw regrade's UID, grading provenance, complete test outcomes, summary and scores. Raw report/regrade hashes and source/test/harness manifest bytes match their retained bundles; historical published/archive result hashes resolve correctly. The twelve CSV rows reproduce the JSON scores and generation UIDs.
- The package is explicitly a separate regrade-summary artifact, preserves historical generation eval 3.2.0, records grading eval 3.2.2, and reports zero additional model calls/cost. It clearly states that full source/raw report bundles remain local; historical published records are not replaced or duplicated as new model-run rows.

Machine-readable audit evidence retained on the grading machine under `work/rs274-revision/review/`: `cohort-audit-3.2.2.json`, `cohort-aggregate-audit-3.2.2.json`, and `package-audit-3.2.2.json`. Per-run audit script retained in that same local directory: `audit_cohort_3_2_2.py`.

## Remaining failure mechanisms

| Mechanism | Failed outcomes | Affected submissions |
|---|---:|---|
| TLC controlled-point frame | 20 | C++ Low, Python High, Python Low, JavaScript Max: five cases each |
| G4 P0 drops concurrent modal delta | 3 | C++ Low, Python Low, JavaScript Low |
| Missing probing precondition guards | 2 | Rust Low: turning spindle and initially tripped probe |

The TLC cluster is the only repeated multi-case mechanism: three direct offset checks and two probe integrations share a coordinate-frame prerequisite. These twenty outcomes represent 80% of remaining failures, not twenty independent bugs. The tests document this bounded dependency, and the package's failure analysis explains it accurately. No dozens-of-tests fixture cascade remains in this observed cohort; fundamental parsing/motion/output prerequisites can still affect multiple cases.

The known incidental failures were removed without replacing the archived source or changing public requirements. The legal empty final parameter-map control improves from 520/556 to 555/555, while corrupt persisted values, missing probe writes, and missing G92 clearing still fail their intended tests. Legal zero-header/comment parameter-file formatting passes. The final exact-blank-separator gate follows the original specification.

## Critical interpretation

The package correctly concludes that these results expose a ceiling limitation for this Astra cohort. Scores range from 98.92% to 100%, with one generation per language/effort; they do not support a reliable reasoning-effort ranking or prove full RS274 coverage. No post-hoc score weighting was introduced. Public phase two should separately settle the documented EOF, implicit-D, G92-map, S0-direction, and explicit-Z/TLC ambiguities before grading new requirements.

Canonical repo/source files were reviewed read-only throughout grading; this reviewer wrote only diagnostic scripts, copied mutants and audit reports under work/.
