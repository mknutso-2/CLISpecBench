# BibTeX 1.2.3 validation — 2026-09-12

This patch repairs hidden tests, their test-owned fixtures, and the C++ reference.
All `Evals/BibTeX/prompt/**` bytes remain identical to v1.2.2; the shared language
prompts are unchanged. Saved submissions can be regraded without another model
run. Original source, generation result, transcript, usage, and cost are retained.

The suite contains **386** cases, up from 376: two parent-inclusion threshold
controls, four illegal-declaration controls, one runtime-underflow control, two
database/BST namespace controls, and one whitespace-only output-buffer control.
No existing test was removed. Existing assertions and fixtures were repaired.

## Public contract and explicit exceptions

The supplied [base prompt](../../Evals/BibTeX/prompt/base-prompt.md), lines 20–28,
and [summary introduction](../../Evals/BibTeX/prompt/docs/summary.md), lines 3–32,
make the supplied WEB and Patashnik guides authoritative over ordinary factual
errors in the navigation summary. For example, WEB `x_preamble` concatenates
values directly, while the summary incorrectly inserts spaces.

That general precedence does not erase **expressly permitted approximations**.
Summary §2.6 says implementations “MAY emit a single ASCII space at every
inter-token gap”; §8 deliberately permits bounded approximations, including
ordinary-brace width handling in §8.1. The `top$` row in §3.5 also says
a no-op is acceptable, so its focused probe accepts exactly the faithful
popped-stack result or the permitted preserved-stack result. The direct width probe accepts either
faithful WEB brace contributions or the documented zero-contribution mode.
Existing name probes accept ties or spaces. Canonical style corpora now use one
token per name part, so both spacing modes produce the same expected BBL; multi-
token names remain covered directly. This was checked using a deliberately
modified reference with both permitted simplifications enabled.

## Repairs and source anchors

Line numbers below refer to the unchanged files shipped under
[`prompt/docs/authoritative/`](../../Evals/BibTeX/prompt/docs/authoritative/).
They identify publicly available rules; neither the reference nor an observed
model answer is treated as an oracle.

| Issue | Repair and public basis |
| --- | --- |
| A shared field probe redeclared `crossref`; nine positive styles redeclared `sort.key$` | Use these predefined names without redeclaration. `btxhak.tex` lines 198–200 and 272–274; `bibtex.web` lines 8135–8146. Dedicated negative cases retain duplicate-declaration coverage. |
| Field/type probes accessed undeclared fields or entry-type functions | Declare the actually tested `journal` field and `article`/`book` type functions. `btxhak.tex` ENTRY description and `type$` lines 484–492. Missing-field output writes its label separately so a correct missing-string type default cannot erase the subject label. |
| Month fixtures assumed globally predefined month macros | Define the needed `MACRO` in the style. The four public styles supply their own month abbreviations; WEB uses the `macro_ilk` table at READ. |
| Positive crossrefs placed parents before children | Put parents after children, as `btxdoc.tex` lines 173–175 requires. Existing A/B/C nested probes keep child-before-parent order and the supplied WEB's one-level inheritance result; the guide warns nested crossrefs are unreliable at lines 176–179. |
| Canonical style cases depended on crossref retention/inheritance | Materialize inherited fields in the two test corpora, preserving child overrides. Two named controls independently observe the default one-child and two-child parent-inclusion behavior (`btxdoc.tex` lines 163–175; WEB `min_crossrefs`). |
| Entry-state/disambiguation probes underflowed or observed only inherently unique citation prefixes | Repair stack order and observe the computed suffix itself. Stack operations and `format.name$` follow `btxhak.tex`; the disambiguation test checks exact `aa`, `bb`, and `cZ` output. |
| `top$` expected only a non-popping debug operation; negative `if$` expected true | Accept exactly the faithful popping or explicitly permitted no-op `top$` result. For `if$`, positive integers alone select the true branch. `btxhak.tex` lines 392–398, 486–501 and corresponding WEB builtins; summary §3.5 explicitly permits no-op `top$`. |
| Wrong-type arithmetic/concatenation expected per-operand coercion | The complete result defaults to integer zero or empty string. WEB `x_plus` / `x_concatenate`, lines 8409–8493. A sentinel makes the empty-string observation non-vacuous. |
| Preambles inserted a separator; self-referential macros reused an old binding | Concatenate preambles directly (WEB `x_preamble`, lines 10545–10567); suppress a macro's own reference while scanning its replacement (WEB `Scan a macro name`, lines 5951 onward). |
| Name assertions followed erroneous summary decomposition | Form 1 retains the last token in Last; comma forms keep the contiguous prefix through the last lowercase token in von; extra commas are discarded. WEB lines 9562–9582, 9680–9747, and 9880–9906. Spacing alternatives remain accepted. |
| Successful short output required retaining trailing whitespace | WEB output buffering removes trailing whitespace and distinguishes a true empty line from a nonempty all-space line (lines 7537–7566). Separate focused cases check both behaviors. |
| Command/declaration error probes accepted success or bare crashes | Require exit 1 plus an actual error object for EXECUTE before READ, READ without ENTRY, duplicate functions, unknown function names, repeated ENTRY/READ, built-in redeclaration, and stack underflow. WEB `bst_execute_command` lines 4095 onward, `bst_read_command` lines 4814 onward, declaration lookup, and the technical prompt's error/exit contract. The malformed-BIB case now uses genuinely unterminated input. |
| MACRO incorrectly shared the callable/function namespace | A MACRO may share a spelling with a BST field, but its database abbreviation is not callable as a function. WEB `macro_ilk` definition line 1668, `bst_macro_command` lines 4712–4750, and function lookup use distinct hash namespaces. Two direct controls distinguish these capabilities. |
| Eight canonical style tests referenced an unavailable `/tmp/prompt/docs` path | Bundle byte-identical copies of the four supplied public styles under test fixtures, with hashes. The official grader mounts tests, not the model's prompt directory. |
| Eight expected BBLs were inconsistent with the supplied standard styles | Regenerate independently with an explicitly identified compatible BibTeX oracle, including the required 79-column runtime setting. No repository reference or submission generated the new expectations. |

