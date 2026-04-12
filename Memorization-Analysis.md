# Memorization Analysis — CNCSim and SWE-BuildBench

**Status:** Draft  
**Last Updated:** April 2026

---

## 1. Motivation

Epoch AI's [MirrorCode preliminary results](https://epoch.ai/blog/mirrorcode-preliminary-results)
(Adamczewski, Rein, Owen, Brand; April 2026) raise important questions about
how much of a model's performance on coding benchmarks is attributable to
memorization of training data versus genuine problem-solving. This document
analyzes what those findings mean for interpreting CNCSim scores and proposes
concrete experiments to measure and mitigate memorization effects.

---

## 2. MirrorCode's Memorization Methodology (Summary)

MirrorCode detects memorization by prompting models to reproduce individual
functions from target codebases with minimal context, then measuring
whitespace-normalized Levenshtein similarity against the originals.

Key findings:

- **Baseline similarity is ~0.34** even for code the model provably never saw
  (post-training-cutoff programs). Similar problems produce similar code.
- **Included programs scored 0.31–0.41**, near baseline — minimal memorization.
- **One excluded program scored 0.74** with 83% of functions above 50%
  similarity — clear memorization signal.
- **Memorization decreased across model generations** for most programs,
  suggesting capability improvements rather than increased reliance on memorized
  code.

Critical limitation they acknowledge:

> "Perhaps our memorization measurements are insufficiently sensitive, or
> perhaps AIs could memorize other relevant details, such as discussion of the
> codebases and their algorithmic approaches."

This limitation is directly relevant to CNCSim.

---

## 3. CNCSim's Memorization Risk Profile

### 3.1 What is certainly in training data

| Artifact | Risk | Notes |
|----------|------|-------|
| RS274/NGC spec (NISTIR 6556, 2000) | Spec is the input — this is intentional | Models have read the spec; so do eval subjects |
| NIST RS274 C++ interpreter | High | The original reference implementation is public |
| LinuxCNC interpreter | High | Large, active open-source project |
| GRBL / grblHAL | High | Extremely popular embedded G-code parsers |
| Assorted tutorials, blog posts | High | "How to build a G-code interpreter" is well-covered |

### 3.2 What is NOT in training data

| Artifact | Status | Notes |
|----------|--------|-------|
| CNCSim hidden test suite | Private | Never published |
| CNCSim CLI contract + JSON schema | Public but novel | Custom to this eval |
| CNCSim reference implementations | Public but post-2025 | Original code, not copies |

### 3.3 The unmeasurable gap

MirrorCode's function-level Levenshtein test cannot be applied to CNCSim
because CNCSim asks "implement this spec," not "reproduce this codebase." There
is no single target to compare against — any correct RS274 interpreter counts.

The memorization risk that matters is **algorithmic/architectural**: models have
likely internalized modal-group state machines, arc interpolation math,
parameter file semantics, and canned cycle patterns from seeing many G-code
interpreters. MirrorCode explicitly flags this as a limitation they cannot
measure.

---

## 4. Proposed Experiments to Measure Memorization

### 4.1 Obscure-vs-common feature analysis

**Hypothesis:** If memorization dominates, models score much higher on
well-known features than on obscure spec corners.

**Method:**
1. Partition the existing test suite into tiers by feature popularity:
   - **Tier 1 (ubiquitous):** G0/G1 linear motion, G2/G3 arcs, G28 home,
     M3/M4/M5 spindle, tool change
   - **Tier 2 (common):** canned cycles (G81–G89), G92 offsets, parameter
     expressions, feed rate modes
   - **Tier 3 (obscure):** cutter radius compensation edge cases, G87
     back-bore cycle, inverse-time feed with rotary axes, G10 L2 coordinate
     system offsets, probing cycles
2. Score each tier independently across models.
3. If Tier 1 >> Tier 3 beyond what difficulty explains, memorization is likely
   contributing. If scores are uniform, spec comprehension is doing the work.

