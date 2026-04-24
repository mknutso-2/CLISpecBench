# DICOM

DICOM Part 10 structural parser + data-element query eval for CLISpecBench. Agents receive NEMA's DICOM standard (Parts 5, 6, 10) and must produce a CLI tool that parses a DICOM Part 10 file, exposes its dataset as JSON, and answers (group, element) tag queries.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt, tests, or reference implementation yet.

## Why this eval

Medical imaging interchange runs on DICOM Part 10 files: the 128-byte preamble, `DICM` magic, File Meta Information group, and a dataset of tagged data elements encoded under one of a handful of transfer syntaxes. The format is dense, binary, and genuinely stateful — a parser has to interpret the File Meta group first (encoded as Explicit VR Little Endian) to learn which transfer syntax the rest of the dataset uses, then switch encodings and continue. That bootstrapping sequence, combined with sequence nesting (SQ with item/sequence delimiters), private tags without VRs, and encapsulated pixel data, makes DICOM a plausible mid-to-heavy spec-comprehension task along the same axis as RS274 and IGES.

The audience framing is strong. A radiology IT administrator inspecting files off a scanner has a concrete, non-developer use for this tool — "open this file, show me what it claims to be, let me ask for the Patient ID or the Modality" — and that framing lets the base prompt stay in domain-expert voice without smuggling in parser guidance. The behavior is anchored in three authoritative NEMA documents that are freely downloadable for reading and implementation without a license, but whose *reproduction* requires permission from the DICOM Secretariat (NEMA's own policy — see [dicomstandard.org/patent](https://www.dicomstandard.org/patent)). That is a remediable blocker, not a clean pass on the "publicly distributable docs" criterion — see Risks below.

The eval deliberately scopes out image decoding. DICOM's pixel-data universe (JPEG, JPEG 2000, JPEG-LS, RLE, plus raw variants) is a separate compression-format tarpit that would blow up the test surface without adding spec-comprehension signal. The agent must correctly *locate and skip* encapsulated pixel data (parsing the fragmented Item structure under undefined length) and emit a structural reference to it, but does not decode pixels. This keeps the eval focused on the structural parsing story that Part 10 and Part 5 describe.

## Documentation Corpus

The corpus lives in `prompt/docs/` and draws from three separate NEMA PS3.x documents — these are *different* publications that ship under the same "DICOM standard" umbrella:

- **PS3.10 — Media Storage and File Format for Media Interchange.** Defines the Part 10 file wrapper: 128-byte preamble, `DICM` magic, File Meta Information group (0002,xxxx), and the rule that File Meta is always Explicit VR Little Endian even when the dataset that follows is not. This is the shortest of the three and is the structural spine of the eval.
- **PS3.5 — Data Structures and Encoding.** Defines data elements, value representations (VRs), the Explicit VR and Implicit VR Little Endian transfer syntaxes, Big Endian (retired but still present in real files), sequence (SQ) nesting with item/sequence delimitation tags (FFFE,E000 / FFFE,E00D / FFFE,E0DD), undefined length encoding (FFFFFFFFH), and encapsulated pixel data framing.
- **PS3.6 — Data Dictionary.** Maps every standard (group, element) tag to its VR, VM, and keyword. PS3.6 is **mandatory** for this eval: under Implicit VR Little Endian, the element stream carries no VR bytes and the parser must look up each standard tag's VR in Part 6 to know how to decode the value. Without Part 6 the implicit-VR path is undecidable for standard tags. Private tags (odd group numbers) remain ambiguous in implicit VR — the eval handles that by requiring Unknown (UN) treatment, matching spec guidance in PS3.5 §6.2.2.

All three documents are published openly at `dicom.nema.org` (HTML + PDF) and `dicomstandard.org/current`, are updated several times a year, and carry NEMA's copyright. NEMA's policy ([dicomstandard.org/patent](https://www.dicomstandard.org/patent)) is that no license is required to read or implement the standard, but *reproduction* of the publication requires permission from the DICOM Secretariat. That means checking a verbatim copy into `prompt/docs/` is not automatic — options are (a) request redistribution permission from NEMA, (b) transcribe the parts-we-use into our own Markdown and cite heavily (the structure and VR tables are factual; the prose is not), or (c) scope to the freely-referenced text in third-party implementer guides. Rough corpus size: PS3.10 is the smallest (tens of pages of structural content); PS3.5 is the bulk of the parsing rules (hundreds of pages, much of it tabular VR definitions); PS3.6 is a huge tag table (thousands of entries) but is structurally simple — a single table we can include as-is, and the agent is expected to read it mechanically rather than linearly.

## Base Prompt (sketch)

> I run IT for a radiology department. Every day we get DICOM files off our CT and MR scanners — sometimes on CD, sometimes pushed to a share — and when something looks off I want to be able to open the file and see what it actually contains without waiting on the PACS vendor. Please build me a command-line tool that reads a DICOM file and tells me what's inside: who the patient was, what kind of scan it is, what the scanner was, how the pixel data is stored, the whole tag list. I also want to be able to pull a specific value by its tag — for example, Modality at (0008,0060) or Patient ID at (0010,0020) — so I can script simple checks across a folder. The tool should not try to show me the image itself; I have a viewer for that. I just need to see the file's structure and any of its tag values, including nested sequences like the one for Referenced Study. The file format is described in the DICOM standard documents I've provided.

This framing stays squarely in non-developer voice: "I want to see what's inside," "pull a specific value by its tag," "nested sequences like Referenced Study." The technical contract (exit codes, JSON schema, CLI flags) lives in `technical-requirements-prompt.md`, not here.

## Technical Requirements (sketch)

Single binary, two subcommands, JSON output on both success and error, RS274-style exit codes (0 success, 1 invalid input, 2 internal error).

| Subcommand | Purpose |
|---|---|
| `dicom parse --input <file.dcm> --output <out.json>` | Parse full Part 10 file into canonical DICOM-JSON. |
| `dicom query --input <file.dcm> --tag <gggg,eeee> --output <val.json>` | Extract a single data element by tag (supports dotted path for nested sequences, e.g. `0008,1110.0.0008,1150` for item 0 of Referenced Study Sequence). |

Canonical JSON schema at high level:

- `file_meta`: object keyed by tag string (`"0002,0010"`), each value `{vr, value, length}`. Always parsed under Explicit VR Little Endian per PS3.10.
- `transfer_syntax_uid`: the UID found in `(0002,0010)`, reported separately for convenience.
- `dataset`: object keyed by tag string, each value `{vr, value, length, items?}`. For SQ elements, `items` is an array of nested datasets. Values are rendered per-VR: numeric VRs as numbers, string VRs as strings, binary VRs (OB/OW/OF/OD/UN) as `{inline_base64?, length, skipped: true|false}`.
- `pixel_data`: if `(7FE0,0010)` is present, a structural stub `{vr, encapsulated: bool, num_fragments?, length, skipped: true}` — **no pixel decoding**.
- `warnings`: array of structural anomalies that do not fail the parse (unknown private VRs, trailing bytes, etc.).

**Scope — no pixel decoding.** The agent must parse the pixel data element's *framing* correctly (defined-length OB/OW for native transfer syntaxes, encapsulated fragments under undefined length for compressed syntaxes — counting fragments, skipping bytes, terminating on the Sequence Delimitation Item), but must not attempt to decompress JPEG/JPEG 2000/JPEG-LS/RLE, compute pixel arrays, apply rescale slopes, or render images. Tests assert only on the structural stub. Any mention of "image," "photometric interpretation decoding," or "pixel buffer" is out of scope.

**Transfer syntaxes in scope:** Implicit VR Little Endian (1.2.840.10008.1.2), Explicit VR Little Endian (1.2.840.10008.1.2.1), Explicit VR Big Endian retired (1.2.840.10008.1.2.2), and structural pass-through for the common encapsulated compressed syntaxes (JPEG baseline, JPEG 2000, RLE Lossless) where the parser recognizes the syntax, frames pixel data as encapsulated, and skips fragment payloads. Deflated Explicit VR Little Endian (1.2.840.10008.1.2.1.99) is a stretch goal — it wraps the post-File-Meta dataset in zlib and may be scoped out.

**Other CLI:** `--transfer-syntax-override <uid>` to force a syntax when File Meta is missing or malformed; `--max-value-length <bytes>` to cap inline base64 in output; no network, no DIMSE, no DICOMDIR file-set walking.

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| Preamble + DICM magic + File Meta group parsing | ~6 |
| Transfer syntax selection and switching (Implicit/Explicit LE, Explicit BE) | ~8 |
| Per-VR decoding (UL, US, SL, SS, FL, FD, DS, IS, PN, DA, TM, DT, UI, CS, LO, SH, LT, ST, UT, AE, AS, AT, OB, OW, OF, OD, UN) | ~28 |
| Multi-valued elements + VM handling (per Part 6 VM column) | ~5 |
| Sequences: defined length, undefined length with item delimiters, nested sequences | ~10 |
| Private tags: odd group, private creator, implicit-VR UN fallback | ~6 |
| Encapsulated pixel data framing (fragment counting, skipping, delimiter termination) | ~5 |
| Big Endian byte-order handling on numeric VRs and tag bytes | ~4 |
| `dicom query` subcommand: flat tag, dotted path into SQ, missing tag, malformed tag | ~6 |
| Malformed-input handling (bad preamble, missing DICM, truncated element, bad length, exit-code 1 + diagnostic) | ~8 |
| Warnings surface (trailing bytes, unknown private VR, retired VR) | ~3 |
| Build + CLI contract smoke | ~2 |
| **Total** | **~91** |

This comfortably clears the ~50-test floor from `CHOOSING_EVALS.md` and the RS274/IGES precedent. The surface is wide enough to sustain independent failure modes: a bug in implicit-VR decoding fails its own block without taking down Big Endian or sequences or the query subcommand.

## Implementation Size Estimate

A minimal but compliant reference implementation covering the scope above — Part 10 file meta bootstrap, three transfer syntaxes, full VR decode table from Part 6, sequence handling, private-tag fallback, encapsulated pixel framing, JSON emission, and the `query` subcommand — is estimated at **~1,800–2,800 LOC in C++ or Python**, plus a ~4,000-entry Part 6 tag table (generated, not hand-written, and counted separately).

Grounding:

- **pydicom** (pure-Python, full-featured including pixel decode, DICOMDIR, networking via pynetdicom sibling): substantially larger than our scope, with reading/writing, dataset mutation, and many VR paths. Our scope is a structural-read-only subset of pydicom's file-I/O layer.
- **suyashkumar/dicom** (Go, ~994 GitHub stars): a focused read-and-write parser. Its `cmd/dicomutil` CLI plus parser core is the closest architectural analog to the proposed reference implementation and lands in the low thousands of LOC.
- **chafey/dicom-parser-rs** and **Enet4/dicom-rs**: Rust parsers in the same size band; `dicom-rs` is a multi-crate ecosystem (parser, object model, pixel data, encoding) and is larger than our target scope.
- **dcmjs** / **cornerstonejs/dicomParser**: JS parsers focused on Part 10 structural reading only, without networking or DIMSE, are in the ~2–3k LOC range and are a fair match for what this eval is asking for.
- **DCMTK** (C++, 30 years old, 20+ libraries) is a bad LOC reference — it includes DIMSE, print management, SCU/SCP, structured reporting, and many other scopes we are explicitly not evaluating.

This clears the "roughly 1000 LOC" system-complexity floor in `CHOOSING_EVALS.md`.

## Contamination & OSS Landscape

**Specific implementations found:**

- [pydicom/pydicom](https://github.com/pydicom/pydicom) — Python, pure-Python, full-featured (read/write/modify, pixel decode, file-sets). The dominant Python DICOM library and the most likely contamination source for Python-language submissions. Widely used in Kaggle notebooks and medical-imaging tutorials.
- [DCMTK/dcmtk](https://github.com/DCMTK/dcmtk) — C++, first commit 1995, estimated ~300 person-years of effort (Open Hub COCOMO). Massive scope beyond structural parsing. Likely well-represented in training data as reference prose but implementations are sprawling enough that memorized "copy DCMTK" is not a viable shortcut to pass an 80-column-tight test suite.
- [fo-dicom](https://github.com/fo-dicom/fo-dicom) — C# / .NET. Popular in Windows medical-imaging stacks.
- [dcm4che](https://github.com/dcm4che/dcm4che) — Java. Server-oriented; more DIMSE than pure Part 10 parsing.
- [cornerstonejs/dicomParser](https://github.com/cornerstonejs/dicomParser) / [dcmjs](http://dcmjs.org/) — JavaScript. `dicom-parser` on npm reports 125 downstream dependents; focused on Part 10 structural read.
- [suyashkumar/dicom](https://github.com/suyashkumar/dicom) — Go, ~994 stars. A clean, focused read/write parser with a CLI (`dicomutil`).
- [Enet4/dicom-rs](https://github.com/Enet4/dicom-rs) — Rust multi-crate ecosystem (parser, objects, pixeldata, encoding). Most polished Rust option.
- [chafey/dicom-parser-rs](https://github.com/chafey/dicom-parser-rs) — Rust, streaming-oriented, smaller than dicom-rs.
- [GoogleCloudPlatform/go-dicom-parser](https://github.com/GoogleCloudPlatform/go-dicom-parser), [grailbio/go-dicom](https://github.com/grailbio/go-dicom), [gradienthealth/dicom](https://github.com/gradienthealth/dicom) — other Go parsers.

**Tutorials / walkthroughs:**

- [DICOM is Easy](https://dicomiseasy.blogspot.com/) — long-running blog with multi-chapter DICOM intro, transfer syntax deep-dives, networking walkthroughs. High-level but extensively cited.
- [Saravanan Subramanian's DICOM tutorials](https://www.saravanansubramanian.com/dicom/) — "Making Sense of the DICOM File" style walkthroughs in .NET (fo-dicom) and Java (PixelMed). Shows file layout and VR handling with working code.
- [Innolitics' DCMTK overview](https://innolitics.com/articles/overview-of-DCMTK-the-DICOM-toolkit/) and the Innolitics DICOM Standard Browser.
- [Leadtools DICOM C API help](https://www.leadtools.com/help/sdk/dicom/api/) — vendor docs with detailed Part 10 structure explanations that have been indexed widely.
- [plastimatch DICOM tutorial](https://plastimatch.org/dicom_tutorial.html), [nibabel DICOM intro](https://nipy.org/nibabel/dicom/dicom_intro.html) — academic/scientific-imaging walkthroughs.
- Kaggle notebooks and Medium posts on pydicom basics (high volume, but they teach "how to *use* pydicom," not how to parse bytes from scratch).

**Contamination risk:** **medium-high.** DICOM is older, better-documented, and more widely tutorialized than either RS274 or IGES. The file-format layer (preamble, DICM, File Meta, Explicit VR LE) is especially well-covered; a frontier agent will almost certainly recognize it by pattern. *However*, the contamination threat is uneven:

- The generic "recognize a DICOM file" task is saturated.
- The bytes-accurate sequence-delimiter + undefined-length + encapsulated-pixel-framing + implicit-VR-data-dictionary-lookup path is much less saturated — very few tutorials walk through all of it together, and most of the hardest tests live there.
- Private-tag UN fallback, Big Endian on numeric VRs, and the exact dotted-path query semantics are eval-specific and cannot be lifted from a tutorial.

The eval design should lean on hidden tests in the less-saturated corners (sequences with undefined length, encapsulated framing, private tags, Big Endian, malformed-input diagnostics) rather than on happy-path Patient ID retrieval. Contamination is real but manageable — on par with IGES structural parsing, less severe than a "write a JSON parser" eval would be.

## Risks and Open Questions

- **Part 6 as data rather than prose.** The data dictionary is a 4000+ row table. Shipping it verbatim to the agent is fine (structured, not prose) but the agent must handle a large mechanical lookup surface. We should commit to a single frozen DICOM edition (e.g. 2025e) and pin the tag table; otherwise minor yearly additions create test churn.
- **Private-tag semantics.** PS3.5 §6.2.2 says unknown elements take VR `UN`, but real-world private tags are messy. The eval must state explicitly: "under Implicit VR, private tags are decoded as UN (binary pass-through)"; tests must not assert on private-tag VR beyond that.
- **Encapsulated pixel data gotcha.** There is a known issue (see pydicom issue #1140) where a fragment's payload can contain the four bytes `FE FF DD E0` and fool a naive delimiter scan. Tests probing this edge case are legitimate but need careful framing to avoid punishing reasonable implementations that haven't yet special-cased it.
- **Big Endian realism.** Explicit VR Big Endian was retired in 2006 but files in the wild still exist. Including it in scope is defensible; excluding it simplifies the agent's byte-swap logic. A call either way is needed.
- **Transfer syntax breadth.** Where to cut encapsulated syntaxes? The proposed cut is "frame them structurally, skip payload." Deflated LE (zlib-wrapping the dataset) is borderline — decoding it is small but it's a second byte-stream layer. Suggest excluding Deflated in v1.0.
- **Corpus redistribution.** NEMA's policy ([dicomstandard.org/patent](https://www.dicomstandard.org/patent)) grants a no-license right to read and implement the standard but requires permission from the DICOM Secretariat for reproduction. Options before shipping `prompt/docs/`: (a) request written redistribution permission, (b) transcribe the parts we use into our own Markdown (RS274 pattern), or (c) link externally + ship a curated implementer-guide summary. This is on the same severity axis as the Gerber redistribution concern, not a resolved pass.
- **Sample files.** David Clunie's collection and the DCMTK test images are standard, but their licenses vary per file. The eval's hidden test suite should synthesize minimal DICOM files from scratch (the reference implementation's writer path) for most tests, and only reference real-world corpora as smoke fixtures.

## CHOOSING_EVALS Checklist

- **Documentation-first:** **pass.** Parts 5, 6, 10 together are a self-sufficient behavioral spec for the in-scope subset. No unstated lore required.
- **Non-developer describable:** **pass.** Radiology IT admin is a credible domain-expert persona with a natural reason to inspect DICOM files. The base-prompt sketch above stays in that voice without smuggling parser guidance.
- **Authoritative source material:** **pass.** NEMA DICOM is *the* authoritative reference; PS3.10, PS3.5, PS3.6 have been the standard since the 1990s and are updated on a predictable cadence.
- **No solver code in corpus:** **pass.** NEMA docs describe the byte layout and rules; they do not ship an executable parser or extensive pseudo-code. Tables of VRs and tags are data, not code.
- **Behaviorally unambiguous:** **partial.** Most of the structural layer (preamble, File Meta bootstrap, VR encoding rules, sequence delimitation) is sharp. Edges (private tags with no VR under implicit VR, truncated file recovery, encapsulated-fragment-with-embedded-FFFE bytes) have known real-world ambiguity. Mitigation: pin an explicit scope in `technical-requirements-prompt.md` for each ambiguous case (e.g. "private implicit-VR elements decode as UN"; "truncated elements at end of dataset emit a warning and return what was parsed").
- **Deterministic scoring surface:** **pass.** JSON output keyed by tag string, with per-VR canonical value formatting, is directly comparable. No wall-clock or nondeterminism.
- **Independent failure modes:** **pass.** Sequences, private tags, Big Endian, query path, and malformed-input diagnostics are genuinely independent. A bug in one does not cascade into the others the way a bad parser state machine in a single-pass tokenizer would.
- **System-level complexity:** **pass.** Estimated ~1,800–2,800 LOC reference implementation clears the "roughly 1000 LOC" floor, and the architecture is genuinely multi-module (byte reader, VR decoders, sequence stack, data dictionary, JSON emitter, CLI).
- **Test-suite scalability:** **pass.** ~91 tests sketched above, well clear of the 50-test floor; the VR decode axis alone can be expanded indefinitely.
- **Contamination resistance:** **partial — medium-high risk.** DICOM is older and more tutorialized than RS274 or IGES. Happy-path Part 10 reading is likely memorized by frontier agents. Mitigation: concentrate hidden tests in the less-saturated corners (undefined-length sequences, encapsulated framing edge cases, private-tag UN, Big Endian numeric swapping, exact dotted-path query semantics, malformed-input diagnostics). This is worse than RS274's contamination profile but comparable to IGES's.
- **Reference implementation feasibility:** **pass.** Scope is well-bounded; existing OSS parsers (pydicom, suyashkumar/dicom, dicom-rs) demonstrate that a structural-read-plus-query tool is tractable in every target language.
- **Reasonable harness fit:** **pass.** Local files in, JSON out, CLI-driven, no network, no GUI, no hosted services, deterministic. Identical harness shape to RS274 and IGES.
- **Publicly distributable docs:** **partial.** NEMA publishes DICOM openly at `dicom.nema.org` and grants a no-license read/implement right, but per [dicomstandard.org/patent](https://www.dicomstandard.org/patent) *reproduction* of the publication requires permission from the DICOM Secretariat. Remediation is one of (a) written permission from NEMA, (b) transcription of the parts we use into our own Markdown (the RS274 pattern), or (c) linking externally + shipping a curated implementer-guide summary.

## Summary

DICOM Part 10 structural parsing is a credible CLISpecBench candidate in the RS274/IGES tier: dense authoritative spec (three NEMA publications), a natural non-developer persona (radiology IT admin), deterministic JSON-output scoring, ~1,800–2,800 LOC of reference implementation, and ~90+ independent-failure-mode tests. Two risks gate a v1.0: **redistribution rights** (NEMA grants read/implement but not reproduction without Secretariat permission — same severity axis as Gerber) and **contamination** (DICOM is older and better-tutorialized than the sibling evals, and happy-path Part 10 reading is likely saturated in training data). Mitigating contamination requires the hidden test suite to concentrate on the less-saturated corners (undefined-length sequences, encapsulated pixel framing, private-tag UN fallback, Big Endian, precise dotted-path query semantics, malformed-input diagnostics). Scope is sharply bounded by the explicit "no pixel decoding" rule, which keeps the eval about structural byte-level comprehension of the DICOM standard rather than the separate compression-format tarpit of modality-specific image codecs. Worth building a v1.0 shell to validate, after the redistribution path is chosen.