## Oracle provenance and reproducibility

The local oracle is Ubuntu `texlive-binaries` package
`2023.20230311.66589-9build3`, reporting **BibTeX 0.99d (TeX Live 2023/Debian)**.
The package was extracted into scratch; no system installation was needed.
Its executable SHA-256 is
`09d80947981f425cf7ca25d8a3bdb32df352fecd4eb00973771edf8598e6edd7`.

The public prose calls the authority 0.99c, but the shipped WEB banner actually
says **0.99e** (line 136). Its own history says the 0.99d release changed output
wrapping at whitespace and that 0.99e has no functional changes (lines 40–46).
Thus 0.99d matches the shipped authoritative implementation's semantics. The
public-file SHA-256 is
`04c15be36dce19be38361617f139b1b8a70aa21f97def5cdc478622941398fa0`.
The prose version mismatch is deferred for a later public-input clarification.

[`tests/fixtures/oracle-provenance.json`](../../Evals/BibTeX/tests/fixtures/oracle-provenance.json)
records package/executable identity and every corpus, citation-list, style, and
BBL hash. Each of the eight combinations ran in a fresh directory with
`max_print_line=79`, `min_print_line=3`, and default `min_crossrefs=2`; each exited
0. Expected empty-booktitle/journal warnings on the edge corpus are harmless.
The raw Unicode label ambiguity was avoided by spelling Gödel with the public
TeX accent notation; separate tests retain UTF-8 input coverage.

The regeneration helper now requires an explicit executable or immutable local
Docker image, supports `--check`, and records identity, runtime settings and
all input/output hashes. Its independent executable `--check` reproduces all
eight final BBLs byte-for-byte. The helper no longer selects a floating image
or silently uses a different line-width default.

## Validation and failure independence

Final suite SHA-256:
`17b0e8dc3fa85cf1b6ce431a25321ab978e65d03767bb505133cb647fb66c1a3`.
Full grading used the pinned Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with networking disabled, source/test mounts read-only, and disposable source
copies and builds. Ruff and strict Pyright pass; shell syntax and oracle
regeneration checks pass.

| Source | v1.2.2 | v1.2.3 |
| --- | ---: | ---: |
| Original C++ reference, unchanged | 376/376 | 353/386 |
| Corrected C++ reference | — | 386/386 |
| Saved Terra Max Python | 353/376 | 375/386 |
| Saved Astra Max Python, rubric validation only | 294/376 | 384/386 |

The Astra run used hosted external tools despite the intended API-only socket
policy. Its preserved source is useful as a diverse rubric check, but these
figures must **not** be published as a qualifying model-performance result.
Terra's full preserved session contains no observed hosted-app/MCP/web calls;
it still predates explicit disablement and retains that cohort qualification.
These checks do not silently upgrade either run's original isolation claims.