**Difficulty control:** Some obscure features are also genuinely harder. To
control for this, compare models against each other within a tier: if a weaker
model matches a stronger model on Tier 1 but diverges on Tier 3, the stronger
model's Tier 1 advantage may be memorization-driven.

### 4.2 Spec-contradicting probes (the strongest signal)

**Hypothesis:** If a model follows a deliberately non-standard spec instruction
over its internalized knowledge, it is reading the document, not recalling
memorized implementations.

**Method:**
1. Create a modified spec document ("RS274-Alt") with targeted semantic changes:

   | Standard RS274 behavior | RS274-Alt modification |
   |-------------------------|----------------------|
   | G4 dwell P word = seconds | P word = **milliseconds** (÷1000) |
   | Arc center offsets (I/J/K) are incremental | Arc centers are **absolute** coordinates |
   | G20/G21 sets inch/mm mode | G20 = mm, G21 = inch (**swapped**) |
   | Default plane is XY (G17) | Default plane is **XZ (G18)** |
   | Modal groups: G0/G1/G2/G3 in group 1 | G0/G1 in group 1, G2/G3 in **group 14** (new) |
   | Feed rate F is in units/minute | F is in **units/second** |

2. Run agents against RS274-Alt with a corresponding modified test suite.
3. Score: does the agent produce behavior matching the *modified* spec or the
   *standard* RS274 behavior?

**Interpretation:**
- Agent follows RS274-Alt → genuine spec comprehension
- Agent follows standard RS274 → memorization is load-bearing
- Mixed results → partial memorization; the specific features where the agent
  ignores the modified spec indicate which behaviors are most contaminated

**Scoring:** Each contradicting probe produces a binary signal (followed
modified spec / followed standard behavior), making this the cleanest
measurement available.

### 4.3 Cross-language score comparison

**Hypothesis:** C++ G-code interpreters vastly outnumber Python/JS/Rust ones in
training data. If memorization contributes, models should perform better in
languages where more exemplars exist.

**Method:**
1. Run the same agent against `cncsim-full` (C++), `cncsim-full-py`,
   `cncsim-full-js`.
2. Control for the model's general language proficiency (measure via unrelated
   benchmarks).
3. A delta that exceeds the general proficiency difference suggests
   domain-specific memorization in that language.

### 4.4 Cross-generation comparison

**Hypothesis:** MirrorCode found memorization scores *decreased* across Claude
generations. If CNCSim scores increase while memorization (measured by 4.2)
stays flat or decreases, improvements reflect genuine capability gains.

**Method:**
1. Run CNCSim across multiple model checkpoints (e.g., Opus 3.5, 4.0, 4.6;
   GPT-4o, o3; Gemini 2.5).
2. Run spec-contradicting probes (4.2) on each.
3. Plot: (CNCSim score) vs. (spec-adherence rate on contradicting probes).
4. If these correlate positively, better models are better readers. If CNCSim
   score rises but spec-adherence is flat, newer models may just have more
   G-code data.

### 4.5 Direct function-level memorization probing

**Method:** Prompt models outside the eval context:

> "Write the `convert_arc` function from an RS274 G-code interpreter in C++."

Compare outputs (Levenshtein) against the NIST reference interpreter,
LinuxCNC, and our own reference implementation. If a model reproduces one of
these verbatim (similarity > 0.6), it has memorized that implementation. If it
produces something structurally different but functionally equivalent, the
signal is ambiguous.

This is informative but not conclusive — a model can memorize source code
without that memorization being *activated* during the eval (where it receives
the spec and builds from scratch).

---

## 5. Mitigation: The RS274-Alt Spec

Beyond measurement, spec-contradicting modifications can serve as a
**mitigation** — a contamination-resistant variant of the CNCSim eval.

### 5.1 Design: RS274-Alt (Modified G-code Semantics)

