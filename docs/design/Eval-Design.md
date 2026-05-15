# CLISpecBench — Design Document

**Author:** Matthew G. Knutson
**Status:** Living design document
**Last Updated:** May 2026

---

> **Note on task IDs.** The harness exposes explicit language task IDs such as
> `rs274-cpp`, `iges-js`, and `marc21-py`. Registered evals currently include
> BibTeX, GEDCOM, ICal, IGES, LAS, MARC21, RS274, and WordCount. The task ID
> shape is `<eval>-<language>`; a reference implementation may exist for only a
> subset of languages even when the harness can run submitted implementations
> for all shared language prompts.

## 1. Overview

CLISpecBench is a benchmark suite for evaluating **AI coding agents** on **documentation-driven system implementation** tasks. Each task gives the agent a curated documentation corpus — which may be a single specification document or a realistic collection of related documents — and asks it to produce a fully functional, compilable/runnable implementation, with no access to the hidden test suite used to score it.

The central question CLISpecBench asks is:

> *Given only a real-world documentation corpus, can an AI coding agent extract requirements, design a system architecture, implement it correctly across multiple files, and write meaningful tests for its own output?*

This differs from existing coding benchmarks in a fundamental way. HumanEval and its descendants test function completion. SWE-bench tests bug-fixing in existing codebases. CLISpecBench tests the full upstream engineering loop: document comprehension, system design, multi-file implementation, and self-verification — the things engineers actually do.

**On the name.** "CLI" foregrounds the core abstraction of the benchmark: every
task asks the agent to build a command-line application that can be exercised
through a shared harness contract, regardless of implementation language.
"Spec" reflects the source of truth the agent receives — a dense specification
or closely related documentation corpus defining the CLI application's required
behavior. "Bench" signals a formal, reusable benchmark intended for citation,
leaderboards, and longitudinal comparison.

CLISpecBench evaluates coding agent CLIs — tools such as Claude Code, Codex CLI, and Gemini CLI — that have access to a file system, terminal, compiler, and the ability to iterate on their own output. This mirrors how engineers actually use these tools and is where the interesting capability signal lives: whether the agent can extract requirements from documentation, design a multi-file system, implement it, and verify its own work without supervision.

---

## 2. Design Principles

**One corpus, one task.** Each task provides a curated documentation corpus: one or more publicly available documents that together constitute a complete and authoritative description of what must be built. The corpus composition is a deliberate task design decision — it may be a single dense specification (as in RS274), or a realistic multi-document collection (a primary spec, errata, worked examples, architecture notes) that more closely mirrors how engineers encounter requirements in practice. What the corpus must never include is a reference implementation or working code that solves the task. The subject must extract all requirements from the documentation itself.

**Deterministic scoring.** Every correctness test has an exact expected output. There is no ambiguity in whether a test passes. The hidden test suite is written and locked before any model is evaluated.

**Contamination resistance by design.** Test cases are never published. The full test suite lives in a private repository. Tasks are chosen from domains where ground-truth implementations do not saturate model training data.

**Language is a task parameter, not a framework requirement.** The CLI contract and scoring schema are consistent across all tasks. A single eval (prompt, docs, hidden test suite, reference implementations) may be offered in multiple target languages, and each (eval, language) pair is registered as a distinct task ID (e.g. `rs274-cpp` vs `rs274-py`). The hidden test suite is language-agnostic and exercises the submission through the shared CLI contract.

**The meta-score is an aggregate, not an average.** The CLISpecBench score is the geometric mean of task scores, not the arithmetic mean. This penalizes models that score well on one task but fail on others — generalization matters.

