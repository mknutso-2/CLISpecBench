# IGES 1.0.20 canonical View fixtures — 2026-09-26

Test-suite SHA-256:
`22c97f88646c36e412dbe016f8c7359584338b0cde343c20bab2abcc67339186`.
This is a hidden-test correction. All 28 assembled collection prompts, all
IGES reference implementations and all saved generated sources are unchanged.
The suite retains the same **249 case IDs and assertions**.

## Evidence and scope

Sol Max C++ `3b6e00d7-4911-41ce-915d-2309db916a24` completed voluntarily at
241/249 under 1.0.19. Four failures arose before the intended observations:

- The DE-pointer, Drawing Form 0 and View Form 0 fixtures supplied nonzero
  unused perspective vectors. A strict writer rejected these noncanonical
  inputs before pointer/Drawing/View behavior could be assessed.
- The Drawing Form 1 fixture's supporting orthographic Views omitted required
  canonical fields, masking its angle and annotation observations.

Technical requirements lines 630–649 require unused-form fields to remain
present with defaults; Appendix A Type 410 describes the mutually exclusive
wire fields and fixed Vec3 shape. Fixtures now use complete zero-valued Vec3
and scalar defaults. Six vector literals change across three cases, and the
fourth gains the missing fields. This imposes no new requirement to accept or
reject nondefault unused data. Comments cite the existing public authority.
The shared View prerequisite explains four observations, not four model bugs.

Two public clarifications remain deferred: generic array-default wording versus
fixed Vec3 shape, and the benchmark's explicit Type 130 direct-displacement
rule versus the physical IGES normal-cross-tangent formula. No public content
changes or retroactive new requirements are included here.

## Validation

The unchanged C++ reference passes **249/249** in offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
Ruff format/check and strict Pyright pass. AST comparisons preserve every
assertion and every other Python function; independent review counts all 696
assertions unchanged and approves the four-case scope.

Independent pure-data observation controls pass all four legal baselines and
reject eleven targeted corruptions: each DE pointer, Drawing count/reference,
View number/scale/clips, and Drawing Form 1 reference/angle/annotations. These
controls establish assertion sensitivity, not serialization correctness; Docker
reference and retained-source grades provide separate execution evidence.

The original submission review also reproduced ex1's exact parser diagnostic
in the pinned Docker image: missing parameter field scale at line 54. Type 408
allows that trailing field to default to 1. Three offset observations reflect
one mismatch with the explicit benchmark-specific direct-direction rule.
They are not three independent geometry defects, and the model's formula does
match the underlying physical IGES specification.

Five retained sources were regraded sequentially under rubric commit `09dfecc`
and the pinned image. Every source retains all 245 untouched outcomes, all
249 node IDs, and immutable original source/result/session/accounting artifacts.

| Saved submission | 1.0.19 | 1.0.20 |
|---|---:|---:|
| Astra Max C++ | 247/249 | 247/249 |
| Astra Max Python | 249/249 | 249/249 |
| Astra Max JavaScript | 248/249 | 248/249 |
| Astra Max Rust | 247/249 | 247/249 |
| Sol Max C++ | 241/249 | 245/249 |

Sol gains exactly the four repaired fixture cases; all prior Astra scores and
all four repaired-case outcomes for Astra are unchanged. The four remaining
Sol failures represent two defect families described above. Original grades
and complete prior publications remain in the audit chain. Regrading adds no
model calls or inference cost. Independent corrected-grade review and the full dashboard migration checks
passed. The dashboards contain **1,846 runs and 1,174,102 test rows**; all
unrelated rows are preserved except expected run-index shifts. Unique test
identities remain 20,550. Build/validation peak at 37,156/51,492 KiB RSS under
512 MiB caps, with zero swaps. All 65 validator controls pass. Exact prior
payloads are archived; 2,844 unrelated publication/audit files remain unchanged.
See [machine-readable checks](IGES-1.0.20-checks.json).

Local evidence: `work/non-rs274-audit/iges-1.0.20-validation/`, including
`baseline.json`, `patch-baseline.json`, `patch-review.json`, reference report,
observation controls and prior-publication snapshots. Raw source/session review
is under `work/non-rs274-audit/runs/iges-cpp-gpt-5.6-sol-max/`.
