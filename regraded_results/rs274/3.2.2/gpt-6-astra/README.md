# Astra RS274 3.2.2 regrades

All 12 saved Astra submissions were regraded without model inference or source edits. The original generation eval remains **3.2.0**; the grading eval is **3.2.2**. Every model-input hash matches the corresponding historical run.

| Language | Reasoning | Original (3.2.0) | Regraded (3.2.2) | Score record |
|---|---|---:|---:|---|
| C++ | Max | 478/546 (87.55%) | 555/555 (100.00%) | [cpp-max.json](cpp-max.json) |
| C++ | High | 490/546 (89.74%) | 555/555 (100.00%) | [cpp-high.json](cpp-high.json) |
| C++ | Low | 483/546 (88.46%) | 549/555 (98.92%) | [cpp-low.json](cpp-low.json) |
| Python | Max | 478/546 (87.55%) | 555/555 (100.00%) | [py-max.json](py-max.json) |
| Python | High | 474/546 (86.81%) | 550/555 (99.10%) | [py-high.json](py-high.json) |
| Python | Low | 485/546 (88.83%) | 549/555 (98.92%) | [py-low.json](py-low.json) |
| JavaScript | Max | 477/546 (87.36%) | 550/555 (99.10%) | [js-max.json](js-max.json) |
| JavaScript | High | 483/546 (88.46%) | 555/555 (100.00%) | [js-high.json](js-high.json) |
| JavaScript | Low | 482/546 (88.28%) | 554/555 (99.82%) | [js-low.json](js-low.json) |
| Rust | Max | 483/546 (88.46%) | 555/555 (100.00%) | [rs-max.json](rs-max.json) |
| Rust | High | 481/546 (88.10%) | 555/555 (100.00%) | [rs-high.json](rs-high.json) |
| Rust | Low | 490/546 (89.74%) | 553/555 (99.64%) | [rs-low.json](rs-low.json) |

Grader code commit: `0c7e3d9b10b2b48619e5304dacd5b49f3cc34d67` (clean checkout).
Test suite SHA-256: `3d096665fab1578444b0c0a0f7bfa1975e389a9398a34e265820305b300eca11`.
Immutable Docker image: `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`. Containers used the normal offline scoring pipeline.

Every grade completed all 555 collected tests with no skips or pytest infrastructure errors. Original result bytes and complete source trees were checked before/after grading; source snapshots preserve all regular files and empty directories. The records retain source, prompt, test and harness manifests plus raw-report hashes. All original token/cost accounting is preserved under `original`; additional model calls and model cost are both zero.

The JSON files are explicitly `clispecbench.regrade-summary` artifacts. They contain complete new per-test outcomes, subscores and generation/grading provenance, but do not include source archives or raw pytest reports. Those complete bundles remain on the grading machine. The prior published JSON files remain unchanged and are referenced with their hashes; these observations are not additional model-run rows and are not automatically loaded by the dashboard.

Compare the new cohort using the shared 3.2.2 rubric. The higher scores mostly reflect repaired fixtures and reduced failure coupling, not improved submissions. Counts have different denominators (546 versus 555). A common node ID can contain a corrected test, so recorded outcome transitions are diagnostic rather than paired repeats of an identical measurement.

Each language/effort has only one saved run. These scores do not establish a reliable reasoning-effort ranking, and C++ High reaching 100% does not establish complete RS274 specification coverage. See the [independent review](independent-review.md), [validation audit](../../../../docs/validation/RS274-3.2.2.md) and [failure analysis](failure-analysis.md) for remaining limits and correlated failures.

Public EOF and implicit-D wording, raw versus effective G92 maps, spindle direction at S0, the explicit-Z/TLC question, and complete C++/JavaScript reference trace engines remain separate follow-up topics. No new public interpretation was applied to these historical submissions.
