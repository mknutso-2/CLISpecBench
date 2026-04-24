# GEDCOM

GEDCOM 5.5.1 genealogy-data-exchange eval for CLISpecBench. Agents receive the FamilySearch GEDCOM 5.5.1 specification and must produce a CLI tool that parses, validates, canonicalizes, and queries GEDCOM files.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt, tests, or reference implementation yet.

## Why this eval

GEDCOM 5.5.1 is a dense, line-oriented, hierarchically-structured text format with a tag/level grammar, cross-reference pointers across record types, CONT/CONC line-continuation rules, three-way character-encoding handling (UTF-8, ASCII, ANSEL), and a substantial domain vocabulary (roughly 150 tags across INDI, FAM, SOUR, OBJE, REPO, NOTE, SUBM record types). A competent implementation has to parse a fixed-column grammar, build a graph of cross-references, enforce structural invariants the spec states explicitly, and expose pedigree queries that walk that graph. It sits in the same "dense authoritative spec + deterministic round-trip" class as RS274 and IGES.

The domain is genealogy, not engineering, which gives the base prompt a clean non-developer voice: a professional genealogist importing records from Ancestry or FamilySearch can describe what the tool should do without any software jargon. The scoring surface is naturally deterministic — canonical JSON emission, cross-reference resolution, and ancestor/descendant queries all have exactly-one-correct-answer outputs for a given input file.

