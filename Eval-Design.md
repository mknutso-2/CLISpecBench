# SWE-BuildBench — Design Document

**Author:** Matthew G. Knutson
**Status:** Draft
**Last Updated:** March 2026

---

> **Note on CNCSim naming.** The current harness exposes explicit language task
> IDs such as `cncsim-cpp`, `cncsim-py`, `cncsim-js`, and `cncsim-rs` for the
> single `Evals/CNCSim/` eval that exists today. The repository currently ships
> one CNCSim eval with multiple language variants. See `Evals/CNCSim/README.md`
> for the current framing.

## 1. Overview

SWE-BuildBench is a benchmark suite for evaluating **AI coding agents** on **documentation-driven system implementation** tasks. Each task gives the agent a curated documentation corpus — which may be a single specification document or a realistic collection of related documents — and asks it to produce a fully functional, compilable/runnable implementation, with no access to the hidden test suite used to score it.

The central question SWE-BuildBench asks is:

> *Given only a real-world documentation corpus, can an AI coding agent extract requirements, design a system architecture, implement it correctly across multiple files, and write meaningful tests for its own output?*

This differs from existing coding benchmarks in a fundamental way. HumanEval and its descendants test function completion. SWE-bench tests bug-fixing in existing codebases. SWE-BuildBench tests the full upstream engineering loop: document comprehension, system design, multi-file implementation, and self-verification — the things engineers actually do.

**On the name.** "SWE" follows the convention established by SWE-bench and signals that this is a full software engineering benchmark — not a code completion or patch task. "Build" is the operative word: every SWE-BuildBench task asks an agent to construct a working system from scratch, given only a documentation corpus. This distinguishes it from a companion benchmark we anticipate in the future — **SWE-ModifyBench** — which will ask agents to correctly modify or extend an existing codebase given change requirements. "Bench" signals a formal, reusable, leaderboard-worthy artifact intended for citation and longitudinal comparison.

SWE-BuildBench evaluates coding agent CLIs — tools such as Claude Code, Codex CLI, and Gemini CLI — that have access to a file system, terminal, compiler, and the ability to iterate on their own output. This mirrors how engineers actually use these tools and is where the interesting capability signal lives: whether the agent can extract requirements from documentation, design a multi-file system, implement it, and verify its own work without supervision.

---

## 2. Design Principles

**One corpus, one task.** Each task provides a curated documentation corpus: one or more publicly available documents that together constitute a complete and authoritative description of what must be built. The corpus composition is a deliberate task design decision — it may be a single dense specification (as in CNCSim), or a realistic multi-document collection (a primary spec, errata, worked examples, architecture notes) that more closely mirrors how engineers encounter requirements in practice. What the corpus must never include is a reference implementation or working code that solves the task. The subject must extract all requirements from the documentation itself.

**Deterministic scoring.** Every correctness test has an exact expected output. There is no ambiguity in whether a test passes. The hidden test suite is written and locked before any model is evaluated.

**Contamination resistance by design.** Test cases are never published. The full test suite lives in a private repository. Tasks are chosen from domains where ground-truth implementations do not saturate model training data.

**Language is a task parameter, not a framework requirement.** The CLI contract and scoring schema are consistent across all tasks. A single eval (prompt, docs, hidden test suite, reference implementations) may be offered in multiple target languages, and each (eval, language) pair is registered as a distinct task ID (e.g. `cncsim-cpp` vs `cncsim-py`). The hidden test suite is language-agnostic and exercises the submission through the shared CLI contract.

**The meta-score is an aggregate, not an average.** The SWE-BuildBench score is the geometric mean of task scores, not the arithmetic mean. This penalizes models that score well on one task but fail on others — generalization matters.

