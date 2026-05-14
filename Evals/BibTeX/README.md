# BibTeX

Full BibTeX 0.99c eval for CLISpecBench. Agents receive Oren
Patashnik's original BibTeX documentation (`btxdoc.tex`,
`btxhak.tex`), the complete `bibtex.web` literate-Pascal source, and
the four canonical reference styles (`plain.bst` / `alpha.bst` /
`unsrt.bst` / `abbrv.bst`). They must produce a CLI that executes a
`.bst` program against a cited subset of a `.bib` database and writes
the `.bbl` output BibTeX 0.99c would produce — **byte-exact on the
reference styles against the reference `.bib` corpora** (modulo the
documented approximations in `summary.md` §8).

> **Status.** v1.2.1 — documentation-consistency release over
> v1.2.0. v1.2.0 hardened test independence around output flushing
> and name probes. The current suite collects **375 tests** across
> deeper built-ins, `bibtex.web` §15 forward-scan wrapping,
> SORT / REVERSE / ITERATE semantics, cross-entry state, a second
> reference `.bib` corpus for byte-exact parity, `.bst` parser
> edges, error line/column precision, `#`-concatenation +
> `@string` corners, and UTF-8 byte preservation.

## Directory structure

```
prompt/
  base-prompt.md                    # domain-expert persona prompt
  technical-requirements-prompt.md  # CLI contract + log JSON schema
  docs/
    LICENSES.md                     # Knuth License notices
    summary.md                      # reading index + eval clarifications
    authoritative/
      btxdoc.tex                    # BIBTEXing (user guide)
      btxhak.tex                    # Designing BibTeX Styles
      bibtex.web                    # complete BibTeX 0.99c source
      plain.bst                     # reference style 1
      alpha.bst                     # reference style 2
      unsrt.bst                     # reference style 3
      abbrv.bst                     # reference style 4
tests/
  conftest.py                       # EVAL_CONFIG + probe .bst styles + helpers
  fixtures/                         # reference .bib corpora + expected .bbl
  test_bib_parsing.py               # .bib parsing via PROBE_STYLE_FIELDS
  test_bst_language.py              # top-level commands + core built-ins
  test_bst_parser_edges.py          # .bst syntax and command edge cases
  test_build.py                     # smoke: binary builds
  test_builtins_deep.py             # deep built-in semantics
  test_builtins_exhaustive.py       # all 37 built-ins with edge inputs
  test_concat_and_macros.py         # # concatenation + macro ordering
  test_cross_entry_state.py         # global/per-entry state across entries
  test_crossref_corners.py          # chains / cycles / case preservation
  test_direct_bbl.py                # direct .bbl assertions (no probe)
  test_error_precision.py           # error source/line/column details
  test_errors.py                    # exit-1 cases (malformed .bib/.bst)
  test_library_divergence.py        # adversarial fixtures
  test_name_grammar_exhaustive.py   # every Form 1/2/3 corner from btxhak §2
  test_names.py                     # author-name grammar via format.name$
  test_output_buffer.py             # 79-col wrap edge cases
  test_output_wrap_forward.py       # §15 forward-scan wrap fallback
  test_reference_styles.py          # byte-exact .bbl parity on plain/alpha/etc.
  test_sort_iterate.py              # SORT / ITERATE / REVERSE ordering
  test_unicode.py                   # UTF-8 and byte-oriented text behavior
reference-implementation-cpp/
  CMakeLists.txt
  src/                              # see below
VERSION                             # 1.2.1
CHANGELOG.md
```

## What this eval evaluates

The eval scores the submission along four surfaces:

1. **`.bib` parsing.** Entry types, keys, fields (both brace-
   and paren-delimited), macros (user `@string` plus 12 predefined
   months spelled out — `January` / `February` / ...), `#`
   concatenation, `@preamble`, `@comment`, `crossref` inheritance
   (case-insensitive lookup, child fields before inherited).
2. **Author-name grammar.** Full Form 1 / 2 / 3 decomposition,
   tokenization with brace protection, tie character, von
   classification, leading-caps-before-first-lowercase prepended to
   Last in Form 2/3, `format.name$` formatting with single/double
   letter units.
