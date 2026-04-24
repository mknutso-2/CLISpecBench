# MusicXML

MusicXML 4.0 Partwise ingestion eval for CLISpecBench. Agents receive the
W3C MusicXML 4.0 specification and must produce a CLI tool that parses
scores and emits a flat, time-aligned table of sounding notes.

> **Status.** Proposed eval shell. This README is a design sketch — no
> prompt, tests, or reference implementation yet.

## Why this eval

RS274 tests dense-spec interpretation against a narrow, CNC-specific domain.
IGES tests a wider 87-entity CAD interchange surface. MusicXML sits between
the two in document character but pushes on a different axis: an
*XML-schema-driven* behavioral spec where the ingestion task mixes pure
parsing with several layers of nontrivial calculation.

What an agent actually has to get right is the calculation chain from
written notation to sounding events:

- Divisions-per-quarter -> real durations (changes per part, sometimes
  per measure).
- Tempo (`<sound tempo>` / `<metronome>`) -> real beat times, accumulated
  across measures.
- `<transpose>` + `<alter>` + `<key>` -> correct MIDI pitch for
  transposing instruments.
- `<chord/>` markers -> stacked onsets at the same beat.
- Repeat barlines + `<ending>` voltas -> correct playback-order expansion,
  which changes every subsequent beat time.
- `<backup>` / `<forward>` -> multi-voice parts whose events do not
  advance the measure cursor linearly.

Each of those is individually well-documented in the spec and individually
straightforward; chaining them correctly across a real score is where
pattern-matched solutions tend to drift. That chain is what makes the eval
worthwhile.

## Documentation Corpus

The public prompt corpus would ship the W3C MusicXML 4.0 Recommendation
(Community Group Final Report, June 2021), which is redistributable under
the W3C Community Final Specification Agreement. That covers:

- The 9-part narrative tutorial (structure, notation basics, the
  MIDI-compatible subset, etc.).
- The element reference pages covering ~400 element types in the schema.
- The `partwise.xsd` XSD schema and `musicxml.xsd` aggregate schema,
  transcribed for inline reference.

We would **drop** timewise coverage (the `<score-timewise>` root and the
`parttime.xsl` / `timepart.xsl` XSLT stylesheets), Container/Opus/Sounds
references, and the music-font / layout chapters, since they are out of
scope for ingestion.

The corpus is stable (4.0 is the current final report), single-vendor
(W3C Music Notation CG), and has clear internal structure. It is a good
fit for the benchmark's "dense authoritative spec" pattern.

## Base Prompt (sketch)

I arrange music for community bands and I want a command-line tool to help
me prep parts. Given a MusicXML 4.0 score — the format I export from
Finale or MuseScore — I want a flat, time-aligned list of every sounding
note in the piece: which part it belongs to, which measure it lands in,
what beat within the piece it starts on, how long it lasts, and what
MIDI-number pitch will actually play. Transposed instruments (the
clarinet in B-flat, the horn in F) should come out in concert pitch,
because that is what I need to compare parts against each other. When a
tempo or time signature changes, the beat numbers should reflect that
change. When a section has a repeat with a first and second ending, the
output should lay the notes out in playback order so I am reading the
piece the way the band actually performs it. I do not need rendering or
playback audio — a plain table of notes is enough.

## Technical Requirements (sketch)

- Language: C++23 (initial ref impl), plus Python/JS/Rust targets after.
- Build: CMake for C++; existing patterns for the others.
- CLI:
  - `musicxml notes --input <score.musicxml> --output <notes.json>` — the
    primary extraction: flat list of `(part_id, measure_number,
    beat_onset, duration_beats, duration_seconds, midi_pitch, voice,
    chord_index, tied_from_prev, tied_to_next)` rows.
  - `musicxml measures --input <score.musicxml> --output <measures.json>`
    — measure boundary table: `(measure_number, divisions, time_sig_num,
    time_sig_den, tempo_qpm, starts_at_beat, starts_at_seconds)`.
  - `musicxml query --input <score.musicxml> --from-beat <f>
    --to-beat <f> --output <window.json>` — windowed note extract.
