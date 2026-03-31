## Unresolved Scope Disagreement: `G38.3` / `G38.4` / `G38.5`

Context:
- Repo: `SWE-BuildBench` / `CNCSim`
- Current task: continue working through the remaining agreed CNCSim coverage gaps
- Why this file exists: `AGENTS.md` requires explicit recording of unresolved disagreements when Claude cannot complete the needed reconciliation round
- Current blocker: Claude CLI is rate-limited before a targeted follow-up on this exact item could complete

### My Current Position

`G38.3`, `G38.4`, and `G38.5` should **not** remain in
[CNCSim/REMAINING_TEST_GAPS_TODO.md](C:/Git/SWE-BuildBench/CNCSim/REMAINING_TEST_GAPS_TODO.md)
as open RS274 coverage gaps.

Reason:
- The RS274 source in this repo appears to define only `G38.2`.
- Relevant references from
  [RS274NGC.md](C:/Git/SWE-BuildBench/CNCSim/prompt/docs/RS274NGC.md):
  - [RS274NGC.md](C:/Git/SWE-BuildBench/CNCSim/prompt/docs/RS274NGC.md#L1762)
    defines section `3.5.9 Straight Probe — G38.2`
  - [RS274NGC.md](C:/Git/SWE-BuildBench/CNCSim/prompt/docs/RS274NGC.md#L1769)
    begins `Program G38.2 X… Y… Z… A… B… C…`
  - `rg` over the RS274 doc finds `G38.2` only, with no occurrences of
    `G38.3`, `G38.4`, or `G38.5`

My conclusion:
- treating `G38.3/.4/.5` as remaining RS274-required test gaps likely
  overreaches beyond the spec actually in `docs/RS274NGC.md`

### Claude's Earlier Position

In an earlier consensus pass, Claude accepted the TODO item listing
`G38.3`, `G38.4`, and `G38.5` as open directly testable gaps.

That earlier acceptance is now in tension with the direct RS274 source check
above.

### Needed Follow-Up

When Claude CLI is available again, do one narrow follow-up only on this item:

- inspect `CNCSim/prompt/docs/RS274NGC.md`
- confirm whether `G38.3/.4/.5` are actually in scope for CNCSim-Full under the
  repo's explicit-RS274-only rule
- then either:
  - remove the item from the TODO as out of scope, or
  - keep it and record the exact RS274 basis

## Unresolved Bucketing Disagreement: Full `G88` Success-Path Coverage

Context:
- Repo: `SWE-BuildBench` / `CNCSim`
- Current task: continue working through the remaining agreed CNCSim coverage gaps
- Why this section exists: earlier Claude responses were internally inconsistent
  about whether `G88` success-path coverage belongs in the directly testable
  bucket or the observability-limited bucket, and Claude CLI is currently
  unavailable for a fresh narrowing pass

### My Current Position

The directly observable subset of `G88` success behavior can be tested, but the
full line-end state cannot be pinned under the current harness.

Reason:
- [RS274NGC.md](C:/Git/SWE-BuildBench/CNCSim/prompt/docs/RS274NGC.md#L2250)
  section `3.5.16.9` explicitly says:
  - `3.` Stop the spindle turning.
  - `4.` Stop the program so the operator can retract the spindle manually.
  - `5.` Restart the spindle in the direction it was going.
- That makes the restored spindle direction directly observable and suitable for
  a requirement-bearing test.
- But the operator's manual retract position is not deterministic in the
  current single-run payload, so the full final-position behavior should remain
  in the observability-limited bucket.

My conclusion:
- a limited positive `G88` test is in scope
- a full deterministic `G88` success-path endpoint test is not

### Claude's Earlier Positions

Claude gave two inconsistent classifications in
[repo-gap-consensus.md](C:/Git/SWE-BuildBench/claude-conversations/repo-gap-consensus.md):

- at `2026-03-30T20:10:59`, Claude said `G88` belongs in the observability /
  hardware / timing bucket because the operator-manual-retract step makes the
  final position undefined
- at `2026-03-30T20:12:48`, Claude instead left `G88 success path` in the
  directly testable bucket

### Needed Follow-Up

When Claude CLI is available again, do one narrow follow-up only on this item:

- inspect [RS274NGC.md](C:/Git/SWE-BuildBench/CNCSim/prompt/docs/RS274NGC.md#L2250)
  section `3.5.16.9`
- decide whether the current split is the right one:
  - directly observable `G88` spindle-direction restoration covered
  - operator-manual-retract final-position behavior left in the
    observability-limited bucket