The unchanged old reference's 33 failures are useful regression controls:
25 focused behavior/error cases plus all eight independently regenerated style
cases. The corrected reference resolves each. A variant enabling both permitted
always-space name rendering and ordinary-brace-zero width passes all eight
canonical parity cases, demonstrating that those alternatives are not secretly
penalized through style output.

Terra now passes all eight style cases while failing both focused crossref
threshold cases. That directly demonstrates removal of the crossref prerequisite
from unrelated style scores. Its other nine failures concern callable MACROs,
wrong-type concatenation, preamble separators, self-reference, two built-in
redeclarations, extra commas in names, and the two whitespace-buffer behaviors.
The two remaining Astra failures are the distinct MACRO namespace controls.
All are grounded in unchanged public rules and independently checked against
WEB or the standalone oracle. Neither saved source was modified to improve its
score.

This does not make every scored case a count of a distinct implementation bug.
Canonical style tests remain intentional integration tests: a primitive defect
can affect several styles. The suite retains separate boundary and feature
checks rather than hiding such defects with a generic skip/gate. Shared positive
fixtures use valid, conservative prerequisites, while narrow negative controls
retain the corresponding validation requirements. All new error controls require
structured rejection; a crashed or vacuously empty program does not pass them.

Independent review caught and corrected an accidental nested-crossref fixture
reorder, the explicit approximation exceptions, database/BST namespace conflation,
the whitespace-only flush distinction, and the explicit no-op `top$` permission
before this final freeze. Both the
test changes and four reference source changes received independent peer review.

## Final summary-versus-WEB audit

The unchanged base prompt (lines 24–28) and summary introduction (lines 28–32)
explicitly resolve ordinary contradictions in favor of the supplied authoritative
sources. A concrete summary example or a capitalized requirement does not itself
reverse that precedence. Separately worded permissions and deliberate bounded
approximations remain accepted:

| Public text overlapping this patch | Treatment in the hidden tests |
| --- | --- |
| §1.5 says month names are predefined | Positive probes declare the needed style MACRO, making the fixture valid under both descriptions. The log's required month-name metadata remains covered independently. |
| §2.2/2.3/2.5 describe different name partitions and extra commas | Supplied WEB determines the partitions; §2.6's expressly permitted tie/space alternatives remain accepted. |
| §3.3 describes wrong-type defaults | Whole-result defaults follow WEB and the summary's zero/empty result types, with non-vacuous sentinels. |
| §3.5 describes nonzero `if$`/`while$`, space-joined `preamble$` | Ordinary source conflicts follow WEB. The preamble case requires direct concatenation. Canonical corpora have zero or one preamble, so they do not multiply this focused failure. |
| §3.5 explicitly says a no-op `top$` is acceptable | The focused case accepts exactly `X` after faithful popping or `debug` after a no-op, each produced by a subsequent `write$`. No canonical style invokes `top$`. Both the original no-op reference and corrected popping reference pass this case. |
| §3.6 says short trailing whitespace MUST be retained | This ordinary contradiction follows WEB's `output_bbl_line` trimming. End-of-run flushing, which both sources require, remains covered. |
| §5.3 explicitly permits quoted undefined names as load-time warnings | No scored negative requires rejection of a quoted unknown name. The structured-error cases use unquoted unknown names. The reference selects faithful WEB rejection; the documented warning alternative is not privately prohibited by these tests. |
| §8's ordinary-brace width and deep-accent approximations | Preserve the named approximations. The combined allowed brace-width/name-spacing variant passes all eight canonical parity cases. |

All remaining reference corrections concern legal fixtures, declarations, stack
underflow, database/function namespace separation, crossref threshold behavior,
or independently regenerated canonical output. They introduce no additional
summary-overriding permission. No model-visible bytes were changed during this
audit. The misleading ordinary descriptions and the relationship of the named
permissions to source precedence need a later public clarification.

## Deferred public clarifications

A later public-input revision should correct the misleading summary descriptions
listed above and identify the actual shipped WEB version. It should also explain
how name-spacing and brace-width exceptions interact with canonical style parity,
and specify Unicode byte/codepoint semantics where raw Unicode affects labels.
This patch uses the documented alternatives or intersection inputs; it does not
privately impose new public behavior. It does not claim that every untested BibTeX
feature, arbitrary Unicode combination, or reference implementation edge case is
fully validated.