Create a fork of the CNCSim eval where the specification document describes a
G-code dialect with deliberately non-standard semantics. This forces the model
to implement what the document says rather than what it "knows" G-code should
do.

**Principles:**
- Changes must be internally consistent and implementable (not contradictory)
- Changes should be scattered across the spec, not concentrated in one area
- Each change should affect observable test output
- The modified spec should remain realistic enough that an engineer unfamiliar
  with G-code couldn't distinguish it from a "real" dialect

**Proposed modifications for RS274-Alt v1:**

| Section | Standard | RS274-Alt | Rationale |
|---------|----------|-----------|-----------|
| Feed rate | Units/minute (G94) | Units/second | Tests numeric interpretation |
| Dwell | P = seconds | P = milliseconds | Tests unit handling |
| Arc centers | Incremental I/J/K | Absolute I/J/K | Tests coordinate math |
| Plane default | G17 (XY) at startup | G18 (XZ) at startup | Tests initialization |
| Inch/mm | G20=inch, G21=mm | G20=mm, G21=inch | Tests unit selection |
| Canned cycle retract | R word = absolute Z | R word = incremental from initial Z | Tests position math |
| Parameter numbering | #1–#5399 | #0–#5398 (zero-indexed) | Tests parameter handling |
| Tool length comp | G43=positive, G44=negative | G43=negative, G44=positive | Tests sign conventions |
| Spindle | M3=CW, M4=CCW | M3=CCW, M4=CW | Tests direction semantics |

### 5.2 Implementation plan

1. **Fork the spec document:** Copy `RS274NGC.md` → `RS274-Alt.md`, apply
   modifications with clear internal consistency.
2. **Fork the test suite:** Adjust expected values in all affected tests. This
   is mechanical — each modification has a known effect on outputs.
3. **Fork the reference implementation:** Modify the Python ref impl (easiest
   to patch) to match RS274-Alt semantics. Use it to generate expected outputs.
4. **Register as a new task:** `cncsim-alt` alongside `cncsim-full`.
5. **Score interpretation:** An agent's score on `cncsim-alt` vs. `cncsim-full`
   directly measures how much the standard semantics being in training data
   contributes. If scores are similar, the model is spec-driven. If
   `cncsim-alt` is much lower, memorization was helping.

### 5.3 Contamination lifecycle

RS274-Alt is itself susceptible to memorization once published. Mitigations:
- Keep the specific modifications private (publish only the task ID and scoring
  methodology)
- Rotate modifications periodically (RS274-Alt-v2, v3, ...) so no single
  variant persists long enough to be memorized
- The *framework* for generating modified specs can be public; the specific
  instance used for scoring should not be

---

## 6. MirrorCode's CLI Tools — Could We Write Spec-Driven Tests?

MirrorCode's four named benchmark programs are `choose`, `cal`, `gotree`, and
`Pkl`. We evaluated whether any have documentation thorough enough to support
SWE-BuildBench-style spec-driven testing (where the spec alone, not a reference
binary, defines correct behavior).

### 6.1 Assessment

| Program | Spec quality | Suitable for spec-driven eval? |
|---------|-------------|-------------------------------|
| **cal** | POSIX spec exists (`cal.1p`) but explicitly leaves output format "unspecified." Man page is brief. | **No.** Output format ambiguity means you can't write deterministic tests from the spec alone. MirrorCode uses the binary as oracle for a reason. |
| **choose** | Program documentation only (README, `--help`). No formal spec. | **No.** Too informal; behavior is defined by implementation, not document. |
| **gotree** | File format docs (Newick, Nexus) + high-level program description. | **Partial.** File formats have formal grammars, but command behavior is not formally specified. You could test parsing but not command semantics. |
| **Pkl** | Language reference at pkl-lang.org. Covers types, evaluation, objects, modules. No formal grammar or reduction rules. | **Maybe.** Closest to a real spec, but lacks the precision of RS274NGC. No BNF grammar, no formal evaluation semantics. You'd need to supplement with the reference binary for edge cases. |