**Non-developer base prompt.** The base prompt is written from the perspective of a domain expert who is not a software developer — someone who knows exactly what they want to build but has no software engineering background. They would not think to specify test coverage, code quality standards, architectural patterns, or implementation strategy, just as they would not specify which sorting algorithm to use. The only exceptions are the three items the evaluation harness physically requires: implementation language, CLI flags, and output JSON schema. These are included with a brief framing note ("for technical compatibility, please use C++20 and produce output in the following format") that signals infrastructure constraint rather than engineering guidance. Everything else — whether to write tests, which architecture to choose, how to handle errors, what quality standards to follow — is left entirely to the agent's judgment. This framing serves two purposes: it measures genuine agent autonomy rather than instruction-following ability, and it emulates a realistic and increasingly common usage pattern where domain experts use coding agents to build real systems without software engineering backgrounds. Prompt variants that add developer-level guidance ("write a test for each discrete feature," "follow C++ Core Guidelines") are evaluated separately and never included in the base leaderboard — their value is measuring how much that guidance helps.

---

## 3. Task Anatomy

Every SWE-BuildBench task consists of two parts with different visibility.

### 3.1 Public (lives in the main repository)

```
tasks/<task-id>/
  TASK.md              # Task definition (see schema below)
  docs/                # The documentation corpus provided to the subject
    primary-spec.pdf   # At minimum one document; additional files as needed
    errata.pdf         # (optional)
    examples/          # (optional — worked examples, sample inputs, etc.)
  prompts/
    base.md            # The canonical minimal prompt — scores reported against this
    variants/          # Optional prompt variants for prompt engineering research
      with-tests.md    # e.g., adds "write a test for each discrete feature"
      with-guidelines.md  # e.g., adds "follow C++ Core Guidelines"
  harness/             # Build scripts and run wrapper
    build.sh           # Compile or install dependencies
    run.sh             # Execute the built artifact with standard args
  sample-tests/        # 10–20 representative test cases (inputs + expected outputs)
```

### 3.2 Private (lives in a separate private repository)

```
tasks/<task-id>/
  full-test-suite/     # 50–500 hidden test cases
    tests.jsonl        # One test per line: {id, input, expected, tags, weight}
  extensions/          # Optional: hidden extension tasks (see Section 4.4)
    ext-01/
      prompt.md        # Extension prompt injected after base task completion
      docs/            # Optional: additional documentation for the extension
      tests.jsonl      # Hidden test suite for this extension
    ext-02/
      ...
  reference/           # Optional: reference implementation used to generate expected outputs
```

### 3.3 TASK.md Schema

```markdown
# Task: <Human-readable name>

## Documentation Corpus
<!-- List every document included in the corpus. At minimum one entry. -->
- Document 1:
  - Title: <Official title>
  - Source: <URL or citation>
  - Version: <Version or date>
  - Role: primary-spec | errata | examples | reference-material
  - Sections relevant: <e.g., "Sections 2–8, Appendix A" — or "all">
- Document 2 (if applicable): ...

## Corpus Rationale
<!-- Why was the corpus scoped this way? Single-document tasks should note that
     this is intentional (e.g., "the RS274/NGC spec is self-contained"). Multi-document
     tasks should explain what each document contributes and why it was included. -->

## Implementation Language
<e.g., C++20>

## CLI Contract
See Section 6.

## Base Prompt
<!-- The base prompt is in prompts/base.md. Document here what it contains
     and confirm it adheres to the minimal prompt contract (Section 5.3 / Prompt Design):
     corpus pointer, CLI interface, output schema, language — nothing else. -->

## Included Prompt Variants
<!-- List any variants in prompts/variants/ and what each one adds.
     Leave empty if no variants have been authored yet. -->

## Scoring
- Correctness weight: <e.g., 0.6>
- Self-test coverage weight: <e.g., 0.2>
- Code quality weight: <e.g., 0.2>
- Quality rubric: <e.g., C++ Core Guidelines — see quality-evals/cpp/>

## Extension Tasks
<!-- Optional. List any extension tasks defined for this task.
     Extension tasks are hidden follow-up prompts used to measure extensibility.
     See Section 4.4. Leave empty or omit if no extensions are defined. -->
- Extension 1: <short description — e.g., "Add G18/G19 arc plane selection">
  - Tests: <number of hidden tests>
  - Weight: <relative weight if multiple extensions>
- Extension 2: ...

## Scope
<Description of what the model is and is not expected to implement.
Be explicit about what is and is not in scope.>

## Known Difficulty Areas
<Optional: notes on parts of the spec that are commonly misimplemented.
Populated after initial evaluation runs.>
```

