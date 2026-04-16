# IGES Eval — Design Document

**Author:** Matthew G. Knutson
**Status:** Draft
**Last Updated:** April 2026

---

## 1. Why this eval exists

CNCSim tests whether an agent can read a single domain spec (RS274NGC)
and produce a stateful interpreter. Early results suggest the task is
trending toward saturation for frontier models. The IGES eval was designed
as a harder doc-comprehension task that shares CNCSim's shape — hidden
pytest suite, Docker-sandboxed build, language-agnostic submission — but
pushes on three axes CNCSim doesn't cover:

1. **Spec breadth.** IGES 5.3 defines 87 entity types spread across
   ~400 pages. CNCSim's RS274 is one ~40-page spec. An agent cannot
   one-shot the whole IGES spec from memory; it has to read, index, and
   reconstruct the parser / writer entity-by-entity.
2. **Lossy round-trips.** Fixed-format ASCII with defaulted fields,
   Hollerith strings, and free-format continuation forces the agent to
   reason about *file-level* invariants (section accounting, DE pointer
   arithmetic) in addition to *entity-level* grammar. CNCSim never has
   to serialize its state back to a format.
3. **Multi-surface CLI.** The submission exposes five subcommands
   (`parse`, `write`, `query`, `eval`, `roundtrip`) that must agree on
   a shared canonical JSON schema. Internal consistency across the
   surface area is its own test — broken serialization will fail the
   round-trip suite even if parse alone is correct.

## 2. CLI contract rationale

Five subcommands rather than one interactive binary:

- **`parse` / `write`** — the core pair. Splitting read from write is
  necessary for round-trip testing; it also means tests can build
  canonical JSON in Python and exercise either half independently.
- **`query`** — a targeted single-entity extract (by DE index). Used by
  tests that want to assert on one entity's fields without walking the
  whole `entities[]` array. Cheap for the agent to implement once
  `parse` works.
- **`eval`** — geometric evaluation at a parametric coordinate. The one
  subcommand that exposes *semantics* beyond structure: an agent must
  implement curve / surface math for Line, Circular Arc, B-Spline,
  primitives etc. Without `eval`, a purely syntactic parser could pass.
- **`roundtrip`** — `parse` then `write` with no intermediate JSON file.
  Distinct from "JSON round-trip" so tests can assert file-level
  idempotence (byte-stability after one normalization pass).

JSON-on-stdin/stdout was considered and rejected. File-path I/O is
simpler for tests, survives OS-specific pipe issues (Windows+WSL
Docker was a repeated pain point during harness development; see
`AGENTS.md`), and composes with the harness's existing `pytest tmp_path`
pattern used by CNCSim.

Resolved contract decisions:

- `eval` returns a `point` plus nullable `tangent` / `normal`; higher
  derivatives are out of scope for the current harness contract.
- The `eval` comparison policy uses a single global tolerance pair:
  relative `1e-9`, absolute `1e-12` near zero.
- `query --de <n>` on an out-of-range or even DE index is invalid input
  (exit code `1`).
- The shipped docs bundle uses the transcribed
  `prompt/docs/iges-5-3-specification.md` only; the original PDF is not
  shipped without an explicit license review.
- `Evals/IGES-SDK/` remains in-repo as the upstream provenance snapshot
  for generator scripts, Catch2 tests, and reference fixtures.

## 3. IGES-JSON schema design choices

Canonical JSON schema (see `prompt/technical-requirements-prompt.md` §2)
is machine-extracted from `Evals/IGES-SDK/src/entities/*.hpp` via
`Evals/IGES-SDK/scripts/extract_entity_schemas.py`. Key choices:

- **Flatten DE fields 10/11/20.** Fields 10/20 are derived sequence
  numbers and field 11 mirrors field 1. The canonical JSON drops all
  three to eliminate the round-trip ambiguity where a user could emit
  a Directory Entry with inconsistent sequence numbers.