**Non-developer base prompt.** The base prompt is written from the perspective of a domain expert who is not a software developer — someone who knows exactly what they want to build but has no software engineering background. They would not think to specify test coverage, code quality standards, architectural patterns, or implementation strategy, just as they would not specify which sorting algorithm to use. The only exceptions are the three items the evaluation harness physically requires: implementation language, CLI flags, and output JSON schema. These are included with a brief framing note ("for technical compatibility, please use C++20 and produce output in the following format") that signals infrastructure constraint rather than engineering guidance. Everything else — whether to write tests, which architecture to choose, how to handle errors, what quality standards to follow — is left entirely to the agent's judgment. This framing serves two purposes: it measures genuine agent autonomy rather than instruction-following ability, and it emulates a realistic and increasingly common usage pattern where domain experts use coding agents to build real systems without software engineering backgrounds. Prompt variants that add developer-level guidance ("write a test for each discrete feature," "follow C++ Core Guidelines") are evaluated separately and never included in the base leaderboard — their value is measuring how much that guidance helps.

---

## 3. Task Anatomy

Every CLISpecBench eval is organized around a prompt/documentation corpus, a
language-neutral pytest suite, and one or more reference implementations. Task
IDs are generated by pairing a registered eval name with a shared language
prompt.

### 3.1 Eval Directory

```
Evals/<EvalName>/
  README.md                         # Eval-specific design notes and scope
  VERSION                           # Eval contract/test-suite version
  CHANGELOG.md                      # Versioned observable changes
  prompt/
    base-prompt.md                  # Domain-expert prompt
    technical-requirements-prompt.md # Harness contract: language, CLI, schema
    docs/                           # Documentation corpus provided to the agent
  tests/
    conftest.py                     # EvalConfig + shared harness fixtures
    test_*.py                       # Language-neutral pytest suite
    *_support.py                    # Test data builders and assertions
  reference-implementation-cpp/     # Optional reference implementation
  reference-implementation-py/      # Optional reference implementation
  reference-implementation-js/      # Optional reference implementation
  reference-implementation-rs/      # Optional reference implementation
```

The authoritative registry lives in `src/clispecbench/harness/task.py`.
Language-specific implementation requirements live in
`Evals/_shared/language-requirements-<lang>.md`, so adding a language is
orthogonal to adding an eval.

### 3.2 Prompt Contract

Each eval prompt is assembled from three sources:

- `base-prompt.md` describes the task from the perspective of a domain expert,
  not a software-engineering manager.
- `technical-requirements-prompt.md` contains only the harness contract:
  language, CLI flags, exit codes, and JSON schema.
- `prompt/docs/` contains the actual domain source material the agent must
  understand.

This split is important: behavioral requirements belong in the base prompt or
docs, while harness mechanics belong in the technical prompt. If a hidden test
depends on behavior that is not derivable from those sources, the prompt/docs
must be fixed before the test is used for scoring.

### 3.3 Test Visibility

The harness treats the pytest suite as the scoring interface. In a public
development repository, tests may be visible for collaboration and reference
implementation validation. In a scored benchmark release, the same suite shape
can be kept private and only result summaries published. In both cases, agents
receive the prompt/docs corpus, not the test implementation.

---

## 4. Scoring Model

Each task produces a correctness score in [0, 1], plus diagnostic capability
breakdowns derived from the hidden test suite. The task score currently equals
correctness. The CLISpecBench meta-score is the geometric mean across all tasks
a model has been evaluated on.

### 4.1 Correctness Score

The harness runs the model's compiled artifact against the hidden test suite. Each test case is pass/fail. Tests may carry different weights (harder tests worth more).

```
correctness = sum(weight_i * pass_i) / sum(weight_i)
```

If the artifact fails to compile or crashes on every test, correctness = 0. Compilation failure is recorded as its own flag separately from the score, so it is visible in results without collapsing all signal to zero.

**Performance tests.** Some tasks include performance test cases that require the artifact to process a large or pathological input within a domain-meaningful time limit. These are ordinary correctness tests with an additional `timeout_seconds` field; they pass or fail like any other test and contribute to the correctness score. The timeout threshold is set generously enough that any correct O(n) implementation passes on any reasonable hardware, and strictly enough that pathologically slow implementations (O(n²) or worse) fail on all hardware. This approach works because the differences that matter are orders-of-magnitude algorithmic failures, not constant-factor variations — hardware variance between runs is at most 2–3×, while the gap between a correct and a catastrophically slow implementation is typically 100–1000×.