---

## 4. Scoring Model

Each task produces three component scores, each in [0, 1]. The task score is a weighted sum. The SWE-BuildBench meta-score is the geometric mean across all tasks a model has been evaluated on.

### 4.1 Correctness Score

The harness runs the model's compiled artifact against the hidden test suite. Each test case is pass/fail. Tests may carry different weights (harder tests worth more).

```
correctness = sum(weight_i * pass_i) / sum(weight_i)
```

If the artifact fails to compile or crashes on every test, correctness = 0. Compilation failure is recorded as its own flag separately from the score, so it is visible in results without collapsing all signal to zero.

**Performance tests.** Some tasks include performance test cases that require the artifact to process a large or pathological input within a domain-meaningful time limit. These are ordinary correctness tests with an additional `timeout_seconds` field; they pass or fail like any other test and contribute to the correctness score. The timeout threshold is set generously enough that any correct O(n) implementation passes on any reasonable hardware, and strictly enough that pathologically slow implementations (O(n²) or worse) fail on all hardware. This approach works because the differences that matter are orders-of-magnitude algorithmic failures, not constant-factor variations — hardware variance between runs is at most 2–3×, while the gap between a correct and a catastrophically slow implementation is typically 100–1000×.

Performance tests are optional per task. Not every domain has a realistic large-input scenario where algorithmic quality is distinguishable. Task authors include performance tests only when there is a plausible real-world input size that exposes meaningful differences (e.g., a 100MB G-code file for CNCSim; not applicable for most Markdown parsing tasks).

*Note: v1.0 uses timeout-as-threshold (pass/fail) as described above. A future version may introduce continuous performance measurement — recording actual wall-clock time and reporting throughput (e.g., MB/s) as a graded metric alongside correctness. This requires pinning to a specific hardware class, running multiple trials to account for OS noise, and enforcing consistent compiler optimization flags in the harness. See Roadmap (Section 11).*

### 4.2 Self-Test Coverage Score

The model is asked to produce both an implementation and a test suite. The harness runs the model's tests against the model's implementation and measures line coverage using the language-appropriate tool (gcov/lcov for C++, coverage.py for Python, etc.).

```
self_coverage = covered_lines / total_lines
```

This dimension is not primarily a reward for high numbers — it is a signal of whether the model *understands what it built*. A model with 80% self-coverage that fails half the hidden tests has written tests that don't probe the right behavior. That gap is a meaningful finding.

### 4.3 Code Quality Score

An LLM judge evaluates the submitted source files against a predefined, language-specific quality rubric. For C++ tasks, the rubric is drawn from the C++ Core Guidelines. Each guideline is evaluated per file and reported as pass/fail. The quality score is the fraction of guideline checks that pass across all files.

Quality rubrics live in `quality-evals/<language>/` and are reused across all tasks in that language. A new language requires a one-time rubric definition effort; subsequent tasks in that language inherit it.

The LLM judge prompt for each guideline check follows a fixed template:

```
You are evaluating a C++ source file against a single C++ Core Guideline.

Guideline: <ID and description>
Rationale: <Why this guideline matters>

File contents:
<source>

Does this file adhere to the guideline? Answer YES, NO, or NOT_APPLICABLE.
If NO, quote the specific line(s) that violate it.
```

Each check uses a small, cost-efficient model (not the model under evaluation).

### 4.4 Extension Task Score (Optional)

An extension task is a hidden follow-up prompt that asks the agent to modify or extend the implementation it just produced. The agent does not know extension tasks exist when it writes its initial implementation — that surprise is the point. An implementation built with clean abstractions and separation of concerns will absorb a new feature more easily than spaghetti code that happens to pass the base test suite. Extension tasks measure maintainability and extensibility behaviorally, by actually attempting the extension, rather than cosmetically.

