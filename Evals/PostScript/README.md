# PostScript

A PostScript Level 1 subset interpreter eval for CLISpecBench: agents receive the Adobe PostScript Language Reference and must produce a stack-machine interpreter that emits a JSON trace of final operand stack, graphics state, and recorded current-path operations — no rasterization.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt, tests, or reference implementation yet.

## Why this eval

PostScript is a dense, well-specified, fully documented stack-based language with a rich behavioral surface: arithmetic with sharp int/real coercion rules, a dictionary stack with scope semantics, a graphics state stack, and a path-building sublanguage with a current transformation matrix. It is a natural CLISpecBench candidate along several axes:

- **Single authoritative spec.** The Adobe PostScript Language Reference, 3rd Edition ("Red Book") is a self-contained, formal language definition — one document, clearly sectioned, covering every operator with precise stack-effect notation.
- **Non-developer audience.** Print-production specialists, parametric-plotter users, and typesetting hobbyists routinely write PostScript by hand; the base prompt voice is natural.
- **Ample independent failure modes.** Hundreds of operators fall into disjoint groups (arithmetic, stack, array, dict, string, control, path). A bug in one group does not automatically fail the others.
- **Stripping rasterization resolves the hardest ambiguity.** By emitting a *trace* of path-building and graphics-state operations rather than a rendered page, the scoring surface becomes deterministic structured JSON — no pixel comparison, no font hinting, no Bezier tessellation tolerance debates.

The harder question is whether the operator scope can be bounded tightly enough to make a 1000–2500 LOC reference implementation feasible while still supporting 50+ independent tests. The subset sketch below argues yes.

## Documentation Corpus

**Primary document:** Adobe PostScript Language Reference, 3rd Edition (PLRM.pdf, freely distributed by Adobe at `adobe.com/jp/print/postscript/pdfs/PLRM.pdf`). Roughly 900 pages. Chapters 3 (Language) and 8 (Operator Details) are the core of the eval; chapters 4 (Graphics) and 7 (Device Control) are scoped down (no rasterization, no device params).

**Corpus pruning:** because the Red Book documents Level 1, 2, and 3, the `prompt/docs/` copy will be either (a) an excerpted transcription limited to Level 1 sections, or (b) the full PDF paired with an explicit scope document (`scope.md`) in the prompt enumerating which operator names are in-scope. Option (b) is likely simpler and avoids misattributed edits — the authoritative PDF is never modified, and the scope file is the contract.

**Non-goals excluded from scope:** font operators (`findfont`, `scalefont`, `setfont`, `show`, character encoding), image operators (`image`, `colorimage`, `imagemask`), rasterization (`stroke`, `fill`, `showpage` produce *trace entries* rather than pixels), filters, file I/O, errordict customization, save/restore snapshotting of VM, composite fonts, color spaces beyond DeviceGray.

## Base Prompt (sketch)

> I write parametric drawing scripts in PostScript for an old Gerber-style plotter pipeline. The plotter itself is offline, but I want to take a PostScript program and understand what it would draw *without* actually plotting anything — I want to see the list of pen movements the program produced, the final state of my coordinate system, and what the calculator stack looked like at the end.
>
> Please build a program that reads a PostScript file and tells me: (1) every moveto, lineto, curveto, and closepath the program added to its current path, in order; (2) the final graphics state — where my pen is, what the transformation matrix looks like, what the line width is, and so on; (3) what values were left sitting on the operand stack when the program finished; (4) any error that stopped execution early.
>
> I don't need the output rendered as a picture. I don't need fonts or text rendering. I don't use image operators. Stick to the Level 1 stack, arithmetic, array, dictionary, string, control, graphics-state, and path-construction operators from the Adobe PostScript Language Reference.

(A domain expert would continue with example scripts and a concrete worked case. The technical-requirements prompt carries the CLI contract and JSON schema separately.)

## Technical Requirements (sketch)