Where GEDCOM differs from RS274 and IGES is contamination: there are mature, widely-distributed GEDCOM parsers in every major language, and the format is old enough (first draft 1984, 5.5.1 **released in 1999**, and then adopted as an open standard in 2019 via FamilySearch's formalization cycle prior to GEDCOM 7.0) that training data contains decades of cumulative exposure. A 1999 standard with continuous 20+ years of open-source tooling is much more contamination-prone than its 2019 re-release date would suggest. This is the largest risk to the eval (see Contamination section), and it is what keeps GEDCOM in the "worth proposing but open question" bucket rather than the "obviously strong" bucket like IGES.

## Documentation Corpus

Planned contents of `prompt/docs/`:

- **`gedcom-5-5-1.md`** — transcription of the FamilySearch GEDCOM 5.5.1 specification (the canonical PDF at [gedcom.io/specifications/ged551.pdf](https://gedcom.io/specifications/ged551.pdf), ~100 pages). Covers Chapter 1 (concepts), Chapter 2 (form description), Chapter 3 (lineage-linked structure), and Appendix A (tag definitions).
- **`ansel-encoding.md`** — brief summary of the ANSEL encoding mapping the spec references (needed to parse legacy files; the spec itself does not inline the ANSEL codepage).

**Redistributability.** The GEDCOM 5.5.1 PDF's notice permits copying "for purposes of review" but is narrower than earlier 5.x releases, which explicitly allowed copying "for purposes of review or programming of genealogical software." GEDCOM 7.0 is Apache 2.0 licensed. For 5.5.1 we would need to either (a) transcribe the spec into our own Markdown and cite heavily (the structure and tag semantics are factual and not themselves copyrightable; the prose *is*), (b) link externally and ship our docs corpus as a curated extract plus citations, or (c) switch the eval to target GEDCOM 7.0, which removes the licensing question entirely but reduces contamination resistance (7.0 is newer but has active tooling in most languages). This is an open question — see Risks below.

**Length.** Target ~2,500–3,500 lines of Markdown after transcription, placing it between RS274 (~6k) and a typical small spec.

## Base Prompt (sketch)

> I'm a professional genealogist. Most of my day is spent importing family-tree data that clients send me as GEDCOM files — the standard export format from Ancestry, FamilySearch, RootsMagic, Family Tree Maker, and every other genealogy program out there. The files are plain text but they're not fun to look at: each line has a level number, a tag like `INDI` or `BIRT`, and sometimes a value or a cross-reference like `@I42@`. Records reference each other across the file (a family record points at two spouses and their children; a child record points back at its family), and the structure is strict — levels have to nest correctly, every pointer has to resolve, dates follow a specific grammar.
>
> I need a command-line tool that reads a GEDCOM 5.5.1 file and gives me answers. First, it should parse the file and write out a canonical JSON representation — one top-level object with the header, individuals, families, sources, media objects, notes, repositories, and submitters, each keyed by their cross-reference ID. Second, it should validate the file and report structural problems: unresolved pointers, duplicate IDs, level-jump violations, the sort of thing that breaks imports in other programs. Third, it should answer relationship questions — given two individual IDs, tell me the ancestors of one, the descendants of the other, and the relationship path between them (if any exists).
>
> The spec I've attached is the FamilySearch GEDCOM 5.5.1 standard. It's the canonical document for this format and it covers everything the tool needs to understand.

## Technical Requirements (sketch)

Single binary (default name `gedcom`) with subcommands. All emit JSON on both success and error paths; exit 0 on success, 1 on invalid input, 2 on internal error (same convention as RS274/IGES).

| Subcommand | Purpose |
|---|---|
| `gedcom parse --input <file.ged> --output <out.json>` | Parse to canonical GEDCOM-JSON |
| `gedcom validate --input <file.ged> --output <report.json>` | Report structural errors (unresolved pointers, duplicate xrefs, malformed dates, level-jump violations) |
| `gedcom query ancestors --input <file.ged> --id <@I1@> --generations <n> --output <out.json>` | Enumerate ancestors up to N generations |
| `gedcom query descendants --input <file.ged> --id <@I1@> --generations <n> --output <out.json>` | Enumerate descendants up to N generations |
| `gedcom query relationship --input <file.ged> --from <@I1@> --to <@I2@> --output <out.json>` | Shortest relationship path through FAM records (or null if disconnected) |

High-level JSON schema fields for `parse`:

- `header` — SOUR/DEST/DATE/CHAR/GEDC structure
- `individuals[@I…@]` — name pieces, sex, events (BIRT/DEAT/MARR/etc.), FAMC/FAMS links, notes, sources
- `families[@F…@]` — HUSB, WIFE, CHIL array, family events
- `sources[@S…@]` — title, author, publication, repository links
- `media[@M…@]`, `notes[@N…@]`, `repositories[@R…@]`, `submitters[@SUBM…@]`
- `encoding` — detected source encoding (`UTF-8` | `ASCII` | `ANSEL`)

CONT/CONC reassembly is done during parse (multi-line values are emitted as single strings with `\n` separators for CONT, no separator for CONC). Cross-reference pointers are resolved to the referenced object in query outputs but preserved as `@…@` strings in the canonical JSON so that round-trip is possible in a future `write` subcommand extension.

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| Line grammar (levels, tags, pointers, values, whitespace) | ~8 |
| CONT/CONC line continuation | ~5 |
| Character encoding (UTF-8, ASCII, ANSEL) | ~6 |
| Header record (HEAD/SOUR/CHAR/GEDC/DATE) | ~5 |
| INDI records (names, sex, events, FAMC/FAMS) | ~10 |
| FAM records (HUSB/WIFE/CHIL, family events, pedigree links) | ~8 |
| SOUR / OBJE / REPO / NOTE / SUBM records | ~8 |
| Date grammar (exact, approximate, range, period, phrase) | ~8 |
| Cross-reference resolution and duplicate-ID detection | ~6 |
| Structural validation (unresolved pointers, level-jumps, required fields) | ~8 |
| Ancestor / descendant queries (generation limits, adoption links) | ~6 |
| Relationship-path query (self, direct, sibling, cousin, unrelated) | ~6 |
| Error handling (malformed input, wrong encoding declared, exit codes) | ~6 |
| Torture-test fixtures (Heiner Eichmann's `allged.ged`, `TGC551LF.ged`) | ~6 |
| **Total** | **~96** |

Comfortably clears the 50-test floor from `CHOOSING_EVALS.md`.

## Implementation Size Estimate

Expected ~2,000–3,000 LOC for a competent C++ reference, broken down roughly as:

- Line grammar / tokenizer (level-tag-value-pointer, whitespace rules) — ~200 LOC
- CONT/CONC reassembly and encoding detection — ~200 LOC
- ANSEL-to-UTF-8 transliteration table — ~250 LOC (mostly data)
- Record-type parsers (INDI, FAM, SOUR, OBJE, REPO, NOTE, SUBM, HEAD) — ~600 LOC
- Date-grammar parser (exact / APPROX / BEF / AFT / BET…AND / FROM…TO / INT / interp) — ~250 LOC
- Cross-reference graph build and validation — ~250 LOC
- Canonical JSON emitter — ~200 LOC
- Pedigree queries (ancestors, descendants, relationship BFS) — ~200 LOC
- CLI / arg parsing / error formatting — ~150 LOC

Anchors: `python-gedcom`'s `parser.py` alone is 531 lines (430 SLOC) and is a parser-only library that does not do validation, queries, or ANSEL. Gramps' `libgedcom.py` is substantially larger (several thousand lines) because it handles quirks of ~20 vendor dialects — we are scoped to spec-conformant input only, so we sit well below that. `gedcom4j` is a three-component Java library (model + parser + writer) and is the closest analogue; a full implementation in that style is in the 3k–5k LOC range for Java and would be meaningfully smaller in C++. Our estimate targets the spec-conformant subset.

This clears the ~1000 LOC "real multi-file system" threshold from `CHOOSING_EVALS.md`.

## Contamination & OSS Landscape

**Specific implementations found:**

- [ged4py](https://github.com/andy-z/ged4py) — Python, MIT, GEDCOM 5.5.1, actively maintained (last release March 2025), UTF-8/ASCII/ANSEL support, pip-installable. **High maturity.**
- [python-gedcom](https://github.com/nickreynke/python-gedcom) — Python, GEDCOM 5.5, 129 stars / 74 forks, `parser.py` is 531 lines (430 SLOC). Origin traces to a 2005 BYU parser. **Medium maturity, well-indexed.**
- [gedcom4j](https://github.com/frizbog/gedcom4j) — Java, MIT, GEDCOM 5.5 and 5.5.1, three-component library (model + parser + writer), multi-thousand LOC. **High maturity.**
- [Gramps](https://github.com/gramps-project/gramps) — Python, GPLv2, full genealogy app. `gramps/plugins/lib/libgedcom.py` is the importer and is several thousand lines because it handles vendor quirks. **Very high maturity and visibility.**
- [read-gedcom](https://www.npmjs.com/search?q=gedcom) and other JS parsers — multiple npm packages; [tmcw/gedcom](https://github.com/tmcw/gedcom) specifically translates GEDCOM structure into JSON, directly overlapping with our `parse` subcommand's contract. **Medium maturity, directly relevant.**
- [pirtleshell/rust-gedcom](https://github.com/pirtleshell/rust-gedcom), [`gedcom`](https://crates.io/crates/gedcom) and [`ged_io`](https://docs.rs/ged_io) crates — Rust; `ged_io` supports both 5.5.1 and 7.0. **Low-medium maturity.**
- [jochenboesmans/gedcom-parser](https://pkg.go.dev/github.com/jochenboesmans/gedcom-parser) — Go, GEDCOM 5.5.1, ged-to-JSON converter. **Low-medium maturity, directly relevant contract.**
- [gedcom-parse](https://gedcom-parse.sourceforge.net/) — C, older but still referenced. **Medium maturity.**

**Tutorials / walkthroughs:**

- [Writing a Family Tree Application in C#: Importing a Gedcom File](https://sjmeunier.github.io/programming/2010/02/22/writing-a-family-tree-application-in-csharp-importing-a-gedcom-file-part-2.html) — step-by-step implementation walkthrough.
- [Tamura Jones, Open Source GEDCOM Parsers](https://www.tamurajones.net/OpenSourceGEDCOMParsers.xhtml) — catalog and critique of existing parsers (not a tutorial, but an orientation document).
- Published reference fixtures: [Heiner Eichmann's GEDCOM 5.5 sample page](http://heiner-eichmann.de/gedcom/gedcom.htm) including `allged.ged` (nearly all tags) and John Nair's torture-test files hosted at [geditcom.com](https://www.geditcom.com/gedcom.html).

**Contamination risk: high.** GEDCOM has multiple mature parsers in every mainstream language, at least one of which (`tmcw/gedcom` for JS, `gedcom-parser` for Go, `ged_io` for Rust) produces a JSON representation that could be very close to whatever canonical JSON schema we pick. The format is old (1984 first spec, 5.5.1 final 2019), widely discussed in blog posts and tutorials, and used in a well-known hobby/research domain — all training-data-friendly properties. This is materially worse than IGES (where `IGES-SDK` is essentially the only fully-worked public C++ reference, and no language has a dominant JSON-emitting parser) and worse than RS274 (where the interpreter semantics are less pattern-match-friendly than a tag/level parser). Partial mitigations: (a) specify our canonical JSON schema in `technical-requirements-prompt.md` in a way that is unlikely to match any existing library's output exactly, forcing the agent to actually read the contract; (b) lean on validation and pedigree-query correctness rather than just parsing (fewer public implementations ship validation or relationship BFS); (c) include adversarial test fixtures from the torture-test set that known parsers have been documented to fail on. None of these fully neutralize the contamination problem.

## Risks and Open Questions

- **License for 5.5.1 corpus.** The 5.5.1 notice permits copying "for purposes of review," not programming. Redistributing the spec verbatim in `prompt/docs/` is at best ambiguous. Options: transcribe the spec into our own Markdown (structure and tag semantics are factual; prose is re-expressible), link externally only and ship a derivative summary, or switch target to GEDCOM 7.0 (Apache 2.0, clearly redistributable) and accept worse contamination resistance in exchange. **Resolution needed before prompt work starts.**
- **5.5.1 vs 7.0.** 7.0 is the current version (released 2021; 7.0.18 current as of the searches above), requires UTF-8, drops CONT/CONC, and is Apache-licensed. 5.5.1 is the format still dominant in the installed base. Picking 7.0 cleans up encoding/CONC complexity and fixes the licensing question but removes one of the domain's two pieces of interesting parser complexity (ANSEL transliteration and CONC reassembly) and cuts against the "what genealogists actually receive" persona. Staying on 5.5.1 keeps those intact but inherits the license and contamination problems. **Open decision.**
- **Contamination ceiling.** Even with schema idiosyncrasy and validation/query emphasis, there is probably a real ceiling on how much the score differentiates frontier models on this task — many will have seen enough GEDCOM to emit a plausible parser from pattern-matching alone. This may make GEDCOM a weaker signal eval than IGES or RS274. Worth accepting only if paired with a harder surface (e.g., semantic validation, relationship BFS on adoption-tangled graphs, ANSEL correctness) where pattern-matched implementations tend to fail.
- **Date grammar complexity.** GEDCOM dates are a small grammar of their own (`EXACT`, `ABT`, `BEF`, `AFT`, `BET…AND`, `FROM…TO`, `INT …`, `(phrase)`). This is genuine spec-comprehension work and a strength of the eval, but it also drags in Julian/Gregorian/French-Republican/Hebrew calendar escapes. We should decide whether to include the non-Gregorian calendars (more realistic, more contamination-resistant) or restrict to Gregorian (less work, less signal).
- **Pedigree queries as a scored surface.** Ancestor/descendant enumeration and relationship BFS are not directly in the spec — they are downstream of it. Including them strengthens the eval (tests real graph-construction correctness, is less contaminated than parsing alone) but means parts of the behavior live in `technical-requirements-prompt.md` rather than the domain docs. This is a soft violation of "native behavioral contract" from `CHOOSING_EVALS.md` but matches how IGES handles `eval` and `roundtrip` subcommands.

## CHOOSING_EVALS Checklist

- **Documentation-first: partial.** The spec + harness contract cover parsing and validation fully. Ancestor/descendant/relationship queries are defined in the harness contract, not the spec, which is a partial miss on "native behavioral contract." Mitigable by keeping the query semantics simple and fully specified in `technical-requirements-prompt.md`.
- **Non-developer describable: pass.** A genealogist can plausibly ask for exactly this tool in plain language without any engineering guidance (see base prompt sketch).
- **Authoritative source material: pass.** The FamilySearch GEDCOM 5.5.1 PDF is the canonical reference, stable since 2019.
- **No solver code in corpus: pass.** The spec is prose + grammar, not a shipped reference implementation. No worked code appears in the PDF.
- **Behaviorally unambiguous: partial.** The tag/level grammar, CONT/CONC rules, and record structures are clearly specified. Date grammar edge cases and ANSEL character handling have known ambiguities that real parsers handle differently. The hidden suite must restrict to unambiguous cases or explicitly resolve ambiguities in the harness contract.
- **Deterministic scoring surface: pass.** JSON comparison, validation reports, and pedigree query outputs are all deterministic.
- **Independent failure modes: pass.** A broken date parser does not break pedigree queries; a broken ANSEL handler does not break UTF-8 parsing; a broken relationship BFS does not break `parse` or `validate`. Failure modes partition cleanly.
- **System-level complexity: pass.** ~2,000–3,000 LOC across line grammar, encoding, record parsers, date grammar, xref graph, JSON emitter, and query engine. Clears the ~1000 LOC floor.
- **Test-suite scalability: pass.** ~96 planned tests, above the 50-test floor, with genuine behavioral depth per category.
- **Contamination resistance: fail.** Abundant open-source implementations in every language, multiple JSON-emitting parsers whose output closely resembles any canonical schema we'd pick, published tutorials, mature reference fixtures. This is the eval's biggest weakness and would need explicit mitigation before it's worth building.
- **Reference implementation feasibility: pass.** Straightforward to build in C++ in the 2–3k LOC range; existing OSS in other languages confirms the domain is implementable at benchmark scale.
- **Reasonable harness fit: pass.** Pure CLI, file-in/file-out, no network, no GUI, no wall-clock dependencies. Fits the harness model directly.
- **Publicly distributable docs: fail (for 5.5.1) / pass (for 7.0).** 5.5.1's "copy for review" notice is a redistribution concern; GEDCOM 7.0's Apache 2.0 license resolves it. This is the most urgent open question for the eval.

## Summary

GEDCOM 5.5.1 is a strong structural fit for CLISpecBench on most axes — dense authoritative spec, deterministic scoring, natural non-developer voice, clean CLI contract, ~96 scorable tests, ~2–3k LOC reference implementation. Two real weaknesses make it a "propose and debate" rather than "obviously strong" candidate: (1) the spec's restrictive 5.5.1 copy-notice pushes us toward either a transcription-with-citations corpus or switching to GEDCOM 7.0 (Apache 2.0) at the cost of losing ANSEL and CONC as parser-complexity surface; and (2) contamination is materially worse than IGES or RS274 — mature, JSON-emitting parsers exist in every major language and the domain is highly pattern-match-friendly. If the contamination ceiling is accepted (and partly mitigated by emphasizing validation and pedigree-query correctness, not just parse-to-JSON) and the licensing question is resolved in favor of transcription or 7.0, GEDCOM is a reasonable third or fourth eval; if not, it's worth deferring in favor of a harder, less-contaminated format from the same "structured text interchange" class.