- **TypeScript-style schema for `entity.data`.** Agents read the schema
  section into their context; TS syntax is dense and self-documenting
  for union types (form-dependent entities).
- **Tagged-variant encoding for `FieldValue`.** The IGES Property entity
  carries heterogeneous value lists. JSON doesn't have a native
  discriminated union, so `{"kind": "int" | "real" | "string" | "bool"
  | "defaulted", "value": ...}` tags each element. Verbose, but
  unambiguous.
- **Form-dependent entities emit the full field union.** Drawing (404),
  External Reference (416), Line Font Definition (304), Ordinate
  Dimension (218), Radius Dimension (222), View (410), Surfaces of
  Revolution (190-198), and Attribute Table Definition (322) have
  per-form payload shapes. Rather than materialize `FormNUnion`
  TypeScript types, the schema lists every field and the prompt
  points agents at the spec section. A follow-up could narrow these
  to per-form literal unions if agents routinely conflate forms.

## 4. Scoping

**In scope.**

- Fixed Format (80-column ASCII) — the only format the spec requires.
- All 87 entity types listed in `technical-requirements-prompt.md`
  appendix A.
- Parse, write, query, eval, roundtrip over the three reference
  fixtures (ex1/ex2/ex3) plus Python-generated canonical JSON.

**Explicit non-goals.**

- **Binary Format** (§3.1). Binary is a compressed alternative to the
  ASCII format; supporting it roughly doubles the parser surface for
  diminishing returns. Agents are told this in the prompt.
- **Compressed Format** (§3.2). Similarly optional in the spec.
- **MACRO capability** (§5). The MACRO extension is Turing-complete and
  out of scope for a one-shot benchmark.
- **Drafting-only conformance class.** Drafting-only scope excludes
  solid / surface geometry, which we want to test.

## 5. Known spec ambiguities (deliberately not asserted)

Some corners of IGES 5.3 are under-specified; these are things an agent
could read two ways and we don't want to grade on subjective calls.

- **Byte layout of the Terminate section beyond the accounting counts.**
  §2.2.4.6 specifies the T record's field widths but is silent on
  trailing whitespace. Tests only assert the sequence counts.
- **Global section defaulted-field round-trips.** The writer may emit
  `1H,,1H;,...` explicitly rather than relying on implicit defaults.
  Tests compare semantically after a `parse → write → parse` cycle
  (see `test_roundtrip_cli.py`).
- **Hollerith case preservation.** The spec is silent on whether
  trailing blanks inside a Hollerith are significant. Tests use
  strings without trailing blanks.
- **Circular Arc parameterization for `iges eval`.** §4.3 defines the
  entity geometrically but does not prescribe a `t`-parameter
  convention. The current reference implementation treats `t` as the
  angular parameter in radians, matching what the SDK's
  `CircularArcEntity::evaluate()` does. This is *inconsistent* with
  the Line entity, where `t ∈ [0, 1]` and `C(t) = P₁ + t·(P₂ − P₁)`.
  Tests assert the ref-impl's behavior. A follow-up should either (a)
  normalize arc `t` to `[0, 1]` across the contract, or (b) document
  the per-entity-type convention in `technical-requirements-prompt.md`.

## 6. Reference implementation

`Evals/IGES/reference-implementation-cpp/` is a C++23 port of the
private `Evals/IGES-SDK/` library, trimmed to the five-subcommand CLI
plus ADL-based nlohmann::json serializers for all 87 entities. It
serves three roles:

- **Build / test target.** `pytest Evals/IGES/tests` runs the hidden
  suite against the ref-impl by default (see `conftest.py`).
- **Prompt extraction.** The entity structs are the source of truth
  for the canonical JSON schema (appendix A of the tech-requirements
  prompt); any schema change must originate in the ref-impl and
  propagate via `extract_entity_schemas.py`.
- **Fairness baseline.** The ref-impl was written independently from
  the hidden test suite to avoid coupling test assertions to
  implementation details.

Py / JS / Rust ref-impls are planned as follow-ups (PLAN.md §8).
