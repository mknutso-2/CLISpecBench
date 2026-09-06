# GPT-5.6 RS274 3.2.2 regrades (cross-cohort check)

All 36 published `api-only` GPT-5.6 RS274 submissions, regraded without model inference or
source edits. The original generation eval is **3.2.0**; the grading eval is **3.2.2**. Every
model-input hash matches the corresponding historical run, and matches the hashes recorded for
the [GPT-6 Astra cohort](../gpt-6-astra/README.md) — both cohorts were generated against
byte-identical prompts.

This cohort exists to test a question the Astra audit could not settle on its own. The v3.2.2
fixture corrections were derived by analyzing the Astra cohort's failures, which is a sound way to
find fixture bugs and also the process most likely to overfit a suite to one model.

**This is a cross-cohort check, not a blinded holdout.** `Evals/RS274/TODO.md`, as of `9938b1b`
and therefore before the audit commits, already names two of these runs — GPT-5.6 Terra high and
max C++ — with their official scores (261/546, 266/546) and diagnostic scores of 442/546 and
484/546 obtained from manually modified copies of those submissions with only their EOF rejection
disabled; `docs/validation/RS274-3.2.1.md` refers to that TODO. That is source-mutant evidence,
distinct in kind from the unchanged-source regrades in this table. Those runs were known and used
investigatively while the corrections were under consideration. Nothing here shows
fixtures were tuned to them, but this cohort cannot be presented as proof of independence from all
design influence. What it establishes is that the corrections apply beyond Astra.

## Selection

Runs were selected by **published run UID**, not by score or directory order. Of the 47 saved
GPT-5.6 RS274 runs at eval 3.2.0, exactly 36 carry `metadata.network_policy == "api-only"` and
exactly those 36 are published. The other 11 have no policy marker and are excluded; they are
separate diagnostics, not cohort members. See the cohort rules in
[`docs/operations/Regrading.md`](../../../../docs/operations/Regrading.md).

## Grading environment

- Test suite SHA-256: `3d096665fab1578444b0c0a0f7bfa1975e389a9398a34e265820305b300eca11` (same as Astra)
- Docker image: `sha256:922c3bc7435e5546e737bf77b5bc8c07d15f86c9bad7f6fc68555cf8fbf04dc5`
- Offline containers, normal scoring pipeline, one image for all 36

**The image differs from the Astra cohort's `sha256:9a4f1fe0…`, which is not available on the
auditing workstation.** These 36 are internally comparable with each other under one grader, but
are *not* a same-image replication of the Astra grading. Treat cross-cohort comparisons as
indicative.

Toolchain control: the C++, Python and JavaScript reference implementations were graded under this
same image and reproduced their documented figures exactly — 447/555, 555/555 and 447/555
respectively (see `docs/validation/RS274-3.2.2.md`). The Rust reference suite could **not** be
validated here: it depends on `serde` and `serde_json`, which an offline build cannot fetch without
a pre-populated cargo cache. That gap is dependency-specific, not a missing compiler. Rust
submissions built and graded normally — the Rust backend compiles fresh into a newly allocated
build directory rather than reusing any `target/` tree in the saved source, and a dependency-free
submission compiles offline without difficulty.

## Results

