# BibTeX Eval Changelog

## v1.0.0 — 2026-04-22

**Authoritative-spec release.** Previous versions shipped a
clean-room ~500-line summary of BibTeX 0.99c. v1.0 reverses the
authority relationship: the agent now receives Oren Patashnik's
original documentation and source, and the clean-room file is
demoted to a navigation index.

Test count: **258** (was 107).

**New docs structure** ([`prompt/docs/`](prompt/docs/)):

- `docs/authoritative/btxdoc.tex` — *BIBTEXing* (~42 KB), the
  user-facing guide shipped with BibTeX.
- `docs/authoritative/btxhak.tex` — *Designing BibTeX Styles*
  (~26 KB), the style-language reference.
- `docs/authoritative/bibtex.web` — the complete BibTeX 0.99c
  implementation in literate Pascal (~384 KB), ultimate authority
  on stack discipline, built-in semantics, and output-buffer rules.
- `docs/authoritative/plain.bst`, `alpha.bst`, `unsrt.bst`,
  `abbrv.bst` — the four canonical reference styles. These are
  executed as part of the test suite: against a reference `.bib`,
  their `.bbl` output must match BibTeX 0.99c byte-exactly.
- `docs/summary.md` — reworked from the former clean-room spec
  into a reading index; explicitly notes the authoritative sources
  govern when they disagree.
- `docs/LICENSES.md` — preserves the Knuth License notices.

**Contract changes**:

- `base-prompt.md` reverses the "docs spec is source of truth"
  language: authoritative sources are primary, summary.md is a
  navigation aid. The byte-exact match claim is reinstated — the
  agent *is* expected to produce BibTeX 0.99c's output when
  running `plain.bst` / `alpha.bst` / `unsrt.bst` / `abbrv.bst`
  against a reference `.bib`.
- `technical-requirements-prompt.md` adds several new warning
  kinds and log keys for the expanded coverage. Top-level log key
  order is no longer asserted.

**Test-suite expansion** — targeting exhaustive coverage of
Patashnik's authoritative surface:

- `test_reference_styles.py` (new): end-to-end byte-exact `.bbl`
  parity. For each of `plain.bst` / `alpha.bst` / `unsrt.bst` /
  `abbrv.bst`, run the submission against a curated reference
  `.bib` and compare the produced `.bbl` against a known-good
  artifact generated from BibTeX 0.99c itself. This is the single
  largest discriminator.
- `test_name_grammar_exhaustive.py` (new): every Form 1/2/3
  corner from btxhak §2, including tied tokens, brace-protected
  von, all-caps heads, Jr variants, mixed ties.
- `test_builtins_exhaustive.py` (new): every one of the 37
  built-ins individually, with stack-type checking, edge inputs
  (empty string, zero integer, missing field, maximum-length
  string), and the interactions between them.
- `test_output_buffer.py` (new): 79-column wrap edge cases — long
  unbroken tokens, wrap at exactly 79, cross-boundary strings,
  line containing `\n` mid-string, empty `write$`.
- `test_crossref_corners.py` (new): long crossref chains, cycles,
  case preservation under case-insensitive lookup.

**Reference implementation** expanded for `width$` with real CMR-10
widths (replacing the v0.3 approximation), `change.case$` recursion
through nested LaTeX accent macros, full `purify$` semantics with
LaTeX control-sequence handling, and the output-buffer wrap rules
from `bibtex.web` §15.

## v0.3.0 — 2026-04-22

Response to the adversarial Codex review (transcript:
`codex-conversations/2026-04-21-22-05-adversarial-bibtex-review.md`).
Focus: fix contract inconsistency between base-prompt and CHANGELOG,
codify the approximations the eval accepts, split test-probe coupling,
add a more realistic `.aux` input flow.

**Spec changes** ([`prompt/docs/bibtex-spec.md`](prompt/docs/bibtex-spec.md)):

- Added **§8 "Approximations and bounded divergences from BibTeX
  0.99c"**, which pins the behavior the eval actually tests:
  - §8.1 `width$`: deterministic monotone string-width score with
    fixed weights (alphanumeric=500, space=250, punct=300). Not
    claimed to match cmr10 byte-for-byte.
  - §8.2 `change.case$`: brace protection at depth 1 is required;
    deeper LaTeX-accent case-change recursion is NOT required and
    NOT tested.
  - §8.3 `purify$`: brace-control-sequence simplification pinned.
  - §8.4 `text.length$`: `{\cmd...}` counts as 1.
  - §8.5 `.bbl` output is semantic, not byte-exact with historic
    BibTeX.

