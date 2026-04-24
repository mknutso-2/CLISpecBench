# New Eval Candidates — Analysis and Ranking

This document now combines two adjacent candidate-analysis passes:

1. the broad cross-domain slate currently tracked on `main`
2. a later format-heavy slate recovered from local WIP and reconciled here

They are kept together because several evals that were later prototyped in
this repo — especially `GEDCOM`, `LAS`, `MARC21`, and `SEGY` — were selected
from the second pass, while the first pass remains the better top-level view
of overall benchmark portfolio fit.

The broad cross-domain slate below is still the primary ranking for "what
should CLISpecBench add next?" The later format-heavy section is retained as a
focused appendix on large spec-shaped data formats. When the two analyses
disagree on a raw rank number, prefer the explanation over the number: the
first pass optimized for portfolio diversity and contamination resistance
across domains, while the second optimized for relative promise within a much
narrower cohort of file-format candidates.

Repository-cleanup intent follows the same distinction. Candidate-only
directories that are clearly abandoned should be removed from `Evals/`.
Directories for candidates that are merely conditional or deferred should stay.
Already-registered evals may also stay even when the candidate discussion is
negative, because repo cleanup and future-candidate ranking are not identical
questions.

The broad slate was drafted in a first pass, then critiqued by a second
opinion (Codex GPT-5.4 acting as skeptical reviewer; transcript in
[`codex-conversations/2026-04-20-22-33-new-eval-analysis-review.md`](../codex-conversations/2026-04-20-22-33-new-eval-analysis-review.md)),
then revised to converge on a joint ranking. Concrete changes from the
first-pass analysis:

- **Factual corrections applied to the underlying READMEs.**
  - DICOM: the original claim that "the three NEMA documents are freely
    redistributable" is materially overstated. NEMA's own policy
    ([dicomstandard.org/patent](https://www.dicomstandard.org/patent))
    grants a no-license right to read and implement the standard, but
    *reproduction* requires permission from the DICOM Secretariat. Fixed
    in [Evals/DICOM/README.md](DICOM/README.md).
  - GEDCOM: "5.5.1 finalized 2019" in the original was wrong. 5.5.1 was
    released in 1999, with a 2019 re-release as FamilySearch formalized
    the standard before GEDCOM 7.0 arrived. A 1999 standard with 20+
    years of continuous OSS tooling is much more contamination-prone
    than implied. Fixed in [Evals/GEDCOM/README.md](GEDCOM/README.md).
  - Tar: the README originally asserted the POSIX spec was "freely
    redistributable" in prose while marking the checklist item as
    partial — an internal contradiction. Resolved toward *partial* with
    the Open Group / IEEE copyright noted. Fixed in
    the former `Evals/Tar/README.md` candidate shell before that
    directory was removed.
  - MusicXML: the claim "Any agent that reaches for music21 has the
    entire task solved" was too absolute — music21 itself has filed
    bugs on the target semantics. Softened to "a capable agent can
    reproduce large parts of the required behavior by recalling
    music21's algorithm structure rather than reasoning from the W3C
    spec." Fixed in [Evals/MusicXML/README.md](MusicXML/README.md).
- **Methodology change.** The original single "hard-requirement fails"
  column conflated remediable paperwork (Gerber / DICOM redistribution)
  with structural impossibility (SMILES canonical-form
  non-determinism). Replaced with four columns — *fatal blocker*,
  *remediable blocker*, *ref-impl burden*, *contract leakage* — that
  isolate those axes.
- **Dual ranking.** The original published one order; this revision
  publishes two — **current state** and **if all remediable blockers are
  resolved** — so Gerber-with-permission and MusicXML-with-mitigation
  are not buried by their current blockers.
- **Ranking changes.** SAM moved from *hold* to *build later* (above
  DICOM — shorter spec, less IGES overlap, less authoring burden).
  MusicXML moved from *abandon* to *hold (conditional)* — contamination
  is still a structural concern but the composed-pipeline reasoning
  surface is genuine enough to keep the proposal alive pending a
  concrete mitigation plan.

The existing lineup — [`RS274`](RS274/README.md) and
[`IGES`](IGES/README.md) — already tests dense-spec comprehension on a
narrow 3D kinematics domain and a wide 80-column fixed-format CAD
schema. Any new eval should either push on a different behavioral axis,
cover a genuinely different domain with low-contamination source
material, or both.

---

## Candidates at a glance

| # | Eval | Domain | Est. tests | Est. LOC | Fatal blocker | Remediable blocker | Ref-impl burden | Contract leakage |
|---|------|--------|-----------:|---------:|---|---|---|---|
| 1 | [BibTeX](BibTeX/README.md) | Stack-language interpreter for bibliography styles | ~130 | 2,500–3,500 | — | — | moderate | low |
| 2 | [ICal](ICal/README.md) | Calendar recurrence semantics (RFC 5545) | ~102 | 1,800–2,200 | — | — | moderate | moderate (inlined VTIMEZONE is a harness choice) |
| 3 | [Gerber](Gerber/README.md) | PCB manufacturing files | ~75 | 2,500–3,500 | — | **yes — Ucamco redistribution** | moderate | low |
| 4 | [SAM](SAM/README.md) | Bioinformatics alignment records | ~95 | 1,200–1,800 | — | possibly (hts-specs license unclear) | low | low |
| 5 | [PostScript](PostScript/README.md) | Stack-language interpreter / graphics trace | ~99 | 2,000–2,800 | — | — | **high** (operator scope must be explicit) | moderate (published op list + arc-flattening rule) |
| 6 | [DICOM](DICOM/README.md) | Medical imaging binary format | ~91 | 1,800–2,800 | — | **yes — NEMA reproduction permission** | moderate | moderate ("no pixel decoding" is a harness choice) |
| 7 | [MusicXML](MusicXML/README.md) | Music notation ingestion | ~75 | 1,500–3,000 | — | possibly (contamination plan required) | moderate | low |
| 8 | [GEDCOM](GEDCOM/README.md) | Genealogy records | ~96 | 2,000–3,000 | — | ambiguous 5.5.1 license | moderate | **high** (pedigree queries are harness-defined) |
| 9 | `SMILES` | Chemistry notation | ~100 | 1,200–2,000 | **yes — canonical form is not deterministic across implementations** | — | moderate | low |
| 10 | `Tar` | POSIX archive format | ~96 | 1,500–2,500 | **yes — tutorial-level saturation** | possibly (Open Group/IEEE copyright) | low | **high** (GNU extensions + path safety are evaluator policy) |

**Column definitions.**

- *Fatal blocker* = a hard requirement that cannot be remediated without
  redefining the eval. Marking this kills the candidate.
- *Remediable blocker* = a hard requirement that fails now but has a
  concrete remediation path (permission request, transcription,
  adversarial-fixture program).
- *Ref-impl burden* = the relative cost of writing and maintaining at
  least one reference implementation plus 50+ hidden tests.
  *Low*/*moderate*/*high* is relative to RS274 (moderate) and WordCount
  (low).
- *Contract leakage* = how much behavior lives in
  `technical-requirements-prompt.md` rather than the native spec. Low
  is good; high means CLISpecBench is measuring "follow the eval
  author's instructions" as much as "understand the spec."

---

## Consensus ranking — current state

| Rank | Tier | Eval | Justification |
|---:|---|---|---|
| 1 | **Build now** | [BibTeX](BibTeX/README.md) | Best asymmetry in the set: ubiquitous `.bib` parsing but rare `.bst` execution; small authoritative corpus; strong system-level interpreter task. |
| 2 | **Build now** | [ICal](ICal/README.md) | Single RFC + the strongest published spec-vs-library divergence evidence (rrule.js #375/#309/#556, dateutil #1398) in the core task, so hidden RRULE tests measure reasoning, not recall. |
| 3 | **Build later** | [SAM](SAM/README.md) | Short dense spec, clean orthogonal subproblems (flags, CIGAR, MD-tag reconstruction, optional typing), lower authoring burden than DICOM, less IGES overlap. |
| 4 | **Build later** | [PostScript](PostScript/README.md) | Distinct behavioral axis and good native spec, but high contract-design and reference-implementation burden (operator scope, arc-flattening rule). |
| 5 | **Build later** | [DICOM](DICOM/README.md) | Real candidate, but the docs-rights story requires remediation before `prompt/docs/` can exist, and it overlaps IGES more than SAM or PostScript do. |
| 6 | **Conditional** | [Gerber](Gerber/README.md) | Architecturally strong; blocked today by Ucamco's spec-redistribution restriction. If permission lands, jumps to tier 1. |
| 7 | **Hold (conditional)** | [MusicXML](MusicXML/README.md) | Keep alive only with a concrete plan for (i) adversarial-fixture authoring outside the music21 / LilyPond / Verovio corpora and (ii) evidence that the major libraries miss the repeats-tempo-transpose chain. Without those, contamination dominates. |
| 8 | **Abandon** | [GEDCOM](GEDCOM/README.md) | Heavy contamination (1999 standard, 20+ years of OSS tooling) and too much interesting behavior lives in harness-defined relationship queries rather than the native spec. |
| 9 | **Abandon** | `SMILES` | Canonicalization is not deterministic across implementations (OpenSMILES §5 explicitly defers the algorithm); removing it leaves a much weaker eval that falls below the system-level bar. |
| 10 | **Abandon** | `Tar` | Tutorial-level saturation ("Build Your Own Tar" is Coding Challenge #54, field-offset tables are on Wikipedia); too much of the interesting behavior (GNU extensions, path-safety) lives in evaluator policy rather than POSIX text. |

## Consensus ranking — if all remediable blockers resolved

| Rank | Tier | Eval | Change vs. current | Justification |
|---:|---|---|---|---|
| 1 | **Build now** | [BibTeX](BibTeX/README.md) | — | Still the cleanest high-signal addition. |
| 2 | **Build now** | [ICal](ICal/README.md) | — | Still the strongest non-BibTeX candidate; the public-library bug trail maps directly to the core task. |
| 3 | **Build now** | [Gerber](Gerber/README.md) | **+3** (was #6 conditional) | Once permission lands, becomes a top-tier distinct-axis eval — stateful 2D graphics, strong domain persona, good system complexity. |
| 4 | **Build later** | [SAM](SAM/README.md) | −1 | License cleanup plus its lower authoring burden make it the best next "later" candidate. |
| 5 | **Build later** | [MusicXML](MusicXML/README.md) | **+2** (was #7 hold) | Only if the hold conditions are met; if someone proves real library divergence on the target chain and authors non-music21 fixtures, it becomes a serious build-later candidate with a richer composed pipeline than DICOM. |
| 6 | **Build later** | [PostScript](PostScript/README.md) | −2 | Still viable, but the subset-contract and ref-impl effort keep it behind Gerber/SAM/MusicXML once their blockers clear. |
| 7 | **Build later** | [DICOM](DICOM/README.md) | −2 | With NEMA permission, still useful, but IGES overlap and the multi-part corpus maintenance burden keep it below the other build-later candidates. |
| 8 | **Abandon** | [GEDCOM](GEDCOM/README.md) | — | License cleanup does not fix the core contamination or the harness-defined-queries problem. |
| 9 | **Abandon** | `SMILES` | — | Same deterministic-surface problem remains; not a paperwork blocker. |
| 10 | **Abandon** | `Tar` | — | Same saturation problem remains; not a paperwork blocker. |

---

## Ranked analyses (current state, best → worst)

### 1. BibTeX — **build now**

BibTeX 0.99c is the strongest candidate in the set. Its corpus
(Patashnik's `btxdoc` + `btxhak`) is two short, LPPL-redistributable
documents that together cover the full `.bib` grammar and the `.bst`
stack-language reference including all 37 built-ins. The non-developer
persona — an academic author who routinely runs BibTeX during LaTeX
compilation — is natural and does not require engineering framing.

The decisive advantage is the **sharp asymmetry between `.bib` parsing
and `.bst` execution in OSS**. `.bib` parsers exist in every major
language. `.bst` interpreters exist in about four places (BibTeX itself
in WEB/Pascal, pybtex, cl-bibtex, BiBTeXML), none of them extensively
tutorialized. Targeting `.bst` execution — the full stack machine with
`ITERATE`/`REVERSE`/`SORT` over a citation database, name-parsing
grammar, LaTeX accent macros, byte-compared `.bbl` output — puts this
eval in genuinely low-contamination territory while matching the
interpreter-construction character of RS274.

One honest flag: `btxhak` is close enough to a literate specification
of the built-ins that it sits nearer the "no solver code in corpus"
line than a typical dense spec does. Mitigation: if the README's
currently-optional `bibtex.pdf` (the typeset 0.99e processor) is
included, that's further toward the line — default should be
`btxdoc` + `btxhak` only, and reserve `bibtex.pdf` as a fallback if
built-ins prove under-specified.

**Recommendation: build.** Strongest candidate, slots cleanly alongside
RS274 as a second interpreter eval with a distinct language family and
scoring model (byte-exact `.bbl` vs. structured end-state JSON).

### 2. ICal — **build now**

ICal (RFC 5545) inherits every CLISpecBench advantage RS274 has —
single dense authoritative spec, domain-natural non-developer persona,
deterministic scoring, independent failure modes — and pushes on a
different behavioral axis. The crux is **verified spec-vs-library
divergence**: the README documents four specific RRULE bugs in
mainstream libraries (rrule.js #375, #309, #556; dateutil #1398), all
in the same adversarial BYSETPOS / BYDAY / WKST corner. A hidden test
suite targeting those corners is not just "the spec is hard" — it is
verified to be unsolved by the public libraries an agent might
pattern-match against, which is strong evidence the eval measures
reasoning rather than recall.

Honest partials: behavioral unambiguity (RFC 5545 has known errata in
exactly the hard corners) and contamination resistance (the major
libraries are everywhere in training data). Both are addressed in the
README's test-curation plan. Contract leakage is moderate — the
"inlined VTIMEZONE in test fixtures" decision is a harness choice
rather than a native-spec requirement — but it is small and
well-motivated (tzdata drift would otherwise defeat scoring
determinism).

**Recommendation: build.** Pair with BibTeX. Together with RS274 and
IGES, the resulting four-eval lineup covers modal G-code interpretation,
wide CAD schemas, stack-language interpretation, and recurrence-rule
expansion — four distinct spec-comprehension axes.

### 3. SAM — **build later**

SAM 1.6 has a short, dense, authoritative spec (~25 pages, samtools
group, public GitHub mirror) and a clean decomposition into orthogonal
subproblems: header parsing, 11-field mandatory parsing, 12-bit flag
decoding, CIGAR grammar, optional-field typing, MD-tag reconstruction,
region query. Independent-failure-mode discipline comes naturally —
a bug in flag decoding does not cascade into CIGAR or MD.

Concerns are real but smaller than DICOM's or PostScript's. Licensing
on the `hts-specs` repo is ambiguous (no explicit LICENSE file for the
spec documents); this is the same severity class as Tar's Open-Group
concern, and is remediable by transcription. Contamination is
medium-high (samtools, pysam, htsjdk, htslib, noodles are everywhere),
but CIGAR + MD-tag reconstruction has well-documented implementation
divergence — Heng Li's own blog posts on the `X` CIGAR operator and MD
subtleties are public artifacts of how hard getting this right is.

Originally downgraded to *hold* in the first-pass analysis; Codex
argued that SAM's lower authoring burden, shorter spec, and smaller
IGES overlap put it above DICOM in the build-later tier. Agreed.

**Recommendation: build later, above DICOM.**

### 4. PostScript — **build later**

PostScript Level 1 is the second interpreter candidate after BibTeX
and the only one that introduces a graphics-state model. The
trace-based scoring (emit operand stack, graphics state, current-path
op list rather than rasterize) is the right insight and sidesteps the
font/raster tarpit.

The cost is **contract design burden**. Four things require explicit
harness-level commitments before tests can be authored: the in-scope
operator list (~120 operators), arc-flattening (implementation-defined
in the Red Book), procedure serialization bounds, and `def`/`store` vs.
`bind` semantics. All of these are contract-design work the eval
author has to do up front; none are in the native Red Book. This puts
PostScript in a higher ref-impl-burden + contract-leakage class than
BibTeX or ICal.

Not worth ahead of BibTeX, because BibTeX gets you most of the
interpreter-class signal with a sharper spec and a smaller contract
surface. If a *second* interpreter eval is wanted after BibTeX ships,
PostScript is the natural pick.

**Recommendation: build later, after BibTeX reception justifies a
second interpreter eval.**

### 5. DICOM — **build later (remediable blocker)**

DICOM Part 10 with Parts 5 and 6 as the corpus is a strong
structural-parsing eval for binary files. Bootstrapping the File Meta
group under Explicit VR Little Endian to discover the dataset's
transfer syntax, then switching encodings and continuing, is a
genuinely non-trivial stateful parse. The three-document corpus is
unusual for CLISpecBench but justified — PS3.10 (file wrapper), PS3.5
(encoding), PS3.6 (data dictionary) have distinct roles and Part 6 is
*required* because implicit-VR decoding is undecidable without it.

Two concerns moved DICOM down from the first-pass position:

1. **Redistribution is not automatic.** Original claim that NEMA docs
   are "freely redistributable" was overstated (fixed). NEMA's own
   policy grants read/implement but requires permission for
   reproduction. Same severity axis as Gerber — remediable by (a)
   permission request, (b) transcription (RS274 pattern), or (c)
   external link + curated summary.
2. **Overlap with IGES** on the "parse a stateful file format into
   structured JSON" axis. Until IGES has production data showing
   whether that axis is saturated or discriminating, DICOM's
   marginal value over IGES is unclear.

**Recommendation: build later, after (a) NEMA redistribution path is
chosen and (b) IGES demonstrates the parse-to-JSON axis is still
discriminating at the top end.**

### 6. Gerber — **conditional (remediable blocker)**

Gerber X2 is architecturally excellent. Stateful 2D graphics with
nested step-and-repeat, an aperture macro sub-language, and an
attribute stack is a genuinely different behavioral axis from RS274
(3D kinematics) and IGES (record schema). The three-verb CLI (parse /
write / flatten) decomposes cleanly, ~75 independent tests, ~2,500–3,500
LOC. The non-developer persona (an electrical engineer sending files
to a PCB fab) is the cleanest in the set.

Single blocker: **Ucamco's copyright notice explicitly forbids
redistribution without prior written permission.** Three remediations
are possible — (a) written permission, (b) clean-room spec summary
(c) scope restricted to freely-redistributable third-party
descriptions. Until one of these lands, `prompt/docs/` cannot exist.

If permission lands, Gerber **jumps to build-now #3** in the
post-remediation ranking. Stateful 2D graphics is a distinct
behavioral axis the benchmark currently lacks; the contamination is
real but tractable via adversarial macro / SR / attribute-stack test
curation.

**Recommendation: conditional.** Do not author `prompt/docs/` until
the redistribution path is chosen. If Ucamco grants permission,
promote ahead of SAM/PostScript/DICOM.

### 7. MusicXML — **hold (conditional)**

*Changed from abandon to hold-conditional based on second-opinion
review.*

MusicXML has a clear non-developer persona (a music arranger) and a
rich calculation chain (divisions → beat times through repeats, tempo
changes, transposition, multi-voice `<backup>`/`<forward>`) that
chains several well-defined subtasks into a non-trivial composite.
The composed reasoning surface is the pitch for keeping this eval
alive — it is genuinely different from ICal's RRULE focus.

The concern is contamination. music21's public API maps closely onto
the proposed CLI, which makes pattern-matching tempting. The original
analysis marked this *abandon*; the revised position is *hold with
two explicit conditions*:

1. **Evidence of library divergence.** A cluster of public issues in
   music21 / MuseScore / Verovio that hit the precise target chain
   (repeat endings across tempo changes, concert-pitch transposition,
   multi-voice `<backup>`/`<forward>` timing) comparable to ICal's
   rrule.js/dateutil bug trail. The current evidence (music21 #355,
   MuseScore #28305, scattered release-note fixes) is suggestive but
   not conclusive.
2. **Adversarial-fixture plan.** Concrete strategy for authoring
   hidden-test scores outside the music21 / LilyPond / Verovio test
   corpora so an agent cannot pass by reproducing known passing
   fixtures.

Neither condition is structurally impossible. Both are work. Without
either, *abandon* is still the right call — the original finding
holds. With both, MusicXML moves to build-later tier 5 ahead of
PostScript and DICOM in the post-remediation ranking.

**Recommendation: hold pending a documented mitigation plan for both
conditions above.**

### 8. GEDCOM — **abandon**

GEDCOM 5.5.1 is similar in shape to IGES. Two concerns compound:

1. **Contamination.** The original analysis said "5.5.1 finalized
   2019"; corrected to 1999 (20+ years of continuous OSS tooling).
   Abundant JSON-emitting parsers exist in every language (ged4py,
   python-gedcom, gedcom4j, Gramps, Rust/Go/JS variants). Tamura
   Jones' parser catalog is exhaustive.
2. **Contract leakage is high.** Pedigree queries (ancestors,
   descendants, relationship path) are the main reasoning surface,
   but the *structure* of those queries is defined in
   `technical-requirements-prompt.md` rather than in the GEDCOM
   spec — the spec describes records and cross-references, not
   pedigree traversal. An agent is being asked to follow the eval
   author's query contract as much as to understand GEDCOM itself.

Unlike MusicXML, no saving-grace calculation chain offsets the
contamination. Unlike ICal, no evidence of library divergence on the
target behavior.

**Recommendation: abandon.** Even resolving the 5.5.1-vs-7.0 license
question does not address the core issues.

### 9. SMILES — **abandon**

The structural issue is that **canonical SMILES is not deterministic
across implementations**. OpenSMILES §5 explicitly declines to
specify the algorithm. RDKit, Open Babel, and Daylight produce
different canonical strings for the same molecule; the Daylight
algorithm itself has shifted across versions. Two academic papers
(Schneider 2015, O'Boyle 2012) exist specifically because the
disagreement is structural, not incidental.

This is a direct conflict with CLISpecBench's "deterministic scoring
surface" hard requirement. The recommended fallback — drop
canonicalization, score only parse + formula + weight — reduces the
eval to a parser + a periodic-table lookup, which is below the
system-level LOC floor and the adversarial-testability threshold.

Add to that a contamination fail (at least four explicit "build a
SMILES parser from scratch" tutorials — Depth-First in Rust,
Metamolecular, the aromaticity walkthrough, a generic AST
walkthrough — plus RDKit, OpenBabel, Indigo, CDK, pysmiles, Purr,
smiles-parser, SmilesDrawer), and the scope that keeps SMILES
deterministic is not large enough to be a system-level eval; the
scope that makes it system-level is not deterministic.

**Recommendation: abandon.** This is a *fatal* blocker — not
remediable by paperwork.

### 10. Tar — **abandon**

Tar is the cleanest contamination fail in the set. Unlike the other
candidates where contamination is at the library level, Tar is
saturated at the **tutorial level**: "Build Your Own Tar" is Coding
Challenge #54, Wikipedia documents the ustar field offsets, multiple
blog walkthroughs parse headers field-by-field. CPython ships
`tarfile.py` as pure Python stdlib; Go ships `archive/tar`.

The PAX edge cases (GNU `@LongLink`, base-256 size encoding,
unsigned-vs-signed checksum ambiguity, sparse-file headers) do offer
some discrimination signal, but the headline behavior — list and
extract a ustar archive — is so heavily tutorialized that the base
score ceiling is too high. Contract leakage is also high: GNU
extensions and path-safety rules are evaluator policy, not POSIX
text.

The internal contradiction in the original README (prose "freely
redistributable" vs checklist "partial") was resolved toward
*partial* with the Open Group / IEEE copyright noted.

**Recommendation: abandon.** The saturation is structural — no
paperwork fix helps. If an archive-format eval is desired in the
future, a less-tutorialized binary container (e.g. a proprietary
game/firmware format with a published spec) is a better starting
point.

---

## Recommendations summary

### Build next (current state)

1. **[BibTeX](BibTeX/README.md)** — low-contamination stack-language
   interpreter.
2. **[ICal](ICal/README.md)** — adversarial RRULE semantics backed by
   published library-divergence evidence.

### Build after that, in order

3. **[SAM](SAM/README.md)** — after ICal ships; shortest spec among
   the remaining candidates, smallest authoring burden.
4. **[PostScript](PostScript/README.md)** — only if appetite for a
   second interpreter eval after BibTeX; contract-design cost is real.
5. **[DICOM](DICOM/README.md)** — only after NEMA redistribution path
   is chosen and IGES shows the parse-to-JSON axis is still
   discriminating.

### Conditional (remediable blockers)

6. **[Gerber](Gerber/README.md)** — promote ahead of SAM/PostScript/
   DICOM if Ucamco grants redistribution permission.
7. **[MusicXML](MusicXML/README.md)** — promote to build-later tier
   if both contamination-mitigation conditions are met.

### Abandon

8. **[GEDCOM](GEDCOM/README.md)** — contamination + harness-defined
   queries.
9. **`SMILES`** — canonical-form non-determinism
   conflicts with a hard requirement; deterministic fallback scope
   too weak.
10. **`Tar`** — tutorial-level saturation, no
    paperwork remediation possible.

### Candidate-directory cleanup implied by this discussion

- Delete `Evals/SMILES/` and `Evals/Tar/`. They are candidate-only shells and
  both are abandoned for structural reasons rather than temporary blockers.
- `BGP4` and `EPUB` are also abandoned in the narrower format-heavy pass, but
  there are no corresponding directories to delete on the current `main`
  branch.
- Keep `DICOM`, `Gerber`, `MusicXML`, `PostScript`, and `SAM` because they are
  still conditional or deferred rather than rejected.
- Keep existing shipped eval directories such as `GEDCOM`, `LAS`, `MARC21`, and
  `SEGY`; their continued presence in the repo is a separate question from
  whether they would rank highly as brand-new candidates today.

---

## Observations on the candidate set

- **Contamination resistance is the hardest criterion to satisfy
  for mature public formats.** Seven of ten candidates marked
  contamination at least `partial`. The formats that tend to be
  contamination-resistant share three properties: (a) explicit
  tutorial absence, (b) library asymmetry (parsers common but
  interpreters/expanders rare), and (c) spec-vs-implementation
  divergence in the adversarial corner. BibTeX's `.bst` execution
  and ICal's RRULE semantics both hit all three. Gerber, SAM, and
  PostScript hit two of three. MusicXML, Tar, and SMILES hit none.

- **"Parse + emit JSON" is a saturated behavior.** Most candidates
  default to a parse-first CLI surface. The differentiation comes
  from what else the eval tests (execute, expand, canonicalize,
  reconstruct, flatten). BibTeX's `.bst` execution, ICal's RRULE
  expansion, DICOM's transfer-syntax bootstrap, PostScript's
  trace, Gerber's flatten, and SAM's MD-tag reconstruction all add
  a second axis that the parse task alone does not.

- **Redistribution is not reliably "pass" even for nominally open
  standards.** Four of ten candidates have live redistribution
  concerns (Gerber fails; DICOM requires Secretariat permission;
  GEDCOM 5.5.1 license is narrower than earlier revisions; SAM
  hts-specs repo lacks explicit LICENSE on the documents). The
  CLISpecBench transcription pattern (RS274's `RS274NGC.md`) is a
  viable workaround for several of these but adds real
  transcription work.

- **Three interpreter-class evals may be one too many.** BibTeX,
  PostScript, and RS274 all test "build a small interpreter for a
  domain-specific language." Once one or two are in service, the
  marginal signal from a third is unclear. This is why DICOM, SAM,
  and ICal rise in the revised ranking: they add genuinely
  different behavioral axes.

- **The "one order" fiction.** The first-pass analysis tried to
  publish a single ranking. That obscured the fact that several
  candidates have specific, actionable blockers (not "this isn't
  viable" but "this can't be built until X happens"). The
  current-state vs. post-remediation dual ranking is a better
  framing for maintainer planning — it says directly what work
  would unlock which candidate.

---

## Format-heavy slate — recovered and reconciled

A later narrower pass looked specifically at ten largely file-format-oriented
candidate evals:

- `GEDCOM`
- `LAS`
- `SEGY`
- `MARC21`
- `FITS`
- `VCF`
- `SPDX`
- `GerberX3`
- `EPUB`
- `BGP4`

That pass asked a different question from the broad ranking above: among
large public specs that look naturally like `inspect` / `render` /
`validate` / `roundtrip` tasks, which ones are the strongest next
experiments? The narrower cohort is why some ranks differ materially from the
broader cross-domain view above.

The recovered pass originally concluded:

- strongest within that narrowed cohort: `GEDCOM`, `LAS`, `SEGY`, `MARC21`
- later / conditional: `FITS`, `VCF`, `SPDX`
- blocked but interesting: `GerberX3`
- abandon for now: `EPUB`, `BGP4`

The table below preserves that information, but reframes it in light of the
current repo state and the broader candidate analysis above.

### Narrow-slate ranking and present interpretation

| Narrow rank | Eval | Earlier verdict | Present interpretation |
| ---: | --- | --- | --- |
| 1 | `GEDCOM` | Keep now | Attractive inside a format-only cohort because the spec is readable and the graph surface is naturally testable. In the broader slate, though, it still grades worse on contamination and contract leakage than the raw rank suggests. |
| 2 | `LAS` | Keep now | Still the strongest surviving outcome of that pass. Full-spec binary format, many independent failure axes, and a cleaner native contract than GEDCOM or MARC21. |
| 3 | `SEGY` | Keep now | Conceptually strong, but later dropped from active work once full official-spec mirroring looked less comfortable from a redistribution standpoint. |
| 4 | `MARC21` | Keep now | Still promising if the eval genuinely uses the full LOC corpus and tests more than transport-level parsing. The main under-modeling risk is not the standard; it is the authored eval surface. |
| 5 | `FITS` | Keep later / conditional | Remains a plausible future binary-format eval, but contamination and convention drift are still real enough that it should stay behind LAS. |
| 6 | `VCF` | Keep later / conditional | Same basic conclusion still holds: useful structure, but too much real-world behavior is effectively anchored on `htslib` and its descendants. |
| 7 | `SPDX` | Keep later / conditional | Viable only if it becomes a graph/canonicalization/relationship task rather than a schema-validation task. |
| 8 | `GerberX3` | Keep later / blocked | Best read today as the narrower sibling of the broader `Gerber` candidate above. The current `Gerber` analysis supersedes this one, but the redistribution blocker remains the common issue. |
| 9 | `EPUB` | Abandon for now | Still abandoned for the same reason: too much risk that the task collapses into ZIP/XML/HTML plumbing and `EPUBCheck` agreement. |
| 10 | `BGP4` | Abandon for now | Still weak for this benchmark track because the implementation surface is crowded and the eval boundary is easy to underspecify. |

### Reconciliation notes

- `LAS` is the clearest durable win from the recovered pass. Even after the
  broader ranking and the later implementation work, it still looks like one
  of the best large binary-spec candidates in the repo.
- `MARC21` remains worth pursuing, but only if the eval is written against the
  full official HTML corpus and the tests cover the field-by-field semantics of
  the standard rather than a compressed transport-profile summary.
- `GEDCOM` is where the two analyses diverge most sharply. The recovered
  format-heavy pass liked it because GEDCOM files are small, the graph shape is
  natural, and the official FamilySearch docs are readable. The broader pass
  penalized it because relationship-query work tends to migrate into
  harness-defined semantics rather than staying inside the native standard.
- `SEGY` was a strong technical candidate in the narrow pass, but it no longer
  has the same practical standing because the decision to require full
  official-spec documents in-repo makes its documentation story materially less
  attractive than `LAS` or `MARC21`.
- `GerberX3` and the broader `Gerber` candidate are not contradictory analyses;
  they are two views of the same family. The current broader `Gerber`
  evaluation should be treated as the authoritative one.

### Focused recommendations from the format-heavy pass

1. Keep investing in `LAS` if the goal is to find a hard full-spec binary
   format eval with many independent failure modes.
2. Keep `MARC21` in play, but only under a strict "full official corpus, no
   compressed evaluator summaries in `prompt/docs/`" discipline.
3. Treat `FITS`, `VCF`, and `SPDX` as reserve candidates rather than near-term
   priorities.
4. Leave `EPUB` and `BGP4` abandoned unless the benchmark goals change.
5. Treat `GEDCOM` as historically important to the repo's prototyping path, but
   not as strong evidence that it should outrank the broader cross-domain
   candidates above.

---

*This analysis was revised in consultation with Codex GPT-5.4 acting
as skeptical reviewer. The review transcript is at
[`codex-conversations/2026-04-20-22-33-new-eval-analysis-review.md`](../codex-conversations/2026-04-20-22-33-new-eval-analysis-review.md).*