**Why this exists alongside the LLM judge (Section 4.3).** The code quality score measures static quality: does the code follow idioms, naming conventions, and structural guidelines? The extension task score measures dynamic quality: can the code absorb a change? These are complementary signals. A codebase can follow every C++ Core Guideline and still be a nightmare to extend if its abstractions are wrong. Conversely, well-structured code with inconsistent naming will extend cleanly. Reporting both dimensions gives a richer picture than either alone.

**Extension tasks are optional per task.** Not every task has a natural extension point, and designing good extension tasks requires domain expertise. Tasks without extensions still have a quality signal through the LLM judge. Tasks with extensions report an additional extensibility score. This keeps the contribution bar achievable: a contributor can submit a valid task with the three required scoring dimensions and add extensions later (or not at all).

**Harness flow.** After the base task is scored, the harness injects the extension prompt into the same agent session so the agent retains full context of the code it just wrote. The agent modifies its own code, and the harness scores the result against a separate hidden test suite specific to the extension. If a task defines multiple extensions, they are run sequentially in the same session — each one builds on the state left by the previous extension.

```
extension_score = sum(ext_weight_i * ext_pass_rate_i) / sum(ext_weight_i)
```

where each `ext_pass_rate_i` is the fraction of hidden tests passed for extension `i`.

**Interpretation caveat.** The extension score reflects the joint capability of code maintainability and the agent's modification skill. A capable agent may successfully extend poorly-structured code through brute-force refactoring, so a high extension score doesn't cleanly isolate structure from modification ability. Persistently low extension scores across capable agents, however, are a reasonable signal of structural rigidity in the underlying implementation.

**The extension score is reported separately from the base task score.** It is not folded into the weighted sum that produces the task score. This ensures that the base task score remains comparable across all tasks regardless of whether they include extensions, and that a model's base correctness and extensibility are visible as distinct signals.

### 4.5 Task Score

```
task_score = (correctness_weight * correctness)
           + (coverage_weight   * self_coverage)
           + (quality_weight    * code_quality)
```

Default weights: correctness 0.6, self-test coverage 0.2, code quality 0.2. Weights are defined per task in TASK.md and may vary if a task has different scoring priorities.

### 4.6 SWE-BuildBench Meta-Score

```
swe_buildbench_score = geometric_mean(task_score_1, task_score_2, ..., task_score_n)
```

Geometric mean is used rather than arithmetic mean because a model that excels at one task but fails another represents worse generalization than one that scores moderately across all tasks. The geometric mean penalizes zero or near-zero scores more severely.

The meta-score is only reported for agents evaluated on all current tasks. Partial coverage is reported as individual task scores only.

---

## 5. Evaluation Execution

### 5.1 Agent Execution

The harness invokes a coding agent CLI — Claude Code, Codex CLI, Gemini CLI, or similar — inside a sandboxed Docker container. The agent receives the documentation corpus and the task prompt, then operates autonomously: reading files, writing source code, running the compiler, observing errors, and iterating until it signals completion or the session times out.

The harness provides:
- A clean working directory containing the documentation corpus and the prompt file
- A Docker container with the task's required compiler and toolchain, but no internet access beyond the agent's own API host
- A time limit and token budget (see Section 5.2)

The agent produces:
- A directory of source files and a build system (e.g., CMakeLists.txt)
- A test suite in a `tests/` subdirectory
- Whatever README or documentation it chooses to write

The harness then calls `build.sh` on the resulting directory and proceeds to scoring. The agent's ability to iterate — to write code, compile it, see errors, and fix them — is not a confound to be controlled for; it is the capability being evaluated.

### 5.2 Infrastructure Requirements

**Sandboxing.** Agent runs must execute in Docker containers with no outbound network access, resource limits (CPU, memory), and filesystem isolation. An agent that can execute arbitrary shell commands must not be able to affect the host system or contact external services.

**No artificial timeouts.** Agent sessions run until the agent exits naturally. The harness has a 24-hour safety backstop to catch truly hung containers, but this is not intended as a meaningful constraint. Agents that need hours to iterate should be allowed to finish — killing a run mid-execution produces artificially low scores and wastes compute.