Performance tests are optional per task. Not every domain has a realistic large-input scenario where algorithmic quality is distinguishable. Task authors include performance tests only when there is a plausible real-world input size that exposes meaningful differences (e.g., a 100MB G-code file for RS274; not applicable for most Markdown parsing tasks).

*Note: the current benchmark uses timeout-as-threshold (pass/fail) as described above. A future version may introduce continuous performance measurement — recording actual wall-clock time and reporting throughput (e.g., MB/s) as a graded metric alongside correctness. This requires pinning to a specific hardware class, running multiple trials to account for OS noise, and enforcing consistent compiler optimization flags in the harness. See Current Status and Future Work (Section 11).*

### 4.2 Capability Breakdowns

The harness groups hidden test outcomes by test-file name and records a
passed/total pair for each capability bucket. For example,
`test_canned_cycles.py` contributes `subscore.canned_cycles.passed` and
`subscore.canned_cycles.total` in the result JSON. These values are diagnostic:
they explain where a score came from without introducing a second hand-maintained
tagging system.

Capability breakdowns are not folded into `task_score`; they are a structured
view of the same test outcomes that produce correctness.

### 4.3 Task Score

```
task_score = correctness
```

### 4.4 CLISpecBench Meta-Score

```
clispecbench_score = geometric_mean(task_score_1, task_score_2, ..., task_score_n)
```

Geometric mean is used rather than arithmetic mean because a model that excels at one task but fails another represents worse generalization than one that scores moderately across all tasks. The geometric mean penalizes zero or near-zero scores more severely.

The meta-score is only reported for agents evaluated on all current tasks. Partial coverage is reported as individual task scores only.

---

## 5. Evaluation Execution

### 5.1 Agent Execution

The harness invokes a coding agent CLI — Claude Code, Codex CLI, Gemini CLI, or similar — inside a sandboxed Docker container. The agent receives the documentation corpus and the task prompt, then operates autonomously: reading files, writing source code, running the compiler, observing errors, and iterating until it signals completion or the session times out.

The harness provides:
- A clean working directory containing the documentation corpus and the prompt file
- A Docker container with the task's required compiler and toolchain, under the
  current network-access policy documented in `../operations/Agent-Run-Notes.md`
- A time limit and token budget (see Section 5.2)

The agent produces:
- A directory of source files and a build system (e.g., CMakeLists.txt)
- A test suite in a `tests/` subdirectory
- Whatever README or documentation it chooses to write

The harness then prepares the submission with the language-specific build
backend (`CMakeBackend`, `PythonBackend`, `JavaScriptBackend`, or
`RustBackend`) and proceeds to scoring. The agent's ability to iterate — to
write code, compile it, see errors, and fix them — is not a confound to be
controlled for; it is the capability being evaluated.

### 5.2 Infrastructure Requirements

**Sandboxing.** Agent runs must execute in Docker containers with resource limits (CPU, memory) and filesystem isolation. The original design intent was no outbound network access except the agent's API endpoint. A May 2026 audit found that already-published runs did not fully enforce that API-only policy, so the current study preserves the same effective web-access level for consistency. A future offline/API-only series must be labeled separately and should not be mixed with the current results.

**No artificial timeouts.** Agent sessions run until the agent exits naturally. The harness has a 24-hour safety backstop to catch truly hung containers, but this is not intended as a meaningful constraint. Agents that need hours to iterate should be allowed to finish — killing a run mid-execution produces artificially low scores and wastes compute.

**Token budgets.** Agent sessions are capped at 500,000 tokens. This is logged per run. Sessions approaching the cap are noted in results, as context exhaustion is a meaningful capability dimension.

**Cost.** A single agent run for a complex task may consume 100,000–500,000 tokens. At current pricing, evaluating three agents on a single task costs $30–100. Full leaderboard updates should be budgeted accordingly.

