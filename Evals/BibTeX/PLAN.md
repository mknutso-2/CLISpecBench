# BibTeX Eval — Test Surface Expansion Plan

Post-v1.0 plan to push the BibTeX eval from 258 tests to ~360 by
filling gaps identified in the Codex adversarial review of v1.0
plus natural extensions of the `.bst` stack machine and `.bib`
parser surface that are already formally in-scope but lightly
probed.

**Baseline**: 258 tests, 100% pass vs. the cpp reference impl.
**Target**: ~360 tests. **Branch**: `bibtex-test-expansion`.

## Guiding principles

- Every new test is self-contained — one bug, one failure.
- Tests must derive unambiguously from the authoritative sources
  under `prompt/docs/authoritative/` (`btxdoc.tex`, `btxhak.tex`,
  `bibtex.web`).
- No test should assert behavior that `summary.md` §8 explicitly
  designates as an approximation — those are exclusion zones.
- When a Codex v1.0 finding calls out a gap, that's a direct
  reference point: the finding is cited in the priority header.
- For each priority, we commit a single feature commit with the
  test additions + any reference-implementation changes needed to
  pass them. Progress table at the bottom tracks state.

## Priority 1 — Deepen shallow built-ins (~40 tests)

**Codex finding #8** (v1.0 review): `test_builtins_exhaustive.py`
has only shallow assertions for `width$`, `change.case$`, `top$`,
`stack$`, and `warning$` — a half-working interpreter can pass
them all.

Areas to deepen:

1. **`width$`**. Currently tests only assert relative ordering.
   Add:
   - Concrete width pins for specific strings against the
     `bibtex.web §13` cmr10 width table (e.g. `"foo"` = 500+500+500
     = 1500 for the three lowercase letters; `"{\\AE}"` = 903).
   - Widths for ligatures inside `{\...}` specials (all five:
     `\ss`, `\ae`, `\oe`, `\AE`, `\OE`).
   - Width of a brace group is the sum of contained widths, not
     the brace characters themselves.
   - `width$` on the empty string is 0.
   - `width$` used inside SORT with tie-breaks — two equal-width
     entries must preserve READ order.

2. **`change.case$`**. Current tests cover the basic 'l', 'u', 't'
   modes and first-letter preservation in 't'. Add:
   - `:` + whitespace run → next alpha char stays upper-cased in
     't' mode (btxhak §3.5 / bibtex.web §10651).
   - Brace-protected ASCII stays literal in all three modes.
   - Depth-1 LaTeX accent group `{\"O}` — 'l' mode should
     lowercase the `O` to `o` inside the accent group per btxhak;
     verify our impl matches.
   - `change.case$` + mode character is itself NOT case-sensitive
     (`"L"` and `"l"` both mean lowercase).
   - Empty input returns empty without type error.
   - A malformed mode character (e.g. `"x"`) — does BibTeX emit a
     warning or silently pass through?