**Token budgets.** Agent sessions are capped at 500,000 tokens. This is logged per run. Sessions approaching the cap are noted in results, as context exhaustion is a meaningful capability dimension.

**Cost.** A single agent run for a complex task may consume 100,000–500,000 tokens. At current pricing, evaluating three agents on a single task costs $30–100. Full leaderboard updates should be budgeted accordingly.

**Non-determinism.** Agent runs are highly non-deterministic: the same agent given the same prompt will produce structurally different code on different runs. Published leaderboard results report the mean of three independent runs ± standard deviation.

### 5.3 Prompt Design

**The non-developer persona.** When writing a base prompt, the author should imagine a domain expert with no software engineering background — a machinist, a protocol designer, a format specification author. This person knows exactly what they want built and can describe it clearly in domain terms. They would not think to ask for unit tests, specify an architectural pattern, request a particular error handling style, or mention code quality standards. The base prompt should sound like it came from that person.

**Base prompt contract.** The base prompt (`prompts/base.md`) must contain:
- A plain-language description of what to build, written in domain terms
- A pointer to the documentation corpus: "The specification is in the `docs/` directory"
- A brief infrastructure note covering the implementation language, CLI interface, and output JSON schema — framed as technical compatibility requirements, not engineering guidance

The base prompt must not contain:
- Instructions to write tests, specify coverage targets, or practice TDD
- Instructions to follow code quality standards, style guides, or linting rules
- Architectural suggestions (state machine, parser combinator, MVC, etc.)
- Phase structure ("first design, then implement, then test")
- Any reference to how the output will be evaluated or scored

The test for a well-written base prompt: could a knowledgeable person in the problem domain — with no software background — have plausibly written this? If yes, it passes. If it sounds like it was written by a developer who knows what a good implementation looks like, revise it.

**What this measures.** An agent receiving the base prompt must independently decide to write tests, choose an architecture, follow quality standards, and structure its work. Whether it makes those decisions, and how well, is the signal. An agent that writes comprehensive tests without being asked is demonstrating better judgment than one that only does so when instructed. The base prompt measures autonomous engineering judgment. The variants measure instruction-following ability and the marginal value of guidance.

**Prompt variants.** A prompt variant adds one or more developer-level instructions to the base prompt. Variants live in `prompts/variants/` and are named to describe what they add. Results from variants are labeled separately and never included in the base leaderboard. Their purpose is to answer a second class of questions: how much does each type of guidance improve output quality?

Example variants for CNCSim:
- `with-tests.md` — adds: "Write a unit test for each discrete G-code command you implement."
- `with-guidelines.md` — adds: "Follow the C++ Core Guidelines when writing your code."
- `with-tdd.md` — adds: "Use test-driven development: write tests before implementation."
- `with-phases.md` — adds: "Begin with a written design document before writing any code."

The difference in correctness score between `base` and `with-tests` directly measures how much a single sentence of test instruction improves implementation correctness. That is a publishable finding.

**Harness invocation with prompt selection:**

```
# Evaluate with base prompt (default — scores count toward leaderboard)
swe-buildbench run --task cncsim-cpp --agent claude-code

# Evaluate with a named variant (scores reported separately)
swe-buildbench run --task cncsim-cpp --agent claude-code --prompt-variant with-tests
swe-buildbench run --task cncsim-cpp --agent claude-code --prompt-variant with-guidelines

# Evaluate with extension tasks (if the task defines them)
# Extensions run automatically after base scoring unless --skip-extensions is passed
swe-buildbench run --task cncsim-cpp --agent claude-code --skip-extensions
```

**Extension task execution flow.** When a task defines extension tasks and `--skip-extensions` is not passed, the harness proceeds as follows after base scoring: (1) the extension prompt is injected into the active agent session so the agent retains context of the code it just wrote; (2) the agent modifies its code; (3) the harness rebuilds and scores against the extension's hidden test suite; (4) if multiple extensions are defined, each builds on the state left by the previous one. Extension scores are reported alongside (but separate from) the base task score.