- Input scope: `<score-partwise>` only. Uncompressed `.musicxml` only
  (skip `.mxl` zip container and `<score-timewise>`).
- Exit codes: 0 success, 1 invalid input (with structured JSON error
  including a `§` spec citation), 2 internal error. Mirrors RS274/IGES.
- Deterministic: given the same input, same output byte-for-byte.
  Floating-point fields quantized to fixed precision.

Explicitly out of scope, with the intent of keeping the surface
behaviorally unambiguous:

- Rendering, playback, or audio output.
- Timewise -> Partwise conversion.
- Chord symbols (`<harmony>`), figured bass, lyrics, fretboard diagrams.
- MACRO-style `<sound>` effects beyond `tempo`, `dynamics`, `dacapo`,
  `segno`, `fine`.
- Ornament expansion (trills, mordents). Grace notes are tracked but
  emitted with zero `duration_beats`.

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| File structure and header (score-partwise, part-list, work) | ~4 |
| `<divisions>` handling, per-part and per-measure changes | ~5 |
| Time signature changes mid-piece | ~4 |
| Tempo changes (`<sound tempo>` and `<metronome>`) | ~5 |
| Pitch -> MIDI: step, alter, octave basics | ~4 |
| Key signature application and accidental carry-within-measure | ~5 |
| Transposing instruments (B-flat clarinet, F horn, A clarinet, piccolo) | ~5 |
| Chord stacks (`<chord/>`) | ~3 |
| Tuplets (triplet, quintuplet, nested) via `<time-modification>` | ~4 |
| Ties vs slurs (tied sounding-duration combination) | ~3 |
| Multi-voice parts with `<backup>` / `<forward>` | ~4 |
| Repeat barlines, simple `|:` `:|` | ~3 |
| Voltas / `<ending>` first-and-second endings | ~4 |
| Dal segno / D.C. al fine jump expansion | ~3 |
| Windowed `query` by beat range | ~3 |
| Measure-table output (`measures` subcommand) | ~3 |
| Grace notes (zero-duration emission) | ~2 |
| Malformed inputs: schema-invalid, unknown pitch, missing divisions | ~5 |
| Round-trip on Lilypond/W3C fixtures | ~4 |
| Determinism (byte-identical reruns) | ~2 |
| **Total** | **~75** |

That is comfortably above the 50-test floor from `CHOOSING_EVALS.md` and
the categories are largely independent — a bug in transposition should
not cascade into the tuplet tests.

## Implementation Size Estimate

Hand-rolling a MusicXML 4.0 Partwise ingester that passes the above suite
is a real multi-file system, but smaller than IGES:

- XML tokenization / DOM or SAX walker over the Partwise schema subset:
  ~500-800 LOC.
- Score model (Part / Measure / Voice / Note / Attributes stacks):
  ~400-600 LOC.
- Timing engine (divisions, tempo, time-sig, beat accumulation,
  `<backup>`/`<forward>`): ~300-500 LOC.
- Pitch engine (alter + key + transpose -> MIDI, accidental carry):
  ~200-300 LOC.
- Playback-order expander (repeats, endings, DS/DC): ~300-500 LOC.
- CLI + JSON emitter + error handling: ~200-300 LOC.

Totals roughly **1500-3000 LOC for a C++ reference**, which meets the
~1000 LOC floor. A Python reference using only `xml.etree` would land
around 1200-2000 LOC. For grounding: the Rust `musicxml` crate and the
`musicxml-interfaces` npm library both weigh in well above this, but
they cover the *entire* schema including timewise, compressed container,
and writer; they are not like-for-like with our scope.

## Contamination & OSS Landscape

**Specific implementations found:**