| Language | Model | Effort | 3.2.0 | 3.2.2 | Δ pp |
|---|---|---|---:|---:|---:|
| C++ | luna | high | 386/546 (70.70%) | 39/555 (7.03%) | −63.7 |
| C++ | luna | low | 112/546 (20.51%) | 185/555 (33.33%) | +12.8 |
| C++ | luna | max | 465/546 (85.16%) | 519/555 (93.51%) | +8.3 |
| C++ | sol | high | 483/546 (88.46%) | 542/555 (97.66%) | +9.2 |
| C++ | sol | low | 256/546 (46.89%) | 404/555 (72.79%) | +25.9 |
| C++ | sol | max | 496/546 (90.84%) | **555/555 (100.00%)** | +9.2 |
| C++ | terra | high | 261/546 (47.80%) | 461/555 (83.06%) | +35.3 |
| C++ | terra | low | 221/546 (40.48%) | 187/555 (33.69%) | −6.8 |
| C++ | terra | max | 266/546 (48.72%) | 545/555 (98.20%) | +49.5 |
| JavaScript | luna | high | 451/546 (82.60%) | 501/555 (90.27%) | +7.7 |
| JavaScript | luna | low | 174/546 (31.87%) | 177/555 (31.89%) | +0.0 |
| JavaScript | luna | max | 474/546 (86.81%) | 527/555 (94.95%) | +8.1 |
| JavaScript | sol | high | 488/546 (89.38%) | 553/555 (99.64%) | +10.3 |
| JavaScript | sol | low | 378/546 (69.23%) | 390/555 (70.27%) | +1.0 |
| JavaScript | sol | max | 480/546 (87.91%) | 554/555 (99.82%) | +11.9 |
| JavaScript | terra | high | 462/546 (84.62%) | 490/555 (88.29%) | +3.7 |
| JavaScript | terra | low | 101/546 (18.50%) | 178/555 (32.07%) | +13.6 |
| JavaScript | terra | max | 476/546 (87.18%) | 552/555 (99.46%) | +12.3 |
| Python | luna | high | 436/546 (79.85%) | 482/555 (86.85%) | +7.0 |
| Python | luna | low | 206/546 (37.73%) | 184/555 (33.15%) | −4.6 |
| Python | luna | max | 472/546 (86.45%) | 522/555 (94.05%) | +7.6 |
| Python | sol | high | 477/546 (87.36%) | 543/555 (97.84%) | +10.5 |
| Python | sol | low | 447/546 (81.87%) | 485/555 (87.39%) | +5.5 |
| Python | sol | max | 487/546 (89.19%) | 554/555 (99.82%) | +10.6 |
| Python | terra | high | 436/546 (79.85%) | 470/555 (84.68%) | +4.8 |
| Python | terra | low | 325/546 (59.52%) | 337/555 (60.72%) | +1.2 |
| Python | terra | max | 479/546 (87.73%) | 545/555 (98.20%) | +10.5 |
| Rust | luna | high | 393/546 (71.98%) | 422/555 (76.04%) | +4.1 |
| Rust | luna | low | 68/546 (12.45%) | 64/555 (11.53%) | −0.9 |
| Rust | luna | max | 472/546 (86.45%) | 520/555 (93.69%) | +7.2 |
| Rust | sol | high | 482/546 (88.28%) | 544/555 (98.02%) | +9.7 |
| Rust | sol | low | 376/546 (68.86%) | 390/555 (70.27%) | +1.4 |
| Rust | sol | max | 481/546 (88.10%) | 554/555 (99.82%) | +11.7 |
| Rust | terra | high | 305/546 (55.86%) | 317/555 (57.12%) | +1.3 |
| Rust | terra | low | 0/546 (0.00%) | 0/555 (0.00%) | +0.0 |
| Rust | terra | max | 471/546 (86.26%) | 541/555 (97.48%) | +11.2 |

Rust terra-low did not build in its original run (`build.success: false`, 546 errored cases) and
does not build now (555 errored cases). Its zero reproduces the original state; the record's
transition field reports `error -> error`, not a pass-to-fail change.

## What this cohort shows

**The corrections apply beyond Astra.** Six of these 36 submissions land at or above Astra's
regraded floor of 549/555 (98.92%), and C++ sol-max reaches a perfect 555/555. Submissions from a
different model family benefit from the repairs as the Astra cohort did.

**The corrected rubric is not uniformly generous.** Four submissions score lower than under 3.2.0.
The largest, C++ luna-high at −63.7 points, is a diagnosed defect rather than an artifact. That
submission's input loop breaks on any standalone `%` line, including the opening delimiter, before
executing a block — `if(raw.find('%')!=string::npos&&noSpace(raw)=="%")break;`. Paired probes on a
fresh build in the same image confirm it: unframed `G0 X10\nG0 X20` ends at X=20, framed
`%\nG0 X10\nG0 X20\n%` ends at X=0, closing-percent-only ends at X=20. Under framed programs it
executes nothing and reports startup defaults. RS274 section 3.2 carries the file-demarcation
requirement; the old undelimited fixtures could not observe this.

**Exact ordering changes, concentrated in C++.** Spearman between 3.2.0 and 3.2.2 pass counts is
0.899 over all 36; per language it is C++ 0.667, JavaScript 0.950, Rust 0.967, Python 0.996. The
C++ movement has a documented cause: `TODO.md` records that Terra high and max C++ implemented the
documented percent/M2-M30 requirement and were penalized by the undelimited fixtures, and they move
+35.3 and +49.5 here, while luna-high moves the other way for the opposite reason. Historical 3.2.0
orderings are not a reliable proxy for ordering under the corrected rubric; they remain accurate
descriptions of performance under the historical rubric.

**A ceiling concern applies to the strongest submissions, not to every comparison.** All four
sol-max rows reach 554–555 of 555, alongside Astra's 549–555, so comparisons among top submissions
measure the ceiling. The cohorts still separate at lower effort: sol-low regrades to 404 (C++), 390
(JS), 485 (Python) and 390 (Rust) against Astra low at 549, 554, 549 and 553.

## Provenance and limits

Each record is a `clispecbench.regrade-summary`: complete per-test outcomes, subscores, and
generation/grading provenance, with source archives and raw pytest reports excluded. Records retain
original UIDs, original scores, original token/cost accounting, and the SHA-256 of both the archived
and published result JSON. Transition fields preserve actual outcome labels, including `error`.
Additional model calls and model cost are zero. All 36 completed 555 collected tests with no skips
and no pytest infrastructure errors, on one test hash and one image.

These are grading observations, not new model trials, and not published dashboard rows. The
published records remain unchanged. One saved run per language and effort does not support a
reliable reasoning-effort ranking. The differing grader image, and the TODO history described
above, are the main limits on reading these against the Astra cohort.
