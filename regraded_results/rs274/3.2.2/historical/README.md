# Historical RS274 regrades at v3.2.2

286 published RS274 submissions regraded under the v3.2.2 rubric with no model inference and no
source edits. Generation eval is **3.1.11**; grading eval is **3.2.2**. Every row's
`prompt_content_sha` matches the current assembled prompt for its language, so model inputs are
unchanged and the comparison isolates the grading change.

Rust rows generated against an older prompt live in
[`../historical-rs-older-prompt/`](../historical-rs-older-prompt/README.md) and are **not** part of
this cohort. The other two cohorts are [`../gpt-6-astra/`](../gpt-6-astra/README.md) and
[`../gpt-5.6-codex-cli/`](../gpt-5.6-codex-cli/README.md).

## Selection and environment

Runs were selected by **published run UID**, never by score or directory order. Across all four
cohorts, 385 of the 387 published RS274 rows are now regraded; the two exceptions never had source
preserved and stay at their original rubric (see
[`docs/operations/RS274-3.2.2-Migration.md`](../../../../docs/operations/RS274-3.2.2-Migration.md)).

- Test suite SHA-256: `3d096665fab1578444b0c0a0f7bfa1975e389a9398a34e265820305b300eca11`
- Docker image: `sha256:922c3bc7435e5546e737bf77b5bc8c07d15f86c9bad7f6fc68555cf8fbf04dc5`
- Every record: 555 collected tests, no skips, no pytest infrastructure errors

The Astra cohort was graded under a different image (`sha256:9a4f1fe0…`) that is not available on
this workstation. That limit is unchanged and is recorded in
`docs/validation/RS274-3.2.2-Cross-Cohort.md`.

## Grading concurrency and its verification

Most of these regrades ran five at a time. Because the suite invokes each submission under a hard
5-second per-call timeout, parallel load can in principle manufacture false failures, so every
result was screened and the screen was itself validated:

1. All 337 bundles were scanned for timeout-shaped failures. Nine were flagged.
2. All eight timeout-flagged runs were re-graded **serially** and diffed node by node. All eight
   reproduced exactly — zero outcome changes. Those timeouts are genuine submission defects, not
   contention.
3. Twelve additional runs were sampled at random from the *unflagged* parallel results and
   re-graded serially. All twelve reproduced exactly. This is the check that would catch
   contamination leaving no timeout marker.
4. One run did not merely fail tests but failed **grading**: `rs274-cpp` gemini-3-flash-preview
   exhausted two 20-minute grader attempts under load. The harness refused to emit a score,
   recording `status: failed` with null scores rather than converting a failed grading into a
   zero. Re-graded serially it completed normally at 266/555, and that serial result is the one
   published here. This was the only genuine instance of parallel contamination, and it produced
   no bad data — only a retry.

Net: 20 of 20 serial re-grades reproduced their parallel outcomes node for node.

## Reading these results

**Scores move a long way in both directions.** Across all 385 migrated rows, 241 improved, 131
declined and 13 were unchanged, with a mean change of +3.8 points but a range from −63.7 to +67.5.
The corrected rubric is not a uniform uplift of the old one.

**Rank order is substantially different.** Spearman between 3.2.0/3.1.11 and 3.2.2 pass counts is
0.831 over 385 rows (C++ 0.809, Python 0.835, JavaScript 0.801, Rust 0.878). Historical scores
remain accurate descriptions of performance under the historical rubric, but they are not a
reliable proxy for standing under the corrected one.

**A large share of the movement is one axis: percent framing.** RS274 section 3.2 requires percent
delimiters when a file has no M2/M30, and the v3.2.1 fixtures began framing every test program
accordingly. Two failure modes follow, both visible as tight score clusters:

- 14 rows land on exactly 184/555 across four languages and ten different models, with
  *identical* passing-test sets — only the `*_errors.py` rejection cases pass, because the
  submission exits 1 on every framed program. Neighbouring clusters sit at 183 and 187.
- Others accept the framing but execute nothing, scoring far lower still; `rs274-cpp`
  gpt-5.6-luna high at 39/555 is the diagnosed example, its input loop breaking on any standalone
  `%` including the opening delimiter.

Conversely, submissions that correctly required delimiters and were penalised by the old
undelimited fixtures gain enormously — up to +67.5 points.

**This matters for publication.** `Evals/RS274/TODO.md` proposes a normative clarification that
would permit plain-EOF termination, explicitly overriding the section 3.2 requirement these
fixtures now enforce. Adopting that clarification would move this same axis again. Treat this
cohort as a measurement under the current rubric, not as a settled ranking.

## Provenance

Each record is a `clispecbench.regrade-summary`: complete per-test outcomes, subscores, and
generation/grading provenance, with source archives and raw pytest reports excluded. Records
retain original UIDs, original scores, original token/cost accounting, and the SHA-256 of both the
archived and published result JSON. Transition fields preserve actual outcome labels including
`error`. Additional model calls and model cost are zero.

These are grading observations, not new model trials, and not published dashboard rows. No
published record is modified by their presence.
