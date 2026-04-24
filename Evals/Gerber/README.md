# Gerber

Gerber X2 PCB-manufacturing file-format eval for CLISpecBench: agents receive
Ucamco's Gerber Layer Format Specification and must produce a CLI tool that
parses Gerber files into a canonical JSON representation, re-emits conforming
Gerber, and flattens the image down to a polyline list.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt,
> tests, or reference implementation yet. The single biggest open question
> (spec redistribution) is called out in **Risks and Open Questions** and in
> the checklist; do not start authoring `prompt/docs/` until that is resolved.

## Why this eval

Gerber sits in a near-ideal sweet spot for CLISpecBench along one axis that
the current lineup underweights: **2D image semantics with stateful modal
parsing on top of a text format**. RS274 tests modal state and kinematics for
a 3D motion simulator; IGES tests a wide 87-entity record schema on an
80-column fixed format; Gerber tests neither of those but does test something
they do not — a running 2D graphics machine with a stream of coordinate
commands, a stateful aperture table, a macro language that expands to
primitives, a block-level `SR` (step-and-repeat) nesting construct, a `G36`
region-fill mode, and an attribute layer (`.FileFunction`, `.AperFunction`,
`.N`, `.P`, ...) on top. The closest family member in the benchmark is IGES
(CAD interchange), but Gerber's behavioral surface is much less "schema
walk" and much more "interpret this program."

The non-developer audience is also unusually clean. An electrical engineer
who emails Gerbers to a PCB fab house every month has strong, concrete,
operational intuitions about what the tool should do — "open my KiCad top-copper
file, render it, tell me the drills, re-export it clean" — without needing any
software-engineering framing. That makes the base-prompt writable in the
`Eval-Design.md` §5.3 non-developer voice without smuggling in developer
guidance.

The honest concern, and the reason this README is a proposal rather than an
initial commit, is licensing: **Ucamco's specification is not redistributable
without prior written permission**. That is not a minor logistics issue — it
collides directly with CLISpecBench's "Publicly distributable docs" hard
requirement. The rest of this document proceeds as if that gate can be
passed (e.g., via a licensing request to Ucamco, or by authoring a
cleanly-derived spec summary) and sketches what the eval would look like on
the other side of that gate.

## Documentation Corpus