3. **`.bst` stack-language interpreter.** All top-level commands
   (`ENTRY`, `STRINGS`, `INTEGERS`, `FUNCTION`, `MACRO`, `READ`,
   `EXECUTE`, `ITERATE`, `REVERSE`, `SORT`), value types (integer,
   string, function, missing), entry scope, global scope, 37
   built-in functions including arithmetic, string manipulation,
   name formatting, stack ops, control flow (`if$`, `while$`), and
   output (`write$`, `newline$`).
4. **Output contract.** `.bbl` text written to `--output`, LF line
   endings, 79-column line wrapping, structured JSON log file
   (optional `--log`), exit-1 error JSON with `source` (`bib` /
   `bst` / `runtime`) / `line` / `column` / `message`.

Tests observe internal behavior through **probe `.bst` styles** —
minimal style programs that dump the relevant state (entry fields,
parsed names, stack results) as structured `.bbl` text. This keeps
the contract strictly the one agents see — the only output channel
is the `.bbl` file — while letting tests assert on parse and
execution internals.

## Running tests

```bash
uv run pytest Evals/BibTeX/tests --language=cpp
```

The reference implementation passes all **375** collected tests. Run from the
repository root.

## Task IDs

- `bibtex-cpp` — C++20 target; reference implementation available
- `bibtex-js` — JavaScript target
- `bibtex-py` — Python target
- `bibtex-rs` — Rust target

## Why this task

The contamination asymmetry holds for this eval: `.bib` parsers
exist in every major language (bibtexparser,
biblib, bibtex-tidy, typst/biblatex, nom-bibtex, serde_bibtex), but
`.bst` stack-machine interpreters exist in roughly four places
(BibTeX itself in WEB/Pascal, pybtex, cl-bibtex, BiBTeXML). None
have "how to build a BibTeX from scratch" tutorials in the search
corpus. An agent pattern-matching against public `.bib` parsers
gets the first module right but has no equivalent reservoir for the
stack machine, output formatting, or the 37 built-in semantics.

## Scope

In scope:

- Full `.bib` lexer and parser, `@string` / `@preamble` / `@comment`.
- Author-name grammar with all three forms.
- `.bst` lexer (integers with `#` prefix, strings, function literals,
  quoted names, comments).
- `.bst` top-level command execution.
- Required built-ins: `>`, `<`, `=`, `+`, `-`, `*`, `:=`,
  `add.period$`, `change.case$`, `chr.to.int$`, `int.to.chr$`,
  `int.to.str$`, `substring$`, `text.length$`, `text.prefix$`,
  `width$`, `purify$`, `format.name$`, `num.names$`, `if$`,
  `while$`, `skip$`, `pop$`, `swap$`, `duplicate$`, `cite$`,
  `type$`, `call.type$`, `empty$`, `missing$`, `preamble$`,
  `write$`, `newline$`, `quote$`, `top$`, `stack$`, `warning$`.
- Sort by `sort.key$`, reverse iteration.
- 79-column line wrapping of output.
- Structured JSON log (optional `--log`).
- Error JSON with `source` / `line` / `column` / `message`.

Known bounded gaps vs. real BibTeX 0.99c are documented in
[`prompt/docs/summary.md`](prompt/docs/summary.md) §8 and
[`CHANGELOG.md`](CHANGELOG.md):

- `change.case$` on LaTeX accent macros (e.g. `{\"o}`) uses a
  simplified brace-protection rule; BibTeX's exact behavior on
  nested `\foo{...}` is outside the required contract.
- Byte-exact `.bbl` compatibility is asserted for the canonical
  reference styles against the bundled reference corpora. Outside
  those inputs, only the explicit bounded approximations in
  `summary.md` §8 may diverge from historic BibTeX behavior.

## References

- [`prompt/docs/authoritative/btxdoc.tex`](prompt/docs/authoritative/btxdoc.tex),
  [`btxhak.tex`](prompt/docs/authoritative/btxhak.tex), and
  [`bibtex.web`](prompt/docs/authoritative/bibtex.web) — the
  authoritative sources shipped verbatim.
- [`prompt/docs/summary.md`](prompt/docs/summary.md) — navigation
  index over the above.
- [`prompt/docs/LICENSES.md`](prompt/docs/LICENSES.md) — Knuth
  License redistribution notice.
- [`Evals/EVAL_CANDIDATE_DISCUSSION.md`](../EVAL_CANDIDATE_DISCUSSION.md) — the
  proposal-ranking document that motivated building this eval.