- [music21](https://github.com/cuthbertLab/music21) — Python, BSD-3.
  ~2.2k GitHub stars. MIT-affiliated toolkit with an extensive,
  well-documented MusicXML importer (`xmlToM21.py`) and exporter. This is
  the dominant contamination vector. Its public API (`converter.parse()`,
  `stream.flatten().notes`, `.beat`, `.offset`, `.pitch.midi`,
  `.expandRepeats()`) maps closely onto the CLI surface this eval proposes,
  which makes pattern-matching tempting for an agent. music21 is not a
  silver bullet — it has its own filed bugs in the same areas
  (e.g. [`expandRepeats` issue #355](https://github.com/cuthbertLab/music21/issues/355),
  plus release-note entries for metronome and transposition fixes) — but
  a capable agent can reproduce large parts of the required behavior by
  recalling music21's algorithm structure rather than reasoning from the
  W3C spec.
- [libmusicxml](https://libmusicxml.sourceforge.net/) — C++.
  Long-running library originally from Grame. Mature, covers the full
  schema including timewise.
- [MuseScore](https://musescore.org) — C++. Full notation editor with a
  production MusicXML importer; source is GPL-licensed.
- [Verovio](https://www.verovio.org/) — C++. MEI engraving library that
  includes a MusicXML-to-MEI converter.
- [LilyPond `musicxml2ly`](http://lilypond.org/) — Python script shipped
  with LilyPond; well-known converter from MusicXML to LilyPond source.
- [`musicxml` crate](https://crates.io/crates/musicxml) — Rust. Reads
  both `.musicxml` and compressed `.mxl`.
- [`musicxml-interfaces`](https://www.npmjs.com/package/musicxml-interfaces)
  — JavaScript/TypeScript. Low-level parse/serialize/build/patch.
- [pymusicxml](https://github.com/MarcTheSpark/pymusicxml),
  [partitura](https://github.com/CPJKU/partitura),
  [MuseParse](https://github.com/Godley/MuseParse),
  [musicxml_parser](https://github.com/qsdfo/musicxml_parser) — smaller
  Python libraries, each covers some subset.

**Tutorials / walkthroughs:**

- The W3C MusicXML 4.0 tutorial itself, including the ["MIDI-Compatible
  Part" chapter](https://www.w3.org/2021/06/musicxml40/tutorial/midi-compatible-part/),
  which walks through divisions, duration, pitch, and transposition in
  close detail. This is a strong tutorial — close to a worked
  ingestion spec — but it is also the *authoritative source*, so it is
  in-scope for the corpus.
- [Recordare's 2011 MusicXML 3.0 tutorial PDF](https://www.musicxml.com/wp-content/uploads/2012/12/musicxml-tutorial.pdf),
  a walkthrough of the same material for the 3.0 vintage.
- The [AudioLabs Erlangen MusicXML chapter](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C1/C1S2_MusicXML.html),
  course-style introduction.
- Multiple Medium / personal-blog posts mapping `music21` onto MusicXML.

**Contamination risk:** **high**, with one substantive mitigation.

- *High, because:* `music21` is a first-class, widely-used
  ingestion-plus-analysis toolkit with thorough docs and is almost
  certainly heavily represented in training data. The MusicXML-4.0
  tutorial itself is conceptually close to a worked solution for several
  of the test categories. An agent allowed to `pip install music21` and
  shell out to it would trivially pass most tests.
- *Mitigating factor:* the calculation chain from notation to sounding
  events is exactly where naive ingesters fail in practice. The
  LilyPond/Kainhofer test suite exists *because* every major
  implementation has historically shipped bugs in corners like
  transposing-instrument key application, first/second ending expansion,
  `<backup>` in multi-voice parts, and tempo changes mid-measure. Even
  with heavy training exposure, correctly composing these rules is a
  genuinely hard reasoning task — more so than, say, IGES parse
  correctness.
- *Harness-level mitigations available:* the Docker environment already
  restricts network to the agent API host, so `pip install music21` is
  not available at runtime. The reference implementation writes from the
  spec, not from music21. Test fixtures can be authored with
  music21-known bug patterns deliberately included.

Net: contamination is **high** on the "could the agent have seen a
pattern" axis, **medium** on the "could the agent pass without
reasoning" axis. This deserves discussion in the eval's design doc
before proceeding.

## Risks and Open Questions

- **Repeat expansion is load-bearing.** A single bug in the volta or
  D.S./D.C. expander cascades through every subsequent beat time and
  note index, collapsing 10+ tests into one failure signature. The
  `CHOOSING_EVALS.md` "independent failure modes" bar is real here. We
  can mitigate by (a) testing the expander's *output order* separately
  from the *note content* of expanded sections and (b) making per-test
  expected outputs relative to the repeat-expanded score so a single
  note-level bug only fails its own test.
- **Floating-point timing.** `tempo_qpm * divisions` math is irrational
  for realistic tempos (MM 132 at 480 divisions, etc.). Fixed
  quantization policy (e.g., 7 digits) + rational-number beat accounting
  internally keeps this deterministic, but the contract has to specify
  it explicitly.
- **Behavioral unambiguity of "playback order."** The spec's repeat /
  ending / jump semantics are mostly explicit but have one or two
  corners (nested repeats, missing end-repeat, ending without left
  barline) where real implementations disagree. We may need to exclude
  those cases from the test suite or pin a policy in
  `technical-requirements-prompt.md` — the latter starts to smuggle
  behavior into the harness contract, which is a warning sign.
- **Schema surface.** The Partwise schema defines a lot of elements we
  do *not* care about (layout, appearance, credits, print styling).
  Agents will read them as potentially-relevant and may burn budget
  modeling them. Prompt should state clearly that appearance-only
  elements are ignored.
- **XML pathology.** CDATA, entities, unusual encodings, and
  schema-invalid-but-common files from Finale / MuseScore exports are
  all real. We should pin a policy: "accept schema-valid inputs; reject
  with exit 1 otherwise" is clean but may reject real-world files.
- **Reference-implementation effort.** Versus RS274/IGES, the spec is
  *broader but shallower* per element. Writing the ref impl is probably
  a 2-3 week engineering investment — feasible but nontrivial.
- **`music21` shadow.** If contamination leaks through the chosen test
  cases end up too close to music21 test fixtures (many of which are
  the same LilyPond/Kainhofer fixtures), the eval collapses into a
  music21-reproduction test. We need adversarial fixtures authored
  outside that corpus.

## CHOOSING_EVALS Checklist

- Documentation-first: **pass** — the W3C spec plus the MIDI-compatible
  tutorial covers every testable behavior end-to-end.
- Non-developer describable: **pass** — the arranger persona sketch above
  is plausible without engineering vocabulary.
- Authoritative source material: **pass** — W3C Community Group Final
  Report, single source, stable since June 2021.
- No solver code in corpus: **partial** — the W3C tutorial walks through
  the MIDI-compatible mapping in close detail, including pitch
  arithmetic and transposition rules. It stops short of working code but
  is close to pseudo-code in places. We keep it in because it is the
  authoritative source, but we do not include external tutorials on top.
- Behaviorally unambiguous: **partial** — core behavior is clean, but
  repeat/jump expansion has underspecified corners that must be pinned
  by policy.
- Deterministic scoring surface: **pass** — flat JSON tables with fixed
  numeric precision; one correct output per input.
- Independent failure modes: **partial** — repeat-expansion bugs can
  cascade. Mitigable with careful test design, but it is a real risk.
- System-level complexity: **pass** — estimated 1500-3000 LOC for C++
  ref impl comfortably clears the ~1000 LOC floor.
- Test-suite scalability: **pass** — ~75 tests sketched above, more
  available from the Kainhofer fixture corpus.
- Contamination resistance: **fail** — `music21` is the dominant
  contamination vector, with BSD license, MIT heritage, ~2.2k GitHub
  stars, full tutorial coverage, and public API that maps 1:1 onto the
  proposed CLI. The "compute beats given repeats + tempo + time-sig
  chain" mitigation partially offsets this but does not eliminate it.
  This is the eval's weakest axis and would need explicit discussion
  before adoption.
- Reference implementation feasibility: **pass** — tractable from the
  spec in a few weeks; the Kainhofer test suite gives a backstop corpus.
- Reasonable harness fit: **pass** — local file in, JSON out, CLI flags,
  no GUI, no network. Identical to RS274/IGES shape.
- Publicly distributable docs: **pass** — W3C Community Final
  Specification Agreement explicitly allows free redistribution of the
  DTDs, XSDs, and the specification text.

## Summary

MusicXML 4.0 Partwise ingestion is a tempting eval candidate: the spec is
publicly redistributable, the task has a clean CLI shape that fits the
harness, the domain supports ~75 independent tests, and the
divisions+tempo+transposition+repeats calculation chain is a real
reasoning exercise that trips up every existing implementation. It sits
naturally in the RS274 / IGES family as a third dense-spec eval. The
blocking concern is contamination: `music21` is a polished, BSD-licensed,
widely-taught toolkit whose API solves the eval directly. Before
committing to MusicXML, we should decide whether the calculation-chain
reasoning difficulty is enough to resist contamination in practice, and
whether adversarial fixtures authored outside the
LilyPond/Kainhofer/music21 ecosystem can carry the signal. If the answer
is yes, this is a strong eval; if no, a sibling format with a smaller OSS
footprint (MEI, Humdrum kern) is the safer choice on that axis.

Sources:
- [MusicXML 4.0 W3C Community Group Final Report](https://www.w3.org/2021/06/musicxml40/)
- [MusicXML 4.0 - The MIDI-Compatible Part of MusicXML](https://www.w3.org/2021/06/musicxml40/tutorial/midi-compatible-part/)
- [MusicXML 4.0 - The Structure of MusicXML Files](https://www.w3.org/2021/06/musicxml40/tutorial/structure-of-musicxml-files/)
- [MusicXML - Wikipedia](https://en.wikipedia.org/wiki/MusicXML)
- [w3c/musicxml GitHub repository](https://github.com/w3c/musicxml)
- [music21 GitHub repository](https://github.com/cuthbertLab/music21)
- [music21 documentation](https://music21.org/music21docs/)
- [music21 PyPI](https://pypi.org/project/music21/)
- [Unofficial MusicXML test suite (LilyPond/Kainhofer)](http://lilypond.org/doc/v2.25/input/regression/musicxml/collated-files.html)
- [cuthbertLab/musicxmlTestSuite fork](https://github.com/cuthbertLab/musicxmlTestSuite)
- [Kainhofer 2010: An extensive MusicXML 2.0 test suite](https://kainhofer.com/wp-content/uploads/2010/03/Kainhofer_MusicXML_Testsuite_CMMR2010.pdf)
- [Recordare 2011 MusicXML 3.0 Tutorial PDF](https://www.musicxml.com/wp-content/uploads/2012/12/musicxml-tutorial.pdf)
- [AudioLabs Erlangen - Symbolic Format: MusicXML](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C1/C1S2_MusicXML.html)
- [libmusicxml](https://libmusicxml.sourceforge.net/)
- [Verovio](https://www.verovio.org/)
- [musicxml crate on crates.io](https://crates.io/crates/musicxml)
- [musicxml-interfaces on npm](https://www.npmjs.com/package/musicxml-interfaces)
- [pymusicxml GitHub](https://github.com/MarcTheSpark/pymusicxml)
- [partitura GitHub](https://github.com/CPJKU/partitura)