The spec intended for `prompt/docs/` is **The Gerber Layer Format
Specification, Revision 2024.05**, published by Ucamco. Canonical URL:
[https://www.ucamco.com/en/gerber/downloads](https://www.ucamco.com/en/gerber/downloads).
The PDF is roughly 3.2 MB. Exact page count was not recoverable via text
scraping (the file is a linearized PDF with compressed streams), but every
recent revision has run in the 100–200 page range; gerbv's maintainer notes
describe it growing from "60 to over 200 pages" across the format's lifetime.

Supporting documents that Ucamco publishes separately from the main spec and
that would belong alongside it in `prompt/docs/`:

- **Gerber Layer Format PEG grammar** — Ucamco publishes a formal
  parsing-expression grammar alongside the prose spec. This is an unusually
  clean artifact for a CLISpecBench doc corpus: it is dense, authoritative,
  and directly actionable by an agent. It would make the `prompt/docs/`
  directory meaningfully stronger than "just the PDF."
- **Gerber Job Format Specification, Revision 2020.08** (optional) — only
  relevant if the eval scope extends to the `.gbrjob` sidecar file that
  names the layer stack. The baseline eval does not require this.

**Redistribution.** The Gerber specification PDF explicitly states: *"Ucamco
owns copyrights in this document. All rights reserved. No part of this
document or its content may be re-distributed, reproduced or published,
modified or not, translated or not, in any … [form without prior written]
permission from Ucamco."* Ucamco additionally states that copyright is
retained specifically "to maintain the integrity of the standard." Third
parties **have** re-hosted older revisions of the PDF (notably the PyGerber
docs site hosts the 2020.09 revision), but that is not a green light — it
is third-party behavior that Ucamco has not publicly endorsed. Before
committing the spec to `prompt/docs/`, we should either (a) get written
permission from Ucamco, or (b) author a clean-room spec summary that the
eval can own and redistribute.

## Base Prompt (sketch)

Voice is a working electrical engineer at a small hardware shop, not a
software engineer. Sketch:

> We send PCB fabrication files to JLCPCB every few weeks. I'd like a
> command-line tool I can point at one of those Gerber files and get a clean
> machine-readable summary back: the list of shapes on the board, what
> aperture each one was drawn with, which attributes were set, where any
> step-and-repeat blocks expanded to, and the units. I'd also like it to
> write the file back out again so I can confirm it round-trips, and to
> flatten the whole image down to a plain list of line segments and arcs
> that I can pipe into another tool. Treat the Gerber Layer Format
> Specification (revision 2024.05) as the authoritative reference — my
> files come out of KiCad and Altium and are all X2 with attributes.

This gets the three operational verbs (**parse**, **re-emit**, **flatten**)
from a domain practitioner's mouth without needing to borrow software-craft
vocabulary.

## Technical Requirements (sketch)

Single binary (default name `gerber`) with three subcommands, all JSON-out,
all following the RS274/IGES exit-code convention (0 success, 1 invalid
input, 2 internal error):

| Subcommand | Purpose |
|---|---|
| `gerber parse --input <file.gbr> --output <out.json>` | Parse to canonical Gerber-JSON |
| `gerber write --input <file.json> --output <out.gbr>` | Emit conforming X2 Gerber |
| `gerber flatten --input <file.gbr> --output <polylines.json>` | Expand SR, apertures, macros, and regions down to a flat polyline/arc list |

Canonical JSON schema (high-level, harness-contract level — behavioral
details belong in the prompt, not here):

- `format`: number format, unit (`in`|`mm`), zero-suppression mode.
- `attributes`: file attributes (e.g. `.FileFunction`, `.Part`,
  `.GenerationSoftware`) as a flat map.
- `apertures`: array of aperture records, each `{ d_code, template,
  parameters, aperture_attributes }` where `template` is one of the four
  standard templates (`C`, `R`, `O`, `P`) or the name of a user-defined
  macro.
- `aperture_macros`: array of macros, each `{ name, primitives }`, where
  primitives carry type codes (1, 4, 5, 6, 7, 20, 21, 22), exposure,
  numeric expressions, and rotation.
- `graphics`: time-ordered array of graphical operation records
  (`{ op: "draw"|"arc"|"flash"|"region_start"|"region_end"|... , x, y,
  i?, j?, d_code?, object_attributes? }`), carrying exactly the modal state
  that was active at the time of the op after modal-state resolution.
- `step_repeat_blocks`: nested, not flattened — the `SR` block
  boundaries are preserved so a consumer can either honor them or run the
  `flatten` subcommand to expand them.

`flatten` emits `{ polylines: [...], arcs: [...], regions: [...] }` with
every aperture expanded, every macro instantiated, and every `SR` expanded
in row-major order. Flags like `--units=mm` or `--precision=6` are
candidates but should be minimized to keep the scoring surface canonical.

## Test Suite Estimate

Target: **≥ 50 independent-behavior hidden tests**, comfortably clearable
given the surface area.

| Category | Est. tests |
|---|---|
| Format header (`%FSLAX`, `%MOMM`, `%MOIN`, number format, zero suppression) | ~6 |
| Standard aperture templates (`C`, `R`, `O`, `P` with/without hole) | ~8 |
| Aperture macros (primitives 1/4/5/6/7/20/21/22; exposure; rotation; expressions; variable substitution `$1..$n`) | ~12 |
| Draw / arc ops (G01 linear, G02/G03 CW/CCW arcs, multi-quadrant via G74/G75, IJ form) | ~8 |
| Region mode (G36/G37, contour with mixed draws and arcs, self-intersecting rejection) | ~5 |
| Step-and-repeat (`%SR`, nested SR, attribute inheritance across copies) | ~4 |
| X2 attributes (file, aperture, object; inheritance and deletion with `%TD`) | ~6 |
| Polarity (`%LPD`/`%LPC`, dark/clear interaction with region fill) | ~4 |
| Round-trip (`parse` → `write` → `parse` idempotence, preserving attributes and aperture numbering) | ~6 |
| Flatten correctness (macro expansion, SR expansion, arc tessellation contract, region orientation) | ~6 |
| Error-path diagnostics (malformed coordinate data, unknown D-codes, mismatched `G36`/`G37`, truncated macros) | ~6 |
| Legacy-quirk behavior in scope (e.g. RS-274X deprecated-but-still-used constructs called out by the spec) | ~4 |
| **Total** | **~75** |

The two-dimensional structure — per-entity parse correctness × round-trip
fidelity × flatten fidelity — gives Gerber the same "a small bug localizes
to one category" property that RS274's trace tests and IGES's per-entity
tests have; one schema slip does not collapse half the suite.

## Implementation Size Estimate

Target for a competent C++ reference implementation: **~2,500–3,500 LOC**,
well above the ≥1,000 LOC floor. Rough breakdown:

- **Lexer / tokenizer** (commands, aperture defs, coordinate words, macro
  syntax): ~400 LOC.
- **Aperture macro interpreter** (expression evaluator over `$n` variables,
  primitive geometry synthesis, rotation composition): ~500 LOC. Macros
  are the single largest implementation pain point — the *"Gerber Aperture
  Macros are hard for everyone"* Horizon EDA blog post is not a joke.
- **Graphics state machine** (modal interpolation mode, current point,
  polarity, region-mode toggle, current aperture, coordinate format,
  unit): ~400 LOC.
- **Step-and-repeat engine** (nested block capture, deferred expansion,
  attribute inheritance): ~300 LOC.
- **X2 attribute handling** (stack discipline, `%TF`/`%TA`/`%TO`/`%TD`,
  attachment to current object): ~300 LOC.
- **Canonical-JSON writer** (stable field order, deterministic
  serialization): ~300 LOC.
- **Gerber writer** (formatting numbers per `FS`, emitting apertures and
  macros, attribute re-emission, `M02` termination): ~400 LOC.
- **Flatten engine** (macro → primitive → polyline/arc, SR expansion,
  region contour tessellation): ~500 LOC.
- **CLI + error diagnostics**: ~200 LOC.

Cross-check against existing implementations:

- **gerbv** (C, BSD/GPL) is the reference open-source viewer. Its parser
  core lives in `src/gerber.c` alone (roughly a few thousand lines before
  rendering code), and the broader codebase spans 2,010 commits with ~81%
  C. The full gerbv project is larger than CLISpecBench's reference-impl
  target because it also ships a GUI, image-diff, Excellon support, and
  the TinyScheme layer.
- **gerbonara** (Apache-2.0) is reported as 17.6% Python / 61.9% C++ /
  19.2% ANTLR, i.e. a hybrid where the parser is largely driven by an
  ANTLR grammar and the rendering backend is C++. The pure-Python slice
  is correspondingly smaller but covers read + modify + write.
- **PyGerber** (Argmaster/pygerber, Apache-2.0, 965 commits, 100%
  Python) is the clearest "full format, one language" reference point. A
  C++ port of its parse + write + flatten core — omitting its rendering
  engine and language-server — should land in the ~3k LOC neighborhood.

This comfortably satisfies the "real multi-file system, at least ~1000 LOC"
rule of thumb.

## Contamination & OSS Landscape

Gerber has **substantially more mature OSS coverage than IGES or RS274**,
which is the central contamination concern for this eval. Every major
ecosystem has at least one maintained parser, and several have
production-quality ones. Any of the following could plausibly have
appeared verbatim or near-verbatim in model training corpora:

**Specific implementations found:**

- [Argmaster/pygerber](https://github.com/Argmaster/pygerber) — Python,
  100% Python, 965 commits, Apache-2.0. Based on Ucamco's spec revision
  2023.03, now targeting 2024.05. Includes tokenizer, parser, optimizer,
  rasterized/SVG renderers, and a language server. Most "complete" of the
  modern Python implementations. Used as the single backend in
  [diffgerber](https://github.com/ajw287/diffgerber) V2.
- [jaseg/gerbonara](https://github.com/jaseg/gerbonara) — Python + C++ +
  ANTLR, 1,006 commits, 41 tags, Apache-2.0. Refactoring of pcb-tools and
  pcb-tools-extension. Read/modify/write Gerber, Excellon, and IPC-356.
  Ships a CLI for analysis, rendering, modification, and merging.
- [gerbv/gerbv](https://github.com/gerbv/gerbv) (and the older
  [geda-project](http://gerbv.geda-project.org/)) — C, GPL-2.0, 2,010
  commits. The canonical open-source viewer. Parser + editor + exporter +
  renderer. Library form is `libgerbv`.
- [KiCad gerbview](https://github.com/KiCad/kicad-source-mirror/blob/master/gerbview/readgerb.cpp)
  — C++, GPL-3.0. KiCad's built-in Gerber viewer; its read path was
  originally derived from gerbv 2.7.0 and has since diverged.
- [tracespace](https://github.com/tracespace/tracespace) (absorbed the
  older [mcous/gerber-parser](https://github.com/mcous/gerber-parser) npm
  package) — TypeScript, MIT. Stream-based parser + plotter + SVG
  renderer, used for browser-side PCB preview.
- [curtacircuitos/pcb-tools](https://github.com/curtacircuitos/pcb-tools)
  — Python, Apache-2.0. Unmaintained but still widely linked; predecessor
  to gerbonara.
- [Karel-Tavernier/gerber_writer](https://github.com/Karel-Tavernier/gerber_writer)
  — Python. Specifically the *write* side of Gerber.
- [MacroFab/DataGerber](https://github.com/MacroFab/DataGerber) — Perl.
  Niche but public.
- [Kirizu-Official/WebGerber](https://github.com/Kirizu-Official/WebGerber)
  — JavaScript. Browser-side parser/renderer.

**Tutorials / walkthroughs:**

- [Horizon EDA blog — "Gerber Aperture Macros are hard for everyone"](https://blog.horizon-eda.org/misc/2019/11/18/gerber.html)
  — a practitioner's walk through the worst-behaved corner of the spec.
- [fj laboratories — "Understanding Gerbers"](https://fjlaboratories.com/blog/understanding-gerbers)
  — readable overview.
- [Numerical Innovations' Gerber Format page and "Don't Blindly Trust Your
  Gerber Files"](https://www.numericalinnovations.com/pages/gerber-format)
  — industry-side commentary.
- [viewplot.com RS-274X format description](https://www.viewplot.com/info_files/vpl_faq/rs274x-format.html)
  — a compact, third-party-hosted spec summary that pre-dates X2.
- No single "write a Gerber parser from scratch in N steps" blog post
  surfaced in the searches that does the full job end-to-end. What exists
  is (a) the Ucamco spec itself, (b) mature OSS implementations, and
  (c) practitioner commentary on specific pain points.

**Contamination risk: medium-high.** Justification: PyGerber,
gerbonara, pcb-tools, gerbv, tracespace, and KiCad's gerbview are all
public, liberally licensed (except gerbv/KiCad's GPL, which still lets
training scrapers index them), and have been public for years. An agent
trained on public code has almost certainly seen multiple full parsers in
multiple languages. This is closer to SVG or INI-with-state than it is to
RS274/IGES on the contamination axis. Unlike IGES (where "the repo" is
basically OpenCASCADE + academic papers) or RS274 (where complete
implementations are genuinely rare), Gerber has saturated the OSS layer.

That said, the *behavioral tests* — specifically adversarial aperture
macros, SR-nested attribute inheritance, malformed-input diagnostics, and
round-trip fidelity — can still discriminate, because OSS parsers disagree
with each other on precisely these corners. The diffgerber V2 project
explicitly abandoned three of the four original backends because they had
*"eccentricities and limitations"* that disagreed. Testing the spec rather
than the popular interpretation of the spec is where Gerber still earns
its keep.

## Risks and Open Questions

1. **Spec redistribution is the critical blocker.** Ucamco's copyright
   notice explicitly forbids redistribution without prior written
   permission and explicitly declines to grant any IP license. This
   conflicts with CLISpecBench's "Publicly distributable docs" hard
   requirement. Options: (a) email Ucamco for written permission to
   include the PDF in an open benchmark, (b) author a clean-room spec
   summary restricted to the subset the eval actually tests and own the
   copyright, (c) scope the eval to a subset (e.g. only format-header +
   standard apertures + simple draws) whose behavior is also documented
   in freely-redistributable third-party sources (Wikipedia summary,
   ViewPlot description, blog posts). Option (a) is cleanest if it works;
   option (b) is the fallback. **Do not publish `prompt/docs/` until one
   of these is resolved.**
2. **Training contamination is real.** See above. Mitigations: skew the
   test suite toward aperture-macro corner cases, SR nesting, attribute
   stack discipline, and malformed-input diagnostics rather than happy-path
   parse-flat-rectangle tests.
3. **Scope discipline on X3.** Gerber X3 (component metadata / assembly)
   was introduced in 2019 and is a meaningfully different surface (CPL
   data, reference designators, part numbers). Recommendation for v1 of
   the eval: **X2 only**, explicit non-goal to support X3 component
   metadata. This mirrors IGES's "no Binary Format, no MACRO entities"
   non-goal discipline.
4. **Aperture macros are the single largest ambiguity vector.** Rotation
   semantics differ by primitive (the rectangle primitive rotates around
   (0,0), not the rectangle's center — a documented spec oddity that
   real-world generators get wrong). The eval should commit to the
   spec's letter, not the market's convention, and test both cases
   explicitly.
5. **Arc tessellation tolerance in `flatten`.** Flattening arcs to
   polylines requires picking a tolerance. This is structurally similar
   to RS274's `--trace-position-tolerance` problem: if the flattening
   tolerance is a free-form CLI flag, the scoring surface depends on
   whatever the agent picked. Recommendation: emit arcs **as arcs**
   (center, radius, start/sweep) in `flatten`'s output, and only
   tessellate inside regions where a polygon is required, with a single
   baked tolerance (parallel to RS274's baked rapid rate + epsilon). This
   keeps `flatten` deterministic.
6. **Reference implementation licensing.** gerbv (GPL-2.0) and KiCad
   (GPL-3.0) cannot seed a reference implementation we ship. PyGerber and
   gerbonara (Apache-2.0) could, in principle, but we want a clean-room
   ref impl — writing the C++ reference from the spec alone sidesteps
   both the derivative-work question and the contamination question for
   the test suite author.

## CHOOSING_EVALS Checklist

- **Documentation-first: partial.** Passable in principle from the spec
  + PEG grammar alone. The one genuine risk is whether the Ucamco spec
  is actually self-contained for aperture-macro rotation corner cases
  (historically a point of spec ambiguity and implementation divergence);
  if it is not, the eval has to either clarify in
  `technical-requirements-prompt.md` or narrow its test scope.
- **Non-developer describable: pass.** An electrical engineer who sends
  Gerbers to a fab house every month can describe parse / write-back /
  flatten operations in their own vocabulary. The draft base-prompt
  sketch above does not borrow developer terminology.
- **Authoritative source material: pass.** Ucamco's Gerber Layer Format
  Specification is the single authoritative document; it is stable (dated
  revisions) and actively maintained. The companion PEG grammar adds a
  formal-grammar artifact.
- **No solver code in corpus: pass (subject to scope).** The Ucamco spec
  describes the format; it does not ship implementation code. The PEG
  grammar is a grammar, not an interpreter. As long as
  `prompt/docs/` stays to the spec + grammar (plus maybe figures), it
  stays on the "describe, don't solve" side of the line.
- **Behaviorally unambiguous: partial.** The big-ticket parts of the
  spec (format header, standard apertures, draws/arcs, polarity,
  regions) are unambiguous. Aperture-macro rotation semantics and a
  few X2 attribute inheritance rules have historically been
  under-specified enough that real generators disagree. Tests for those
  areas need careful provenance discipline, exactly as RS274's README
  documents: cite the `§` section, and only test what the spec asserts
  clearly.
- **Deterministic scoring surface: pass.** `parse` has one canonical
  JSON output; `write` is scored by re-parsing; `flatten` has one
  canonical expansion once the arc-tessellation / arc-as-arc decision
  above is locked.
- **Independent failure modes: pass.** The per-category test breakdown
  above covers apertures, macros, ops, regions, SR, attributes,
  polarity, round-trip, flatten, and errors as separate axes. A small
  bug in one category does not collapse others.
- **System-level complexity: pass.** ~2.5k–3.5k LOC target, multi-module
  (lexer / macro interpreter / state machine / SR / attributes / writer
  / flatten). Comfortably above the ≥1000 LOC floor.
- **Test-suite scalability: pass.** ~75 independent tests estimated,
  well above the 50 floor, with room to grow via adversarial
  macro/attribute/SR combinations.
- **Contamination resistance: partial (weakest criterion).** Gerber is
  the most-implemented format of any current or proposed CLISpecBench
  eval. PyGerber, gerbonara, gerbv, KiCad, tracespace, and pcb-tools
  collectively cover every common language. A strong agent may well
  succeed on recall rather than reasoning. Mitigation is test
  curation, not contamination avoidance at the domain level.
- **Reference implementation feasibility: pass.** A clean-room C++
  reference in the ~3k LOC neighborhood is achievable with one
  engineer-week of focused work, seeded by the spec + PEG grammar.
  PyGerber's feature matrix is a useful coverage target without being a
  code reference.
- **Reasonable harness fit: pass.** Local files, CLI flags, JSON out,
  no GUI, no network, no wall-clock timing. Builds on the same CMake /
  subcommand-binary pattern as IGES.
- **Publicly distributable docs: FAIL — as specified.** Ucamco's
  copyright notice explicitly forbids redistribution without prior
  written permission. This is the single hardest blocker. The eval can
  only progress if we (a) obtain written permission from Ucamco, (b)
  write a clean-room spec summary for the corpus, or (c) narrow scope
  to what is documented in freely-redistributable third-party sources.
  Until one of those happens, this is a "fail" on the hard
  requirements, not a nit.

## Summary

Gerber X2 would be a genuinely strong CLISpecBench eval on architectural
merit: clean non-developer framing, rich stateful 2D-graphics behavior, a
three-verb CLI contract (parse / write / flatten) that decomposes cleanly
into ~75 independent tests, a ~3k LOC implementation target, and an
authoritative single-document spec with a formal PEG grammar companion.
It covers a dimension — stateful 2D image semantics with nested SR and a
macro sub-language — that neither RS274 (3D kinematics) nor IGES (record
schema) exercises. Two things hold it back and both are honest: Ucamco's
specification is not redistributable without written permission, and the
open-source ecosystem around Gerber (PyGerber, gerbonara, gerbv, KiCad,
tracespace) is mature enough to pose a meaningful contamination risk. The
first is a gating question that must be resolved before `prompt/docs/`
can exist; the second is manageable via test curation biased toward
adversarial aperture-macro, SR-nesting, and attribute-stack corners
where OSS parsers are known to disagree with each other and with the
letter of the spec.

Sources:

- [Ucamco — Gerber downloads](https://www.ucamco.com/en/gerber/downloads)
- [Ucamco — Gerber Layer Format Specification, revision 2024.05 PDF](https://www.ucamco.com/files/downloads/file_en/456/gerber-layer-format-specification-revision-2024-05_en.pdf)
- [Ucamco — Gerber Layer Format Specification revision 2024.05 news release](https://www.ucamco.com/en/news/gerber-layer-format-specification-revision-202405)
- [Ucamco — Reference Gerber Viewer](https://www.ucamco.com/en/gerber/reference-gerber-viewer)
- [Gerber format — Wikipedia](https://en.wikipedia.org/wiki/Gerber_format)
- [Argmaster/pygerber — GitHub](https://github.com/Argmaster/pygerber)
- [PyGerber on PyPI](https://pypi.org/project/pygerber/)
- [jaseg/gerbonara — GitHub](https://github.com/jaseg/gerbonara)
- [gerbonara documentation](https://gerbolyze.gitlab.io/gerbonara/)
- [gerbv — A Free/Open Source Gerber Viewer](https://gerbv.github.io/)
- [gerbv/gerbv — GitHub](https://github.com/gerbv/gerbv)
- [KiCad — Gerber Viewer](https://www.kicad.org/discover/gerber-viewer/)
- [KiCad readgerb.cpp source](https://github.com/KiCad/kicad-source-mirror/blob/master/gerbview/readgerb.cpp)
- [tracespace — GitHub](https://github.com/tracespace/tracespace)
- [mcous/gerber-parser — GitHub](https://github.com/mcous/gerber-parser)
- [curtacircuitos/pcb-tools — GitHub](https://github.com/curtacircuitos/pcb-tools)
- [Karel-Tavernier/gerber_writer — GitHub](https://github.com/Karel-Tavernier/gerber_writer)
- [MacroFab/DataGerber — GitHub](https://github.com/MacroFab/DataGerber)
- [Kirizu-Official/WebGerber — GitHub](https://github.com/Kirizu-Official/WebGerber)
- [Horizon EDA blog — Gerber Aperture Macros are hard for everyone](https://blog.horizon-eda.org/misc/2019/11/18/gerber.html)
- [fj laboratories — Understanding Gerbers](https://fjlaboratories.com/blog/understanding-gerbers)
- [Numerical Innovations — Gerber Format](https://www.numericalinnovations.com/pages/gerber-format)
- [Numerical Innovations — Don't Blindly Trust Your Gerber Files](https://www.numericalinnovations.com/pages/dont-trust-your-gerber-files)
- [ViewPlot — RS-274X format description](https://www.viewplot.com/info_files/vpl_faq/rs274x-format.html)
- [Altium — ODB++ vs. Gerber X2/X3 vs. IPC-2581](https://resources.altium.com/p/pcb-production-file-format-wars)
- [Bay Area Circuits — Advantages of the Gerber X2 Format](https://bayareacircuits.com/advantages-of-the-gerber-x2-format/)
- [ajw287/diffgerber — GitHub](https://github.com/ajw287/diffgerber)
