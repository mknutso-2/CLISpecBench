# IGES

IGES 5.3 file format eval for CLISpecBench. Agents receive the IGES 5.3
specification and must produce a working tool that can parse, query, evaluate,
and write conforming IGES files — the 80-column fixed-format CAD interchange
format used across mechanical CAD systems since 1980.

> **Status.** Active eval. The benchmark ships the IGES prompt, pytest suite,
> and C++/Python/JavaScript reference implementations. The harness
> exposes explicit language task IDs such as `iges-cpp`, `iges-py`, `iges-js`,
> and `iges-rs`; reference implementations are available for the languages
> listed in `tests/conftest.py`.

## Why this eval

RS274 is the benchmark's first eval and has proven valuable, but frontier
agents are beginning to saturate it. IGES is intended as a harder
spec-comprehension challenge along the same axis:

- **Dense authoritative spec** — ~8.3k lines of formal fixed-format grammar,
  87 distinct entity types spanning curves, surfaces, CSG, B-Rep topology,
  annotation, and transformations.
- **Deterministic round-trip scoring** — every IGES file has a canonical
  structure; "parse then write then parse" is a natural pass/fail signal with
  fine-grained partial credit per entity type.
- **Low training contamination** — IGES is widely cited but rarely
  re-implemented from scratch; there is no saturated public corpus of
  reference implementations in agent training data.

Unlike RS274, there is no "lite" variant. Agents are asked for full
87-entity coverage.

## Directory Structure

```
prompt/
  base-prompt.md                    # Domain-expert persona prompt
  technical-requirements-prompt.md  # CLI contract + canonical IGES-JSON schema
  docs/
    iges-5-3-specification.md       # Full IGES 5.3 specification (transcribed)
    figures/                        # 85 specification figures
tests/
  conftest.py                       # Build fixtures (re-exports from pytest_plugin)
  iges_support.py                   # Test helpers (run CLI, build test files)
  test_*.py                         # Python pytest suite
  data/
    ex1.iges / ex2.iges / ex3.iges  # Real-world reference fixtures
reference-implementation-cpp/
  CMakeLists.txt                    # CMake project producing `iges` executable
  src/                              # C++23 reference solution (adapted from IGES-SDK)
reference-implementation-js/        # JavaScript reference implementation
reference-implementation-py/        # Python reference implementation
IGES-Design.md                      # Eval design rationale
CHANGELOG.md                        # Per-eval change log
VERSION                             # Semver for this eval
```

## CLI Contract

The agent's submission is a single binary (default name `iges`) supporting
five subcommands. All emit JSON, all write both on success and error, all
follow RS274's exit-code convention (0 success, 1 invalid input, 2 internal
error).

| Subcommand | Purpose |
|---|---|
| `iges parse --input <file.iges> --output <out.json>` | Parse to canonical IGES-JSON |
| `iges write --input <file.json> --output <out.iges>` | Emit conforming 80-column IGES |
| `iges query --input <file.iges> --de <n> --output <entity.json>` | Extract one entity by DE index |
| `iges eval --input <file.iges> --de <n> --t <f> --output <point.json>` | Evaluate a parametric entity at a curve/surface parameter |
| `iges roundtrip --input <file.iges> --output <out.iges>` | Read then write; idempotence check |

See `prompt/technical-requirements-prompt.md` for the full contract, including
the canonical IGES-JSON schema across all 87 entity types.

## What IGES Evaluates

The pytest suite scores along several independent surfaces:

1. **File-format correctness** — Start/Global/Terminate section formatting,
   Directory Entry layout, Parameter Data line splitting at 64 columns,
   Hollerith string encoding, free-format delimiters.
2. **Per-entity parse correctness** — for each of 87 entity types, minimal
   synthetic files are parsed via `iges query` and every field is asserted.
3. **Per-entity writer correctness** — entity JSON is serialized via
   `iges write`, then parsed back, and fields are asserted preserved.
4. **Round-trip fidelity** — the three reference fixtures (`ex1`/`ex2`/`ex3`)
   must round-trip with entity counts and key fields preserved.
5. **Geometric evaluation** — B-spline curve/surface evaluation, circular
   arc parameterization, composite curve evaluation (via `iges eval`).
6. **Malformed-input handling** — deliberately broken inputs must exit 1
   with a diagnostic citing a spec section (`§X.Y`).
7. **Validation** — structurally-valid-but-semantically-broken files (e.g.
   invalid B-spline knot vector lengths) must be flagged.

## Non-Goals

Carried over from IGES-SDK's original scope:

- **Binary Format (Appendix H)** — deprecated, not tested.
- **MACRO entities (Type 306, 600+)** — not tested.
- **Rendering/visualization** — no graphical output required.
- **Compressed Format** — 80-column fixed format only.

## Contract Discipline

Per `AGENTS.md` and this repo's `CLAUDE.md`:

- `iges-5-3-specification.md` is the **source of truth**. Do not edit it
  unless explicitly asked — same rule as `RS274NGC.md` for RS274.
- `technical-requirements-prompt.md` is a **harness contract**, not a
  behavior spec. Only edit it when the CLI contract changes.
- Tests follow the **three-tier invariant policy** inherited from
  [IGES-SDK ARCHITECTURE.md §2.3](../IGES-SDK/ARCHITECTURE.md): spec says
  it clearly → test it; spec ambiguous but format breaks without it → test
  it with a comment; spec ambiguous and format works either way → do not
  test. Every test cites the `§` section it derives from.
- Every ref-impl bug must have an eval test that enforces the correct
  behavior.

## Task IDs

- `iges-cpp` — C++23 target
- `iges-py` — Python target
- `iges-js` — JavaScript target
- `iges-rs` — Rust target

## References

- [IGES-SDK](../IGES-SDK) — the upstream C++23 library being ported into
  this eval. Will remain as a snapshot; no longer developed independently
  once the port completes.
- [RS274](../RS274) — the sibling eval whose harness conventions this
  eval mirrors (`conftest.py` pattern, multi-language ref-impl layout,
  versioning rules).
- [Eval-Design.md](../../docs/design/Eval-Design.md) — benchmark-level design.
