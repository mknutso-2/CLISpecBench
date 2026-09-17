# IGES 1.0.19 appendix fixtures and scoring weights — 2026-09-17

Test suite SHA-256:
`cf4e0ac576e143e8c6ece701936c0a9a11f99e05f73adbb2bd1a387cb72e0219`.
All four assembled model inputs remain unchanged. Generated sources, original
grades, transcripts and usage are immutable; this revision changes hidden tests.

## Evidence and authority

Astra Max Rust `e81a9c23-e06f-4fe7-8a1e-e39e9941c058` completed normally at
245/261 under 1.0.18. Fifteen failures repeated the initial parse of three
appendix files five times each. They did not establish fifteen distinct bugs.

- `ex2.iges` and `ex3.iges` used space-padded Status Number fields. Supplied
  Table 2 and §2.2.4.4.9 explicitly prohibit spaces in that eight-digit field.
  The hidden copies now zero-pad 90 and 109 fields respectively, preserving
  every numeric value. Rejecting the old spelling was not an implementation
  defect. A status-only diagnostic trial let all five ex3 observations pass.
- The repaired ex2 then exposed a public conflict: its 90 positive Structure
  values are permitted and ignored under §2.2.4.4.3, while the technical JSON
  schema describes zero or negative pointers. These legacy markers now become
  zero, valid under both readings. Their ignored semantics are preserved.
  The conflict is recorded for later public clarification, not resolved by
  imposing a new requirement on saved submissions.
- ex1 is unchanged. Its Type412 has LC=0 and omits trailing DDF. §§2.2.2.1,
  2.2.3 and 4.136 permit the implicit zero and an empty positions list. Rust
  advances past the defaulted scalar, then rejects the zero-length array
  because its generic availability check compares that position with token
  length. This is a real defect, distinct from accepting illegal `0H`.

A byte-level audit reconstructs each changed file from the prior committed
copy using only the listed Status/Structure replacements. Line widths, counts,
Global/Parameter data, other DE fields and all ex1 bytes are unchanged.
Hashes and counts are in `IGES-1.0.19-checks.json`; the full field manifest and
diagnostic reports are in `work/non-rs274-audit/iges-1.0.19-validation/`.

## Explicit scoring change

The previous six parse cases and nine roundtrip cases become three named
integration cases, one per appendix file. Every former observation remains:
the same start/global values, entity type mix and counts, entity data/type/form
preservation, and byte idempotence. The semantic data comparison now uses the
already published §3 real tolerance (relative 1e-12 / absolute 1e-15), retaining
exact discrete comparisons. Byte idempotence stays exact.

The denominator changes **261 → 249**. This deliberately reduces the weight of
the shared workflow; it is not just fixture normalization, and percentages from
the two versions should not be directly compared as an implementation gain.
The other 246 cases remain unchanged. Focused tests still measure component
behavior. Integration dependencies remain within each file and may span files;
even the revised failed-case count is not an independent-bug count.

## Validation

All execution is sequential in offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
using disposable copies. Python, JavaScript and C++ references each pass
**249/249**. Ruff formatting/checks and strict Pyright pass with the explicit
repository virtual environment and test import path.

Independent reviewer `resume_single_review` verified the complete diff,
reconstructed all changed fixture bytes, checked the preserved observations
and report hashes, and found no blocking correctness or policy issue. It
confirmed that the denominator change is an explicit weighting correction.

Four disposable Python-reference controls verify the retained observations:

| Deliberate defect | Focused integration outcome |
|---|---|
| Reject only ex1 before parsing | Exactly one failure; other two pass |
| Remove one repeated entity from parse output | All three fail at entity count |
| Alter one real Parameter value during writing | All three fail at semantic data comparison |
| Add a Start-text prefix on every roundtrip | All three fail at byte idempotence |

The unchanged Rust source passes **247/249** in both diagnostic validation and
the official committed-rubric regrade: ex2/ex3 now pass; `0H` and ex1's
trailing-default/empty-array defect remain. Independent content review
corroborates its release build, nine Rust unit tests and 232 synthetic CLI
checks; those checks did not establish external-corpus conformance.

## Official saved-source regrades

All four regrades used the committed rubric and pinned image, sequentially.
They are published under `regraded_results/iges/1.0.19/gpt-6-astra_max/`.
Original result/source hashes and complete previous publications are preserved.
All 246 retained node outcomes match each submission's preceding 1.0.18 grade.

| Astra Max | Previous 1.0.18 | Current 1.0.19 | Remaining failures |
|---|---:|---:|---|
| Python | 261/261 | 249/249 | None |
| C++ | 259/261 | 247/249 | `0H` reader and writer |
| JavaScript | 260/261 | 248/249 | `0H` reader |
| Rust | 245/261 | 247/249 | `0H` reader and ex1 trailing defaults |

For C++, JavaScript and Python the same failures remain with lower integration
weight. Rust additionally loses the invalid/conflicted ex2/ex3 prerequisites
and four duplicate ex1 penalties. No generated implementation changed.
Rust generation accounting matches its complete session: 56 underlying tool
calls, 23,383 reasoning tokens and a $13.159838 API-equivalent estimate.
Regrading changed no generation accounting and made no model calls.