**Non-determinism.** Agent runs are highly non-deterministic: the same agent given the same prompt will produce structurally different code on different runs. Published leaderboard results report the mean of three independent runs ± standard deviation.

### 5.3 Prompt Design

**The non-developer persona.** When writing a base prompt, the author should imagine a domain expert with no software engineering background — a machinist, a protocol designer, a format specification author. This person knows exactly what they want built and can describe it clearly in domain terms. They would not think to ask for unit tests, specify an architectural pattern, request a particular error handling style, or mention code quality standards. The base prompt should sound like it came from that person.

**Base prompt contract.** The base prompt (`prompt/base-prompt.md`) must contain:
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

**Prompt variants.** A prompt variant adds one or more developer-level instructions to the base prompt. Variants live in `prompt/variants/` and are named to describe what they add. Results from variants are labeled separately and never included in the base leaderboard. Their purpose is to answer a second class of questions: how much does each type of guidance improve output quality?

Example variants for RS274:
- `with-tests.md` — adds: "Write a unit test for each discrete G-code command you implement."
- `with-guidelines.md` — adds: "Follow the C++ Core Guidelines when writing your code."
- `with-tdd.md` — adds: "Use test-driven development: write tests before implementation."
- `with-phases.md` — adds: "Begin with a written design document before writing any code."

The difference in correctness score between `base` and `with-tests` directly measures how much a single sentence of test instruction improves implementation correctness. That is a publishable finding.

**Harness invocation with prompt selection:**

```
# Evaluate with base prompt (default — scores count toward leaderboard)
clispecbench run --task rs274-cpp --agent claude-code

# Evaluate with a named variant (scores reported separately)
clispecbench run --task rs274-cpp --agent claude-code --prompt-variant with-tests
clispecbench run --task rs274-cpp --agent claude-code --prompt-variant with-guidelines
```

### 5.4 Harness Invocation Summary

| Dimension | Value |
|---|---|
| Subject | Coding agent CLI (Claude Code, Codex CLI, Gemini CLI, etc.) |
| Input | Assembled prompt + documentation corpus in a clean working directory |
| Iteration | Agent iterates freely until it signals completion or the safety backstop fires |
| Output | Directory of source files, build config, and tests produced by the agent |
| Scaffolding | Docker sandbox with compiler toolchain; network-access condition documented in `../operations/Agent-Run-Notes.md` |
| Runs per result | 3 (mean ± stddev reported) |

---

## 6. CLI Contract (Submission Interface)