3. **`top$` / `stack$`**. Currently asserts non-crash. Add:
   - `top$` when the stack is empty: per bibtex.web §10942,
     BibTeX emits a trace message to `.blg` but doesn't error; our
     contract says these may be no-ops. Assert either (a) a log
     line appears or (b) the following operation still sees the
     expected top.
   - `stack$` leaves the stack empty (per btxhak §4: "empties the
     entire stack"). Assert a `pop$` after `stack$` is a no-op /
     produces empty.
   - `top$` after `stack$` is a no-op (stack is empty).

4. **`warning$`**. Add:
   - `warning$` emitted during ITERATE carries the current entry's
     key in the warning metadata.
   - `warning$` emitted during EXECUTE (no current entry) has
     `key: null`.
   - Multiple `warning$` calls produce warnings in emission order.
   - `warning$` of the empty string still emits a warning.
   - `warning$` inside a SORT comparator function emits during
     sort-time.

5. **`chr.to.int$` / `int.to.chr$`**. Add:
   - `chr.to.int$` on a multi-char string is an error (per
     bibtex.web).
   - `int.to.chr$` on an out-of-range int (< 0 or > 127 in
     strict mode) — assert the documented error behavior.

6. **`purify$`**. Add:
   - A string with nested LaTeX specials `{\\c{c}}` (c-cedilla via
     accent): depth-1 handling per summary §8 applies.
   - All five ligatures (`\ss`, `\ae`, etc.) restore their letters
     correctly per bibtex.web §10602.
   - A brace group with only non-alphanumeric content is stripped
     to empty.

## Priority 2 — bibtex.web §15 forward-scan wrap (~5 tests)

**Codex finding #9** (v1.0 review): the bibtex.web §15 output
buffer rule requires that when a line has no whitespace in columns
[3, 79] but has whitespace later, BibTeX scans forward past column
79 for the first break point. Our `append_output` only scans
backward; the documented rule is neither implemented nor tested.

Tests to add:
- Payload with no whitespace in [3, 79] but whitespace at col 90.
  Expected: wrap at col 90 with 2-space indent on continuation.
- Payload with no whitespace anywhere. Expected: emit verbatim
  (current behavior).
- Boundary: whitespace at exactly col 79 → breaks there, not
  at col 78 or 80.
- Boundary: whitespace at exactly col 3 → breaks there (first
  permitted break point).
- Wrap depth: a 200-character unbroken-by-leading line should
  wrap at the first forward whitespace and then continue wrapping
  naturally.

**Reference-impl work**: extend `append_output` in
`bst_interpreter.cpp` to implement the forward-scan rule.

## Priority 3 — SORT / REVERSE / ITERATE depth (~15 tests)

`test_bst_language.py` has 4 SORT tests; expand:

- **Stability**: two entries with identical `sort.key$` preserve
  READ order.
- **Stability across all four styles**: validated end-to-end in
  `test_reference_styles.py` once corpus has ties (Priority 5).
- **Missing `sort.key$`**: entry with no sort key is grouped at
  one end (documented which end in btxhak §3.2).
- **Empty `sort.key$`**: same bucket as missing, or different?
- **`sort.key$` is an integer** (not string): coerce to string?
- **REVERSE after SORT** (`SORT REVERSE ITERATE`): reverses the
  sort order.
- **REVERSE without SORT**: iterates in reverse READ order.
- **Multiple SORTs** in sequence — is the last SORT's key the
  effective one? (bibtex.web says yes; we test this.)
- **SORT compares keys lexicographically** not numerically
  (`"10"` < `"2"`).
- **Iteration order after SORT + ITERATE is deterministic** for
  a single run and stable across runs given the same inputs.
- **EXECUTE between SORT and ITERATE** doesn't perturb the
  iteration order.
- **ITERATE of empty entry list** is a no-op (no crash).
- **`sort.key$` is write-only** during ITERATE (per btxhak).

## Priority 4 — Cross-entry state + name disambiguation (~10 tests)

- **Entry-scope STRING persists within one entry's function** but
  is reinitialized per entry in ITERATE.
- **Global STRINGS / INTEGERS** persist across ITERATE iterations
  and across EXECUTE calls.
- **A FUNCTION can be called from ENTRY scope and GLOBAL scope**
  with appropriate variable visibility.
- **Name disambiguation suffix** (a la `alpha.bst`): two entries
  with the same first-author-lastname + year, sorted together,
  produce sort keys that include a disambiguator. This is implicit
  in `alpha.bst` and should be observable via the .bbl (we use the
  ref-style parity fixtures for this).
- **`call.type$` inside EXECUTE** errors (no current entry) —
  per bibtex.web §13230.
- **`cite$` inside EXECUTE** errors similarly.
- **ENTRY fields reset between iterations** — a field written by
  `:=` in entry A is not visible in entry B.

## Priority 5 — Real-world corpus extension (~5 tests)

Current parity tests: 1 corpus × 4 styles = 4 tests.
Target: 2 corpora × 4 styles = 8 tests.

New fixture: `refs-edge.bib` — ~20 entries chosen for:
- Multiple authors with `and` inside braces (non-separator).
- Names in all three canonical forms (mixed in one corpus).
- Entries with `crossref` chains and cycles.
- Predefined month macros + user `@string` macros.
- Concatenation with numeric + string operands.
- `@preamble` with escaped characters.
- Special characters: `{\"o}`, `{\c c}`, ligatures in titles.
- Long-author lists that exercise "and others" / `et al.`.

Parametrize `test_reference_styles.py` over both corpora × all four
styles.

## Priority 6 — `.bst` parser edge cases (~10 tests)

`test_bst_language.py` covers the happy path. Edges not tested:

- Integer literals: `#-1`, `#0`, `#-42`, `#+0`.
- Nested function literals: `{ { { "x" write$ } execute$ } execute$ }`
  and equivalent without `execute$`.
- Quoted function names `'foo` — passing a function by reference
  (used as `quote$`'d arg to something expecting a function).
- `%` comments mid-expression.
- Top-level ordering errors:
  - `ITERATE {f}` before `READ` → load-time error.
  - `FUNCTION {g} { h }` where `h` is defined below — depending on
    how bibtex.web orders name resolution, this may be allowed or
    forbidden. Assert the documented behavior.
- Missing `ENTRY` declaration → style-file error.
- `STRINGS` without braces → parse error.
- Duplicate `FUNCTION` with the same name → overrides or errors?
- `MACRO` redefinition behavior in `.bst`.

## Priority 7 — Error-message line/column precision (~8 tests)

`test_errors.py` has 5 tests asserting only exit=1. Add precision:

- Malformed `.bib`: missing `}` at line N → error JSON has
  `line: N` and a column within that line.
- Malformed `.bib`: unknown entry type token → error pins the token.
- Malformed `.bst`: unknown function reference → error at the line
  of the reference, not at `FUNCTION` definition.
- Runtime stack underflow in a `.bst` function names the calling
  site.
- Unclosed brace group in a field value.
- Unquoted field value followed by a semicolon (valid — BibTeX
  accepts `{` `}` and `"` `"`).
- Missing required CLI flag → exits 1 with a clear error JSON.
- `--aux` file doesn't exist → exits 1 naming the missing path.

## Priority 8 — Field concatenation + macro corners (~8 tests)

- `"" # x # ""` produces the value of `x`.
- `"a" # "b" # "c"` = `"abc"`.
- Number # string: `2024 # "-11"` = `"2024-11"`.
- Macro redefinition: last `@string{foo = ...}` wins per btxdoc §3.
- Forward macro reference: `@article{k, title = foo}` followed by
  `@string{foo = "X"}` — spec says this errors (BibTeX is
  single-pass) per bibtex.web §12250.
- Self-referential `@string{x = x}` — infinite loop prevention.
- `@string{x = x # "a"}` — undefined at first reference time.
- Macro used as both entry type (invalid) and field value
  (valid) — ensure clear error.

## Priority 9 — `.bib` Unicode / non-ASCII preservation (~5 tests)

- UTF-8 title `"Gödel, Escher, Bach"` round-trips through `write$`
  byte-for-byte.
- Non-ASCII author `"Erdős, Paul"` decomposes correctly in
  `format.name$` (depending on how BibTeX treats non-ASCII letters
  — which is locale-dependent in real BibTeX; we assert our
  documented behavior per summary).
- `chr.to.int$` on a multi-byte UTF-8 char — assert the documented
  error or byte-by-byte behavior.
- `int.to.chr$` on an ASCII code produces a 1-byte string.
- `purify$` on a UTF-8 title preserves the bytes (no ASCII
  conversion, per bibtex.web's byte-level view).

## Progress table

| Priority | Status | Tests added | File |
|---|---|---|---|
| P1: Deepen shallow built-ins | ✅ done | 35 | `test_builtins_deep.py` |
| P2: §15 forward-scan wrap | ✅ done | 6 + impl fix | `test_output_wrap_forward.py` |
| P3: SORT / REVERSE / ITERATE | ✅ done | 14 | `test_sort_iterate.py` |
| P4: Cross-entry state | ✅ done | 9 | `test_cross_entry_state.py` |
| P5: Real-world corpus | ✅ done | +4 parity tests | `fixtures/refs-edge.bib` |
| P6: `.bst` parser edges | ✅ done | 16 | `test_bst_parser_edges.py` |
| P7: Error line/column | ✅ done | 8 | `test_error_precision.py` |
| P8: Concat + macro corners | ✅ done | 11 | `test_concat_and_macros.py` |
| P9: Unicode / non-ASCII | ✅ done | 8 | `test_unicode.py` |
| **Total** | **✅ 111 / ~106** | **258 → 369** | |

## Non-goals (not in this plan)

- Changing `summary.md` §8 approximations. That's a contract
  change, handled separately.
- Implementing RFC-area features (this is BibTeX, not ICal).
- Reconciling warning-kind vocabulary (`crossref_missing` vs
  `unresolved_crossref`). Separate cleanup commit.
- Fixing the fixture-provenance issue (Codex finding #6).
  Separate Docker-regeneration task.
- Reverting the byte-exact claim in the base prompt. Separate
  contract decision.

## Exit criteria

- All ~106 new tests pass against the extended reference impl.
- Ruff + pyright strict-mode clean.
- No regression in the existing 258 tests.
- `fixtures/refs-edge.bib` exists and is documented.
- `CHANGELOG.md` gets a v1.1 entry summarizing the expansion.
- `README.md` updates the test count claim.