### 5.4 Harness Invocation Summary

| Dimension | Value |
|---|---|
| Subject | Coding agent CLI (Claude Code, Codex CLI, Gemini CLI, etc.) |
| Input | Assembled prompt + documentation corpus in a clean working directory |
| Iteration | Agent iterates freely until it signals completion or the safety backstop fires |
| Output | Directory of source files, build config, and tests produced by the agent |
| Scaffolding | Docker sandbox with compiler toolchain; network restricted to the agent's API host |
| Runs per result | 3 (mean ± stddev reported) |

---

## 6. CLI Contract (Submission Interface)

All SWE-BuildBench tasks share a standardized command-line interface. This is what enables the harness to be language-agnostic — it invokes the compiled artifact the same way regardless of implementation language.

### 6.1 Required Flags

```
<executable> --input <input_file> --output <output_file>
```

`--input`: path to a task-specific input file (e.g., a G-code program, a binary ROM)
`--output`: path where the artifact should write its JSON result

### 6.2 Output Format

The artifact must write a single JSON object to `--output`. The top-level schema is fixed across all tasks:

```json
{
  "task_id": "cncsim-cpp",
  "status": "ok",
  "result": { }
}
```

The `result` object schema is task-specific and defined in each task's TASK.md. For example, CNCSim writes final machine state; CHIP-8 writes register and memory state at a specified cycle.

### 6.3 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Completed successfully, output written |
| 1 | Input was malformed or invalid |
| 2 | Internal error / unimplemented feature |

Error details go to stderr. The output file may be absent or empty on non-zero exit.

### 6.4 Build Contract

Each task's `harness/build.sh` must produce a single executable at `./build/<task-id>`. The harness calls this script once before running the test suite. Build scripts are allowed to install dependencies but must be deterministic and reproducible. Docker images are provided for each supported language to ensure consistent compiler/runtime versions.

---

## 7. Test Suite Architecture

### 7.1 Public / Private Split

| Asset | Visibility | Location |
|-------|-----------|---------|
| Harness, build scripts | Public | Main repo |
| Prompt templates | Public | Main repo |
| TASK.md definitions | Public | Main repo |
| Sample tests (10–20 per task) | Public | Main repo |
| Full hidden test suite | Private | Companion private repo |
| Extension task prompts + test suites | Private | Companion private repo |
| Reference implementations | Private | Companion private repo |

### 7.2 Living Benchmark