All CLISpecBench tasks share a standardized command-line interface. This is what enables the harness to be language-agnostic — it invokes the compiled artifact the same way regardless of implementation language.

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
  "task_id": "rs274-cpp",
  "status": "ok",
  "result": { }
}
```

The `result` object schema is eval-specific and defined in each eval's
`prompt/technical-requirements-prompt.md`. For example, RS274 writes final
machine state while MARC21 writes parsed or rendered record data.

### 6.3 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Completed successfully, output written |
| 1 | Input was malformed or invalid |
| 2 | Internal error / unimplemented feature |

Error details go to stderr. The output file may be absent or empty on non-zero exit.

### 6.4 Build Contract

Each language backend must produce a runnable command for the submitted
implementation. C++ uses CMake, Python and JavaScript use their entrypoint
files, and Rust uses Cargo. Docker images are provided for supported languages
and agent harnesses to keep compiler/runtime versions consistent.

---

## 7. Test Suite Architecture

### 7.1 Public / Private Split

| Asset | Visibility | Location |
|-------|-----------|---------|
| Harness code and build backends | Public | `src/clispecbench/` |
| Prompt and docs corpus | Public | `Evals/<EvalName>/prompt/` |
| Eval metadata | Public | `Evals/<EvalName>/{README.md,VERSION,CHANGELOG.md}` |
| Reference implementations | Public where released | `Evals/<EvalName>/reference-implementation-<lang>/` |
| Scoring test suite | Private for scored benchmark releases; may be public for repo validation | `Evals/<EvalName>/tests/` shape |
| Published result summaries | Public | `published_results/` |

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

Worked example: an early RS274 C++ run built cleanly and claimed complete, but the agent emitted the required `error` output field only when non-empty, missing the spec's `null` on success. Because 259 behavioral tests asserted `payload["error"] is None` at the top, that single ~5-LOC mistake failed every one of them with `KeyError: 'error'` — costing the run ~55% of the suite before any of its actual RS274 logic was probed. A schema gate plus `.get("error")` in behavioral tests would have localized the failure to one schema test and let the rest of the suite measure what it was named for.

---

## 8. Language Policy

Implementation language is a task-level configuration, not a framework requirement. The harness is language-agnostic — it builds the submission via a per-language build backend, then invokes the resulting command with the standard CLI contract.

A single eval can be offered in multiple languages. The prompt, documentation corpus, and hidden test suite are shared across language variants; the only per-language assets are a short `language-requirements-<lang>.md` prompt (stored once in `Evals/_shared/`) and a per-eval `reference-implementation-<lang>/` directory that must pass the full hidden test suite. Each (eval, language) pair is registered as a distinct task ID (e.g. `rs274-cpp`, `rs274-py`).

Each language requires a one-time setup cost:
- A Docker image with pinned compiler/runtime versions
- A build backend in `clispecbench.build` (e.g. `CMakeBackend`, `PythonBackend`)
- A shared `Evals/_shared/language-requirements-<lang>.md` prompt

Once a language has these components, any new task in that language inherits them at no additional cost. The currently supported languages are C++20, Python 3.11+, JavaScript (Node.js 22+), and stable Rust (the shared prompt currently targets 2021 edition or later).

---

## 9. Community Contributions

### 9.1 Adding a New Task

Contributors follow this process:

1. Create `Evals/<EvalName>/` with `prompt/`, `tests/`, `VERSION`, and
   `CHANGELOG.md`.
2. Add at least one reference implementation, usually
   `reference-implementation-cpp/` unless another language is a better fit.
3. Register the eval in `src/clispecbench/harness/task.py`.
4. Run the reference implementation through the eval test suite and the
   repo-level Ruff/Pyright checks.
5. Document corpus scope, contamination considerations, and known difficulty
   areas in the eval README.

Acceptance criteria:
- The documentation corpus must consist entirely of publicly available, authoritative sources
- The corpus must not include reference implementations or working code that solves the task
- The corpus composition must be justified in the eval README — single-document tasks should explain why the spec is self-contained; multi-document tasks should explain what each document contributes
- Output must be fully deterministic
- The task must not be in a domain likely to have high training data contamination
- The test suite must have meaningful category coverage and independent failure modes
- The reference implementation must build and run cleanly through the shared pytest harness
- Extension tasks are optional; if included, each extension must have its own hidden test suite with at least 20 tests and a prompt that follows the non-developer persona (Section 5.3)

### 9.2 Contributor Incentives

Accepted task contributors are credited as **task maintainers** in the repository and on the leaderboard. Task maintainers receive free evaluations of all submitted agents against their task. If CLISpecBench is cited in papers or model cards, contributors are acknowledged in those citations.

### 9.3 Agent Submission

Agent evaluations are requested by opening a GitHub issue with the agent CLI name, version string, and any authentication details required to run it in the harness sandbox. The maintainer runs the evaluation and publishes results to the leaderboard within two weeks.

---

## 10. Contamination Mitigation Strategy

Three complementary strategies are employed:

**Private test suites.** The full hidden test suite for every task is never published. Evaluations are run by the maintainer (or task maintainer) and only scores are reported publicly. This is the primary protection.

**Domain expertise.** RS274 test cases are designed by someone with professional CNC machining experience. The adversarial cases in particular require deep domain knowledge to write and cannot be reproduced by generalizing from public examples.

**Structural resistance.** "Build a system" tasks require genuine understanding, not recall. Even if a model's training data contained a RS274 test case, knowing the correct answer for one arc endpoint test does not help on a different arc test. Memorization provides negligible advantage over understanding.

**Living benchmark rotation.** Test cases are tracked by date of introduction. Cases pre-dating a model's training cutoff are flagged in analysis but not removed, to preserve longitudinal comparability. New cases are added periodically to maintain forward-looking coverage.

---

## 11. Current Status and Future Work

The original RS274 launch roadmap has been completed and superseded by the
current multi-eval harness. The repository now includes registered evals for
BibTeX, GEDCOM, ICal, IGES, LAS, MARC21, RS274, and WordCount, with shared
language prompts for C++, JavaScript, Python, and Rust. The harness assembles
agent prompts, runs coding-agent CLIs in Docker, builds submitted artifacts,
executes hidden pytest suites through a language-neutral CLI contract, records
token/cost metadata where available, and publishes versioned result JSON.

Current engineering priorities are operational and governance-oriented rather
than a single launch checklist:

- **Result publication and dashboard polish.** Keep the published-results
  format, viewer, and summary generation easy to audit as the result corpus
  grows.
- **Task-template and contribution docs.** Factor the repeated eval structure
  into a clear authoring template and contributor guide.
- **Versioned suite governance.** Document how eval versions, changelogs,
  retired cases, and contamination-sensitive additions are managed over time.
- **CI/runtime efficiency.** Continue sharding expensive eval suites and keep
  reference-test CI representative without making routine changes slow.
- **Optional performance measurement.** If performance becomes a scored
  dimension, pin hardware class, run repeated trials, and report only effects
  larger than the documented noise floor.
- **Future evals and community tasks.** Add new domains when they bring a
  materially different documentation corpus or implementation challenge, not
  simply to increase task count.

---

## 12. Open Questions

- **Partial compilation credit.** If a model's code compiles with minor fixes (e.g., a missing semicolon, an incorrect include path), should the evaluator apply those fixes before scoring? Current position: no — the artifact must compile as submitted. This may be revisited if compilation failures are common and uninformative.

- **Multi-run variance.** LLM outputs are non-deterministic. Current published
  studies generally preserve individual run records and run repeated trials
  where budget permits. The remaining policy question is how to standardize
  aggregation for very expensive models without hiding variance.

- **Sampling controls.** Agent CLIs expose different model and sampling
  controls. Results should record the model, effort/reasoning setting, and any
  explicit sampling parameters that the harness can control. When a CLI does
  not expose a setting, the provider default is part of the evaluated agent
  configuration.

- **Context window handling.** Some evals ship large documentation corpora.
  Current position: provide the intended corpus and let the agent decide what
  to read or summarize; context-window and retrieval limitations are part of
  the measured coding-agent capability.

- **Agent timeout fairness.** Faster agents complete more iterations within the 4-hour wall-clock cap, which may advantage them independent of code quality. Should the cap be token-based rather than time-based? Current position: wall-clock cap is simpler and more operationally meaningful; token cap is logged separately as a secondary dimension.

- **Agent environment scope.** Should the Docker container include the compiler and standard libraries only, or also common third-party libraries (e.g., nlohmann/json for C++ JSON output)? Providing common libraries reduces friction but may mask dependency management capability. Current position: provide only the compiler and standard library; the agent must handle any other dependencies via its build system.

- **What counts as "agent completion"?** Agents may signal completion explicitly (Claude Code exits, Codex CLI returns control) or implicitly (the session times out). Results should note how each session ended. A session that produces a correct implementation but only because it ran to timeout is a different finding than one that completed and exited cleanly.

- **Comparing across agent versions.** Agent CLI versions change frequently. Claude Code v1.2 and v1.3 may produce significantly different results on the same task. Results must be pinned to specific agent version strings, and the leaderboard should support version-specific entries rather than collapsing all runs of "Claude Code" into one row.