**Prompt changes**:

- [`base-prompt.md`](prompt/base-prompt.md) reworded to match §8:
  removed the "byte-for-byte match BibTeX output" language that
  contradicted the CHANGELOG's "known gaps." The agent is now told
  explicitly that the `docs/` spec is the source of truth and that
  a few output corners are approximated.
- [`technical-requirements-prompt.md`](prompt/technical-requirements-prompt.md)
  adds `--aux <path>` as an alternative to `--cites`: the tool now
  accepts LaTeX `.aux` files and extracts `\citation{...}` keys. This
  closes the adversarial review's "persona realism" gap — real
  LaTeX users run BibTeX against `.aux`, not a hand-written cite
  list. `--cites` remains supported.

**Reference implementation**:

- [`main.cpp`](reference-implementation-cpp/src/main.cpp) adds
  `parse_aux()` alongside `parse_cites()`. When both flags are
  given, cites come first, aux second, then the combined list is
  deduplicated (existing v0.2 behavior).

**Test suite restructuring** — addresses the cascade-risk finding:

- [`conftest.py`](tests/conftest.py) **splits the single probe**
  into four narrow single-purpose probes: `PROBE_STYLE_FIELDS`
  (entry field dump), `PROBE_STYLE_NAMES` (name decomposition via
  `format.name$`), `PROBE_STYLE_PREAMBLE`, and `PROBE_STYLE_KEYS`.
  Parser helpers are per-probe (`parse_field_dump`, `parse_name_dump`).
- [`test_direct_bbl.py`](tests/test_direct_bbl.py) (new, 11 tests):
  direct `.bbl` assertions that bypass the probe layer entirely.
  Covers `empty$`/`missing$` isolation, 79-column wrap stress, log
  JSON correctness, `--aux` input flow, `call.type$` dispatch.
  Each test uses its own minimal `.bst` — one bug doesn't cascade.
- [`test_library_divergence.py`](tests/test_library_divergence.py)
  (new, 10 tests): adversarial fixtures targeting corners where
  public `.bib` parsers and `.bst` interpreters diverge — name
  grammar with brace-protected von, tied tokens, `and` in quoted
  strings, macro redefinition order, forward references, crossref
  case preservation, `purify$` / `change.case$` edges, cross-type
  `=` comparison.

Total test count: **107** (was 81).

## v0.2.0 — 2026-04-21

**Full-spec eval.** v0.1 scoped the eval to `.bib` parsing + crossref + name
grammar, deferring the `.bst` stack-language interpreter that was the
original discrimination pitch. v0.2 is the complete BibTeX 0.99c eval:
the agent must implement the full `.bst` style-language interpreter
with all required built-ins and produce `.bbl` output.

**Breaking contract changes** — incompatible with v0.1:

- **New CLI**: `--bib FILE --style FILE --cites FILE --output FILE
  [--log FILE]`. `--style` is new (required); `--log` is new
  (optional, JSON). The output file is now the `.bbl` text, not a
  JSON parse report.
- **New docs corpus**
  ([`prompt/docs/bibtex-spec.md`](prompt/docs/bibtex-spec.md)):
  - Added §3 "The `.bst` style file language": stack machine,
    top-level commands (`ENTRY`, `STRINGS`, `INTEGERS`, `FUNCTION`,
    `MACRO`, `READ`, `EXECUTE`, `ITERATE`, `REVERSE`, `SORT`), value
    types, entry scope, 37 built-in functions.
  - Added §5 "Output files": `.bbl` content, optional JSON `--log`,
    warning kinds.
  - Updated §1.5 (month macros expand to full names per btxdoc, e.g.
    `January` not `Jan.`).
  - Removed §5 "JSON output schema" from v0.1 (which has been
    replaced by §5 "Output files" describing `.bbl` + JSON log).
- **New base prompt** — describes the full BibTeX workflow (bib +
  style + cites → bbl).

**Test suite rewritten.** v0.1 tests asserted on a JSON parse report.
v0.2 tests drive observation through probe `.bst` files that dump
entry fields and author-name decompositions as structured `.bbl`
text. 81 tests total across:

- `test_bib_parsing.py` — `.bib` parsing via PROBE_STYLE_FIELDS.
- `test_bst_language.py` — top-level commands and ~25 built-ins
  exercised with minimal `.bst` programs.
- `test_names.py` — author-name grammar via `format.name$` probe.
- `test_errors.py` — exit-code-1 cases for malformed `.bib` / `.bst`.
- `test_build.py` — the build smoke test.

**Reference implementation** adds three new modules:
`bst_parser.cpp`, `bst_interpreter.cpp`, and a rewritten
`json_writer.cpp` for the new error/log schema. Total C++ LOC grew
from ~1,000 to ~1,900.

**Deferred still** (not required for v0.2 passes, may return in
v0.3+):

- Byte-exact `.bbl` output compatibility with real BibTeX 0.99c on
  every edge case (our spec's line-wrapping and `purify$` /
  `change.case$` implementations are defined but may differ from
  BibTeX in pathological corners; tests avoid those).
- LaTeX accent-macro case handling inside `change.case$` beyond the
  simple brace-protection rule.

## v0.1.1 — 2026-04-20

Fixes from Codex design review. No breaking changes to the CLI contract
or JSON schema shape; tests and spec clarified.

**Spec changes** ([`prompt/docs/bibtex-spec.md`](prompt/docs/bibtex-spec.md)):

- §4.1 Form 1: clarified the rule in normative language (first
  lowercase / last lowercase index-based) rather than the
  right-to-left prose in v0.1.0.
- §4.2 Form 2: pinned down the behavior of uppercase tokens *before*
  the first lowercase in the head. They prepend to `Last`. New
  example: `"Foo van der Pol, Charles"` → Last=`Foo Pol`.
- §4.4 Three-or-more-commas: removed the `malformed_name` warning
  requirement. The tool accepts silently and joins post-second-comma
  text into First.
- §5.4 Warning kinds: removed `malformed_name`; clarified that
  `key` / `field` metadata fields are optional; clarified that
  `crossref_cycle` is only required for immediate two-entry cycles.
- §5.4 Warning ordering: removed the ordering requirement (order is
  unspecified).
- §7 Error handling: removed the soft-recovery clause. All malformed
  input is now a hard error, removing an ambiguity Codex flagged in
  the v0.1.0 spec.

**Reference implementation** ([`reference-implementation-cpp/src/names.cpp`](reference-implementation-cpp/src/names.cpp)):

- Fixed Form 2/3 head decomposition. Leading uppercase tokens before
  the first lowercase are now prepended to `Last` instead of being
  silently dropped.

**Test suite**:

- Added 2 new name tests covering the Form 2 leading-caps and
  all-caps-head cases (test coverage 84 → 86 tests).
- Hardened `conftest.find_entry` / `fields_of` / new `warnings_of`
  helpers to use `.get()` with clear error messages, so a
  top-level-schema failure reports once rather than cascading.
- Loosened `test_unresolved_macro_warning_includes_field` and
  `test_unresolved_crossref_warning_names_key` so they no longer
  assert on warning metadata values (spec only requires `kind`).

## v0.1.0 — 2026-04-20

Initial eval release. Scope: `.bib` database parsing, `@STRING` macro
resolution, `@PREAMBLE` concatenation, `crossref` inheritance, and
BibTeX 0.99c author-name grammar parsing (the `von`/`Last`/`Jr`/`First`
decomposition). Output is canonical JSON listing the subset of cited
entries.

**Deferred to v0.2+** (documented in `README.md`):

- `.bst` style-language execution (the stack machine with 37 built-ins).
- `.bbl` output emission.
- LaTeX accent macro handling inside author names beyond the minimal
  set required by the name grammar itself.

The first-pass proposal in [`Evals/EVAL_CANDIDATE_DISCUSSION.md`](../EVAL_CANDIDATE_DISCUSSION.md)
pitched this eval as `.bst` execution being the low-contamination core.
v0.1 is a narrower first step: it validates that the prompt / docs /
tests / reference-implementation pipeline works end-to-end on the
domain before committing to the larger v0.2 scope. The author-name
grammar alone is a genuine spec-comprehension test — no JSON-emitting
`.bib` parser in the public OSS landscape implements it correctly in
all the spec's corner cases (ties with `~`, multi-`and`, Jr variants,
brace-protected capitalization).
