# BibTeX 1.2.4 validation — 2026-09-12

This patch corrects one existing hidden `format.name$` expectation and the
corresponding C++ reference behavior. All model-visible prompt/documentation
bytes remain unchanged, as do the other 385 scored cases. There are still
386 scored cases. The change repairs an incorrect oracle; it does not relax
the contract to maximize existing submissions' scores.

## Public authority and scope

`prompt/docs/authoritative/bibtex.web`, “Isolate the desired name”, lines
9390–9413, scans until the requested name count is reached **or the name list
ends**. Each scan sets the start pointer. A positive index beyond the list
length emits a warning without resetting the final name's pointers. The
subsequent copying/formatting steps (lines 9365–9373 and 9503 onward) therefore
format that last name. For `John Smith`, index 2 and format `{ll}` produce
`Smith`, not an empty string.

The old test's “empty string (spec §3.5)” comment was unsupported: summary §3.5
specifies a one-based name index but contains no such past-end rule.
`base-prompt.md` lines 24–28 and the summary's authority notice explicitly
give the supplied sources precedence. No explicit permitted approximation
applies to this selection behavior.

`test_builtins_exhaustive.py::test_format_name_out_of_range` retains its
one-name fixture, name-selection body, sentinel, node ID and point count. Its
expected value changes from `|` to `Smith|`. The sentinel makes successful
execution observable without making this name probe depend on EOF newline
formatting. There is no new shared gate or prerequisite.

The C++ reference now selects the final name for a positive past-end index,
checking the signed integer before subtraction or narrowing. Nonpositive
indices and an empty parsed list retain their existing empty result. The
public JSON warning catalog has no exact name-index mapping; `bst_type_error`
specifically describes stack-type/default recovery. This patch preserves the
reference's prior JSON-warning behavior instead of inventing a mapping. The
test asserts neither warning kind, wording, count nor absence. Native BibTeX's
warning is real; its diagnostic mapping remains a future public clarification.

The permitted no-op `top$`, inter-token name spaces, brace-width approximation,
and quoted-unknown-name load warning remain supported exactly as in 1.2.3.

## Independent oracle and negative control

An independent reviewer traced the supplied WEB and ran 20 separate-process
probes against the existing local **BibTeX 0.99d (TeX Live 2023/Debian)** oracle.
Its executable SHA256 is
`09d80947981f425cf7ca25d8a3bdb32df352fecd4eb00973771edf8598e6edd7`;
the supplied WEB SHA256 is
`04c15be36dce19be38361617f139b1b8a70aa21f97def5cdc478622941398fa0`.
The supplied WEB's 0.99e changes are nonfunctional relative to this compatible
oracle, as documented for the 1.2.3 style fixtures.

| Input | Index | Name/sentinel output |
| --- | --- | --- |
| `John Smith` | 1, 2, 3, 99 | `Smith|` |
| `John Smith and Alice Brown` | 1 | `Smith|` |
| `John Smith and Alice Brown` | 2, 3, 99 | `Brown|` |
| Nonempty list | 0 or negative | `|` |
| Empty list | Positive, zero or negative | `|` |

Positive past-end and empty-list requests warn in the native oracle; the
nonpositive probes do not. Priming with a preceding successful formatting call
does not alter the boundary observations. Native warning exit status 2 is not
imported into the task's CLI, whose successful warning-only execution exits 0.

The corrected reference passes **386/386**. The unchanged 1.2.3 reference is
the negative control: it passes **385/386**, failing only the corrected
past-end-name case. This demonstrates that the new observation distinguishes
the former erroneous empty-result behavior without causing another failure.

## Retained submission validation

All grades below use fresh disposable source copies in offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with at most two grader containers. The repository and original sources are
mounted read-only. Source manifests and original-result bytes match before
and after every grade. There are no skips, collection errors or build failures.

| Model / language | Run UID | 1.2.3 | 1.2.4 | Corrected case |
| --- | --- | ---: | ---: | --- |
| GPT-5.6 Sol / Python | `1d8ebecb-4e2c-496a-851c-6b6cb6eae5f9` | 382/386 | 381/386 | Pass → fail |
| GPT-5.6 Terra / Python | `38133d3d-3ef8-4847-ac84-0c040b99897d` | 375/386 | 374/386 | Pass → fail |
| GPT-6 Astra / C++ | `f42bd184-6b73-433d-9201-b076c5af7fb7` | 380/386 | 379/386 | Pass → fail |
| GPT-6 Astra / Python | `6f1f4ac5-698a-4e0e-a6cb-5d005a97bbdf` | 381/386 | 380/386 | Pass → fail |
| GPT-6 Astra / JavaScript | `ebd09450-0e1f-485f-a8ef-83494990e087` | 381/386 | 382/386 | Fail → pass |
| GPT-6 Astra / Rust | `9a58ca19-d746-44b8-b2f6-2d6ffc1bb8b7` | 384/386 | 383/386 | Pass → fail |

For each of the six submissions, **all other 385 node outcomes are identical**
to its 1.2.3 baseline (2,310 unchanged observations). The five decreases remove
false credit for returning empty; the JavaScript increase removes a false
failure for conforming last-name selection. Original generations, sources,
usage/cost metadata and old score records are preserved; these are regrades,
not new model generations. An excluded prior Astra Python generation and an
incomplete Luna generation are not included as eligible validation rows.

Remaining failures are unaffected: namespace/declaration checks, output
whitespace semantics and the prior Sol/Terra primitive/crossref failures retain
their exact outcomes. Multiple tests observing one implementation cause are
reported as clusters: for example, short-line trimming and whitespace-only
line suppression share an output-flush cause. All eight canonical style
integration cases pass in each of these six submissions.

## Reproducibility

- Previous test-suite SHA256:
  `17b0e8dc3fa85cf1b6ce431a25321ab978e65d03767bb505133cb647fb66c1a3`.
- Corrected test-suite SHA256:
  `0354c6331c1aab0bd5b9a0fa60495510ae99683a0513685b3cc6221ce9dcfcc2`.
- Ruff check/format and strict Pyright pass for the changed Python test.
  The isolated Pyright project resolves its own test helper and the repository
  source directory; an initial invocation using the canonical include roots
  could not resolve the scratch `conftest` and was corrected without code edits.
- Independent WEB/oracle review and raw probe inputs/outputs are retained under
  `work/bibtex-name-review/`; complete offline reports, per-node comparisons,
  source manifests, public-byte manifest and the two-slot driver are retained
  under `work/bibtex-name-followup/` beside the repository checkout.

Only `tests/test_builtins_exhaustive.py`,
`reference-implementation-cpp/src/bst_interpreter.cpp`, `VERSION`, `CHANGELOG.md`
and this validation note change in the eval patch. No new public behavior is
introduced. The reference-warning mapping remains explicitly deferred.