- **Language targets:** C++20/CMake first; Python as a secondary reference (PostScript's dynamic semantics map cleanly onto Python). Task IDs `postscript-cpp`, `postscript-py`.
- **CLI:** `postscript --input <program.ps> --output <trace.json>`. Exit codes: 0 on success, 1 on a PostScript error (`stackunderflow`, `typecheck`, `undefined`, etc.) caught during interpretation, 2 on harness/internal error.
- **Output JSON top-level schema:**
  - `operand_stack`: array of stack entries, top-of-stack last; each entry is `{type, value}` with types `integer`, `real`, `boolean`, `string`, `name`, `array`, `dict`, `mark`, `null`, `operator`, `procedure`.
  - `graphics_state`: `{ctm: [6 reals], current_point: [x, y] | null, line_width, line_cap, line_join, miter_limit, dash_pattern, dash_offset, gstate_stack_depth}`.
  - `current_path`: array of path ops, each `{op: "moveto"|"lineto"|"curveto"|"closepath", args: [...user-space coords...]}`, recorded in execution order. `newpath` clears this list; `stroke`/`fill` append a structured marker entry and clear. `showpage` appends a marker entry.
  - `dict_stack_depth`: integer (systemdict + userdict + any user-pushed dicts).
  - `error`: `{name, offending_operator, stack_depth_at_error}` or `null`.
- **Determinism rules** baked into the contract:
  - Integer vs real: `add`, `sub`, `mul`, `div`, `idiv`, `mod` must follow PLRM §8.1 exactly. `div` always produces real; `idiv`/`mod` require integers and produce integer; mixed-type `add`/`sub`/`mul` produce real.
  - CTM representation: always 6 reals (a, b, c, d, tx, ty), never an abbreviated matrix.
  - `dict` objects in the operand-stack dump are serialized by VM identity id + length, not by contents, to avoid cycles; `array` and `procedure` are dumped structurally up to a bounded depth.
  - Number formatting: reals are printed with enough precision to round-trip a 32-bit float (at least 9 significant digits); integers print without a decimal point.
- **In-scope operator list** (published in the prompt, roughly 120 operators): arithmetic (`add sub mul div idiv mod neg abs ceiling floor round truncate sqrt atan cos sin exp ln log`), stack (`pop exch dup copy index roll clear count mark cleartomark counttomark`), array (`array length get put getinterval putinterval aload astore forall`), dict (`dict begin end def load store known where copy forall length`), string (`string length get put getinterval putinterval forall anchorsearch search`), control (`exec if ifelse for repeat loop exit stop stopped`), boolean/relational (`eq ne gt ge lt le and or xor not`), type/conversion (`type cvi cvr cvs cvn cvlit cvx`), graphics-state (`gsave grestore initgraphics setlinewidth setlinecap setlinejoin setmiterlimit setdash currentlinewidth currentlinecap currentlinejoin currentmiterlimit currentdash`), CTM (`matrix identmatrix initmatrix currentmatrix setmatrix concat concatmatrix transform dtransform itransform idtransform translate rotate scale`), path (`newpath moveto rmoveto lineto rlineto curveto rcurveto arc arcn arct arcto closepath currentpoint pathbbox`), painting sentinels (`stroke fill eofill clip showpage` — recorded as markers, not rasterized).
- **Explicitly out-of-scope** (agent should error with `undefined` if encountered): `show`, `charpath`, `image`, `colorimage`, `imagemask`, `findfont`, `scalefont`, `setfont`, `makefont`, all color-space operators except default-gray `setgray`/`currentgray`, `save`/`restore`, all file/filter operators, `run`, `bind` (treated as no-op is acceptable — must be documented as such).

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| Arithmetic (int/real coercion, division flavors, transcendentals) | ~12 |
| Stack ops (roll, copy of mixed types, count, mark/cleartomark) | ~8 |
| Arrays (construction, nested, getinterval, forall, aload/astore) | ~7 |
| Dictionaries (dict stack scoping, def vs store, known/where, forall order) | ~8 |
| Strings (byte-level get/put, search, anchorsearch, length, encoding) | ~5 |
| Control flow (if/ifelse, for/repeat/loop, exit/stop/stopped, nested) | ~8 |
| Procedures and names (literal vs executable, bind, cvx/cvlit, name lookup) | ~6 |
| Type and conversion (cvi/cvr truncation, cvs formatting, type dispatch) | ~5 |
| Graphics state stack (gsave/grestore interleaved with CTM changes) | ~4 |
| CTM operators (translate/rotate/scale composition, concat, setmatrix) | ~6 |
| Path construction (moveto/lineto/curveto, relative variants, current_point) | ~7 |
| Arc operators (arc, arcn, arct, arcto — flattening vs curve recording) | ~5 |
| Path recording semantics (newpath clear, painting sentinels, closepath) | ~4 |
| Error cases (stackunderflow, typecheck, undefined, rangecheck, dictstackunderflow) | ~8 |
| Integration (small published PLRM example programs end-to-end) | ~6 |
| **Total** | **~99** |

Two axes of concern mentioned in `CHOOSING_EVALS.md` §Strong Preferences are addressed:

- *Independent failure modes.* Each category above exercises a different interpreter subsystem; an agent that ships a buggy dictionary stack can still earn arithmetic points.
- *Test-suite scalability.* The floor is 50; this sketch reaches ~99 without stretching, and each path/CTM test can easily be replicated across 5–10 input variations (different matrices, different numeric edge cases, different control-flow wrappings).

## Implementation Size Estimate

Calibration points from the research:

- **Ghostscript**: the industry reference, written in C with a substantial PostScript core of its own (the interpreter is written partly in C and partly in PostScript). The ghostpdl repository is very large (hundreds of thousands of lines), but the bulk is rasterizer and device drivers — not relevant here.
- **xpost** (github.com/luser-dr00g/xpost): primary-C PostScript interpreter, BSD-3, Level 1+ scope with a graphics backend. Exact LOC not advertised, but language breakdown on the repo is 81% C, 15% PostScript (its own bootstrap), suggesting a non-trivial core (order of 10k+ C LOC).
- **Williams CS136 student lab**: a very small Level 1 subset (13 operators: `pstack add sub mul div dup exch eq ne def pop quit ptable`) — course scale, ~200–500 LOC.
- **JaredStrandWSU Python PostScript interpreter** (CS355 assignment): tens of operators, a few hundred lines of Python.

A CLISpecBench-scale subset sits between the student assignments and xpost: ~120 operators, dict stack, graphics state stack with CTM, path recording, error dictionary. Realistic estimates:

- **C++ reference:** ~2000–2800 LOC across scanner, parser-to-objects, interpreter loop, operator tables (one function per operator family), graphics state, path recorder, JSON emitter.
- **Python reference:** ~1200–1800 LOC — Python's dynamic types collapse much of the object-model boilerplate.

Both comfortably clear the 1000-LOC floor in `CHOOSING_EVALS.md`.

## Contamination & OSS Landscape

**Specific implementations found:**
- [Ghostscript](https://ghostscript.com/) — C, hundreds of thousands of LOC total (PostScript interpreter + PDF + rasterizer + devices). Industry reference. Saturated in training data *as a dependency*, but the implementation itself is sprawling and tangled with rasterizer concerns; directly cribbing Ghostscript is unlikely to produce a passing trace-only submission cleanly.
- [xpost](https://github.com/luser-dr00g/xpost) — C, BSD-3-Clause, Level 1-ish with a pluggable graphics backend. Smaller and more approachable than Ghostscript but still well beyond subset scope. Starred but not highly visible.
- [JaredStrandWSU/CS355-PostScript-Interpreter-Python](https://github.com/JaredStrandWSU/CS355-PostScript-Interpreter-Python) — Python, student assignment scale.
- [courtsny/postscript-interpreter](https://github.com/courtsny/postscript-interpreter) — Python, student scale.
- [zanepartain/Postscript-Interpreter](https://github.com/zanepartain/Postscript-Interpreter) — Python 3, stated to support variables, functions, static and dynamic scoping.
- [Wiladams/lj2ps](https://github.com/Wiladams/lj2ps) — LuaJIT PostScript VM.
- [AndyCappDev/postforge](https://github.com/AndyCappDev/postforge) — Level 3 PostScript renderer to PNG/TIFF/PDF/SVG.
- [PostCanvas](http://www.feiri.de/pcan/) — JavaScript PostScript-to-HTML5-canvas interpreter.

**Tutorials / walkthroughs:**
- Paul Bourke's PostScript tutorials (widely cited, domain-oriented not interpreter-oriented).
- [Tom's PostScript tutorial](http://cholla.mmto.org/computers/postscript/tutorial.html).
- [A First Guide to PostScript](https://hint.userweb.mwn.de/compiler/www.cs.indiana.edu/postscript.html).
- [Williams CSCI 136 PostScript lab](https://www.cs.williams.edu/~jannen/teaching/s18/cs136/labs/postscript.html) and [USF CS652 lecture notes](https://github.com/parrt/cs652/blob/master/lectures/postscript.md) — both are *interpreter-writing* walkthroughs targeting a very narrow subset (a dozen operators, no graphics state, no CTM, no path). Useful as contamination vectors for the "basic stack machine" skeleton; *not* useful for the CTM/path/arc/dict-stack work that dominates the scoring surface.
- "Learning PostScript by Doing" (Heck, 2005) and "The PostScript programming language" (Burch, CSBSJU) — both user-facing tutorials, not interpreter guides.

**Contamination risk:** **medium**.

Justification: PostScript-as-a-language is famously well-known — any competent model has seen stack-machine pseudocode, `dup exch def` idioms, and simple tutorials in pretraining. But two properties pull the risk *down*:

1. The "widely known" implementations (Ghostscript, xpost) are *too big* to memorize verbatim and are oriented around rasterization rather than the trace-only JSON surface this eval scores. An agent cannot copy-paste a Ghostscript function and expect it to emit our schema.
2. The available tutorial implementations (Williams lab, USF CS652, a handful of student repos) cover the *easy* operators — basic arithmetic, stack, def — and uniformly stop short of the hard ones: CTM composition, arc-to-curveto flattening, G2/G3-style state recording, integer-vs-real coercion edge cases, `roll` on mixed types, dict stack scoping under nested procedures, `stopped` semantics. These are exactly where the test-suite mass concentrates.

Risk is non-trivial (higher than IGES, lower than RS274), but manageable with test cases drawn from Red Book §8 corner cases rather than tutorial territory.

## Risks and Open Questions

- **Operator scope must be enumerated in the prompt, not left to "Level 1."** The "Level 1 subset" label is fuzzy in the literature — even the Red Book's "Level 1" notation is scattered across hundreds of pages. The base prompt cannot smuggle in a developer-grade operator list, but `technical-requirements-prompt.md` can and should publish the *exact* in-scope operator list. Without this, an agent implementing 60 operators and skipping 60 others would not be behaviorally unambiguous failing — it would be defensibly ambiguous, and the eval would drift toward "guess the author's subset."
- **Path-list determinism under arc operators.** `arc`, `arcn`, `arct`, `arcto` are specified in the Red Book in terms of path segments but the spec permits the interpreter to flatten arcs into line segments or curves at its discretion; Ghostscript and other implementations choose different flattening thresholds. The technical requirements must fix one: *arcs are recorded as their constituent Red Book cubic-Bezier approximations, with a fixed formula for fractional-quadrant sub-arcs*. Otherwise the `current_path` array is not deterministic and this whole eval falls apart.
- **Procedures in operand-stack dumps are nontrivial.** A procedure is an executable array of objects; if the final operand stack contains a procedure, the JSON dump must serialize its structure. Cycles are possible (procedures can reference themselves through the dict stack). The contract needs a bounded-depth, bounded-size serializer, specified in the technical-requirements prompt.
- **Subtle scoping bugs may not show up.** The dict stack is where agents often fail: `def` writes to the topmost dict, `store` scans the dict stack for an existing binding and rewrites it in place, and `load` performs a bottom-up lookup. A bug that silently ignores intermediate dicts on the stack will pass simple programs but fail adversarial ones. The test suite needs explicit nested-`begin`/`end` programs with `def`-vs-`store` differentials.
- **`bind` is a language-level operation with real semantics** (replacing operator names with operator references in a procedure body, affecting later `def`/`store`). The in-scope contract provisionally treats `bind` as a no-op, but this must be explicit — if agents randomly implement `bind` "properly" it changes behavior of subsequent tests.
- **Integer overflow.** PLRM §3.3.1 specifies 32-bit signed integers with implementation-defined overflow-to-real promotion. C++ needs explicit overflow checks; Python needs explicit clamping. The contract should pick one rule (e.g., "integer operations that would overflow 32-bit signed produce a real result") and the test suite should have a dedicated overflow test.
- **Reference implementation maintenance burden.** ~2500 LOC of C++ that faithfully implements the scope is achievable, but path-recording plus dict-stack scoping plus CTM composition plus arithmetic coercion is a *lot* of surface area for the eval author to own. RS274's ~4–5 kLOC C++ reference is a rough upper bound on what this project has sustained; PostScript would be at that level.

## CHOOSING_EVALS Checklist

- **Documentation-first:** **pass** — PLRM 3rd edition is dense, formal, and self-contained for the scoped operator set; every test can be justified by a section reference.
- **Non-developer describable:** **pass** — print/plotter practitioners write PostScript as a native idiom and can describe "what the pen did" without needing software jargon.
- **Authoritative source material:** **pass** — Adobe PLRM is public, stable, and the canonical reference.
- **No solver code in corpus:** **pass** — the Red Book is a language reference, not an implementation guide; it contains no C source for an interpreter. Adobe's "Blue Book" (PostScript Language Tutorial and Cookbook) is PostScript programs, not interpreter code, and will be excluded to stay conservative.
- **Behaviorally unambiguous:** **partial** — most arithmetic, stack, and dict ops are crisp; arc flattening, `bind` semantics, and overflow rules require explicit technical-requirements decisions. Without them: fail.
- **Deterministic scoring surface:** **partial** — JSON path-list + graphics-state + operand-stack is deterministic *if* arc recording and procedure serialization are nailed down in the contract. Assuming they are: pass.
- **Independent failure modes:** **pass** — the ~15 test categories hit disjoint subsystems; arithmetic, dict stack, path, CTM, and control flow fail independently.
- **System-level complexity:** **pass** — scanner + tokenizer + object model + interpreter loop + dict stack + graphics state stack + CTM + path recorder + error dictionary + JSON emitter is a real multi-module system. 1200–2800 LOC depending on language clears the 1000 floor.
- **Test-suite scalability:** **pass** — sketched ~99 tests without padding; the domain easily supports 150+ with input variation.
- **Contamination resistance:** **partial** — medium risk (see above). Mitigated by trace-only scoring surface (Ghostscript can't be copy-pasted) and by concentrating tests on non-tutorial corners, but the basic stack-machine skeleton is broadly known.
- **Reference implementation feasibility:** **partial** — ~2500 LOC of faithful C++ is feasible but non-trivial for a single maintainer. Python reference helps cross-check semantics. A poorly maintained reference would undermine the whole eval.
- **Reasonable harness fit:** **pass** — single binary, `--input`/`--output`, JSON output, no network, no GUI, no hosted services. Mirrors the RS274/IGES mold exactly.
- **Publicly distributable docs:** **pass** — PLRM PDF is freely distributed by Adobe and broadly redistributed; checking a copy (or a transcribed markdown version) into `prompt/docs/` is standard practice.

## Summary

PostScript Level 1 (subset, trace-only) is a plausible CLISpecBench eval in the same weight class as IGES: a dense, authoritative, freely-distributed single-document spec; a domain with real non-developer practitioners; a deterministic structured-JSON scoring surface; and a test-suite floor (~99 sketched, 150+ feasible) that comfortably clears the benchmark's minimum. The work it would require from the eval author is real — a ~2500 LOC faithful C++ reference plus a meticulous technical-requirements document that enumerates the in-scope operator list, pins down arc flattening, defines procedure serialization, and specifies integer-overflow behavior — but none of those asks is fundamentally harder than what RS274 and IGES already absorb. The primary risks are contamination-medium (mitigated by the trace-only surface that frustrates copy-paste from Ghostscript) and scope discipline (the subset must be a published contract, not an author-in-the-loop judgment call). Recommendation: worth prototyping a `base-prompt.md` and a seed operator list before committing to a full reference implementation.
