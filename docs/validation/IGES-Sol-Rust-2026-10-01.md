# Sol Max IGES Rust — October 1, 2026

Run `c70fa561-88ac-4bee-a7eb-0765338c6273` completed voluntarily in
85.17 minutes and scores **244/249** under IGES **1.0.21**, with no errors or
skips. Generation revision is `7e05775`; rubric SHA is
`ec84b63fbbbbf9a90c8d6e4a88cb5e29ab2e93424e7f25f96176569451382135`.
The recorded grader is
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
No tests, public inputs, references or submitted sources changed for this result.

Independent review finds all five failures fair. Two observations cover illegal
zero-count Hollerith: the reader accepts `0H`, while the writer emits it for an
empty `app_protocol`. These exercise separate code paths, and the reader probe
uses an independent raw fixture with a legal control. Three correlated Type 130
observations measure the same physical normal-cross-tangent formula in place of
the explicit benchmark direct-vector override. Five failures therefore describe
two semantic families, not five independent defects. Public offset wording
cleanup remains deferred; there is no new scoring repair here.

The final eight self-tests and release build pass after the last source edit.
Separate CLI, numerical, record-width and fixed-point checks precede that edit.
The implementation is substantial, but its complete-conformance claim is
contradicted by the hidden test failures.

Session accounting agrees with 37,782,672 input tokens (36,447,616 cached),
204,766 output tokens (75,026 reasoning), and 37,987,438 total tokens.
The recorded-rate API-equivalent estimate is **$24.014590**, not a subscription
charge. Raw tool count stays null: 260 canonical actions and one directly
classifiable rejected patch are established; another sequential patch/command
wrapper is outside the conservative parser. Root inspected the paired rejection
at session lines 361/363 and preserved the unavailable metric without discarding
authoritative token/cost data. No exact tool count is published.

Source, raw result and session hashes remain preserved. All 71 prior checkpoint
rows and seven excluded attempts are unchanged. Both dashboards validate at
**1,848 runs / 1,174,600 test rows**. All prior rows remain unchanged apart from
expected test-dashboard run-index shifts. The full streamed comparison peaks at
**34,236 KiB** under a 512 MiB cap. The old aggregate hash matches
the preserved dispatch baseline before its redundant hardlink is released.

[Machine-readable checks](IGES-Sol-Rust-2026-10-01-checks.json) retain independent
content review, objective/accounting evidence and dashboard preservation results.
Local full evidence: `work/non-rs274-audit/runs/iges-rs-gpt-5.6-sol-max/`.
