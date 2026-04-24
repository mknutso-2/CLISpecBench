# SMILES

SMILES (Simplified Molecular-Input Line-Entry System) eval for CLISpecBench.
Agents receive the OpenSMILES specification plus a standard periodic-table
reference and must produce a CLI tool that parses SMILES strings into
molecular graphs, counts rings, computes molecular formula and molecular
weight, and emits structured JSON.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt,
> tests, or reference implementation yet.

## Why this eval

RS274 and IGES both probe dense, *engineering-style* specifications: G-code
and CAD interchange. SMILES extends the benchmark along a genuinely different
axis — a **line notation from cheminformatics** whose authoritative spec is
compact, publicly redistributable under the GNU FDL, and backed by an active
domain (medicinal chemistry, drug discovery, chemical databases) whose
practitioners routinely author and compare SMILES strings without writing
code. That is the persona CLISpecBench needs: a chemist who can describe what
"parse this molecule and tell me its formula" should mean, in plain domain
language, without specifying an implementation.

The behavioral surface is rich enough for a real system (a tokenizer, a
recursive-descent parser with ring-closure bookkeeping, an aromatic model, a
valence/implicit-hydrogen calculator, a ring perception pass, a formula/weight
builder, and a JSON emitter — cleanly separable modules), but narrow enough to
fit a single dense document. Unlike RS274 or IGES, SMILES has no execution
semantics to model: there is no machine state, no round-trip file format to
write byte-for-byte. Correctness is almost entirely a function of *did you
read the spec carefully*.

The caveat — and the reason this is a proposal rather than a committed eval —
is that the canonical-SMILES portion of the problem is known to be
**implementation-specific across all major toolkits**: RDKit, Open Babel, and
Daylight produce different canonical strings for the same molecule, and
OpenSMILES §5 explicitly declines to specify the algorithm. See "Risks and
Open Questions" below; this eval is only viable if that concern is resolved
cleanly, and the design here assumes we scope canonicalization aggressively or
drop it.

## Documentation Corpus

- **`prompt/docs/OpenSMILES.md`** — the OpenSMILES specification (Craig A.
  James, 2007–2016), ~50 pages, dense and self-contained, covering atoms,
  bonds, branches, rings, aromaticity, stereo, isotopes, charges, and
  reactions. Redistributable under GNU FDL 1.2 with copyright preservation.
- **`prompt/docs/periodic-table.json`** — a curated standard-atomic-weight
  table based on the IUPAC 2021 Technical Report (CIAAW abridged values),
  trimmed to the elements expressible in SMILES (H through the heavy
  actinides). Ships in the corpus so the formula/weight computation is
  deterministic against a known reference and agents do not need to guess or
  invent atomic masses. Interval-valued weights (e.g., Ar, Pb) are collapsed
  to single representative values to keep scoring deterministic; the choice
  is documented in the JSON file itself.
- **No solver code** in the corpus. The OpenSMILES spec is descriptive, not
  executable; it defines syntax and semantics without shipping a parser. This
  satisfies the "no solver code in corpus" rule in `CHOOSING_EVALS.md`.

## Base Prompt (sketch)

> I work on a medicinal chemistry team. Every week I get compound libraries
> from partner labs delivered as plain-text SMILES strings — hundreds of
> thousands of them — and before we look at any of them seriously I want a
> small command-line tool that will chew through a file of these strings and
> tell me, for each one: what atoms are in it, what bonds connect them, how
> many rings it has, its empirical formula, its molecular weight, and a
> canonical form I can use as a dictionary key when I compare libraries
> against each other. The SMILES grammar is documented in the attached
> specification; the atomic weights I want you to use are in the attached
> periodic-table file. Please read the spec carefully — there are a lot of
> subtle cases around brackets, ring closures, charges, and aromatic atoms.
> The output should be structured JSON so I can pipe it into our downstream
> tooling. When the input is not a valid SMILES string, I want a clear error,
> not a crash or garbage output.

## Technical Requirements (sketch)

CLI contract (draft, to be refined):

- Binary name: `smiles` (or `smiles.exe` on Windows).
- Primary command: `smiles parse --input <file.smi> --output <out.json>`.
  Input file contains one SMILES string per line, optionally followed by a
  whitespace-separated identifier.
