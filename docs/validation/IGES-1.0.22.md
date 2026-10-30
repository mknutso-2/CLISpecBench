# IGES 1.0.22 eval flag order — 2026-10-29

Suite SHA-256:
`8ce1f801b1f7fa1cfecb36cce7f040b5d6d77cbc0de39c645953ac4e67c017ac`
(1.0.21: `ec84b63fbbbbf9a90c8d6e4a88cb5e29ab2e93424e7f25f96176569451382135`).
All 249 case IDs and assertions, model-visible prompts and docs, reference
implementations and saved generated sources are unchanged. This repair changes
the argument order of one hidden helper.

## Authority and evidence

Technical requirements §1 states that every subcommand takes a final
`--output <path>` flag and shows
`iges eval --input <file.iges> --de <n> --t <f> [--s <f>] --output <point.json>`.
The shared hidden helper `evaluate_entity` built `... --t <f> --output <path>`
and then appended `--s <f>`, so every two-parameter evaluation contradicted the
documented synopsis. Every other hidden invocation already ends with `--output`.

GPT-6.1 Terra Max JavaScript `9e445c9f-5074-493f-929b-2a96287773d6` (unpublished,
graded 227/249 under frozen 1.0.21) rejects any invocation whose penultimate
argument is not `--output`, exactly as the contract describes. That conforming
check failed all 20 surface-evaluation cases before a point was computed.

The helper now emits `--s` before `--output`. The prompt is not relaxed to
accept any flag order: the documented order was already unambiguous, and
leaving model-visible text unchanged keeps every earlier generation under the
same instructions. No behavior, assertion or score weighting changes.

Instrumenting the helper identifies the 21 cases that pass `--s`: 20 surface
evaluations and `test_curve_eval_with_s_is_rejected`.

## Validation

All three references pass **249/249** offline in grader image
`sha256:94753907091d3b0c6a08785521685eddc077fd622d65d5ee96e60b9ad2ea27cf`
(C++, Python and JavaScript). On the Windows host the C++ and Python
references reach 245/249; the same four reader-fixture key lookups fail under
the unmodified 1.0.21 suite too, before any CLI call, because trigonometric
fixture keys differ on that host. Ruff check/format and strict Pyright pass.

## Saved-source regrades

Every locally saved IGES source was regraded with `clispecbench regrade` in the
same image twice: under a clean 1.0.21 checkout and under the 1.0.22 working
tree. Pairing removes earlier rubric changes from the comparison, including for
sources generated under 1.0.15.

| Saved sources | Generated under | Compared |
|---|---|---:|
| Published | 1.0.15 | 194 |
| Published | 1.0.21 | 64 |
| Unpublished | 1.0.15 | 53 |
| Unpublished | 1.0.21 | 23 |

All 334 pairs completed. Only one source changes, and only on the intended
cases; no other outcome differs in any pair.

| Submission | 1.0.21 | 1.0.22 |
|---|---:|---:|
| GPT-6.1 Terra Max JavaScript (unpublished) | 227/249 | 247/249 |

No published score changes. Twelve published 1.0.21 rows also pass no surface
evaluation, but their outcomes are identical under both orders, so those are
real defects rather than this mismatch. The eight published Astra/Sol Max rows
without local source already pass all 20 surface cases. One 1.0.0-era
unpublished run has no run UID and cannot be regraded. Three Rust sources
exceeded Windows path limits in the batch output directory and were regraded
again with shorter paths; their outcomes are identical.

The 1.0.22 grades were taken from an uncommitted working tree; the suite SHA
above is its content hash. No publication or audit file was changed.
[Machine-readable evidence](IGES-1.0.22-checks.json) records the per-source
comparisons.