Test cases are versioned. Old tests that are suspected to be contaminated (e.g., published in a paper that post-dates a model's training) are retired to a `retired/` directory and replaced with new ones. Each agent evaluation record includes the test suite version it was run against, enabling longitudinal comparison even as the suite evolves.

### 7.3 Reproducibility

All evaluations are run in Docker containers with pinned language versions. An agent evaluation record includes:

- Agent CLI name and version string
- Test suite version (git SHA of private repo)
- Docker image SHA
- Date of evaluation
- Raw per-test results (pass/fail + output diff on failure)
- Aggregate scores per dimension

### 7.4 Test Independence

Tests should have independent failure modes. A test named for behavior X should only fail because of X. When many tests share a precondition — a schema assertion, a fixture that parses output, a preamble check — one bug there cascades into all of them, and the score stops measuring N independent capabilities and starts measuring one thing N times. The rule of thumb: **if a test fails, the failure should tell you something you didn't learn from the other tests failing.**

Two patterns to apply when authoring an eval:

- **Gate shared preconditions once.** Put schema/shape checks in one dedicated test (e.g. `test_output_schema.py`), not inside every behavioral test. If the gate fails, downstream behavioral tests still report independently — or are skipped with a single reason — rather than all piling onto the same root cause.
- **Keep behavioral assertions tolerant of detail they are not testing.** Use `payload.get("error") is None` rather than `payload["error"] is None`, so a subtle schema slip (missing key vs. null value) does not crash a motion or state test before it reaches the assertion the test was actually meant to verify.

Worked example: sonnet-4-6's CNCSim cpp run 3 (see `published_results/CNCSIM/results-2_1_1.md`) built cleanly and claimed complete, but the agent emitted the required `error` output field only when non-empty, missing the spec's `null` on success. Because 259 behavioral tests asserted `payload["error"] is None` at the top, that single ~5-LOC mistake failed every one of them with `KeyError: 'error'` — costing the run ~55% of the suite before any of its actual RS274 logic was probed. A schema gate plus `.get("error")` in behavioral tests would have localized the failure to one schema test and let the rest of the suite measure what it was named for.

---

## 8. Language Policy

Implementation language is a task-level configuration, not a framework requirement. The harness is language-agnostic — it builds the submission via a per-language build backend, then invokes the resulting command with the standard CLI contract.

A single eval can be offered in multiple languages. The prompt, documentation corpus, and hidden test suite are shared across language variants; the only per-language assets are a short `language-requirements-<lang>.md` prompt (stored once in `Evals/_shared/`) and a per-eval `reference-implementation-<lang>/` directory that must pass the full hidden test suite. Each (eval, language) pair is registered as a distinct task ID (e.g. `cncsim-cpp`, `cncsim-py`).

Each language requires a one-time setup cost:
- A Docker image with pinned compiler/runtime versions
- A build backend in `swe_buildbench.build` (e.g. `CMakeBackend`, `PythonBackend`)
- A shared `Evals/_shared/language-requirements-<lang>.md` prompt
- A quality eval rubric in `quality-evals/<language>/`
- A coverage measurement script in `coverage/<language>/`

Once a language has these components, any new task in that language inherits them at no additional cost. The currently supported languages are C++20, Python 3.11+, JavaScript (Node.js 22+), and stable Rust (the shared prompt currently targets 2021 edition or later).

---

## 9. Community Contributions

### 9.1 Adding a New Task

Contributors follow this process:

1. Copy `task-template/` and fill in `TASK.md`, `prompt-template.md`, and `harness/`
2. Write at least 20 sample tests (public) and 50 full tests (private)
3. Run `swe-buildbench validate <task-dir>` locally to verify the harness is well-formed
4. Open a pull request with the public assets only
5. Submit the full test suite to the maintainer separately for inclusion in the private repo

Acceptance criteria:
- The documentation corpus must consist entirely of publicly available, authoritative sources
- The corpus must not include reference implementations or working code that solves the task
- The corpus composition must be justified in the `Corpus Rationale` section of TASK.md — single-document tasks should explain why the spec is self-contained; multi-document tasks should explain what each document contributes
- Output must be fully deterministic
- The task must not be in a domain likely to have high training data contamination
- The full test suite must have at least 50 tests with meaningful category coverage
- The harness must build and run cleanly in the provided Docker image
- Extension tasks are optional; if included, each extension must have its own hidden test suite with at least 20 tests and a prompt that follows the non-developer persona (Section 5.3)

### 9.2 Contributor Incentives

Accepted task contributors are credited as **task maintainers** in the repository and on the leaderboard. Task maintainers receive free evaluations of all submitted agents against their task. If SWE-BuildBench is cited in papers or model cards, contributors are acknowledged in those citations.

### 9.3 Agent Submission

Agent evaluations are requested by opening a GitHub issue with the agent CLI name, version string, and any authentication details required to run it in the harness sandbox. The maintainer runs the evaluation and publishes results to the leaderboard within two weeks.

---

## 10. Contamination Mitigation Strategy

Three complementary strategies are employed:

**Private test suites.** The full hidden test suite for every task is never published. Evaluations are run by the maintainer (or task maintainer) and only scores are reported publicly. This is the primary protection.

**Domain expertise.** CNCSim test cases are designed by someone with professional CNC machining experience. The adversarial cases in particular require deep domain knowledge to write and cannot be reproduced by generalizing from public examples.

**Structural resistance.** "Build a system" tasks require genuine understanding, not recall. Even if a model's training data contained a CNCSim test case, knowing the correct answer for one arc endpoint test does not help on a different arc test. Memorization provides negligible advantage over understanding.

**Living benchmark rotation.** Test cases are tracked by date of introduction. Cases pre-dating a model's training cutoff are flagged in analysis but not removed, to preserve longitudinal comparability. New cases are added periodically to maintain forward-looking coverage.

---

## 11. Roadmap

### v1.0 — CNCSim Launch
- [ ] CNCSim task: harness, prompt, hidden tests, sample tests
- [ ] CNCSim current extensions: arc plane selection (ext-01), coordinate offsets (ext-02) with hidden test suites
- [ ] CNCSim future extensions: stock removal simulation (ext-01), Haas dialect (ext-02) with hidden test suites
- [ ] C++ quality eval: C++ Core Guidelines rubric (20–25 selected guidelines)
- [ ] Docker sandbox image per supported agent CLI
- [ ] Scoring harness: correctness + coverage + quality + extension pipeline
- [ ] Initial results for Claude Code, Codex CLI, Gemini CLI
- [ ] Blog post: methodology, findings, failure mode analysis, extensibility findings
- [ ] CONTRIBUTING.md and task-template/

### v1.1 — Second Task
- [ ] CommonMark parser task (most likely candidate: 600+ embedded spec tests, good structural fit)
- [ ] CommonMark extension tasks (e.g., add GFM table support, add footnotes)
- [ ] First SWE-BuildBench meta-score reported
- [ ] Geometric mean aggregation in leaderboard

### v2.0 — Framework Maturity
- [ ] Submission server for automated agent evaluation
- [ ] Additional languages (Rust support)
- [ ] Community-contributed tasks
- [ ] Versioned test suite with retirement/rotation policy
- [ ] Continuous performance measurement: record wall-clock time per test, report throughput (MB/s) as a graded metric alongside correctness. Requires: pinned hardware class for all eval runs, 3–5 trials per test with median reported, enforced compiler optimization flags in harness build template, and documented noise floor (~2–3×) so published results do not make claims about differences smaller than that threshold

---

## 12. Open Questions

- **Partial compilation credit.** If a model's code compiles with minor fixes (e.g., a missing semicolon, an incorrect include path), should the evaluator apply those fixes before scoring? Current position: no — the artifact must compile as submitted. This may be revisited if compilation failures are common and uninformative.

- **Multi-run variance.** LLM outputs are non-deterministic. Should evaluations run each model N times and report mean ± stddev? Current position: one run per model per task for cost reasons, with a note that results may vary. This may change for published results.

- **Temperature.** What sampling temperature should be used? Lower temperatures produce more deterministic output but may suppress architecturally creative solutions. Current position: temperature=0 for reproducibility.

- **Context window handling for CNCSim-Full.** The full RS274/NGC PDF is ~200 pages. Models with smaller context windows may need to truncate. Current position: provide the full document and let the model decide what to include; context window limitations are a valid dimension of model capability.

- **Agent timeout fairness.** Faster agents complete more iterations within the 4-hour wall-clock cap, which may advantage them independent of code quality. Should the cap be token-based rather than time-based? Current position: wall-clock cap is simpler and more operationally meaningful; token cap is logged separately as a secondary dimension.

- **Agent environment scope.** Should the Docker container include the compiler and standard libraries only, or also common third-party libraries (e.g., nlohmann/json for C++ JSON output)? Providing common libraries reduces friction but may mask dependency management capability. Current position: provide only the compiler and standard library; the agent must handle any other dependencies via its build system.

- **What counts as "agent completion"?** Agents may signal completion explicitly (Claude Code exits, Codex CLI returns control) or implicitly (the session times out). Results should note how each session ended. A session that produces a correct implementation but only because it ran to timeout is a different finding than one that completed and exited cleanly.

- **Comparing across agent versions.** Agent CLI versions change frequently. Claude Code v1.2 and v1.3 may produce significantly different results on the same task. Results must be pinned to specific agent version strings, and the leaderboard should support version-specific entries rather than collapsing all runs of "Claude Code" into one row.