### 6.2 Conclusion

None of MirrorCode's named programs have RS274-quality specification documents.
This is by design — MirrorCode's methodology uses **the reference binary as the
spec** (black-box, execute-only access), which sidesteps the need for written
specifications entirely. Their approach measures "can you clone this program's
behavior?" while SWE-BuildBench measures "can you read and implement this
document?"

These are complementary but different capabilities. A model that scores well on
MirrorCode might be an excellent reverse-engineer but a poor spec reader (or
vice versa).

### 6.3 Programs with RS274-quality specs (potential future evals)

Programs that *do* have thorough, formal specifications suitable for
doc-driven implementation benchmarks:

| Program/Domain | Spec document | Contamination risk | Eval potential |
|---------------|---------------|-------------------|----------------|
| **Lua** | *Lua 5.4 Reference Manual* — complete grammar, formal semantics | High (many implementations exist) | Good if paired with spec modifications |
| **JSON Schema** | RFC draft + formal meta-schema | Medium | Good — complex enough, fewer implementations |
| **MQTT** | OASIS standard, very precise | Medium | Moderate — networking adds complexity |
| **MessagePack** | Formal spec with exact byte layouts | Medium | Good — deterministic, testable |
| **Bencoding** (BitTorrent) | BEP-0003, very short formal spec | Low-medium | Too simple for standalone eval |
| **Redis protocol (RESP3)** | Formal spec, precise framing rules | Medium | Good — protocol parser + state machine |
| **PostScript (Level 1)** | *PostScript Language Reference* (Red Book) | Medium-high | Excellent — complex interpreter, formal spec |
| **PDF (subset)** | ISO 32000, very precise | High | Good if scoped to a subset |
| **WASM (binary format)** | W3C spec, fully formal | Medium | Excellent — formal semantics, testable |
| **SQLite (subset)** | Extensive docs but no single formal spec | High | Moderate — behavior defined by implementation |

For contamination resistance, the most promising candidates are those where:
1. The spec is precise enough for deterministic testing
2. The number of independent implementations is small
3. The domain is unfamiliar enough that architectural patterns aren't saturated

---

## 7. Relationship to MirrorCode's Methodology

| Dimension | MirrorCode | SWE-BuildBench (CNCSim) |
|-----------|-----------|------------------------|
| Input to agent | Execute-only binary + docs | Spec document only (no binary) |
| What's measured | "Can you clone this behavior?" | "Can you read and implement this?" |
| Memorization vector | Source code of target program | Algorithmic patterns from similar programs |
| Memorization test | Function-level Levenshtein | Spec-contradicting probes (proposed) |
| Post-cutoff guarantee | Yes (for baselines) | No (RS274 is from 2000) |
| Test oracle | Reference binary output | Written expected values from spec |

The approaches are complementary. A combined evaluation — "implement this
*modified* spec, and also match this binary's behavior on a separate set of
inputs" — would provide the strongest signal about genuine comprehension vs.
memorization.

---

## 8. Recommended Next Steps

1. **Implement experiment 4.2** (spec-contradicting probes) as the
   highest-signal, lowest-cost measurement. Even 3–4 targeted modifications
   with corresponding test assertions would produce actionable data.

2. **Build RS274-Alt v1** as a full parallel eval. Start with the Python
   reference implementation (2,975 lines) — it's the easiest to patch.

3. **Run experiment 4.1** (obscure-vs-common) using existing test results —
   this requires no new infrastructure, just reclassifying existing tests by
   feature tier and re-scoring.

4. **Establish a function-level baseline** (experiment 4.5) for the models
   you're scoring. This is cheap and provides context even if not conclusive.

5. **Consider registering `cncsim-alt` scores separately** on any leaderboard,
   with the delta (`cncsim-full` − `cncsim-alt`) reported as a memorization
   indicator.
