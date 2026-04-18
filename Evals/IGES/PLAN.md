# IGES Eval — Current Plan

This file now tracks remaining backlog, parked investigations, and
operational notes. The original port plan is complete for the current
C++ eval; detailed
landed work lives in `CHANGELOG.md` and git history.

## Status Snapshot

- Current repo state: `v1.0.13`
- Core C++ eval scope is complete through sections 0-7 below.
- Latest local validation (2026-04-16):
  - `uv run pytest Evals/IGES/tests --language=cpp -q` -> `219 passed`
  - `uv run ruff check` -> clean
  - `uv run pyright` -> clean
- Real-agent baseline recorded:
  - `iges` / `claude-code` / `claude-opus-4-6`
  - `43/93` (46.24%), `exit_reason: "completed"`
  - no harness, auth, or rate-limit issue

---

## 0. Naming & Registration

Complete for the current C++ eval. No active TODOs in this section.

## 1. CLI Contract

Complete for the current C++ eval. The active contract lives in
`prompt/technical-requirements-prompt.md`.

## 2. Canonical IGES-JSON Schema

Complete for the current C++ eval. No active schema TODOs remain.

## 3. Prompt Authoring

Complete for the current C++ eval. The docs bundle ships the Markdown
spec only; `IGES5-3.pdf` remains out of scope unless the license
position changes.

## 4. Reference Implementation (C++)

Complete for the current C++ eval. The current C++ ref-impl passes the
full IGES pytest suite.

## 5. Tests (Catch2 -> Python CLI)

Complete for the current C++ eval. The suite covers the CLI-observable
subset of the SDK tests rather than a 1:1 port of every library-level
Catch2 case.

## 6. Eval Design Doc

Complete. Resolved contract decisions live in `IGES-Design.md`.

## 7. End-to-End Validation

Complete. Current validation status is recorded in the snapshot above.

## 8. Follow-up (post-1.0.0)

- [ ] `reference-implementation-py/` — Python ref-impl. Register
      `iges-py`, wire the language-selection path, and make the
      implementation pass `Evals/IGES/tests --language=py`.
- [ ] `reference-implementation-js/` — JavaScript ref-impl. Register
      `iges-js`, wire the language-selection path, and make the
      implementation pass the IGES test suite.
- [ ] `reference-implementation-rs/` — Rust ref-impl. Register
      `iges-rs`, wire the language-selection path, and make the
      implementation pass the IGES test suite.
- [ ] Fuzz / pathological-input coverage — add a `hypothesis`-backed
      property test that feeds random 80-column ASCII blobs to
      `iges parse` and asserts the parser never exits 2 (internal
      error). Requires adding `hypothesis` to the test dependency set
      and tuning the generator for useful coverage. Deferred from the
      Round 2 review as a separate infrastructure investment.

Review-surfaced gaps intentionally left unresolved:

- [ ] §2.2.3 numeric-field-boundary rule: "A numeric field shall end at
      least one column prior to the last data column." No known failing
      implementation pattern; defensive test only. Skip unless a concrete
      regression surfaces.
- [ ] Tangent / normal value checks for `iges eval`: TR §1.5 declares
      these nullable with no value contract. Adding value assertions
      would create a new contract rather than enforce an existing one;
      revisit only if a stricter agent-grading contract is adopted.
- [ ] Broader form coverage for Type 106 Forms 13/20/21/31-38/40 and
      Type 402 Forms 3-19. Same parser/writer code paths as covered
      forms; marginal signal is low.

---

## Resolved Questions

- [x] `IGES5-3.pdf` stays out of the shipped docs bundle pending explicit
      license review; the Markdown transcription is canonical.
- [x] `iges eval` returns `point` plus nullable `tangent` / `normal`;
      higher derivatives remain out of scope.
- [x] Tolerance policy is global: relative `1e-9`, absolute `1e-12`
      near zero.
- [x] `query --de <n>` on an out-of-range or invalid DE index exits `1`.
- [x] Native per-entity parameterization is the eval contract; see
      `IGES-Design.md` and
      `codex-conversations/2026-04-15-08-47-iges-arc-t-convention.md`
      for the rationale.
- [x] Do not split `iges-lite` back out for now. The current agent
      baseline does not justify a fallback variant.

## Known Issues / Investigations

Parked items that are not blockers for the current C++ eval.

- [ ] **Docker build via `run_in_background` silently dropped output**
      (2026-04-14). Observed while backgrounding a
      `wsl.exe ... docker run ...` build: the container never appeared in
      `docker ps`, the redirected log file was zero bytes, and the agent
      had no signal the build had died. Re-running the same command in
      the foreground succeeded. Suspected cause: Windows -> WSL -> Docker
      stdout handoff breaks when the outer shell exits immediately. Next
      step: reproduce deterministically, then decide whether to patch the
      wrapper or forbid backgrounding WSL Docker commands.

- [ ] **`ex2.iges` roundtrip is not byte-identical**
      The current writer normalizes defaulted Global delimiters, expands
      2-digit years, and zero-pads status codes. Those diffs are
      spec-legal; semantic roundtrip is already clean on
      `ex1` / `ex2` / `ex3`. Tests should continue to assert semantic
      equivalence unless we explicitly decide to chase byte identity.

## Dev Notes

Operational notes worth keeping visible for future C++ ref-impl work:

- Regenerating `reference-implementation-cpp/src/json/dispatch.cpp`
  from `Evals/IGES-SDK/scripts/generate_dispatch.py` on Windows should
  use the old safe flow:
  `python Evals/IGES-SDK/scripts/generate_dispatch.py > Evals/IGES/reference-implementation-cpp/src/json/dispatch.cpp`
  followed by LF normalization of the generated file. The older port
  work hit CRLF / output-corruption issues when regenerating via
  redirected stdout.
- Evaluator architecture splits in two:
  self-contained evaluators are auto-detected by
  `generate_dispatch.py`, while resolver-using evaluators need
  hand-written helpers in `src/json/eval_helpers.{hpp,cpp}` plus a
  `RESOLVER_USING[type] = (stem, kind)` registration entry.
- The usual extension loop is: update the SDK-side entity/header or
  helper, sync the change into `reference-implementation-cpp/`,
  regenerate `dispatch.cpp`, run the IGES pytest suite plus
  Ruff/Pyright as needed, and stage only IGES-related files.
- The writer uses `%.15g` formatting. Tests that touch `pi` exactly can
  fail on last-bit rounding; prefer padded numeric fixtures over changing
  writer precision.
- `curve_native_span()` in
  `reference-implementation-cpp/src/json/eval_helpers.cpp` only covers
  the currently needed curve families. Extend it if future resolver-using
  evaluators depend on additional curve types.
- `Vec3` lives in `entities/entity.hpp`, not `types.hpp`. New helper code
  that uses `Vec3` should include the entity header directly.
- Clang LSP diagnostics can lag the built tree. Trust the pytest run over
  stale editor squiggles when they disagree.

## Historical Note

The detailed commit-by-commit rollout, eval-expansion notes, and the
completed per-entity checklist were intentionally removed from this live
plan. Use `CHANGELOG.md` and git history for the landed record.