- Output JSON shape per input line: `{ "input": "...", "atoms": [...],
  "bonds": [...], "rings": N, "formula": "...", "weight": <float>,
  "canonical": "..." }` (canonical field conditional on Open Question 1
  below). Errors emit `{ "input": "...", "error": "...", "error_position":
  <int> }`.
- Exit codes follow RS274/IGES convention: `0` success, `1` invalid input
  (any parse failure on any line), `2` internal error.
- No network, no GUI, no hosted services.
- Reference implementation language: Python first (the domain's lingua
  franca); C++ or Rust as a second reference to keep the eval multi-language.

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| Atom parsing — organic subset (B, C, N, O, P, S, F, Cl, Br, I) | ~8 |
| Bracketed atoms — charges, isotopes, H counts, aromatic flag | ~12 |
| Bond types — single / double / triple / aromatic / unspecified | ~6 |
| Branches — nested, empty, malformed | ~6 |
| Ring closures — single-digit, `%NN` two-digit, cross-branch, bond types on closures | ~10 |
| Aromatic perception — lowercase atoms, Kekulé vs aromatic, heteroaromatic | ~8 |
| Implicit hydrogen / valence model | ~8 |
| Molecular formula — Hill ordering, subscripts, hydrogen accounting | ~8 |
| Molecular weight — against IUPAC table, multi-isotope elements, explicit isotopes | ~6 |
| Ring count — SSSR or equivalent, fused/bridged/spiro systems | ~6 |
| Disconnected structures (`.` delimiter) | ~4 |
| Error handling — unbalanced brackets, unclosed rings, invalid atom, invalid bond | ~10 |
| Canonicalization (if in scope) — idempotence, permutation invariance on a fixed subset | ~8 |
| Large real-world inputs — drug molecules, smoke-test fidelity | ~4 |
| **Total** | **~104** |

This comfortably clears the 50-test floor in `Eval-Design.md` §9.1. The
canonicalization row is the one at risk of being dropped entirely; even
without it the suite is ~96 tests.

## Implementation Size Estimate

A competent reference implementation that covers the full OpenSMILES grammar
(minus stereo, if we descope) plus formula/weight/ring-count should land in
the ~1200–2000 LOC range, based on what open-source implementations actually
spend:

- **pysmiles** (Peter Kroon, Python-only, NetworkX-backed, reader + basic
  writer, no stereo) is organized across `read_smiles.py`, `write_smiles.py`,
  and `smiles_helper.py` — a lightweight implementation acknowledged by its
  author as having a basic writer and better-developed reader. A comparable
  reader-plus-helpers footprint at CLISpecBench reference quality is
  realistically ~800–1200 LOC in Python, more in a statically typed language.
- **Purr** (Rich Apodaca, Rust, recursive-descent parser over the OpenSMILES
  grammar) and **smiles-parser** (hobofan, nom-based) target just the parse
  side and still represent substantial code; adding formula/weight/rings
  easily doubles the surface.
- **RDKit**'s SMILES path (Flex/Bison-generated lexer and parser plus
  canonicalization and aromaticity) is far larger than anything we would
  expect an agent to produce — it is a full cheminformatics toolkit, not an
  apples-to-apples reference. It is cited here as an upper bound, not a
  target.
- **SmilesDrawer** (Probst & Reymond, MIT-licensed JS) bundles parser plus
  drawer; the parser alone is small-to-medium.

Adding the JSON-emitter scaffold, argument parsing, element table lookup, and
Hill-order formula builder adds another few hundred lines. The ~1000 LOC
floor from `CHOOSING_EVALS.md` is clearly met; the ceiling is bounded by how
much aromaticity and ring-perception detail we require.

## Contamination & OSS Landscape

SMILES is an extremely well-traveled format. This is the single biggest
contamination concern for the eval. Concrete findings:

**Specific implementations found:**
- [RDKit](https://github.com/rdkit/rdkit) — C++ core with Python bindings via
  Boost.Python. Flex/Bison-generated SMILES grammar. Full-featured
  cheminformatics toolkit; used as a de facto reference in academia and
  industry. Very large, likely well-represented in training data.
- [Open Babel](https://github.com/openbabel/openbabel) — C++, implements
  OpenSMILES plus radicals extension. `src/formats/smilesformat.cpp` is the
  canonical file; substantial but bounded.
- [Indigo](https://github.com/epam/Indigo) — C++ core with .NET / Java /
  Python / R / WebAssembly bindings. Apache-2.0. Supports canonical
  (isomeric) SMILES via `indigo-cano`.
- [pysmiles](https://github.com/pckroon/pysmiles) — Python-only,
  NetworkX-backed. Lightweight; reader is the more complete half.
- [Purr](https://github.com/rapodaca/purr) / ["Let's Build a SMILES Parser in
  Rust"](https://depth-first.com/articles/2020/05/25/lets-build-a-smiles-parser-in-rust/)
  — Rust, hand-written recursive-descent, explicitly based on OpenSMILES.
- [smiles-parser (hobofan)](https://github.com/hobofan/smiles-parser) —
  Rust, `nom`-based, OpenSMILES.
- [SmilesDrawer](https://github.com/reymond-group/smilesDrawer) — JavaScript,
  MIT. Parser plus SVG renderer.
- [Chemistry Development Kit (CDK)](https://github.com/cdk/cdk) — Java,
  widely used in chemoinformatics teaching.
- [chem (Rust)](https://docs.rs/chem/) — includes a `smiles_writer` module.
- [pysmilesutils](https://github.com/MolecularAI/pysmilesutils) — ML-focused
  SMILES utilities from AstraZeneca/MolecularAI.

**Tutorials / walkthroughs:**
- ["Let's Build a SMILES Parser in Rust"](https://depth-first.com/articles/2020/05/25/lets-build-a-smiles-parser-in-rust/)
  — Rich Apodaca, Depth-First, step-by-step scanner-and-builder walkthrough.
- ["Parsing SMILES from Scratch in JavaScript"](https://metamolecular.com/blog/2013/09/10/parsing-smiles-from-scratch-in-javascript/)
  — Metamolecular, tokenizer-to-graph walkthrough.
- ["A Comprehensive Treatment of Aromaticity in the SMILES Language"](https://depth-first.com/articles/2020/02/10/a-comprehensive-treatment-of-aromaticity-in-the-smiles-language/)
  — Depth-First, aromaticity deep dive.
- ["Abstract Syntax Trees for SMILES"](https://depth-first.com/articles/2020/12/14/an-abstract-syntatx-tree-for-smiles/)
  — Depth-First.
- Chemoinformatics+ Erasmus Mundus master's program materials, CDK-based
  university course notes, and numerous textbook treatments.

**Contamination risk: high.** SMILES is a decades-old format taught in nearly
every chemoinformatics curriculum, and several of the implementations above
are specifically structured as tutorial walkthroughs ("Let's Build…",
"Parsing from Scratch in…"). An agent with broad web training will have seen
the full shape of a correct parser. This is a more severe saturation problem
than RS274 or IGES, and it partially undermines the "success reflects
reasoning, not recall" sanity-check in `CHOOSING_EVALS.md`. Mitigations are
possible — adversarial test cases that exercise the OpenSMILES spec beyond
what tutorials cover (e.g., unusual bracket content, high-index ring
closures, disconnected structures with stereo, exotic charges/isotopes) —
but this is a real weakness and should be weighed before committing.

## Risks and Open Questions

**Open Question 1 — Canonical SMILES determinism. This is the blocker.**
OpenSMILES §5 explicitly defers canonicalization to external graph-theory
literature and does not specify an algorithm. In practice, Daylight, RDKit,
and Open Babel produce **different** canonical SMILES for the same molecule,
and the Daylight algorithm itself has shifted across versions to fix edge
cases. There are published comparison studies (e.g., "Get Your Atoms in
Order", Schneider et al., J. Chem. Inf. Model. 2015, proposing a novel
canonicalization for RDKit because the existing ones had known failures;
"Towards a Universal SMILES", O'Boyle 2012, explicitly motivated by the lack
of inter-toolkit agreement) confirming this is not a quirk but a structural
feature of the problem. For CLISpecBench this is fatal unless addressed,
because the deterministic-scoring-surface rule is non-negotiable.

Three possible resolutions, in decreasing aggressiveness:

1. **Drop canonicalization entirely.** Score only parse correctness, atom
   list, bond list, ring count, formula, and weight. The eval loses some
   surface area but remains substantial (~96 tests, ~1200 LOC). This is the
   honest option and the one this README recommends unless option (2) proves
   viable.
2. **Pick one canonicalization algorithm and specify it in the prompt.** The
   obvious candidates are (a) Weininger's 1989 CANGEN (SMILES paper 2) as
   described in its original J. Chem. Inf. Comput. Sci. publication, with
   the known ambiguities resolved by explicit harness-side disambiguation
   text; or (b) Schneider et al.'s algorithm from "Get Your Atoms in Order"
   (ACS publication). Either requires shipping the algorithm description
   inside `prompt/docs/` (not linking externally) and carries
   contamination risk in reverse — agents trained on the paper text have an
   advantage. The prompt must also be crisp enough that "canonical" means
   exactly one string per molecule.
3. **Score canonical SMILES by equivalence class, not string equality.**
   Run the agent's canonical output back through its own parser and compare
   atom/bond sets to the expected molecule; any valid SMILES that
   round-trips to the same molecular graph passes. This sidesteps the
   algorithmic disagreement entirely but makes the test much weaker: it
   becomes a "does your parser round-trip" test, not a canonicalization
   test. It also requires the harness to reliably re-parse arbitrary
   SMILES, which means shipping a reference parser — a strange artifact.

The current recommendation is **option 1**: drop canonicalization from the
eval, score the rest. Option 2 may be worth a follow-up experiment but
should not gate initial landing.

**Open Question 2 — Aromaticity model.** Aromaticity is the second-largest
spec ambiguity. OpenSMILES reduced but did not eliminate it; RDKit, Open
Babel, and Daylight still differ on edge cases. We must pick one model
(OpenSMILES's relaxed 4n+2-over-SSSR is the obvious choice since the spec
defines it explicitly) and state it firmly in the prompt. Lowercase atoms
in input are unambiguous; the question is what to count as aromatic when
computing rings or formula.

**Open Question 3 — Stereo and isotopes.** The full spec includes `@`/`@@`
chirality, `/` and `\` double-bond stereo, and arbitrary isotope labels.
Stereo is hard to test deterministically (another canonical-form issue) and
adds complexity without adding much signal for a medicinal-chemistry
persona at screening scale. Recommendation: **parse them (so brackets don't
break) but do not score them in v1**; the output JSON can carry them
through passively. Isotope handling is simpler because atomic weight is a
pure function of the explicit isotope when given.

**Open Question 4 — Ring perception algorithm.** "Number of rings" has more
than one reasonable definition (SSSR, ESSR, cycle rank). Commit to cycle
rank (= bonds − atoms + connected-components) in the prompt; it is
algorithm-free and unambiguous for this purpose. SSSR is implementation-
dependent.

**Open Question 5 — IUPAC atomic-weight intervals.** IUPAC 2021 reports
several elements (Ar, Pb, H, Li, B, C, N, O, Mg, Si, S, Cl, Br, Tl) with
interval values rather than single numbers. We collapse to single values in
the shipped periodic-table file and document the choice; agents read from
the file, so there is no ambiguity at scoring time.

**Contamination risk (restated).** High. The eval's score signal may
partly reflect training-data recall rather than genuine spec comprehension.
Mitigation: aggressive adversarial test design that targets OpenSMILES
corners tutorials rarely cover.

## CHOOSING_EVALS Checklist

- **Documentation-first**: *partial* — OpenSMILES covers parsing and
  aromaticity cleanly. Canonicalization is not covered (§5 defers) and
  would violate this rule unless we drop it (see Open Question 1). Formula
  + weight + ring-count scoring is documentable.
- **Non-developer describable**: *pass* — the medicinal-chemistry persona
  above is plausible from a domain expert with zero software background.
  "Parse this SMILES, count rings, give me the formula" is everyday
  domain vocabulary.
- **Authoritative source material**: *pass* — OpenSMILES is the
  community-authored successor to Daylight's proprietary spec, maintained
  by Craig A. James, hosted publicly, and widely cited. IUPAC CIAAW is the
  authoritative source for atomic weights.
- **No solver code in corpus**: *pass* — OpenSMILES describes grammar and
  semantics without shipping a parser. The periodic-table JSON is data, not
  solver code.
- **Behaviorally unambiguous**: *partial* — true for parse, formula,
  weight, and ring count (if we pick cycle rank). False for canonical
  SMILES. Aromaticity has documented edge cases.
- **Deterministic scoring surface**: *partial* — deterministic for parse
  output, formula, weight, and ring count. Non-deterministic for canonical
  SMILES across toolkits. Resolved only if we drop canonicalization (Open
  Question 1).
- **Independent failure modes**: *pass* — tokenizer bugs, valence bugs,
  ring-closure bugs, formula-ordering bugs, and weight-table bugs are
  naturally independent. One bug does not collapse the suite.
- **System-level complexity**: *pass* — ~1200–2000 LOC reference
  implementation with multiple cleanly separable modules (tokenizer,
  parser, aromatic model, valence/H-count, ring perception, formula
  builder, weight calculator, JSON emitter).
- **Test-suite scalability**: *pass* — ~104 tests estimated, ~96 even
  without canonicalization, comfortably above the 50-test floor.
- **Contamination resistance**: *fail* — SMILES is heavily represented in
  training data, with explicit "build a SMILES parser" tutorials in at
  least Rust, JavaScript, and Python, plus RDKit/OpenBabel/CDK/Indigo
  source in the open. This is the eval's weakest dimension.
- **Reference implementation feasibility**: *pass* — Python reference is
  straightforward; a C++ or Rust reference is also viable. Multiple
  existing open-source implementations demonstrate feasibility for the
  language-agnostic surface.
- **Reasonable harness fit**: *pass* — local files, CLI flags, JSON
  output, no network. Slots cleanly into the CLISpecBench harness.
- **Publicly distributable docs**: *pass* — OpenSMILES is GFDL 1.2
  (redistributable with copyright preservation). IUPAC atomic-weight data
  is publicly published.

## Summary

SMILES is a plausible-but-flawed CLISpecBench eval. The medicinal-chemistry
persona is authentic and the OpenSMILES spec is a genuinely high-quality
single-document corpus, redistributable, widely understood, and rich enough
to justify a ~1500-LOC reference implementation with ~100 meaningful tests.
The scoring surface splits cleanly into parse correctness, formula, weight,
and ring count — all deterministic, all independently scorable. Two serious
concerns weigh against it: contamination is high (many open-source parsers,
several explicit tutorials), and the canonical-SMILES portion is
structurally non-deterministic across correct implementations because
OpenSMILES §5 itself declines to specify the algorithm. The honest path
forward is to drop canonical SMILES from v1, lean on adversarial test
design to blunt the contamination concern, and ship the eval as a
parse-plus-formula-plus-weight-plus-rings task. With those scope cuts, it
passes the CHOOSING_EVALS criteria that matter and loses only on a
contamination axis we can quantify empirically once we run it.

Sources:
- [OpenSMILES specification](http://opensmiles.org/opensmiles.html)
- [OpenSMILES GitHub (asciidoc source)](https://github.com/timvdm/OpenSMILES/blob/master/opensmiles.asciidoc)
- [RDKit source and SMILES parsing docs](https://github.com/rdkit/rdkit)
- [Open Babel source](https://github.com/openbabel/openbabel)
- [Indigo toolkit](https://github.com/epam/Indigo)
- [pysmiles](https://github.com/pckroon/pysmiles)
- ["Let's Build a SMILES Parser in Rust" — Depth-First](https://depth-first.com/articles/2020/05/25/lets-build-a-smiles-parser-in-rust/)
- ["Purr: A SMILES Toolkit for Rust" — Depth-First](https://depth-first.com/articles/2021/03/03/purr-a-smiles-toolkit-for-rust/)
- [smiles-parser (hobofan)](https://github.com/hobofan/smiles-parser)
- [SmilesDrawer](https://github.com/reymond-group/smilesDrawer)
- ["Parsing SMILES from Scratch in JavaScript" — Metamolecular](https://metamolecular.com/blog/2013/09/10/parsing-smiles-from-scratch-in-javascript/)
- ["A Comprehensive Treatment of Aromaticity in the SMILES Language" — Depth-First](https://depth-first.com/articles/2020/02/10/a-comprehensive-treatment-of-aromaticity-in-the-smiles-language/)
- [RDKit issue #3373 — PubChem vs Daylight canonical SMILES](https://github.com/rdkit/rdkit/issues/3373)
- [Canonical SMILES discussion (rdkit-discuss, Narkive)](https://rdkit-discuss.narkive.com/VNZkkpEv/canonical-smiles)
- ["Get Your Atoms in Order" — Schneider et al., J. Chem. Inf. Model. 2015](https://pubs.acs.org/doi/abs/10.1021/acs.jcim.5b00543)
- ["Towards a Universal SMILES representation" — O'Boyle 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3495655/)
- [IUPAC Standard Atomic Weights 2021 Technical Report](https://iupac.qmul.ac.uk/AtWt/AtWt21.html)
- [IUPAC CIAAW](https://www.ciaaw.org/atomic-weights.htm)
