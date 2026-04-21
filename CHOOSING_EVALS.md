# Choosing Eval Candidates

A good CLISpecBench eval is not just "interesting." It must isolate document
comprehension and autonomous system-building while staying testable,
reproducible, and relatively contamination-resistant.

## Hard Requirements

- **Documentation-first.** The task must be passable in principle from
  `base-prompt.md`, `technical-requirements-prompt.md`, and `prompt/docs/`
  alone. If success depends on unstated domain lore, evaluator intuition, or
  reverse-engineering the reference implementation, it is a bad fit.
- **Non-developer describable.** The base prompt must be plausibly writable by
  a domain expert with no software background (see `Eval-Design.md` §5.3). If
  the task only works when the base prompt smuggles in developer-level guidance
  ("write tests," "use pattern X," "handle errors like Y"), it violates the
  benchmark's core design principle and measures instruction-following rather
  than autonomous judgment.
- **Authoritative source material.** The documentation corpus should be public,
  stable, and authoritative. Ideally it is one dense spec or a small curated
  set of documents with clearly defined roles.
- **No solver code in the corpus.** The public docs corpus (`prompt/docs/`)
  should explain the problem, not solve it — no shipped reference
  implementation, extensive worked code, or de facto executable tutorial. This
  is separate from the private reference implementation the eval author
  maintains as a test-suite backstop (see `Reference implementation
  feasibility` below); that ref impl lives under
  `reference-implementation-<lang>/` and is never served to the agent as part
  of the prompt corpus.
- **Behaviorally unambiguous.** Hidden tests should assert only behavior that is
  explicit and unambiguous in the public prompt/docs corpus or the harness
  contract. If the author has to argue from "what the spec probably meant," the
  task is not ready.
- **Deterministic scoring surface.** Given the same inputs and initial state,
  there should be one correct observable result. The harness should be able to
  drive the submission through a simple CLI and compare structured output.
- **Independent failure modes.** The task should admit a hidden suite where one
  small bug does not collapse half the benchmark into the same failure. If the
  domain forces heavy shared preconditions, the resulting score signal is weak.
- **System-level complexity.** The implementation should be a real multi-file
  system, not a toy script or algorithm exercise. As a rule of thumb, expect at
  least roughly 1000 LOC for a competent reference implementation.
- **Test-suite scalability.** The domain must plausibly support at least 50
  independent-behavior hidden tests of meaningful depth (`Eval-Design.md` §9.1
  floor). If the behavior surface is so narrow that 50 genuinely distinct tests
  cannot be authored, the score signal is too coarse for a benchmark track.
- **Contamination resistance.** Avoid domains with abundant polished
  open-source implementations, tutorial walkthroughs, or public benchmark
  suites that likely saturated model training data.
- **Reference implementation feasibility.** We should be able to maintain at
  least one reference implementation that passes the full suite and acts as a
  backstop for test legitimacy.
- **Reasonable harness fit.** The task must build and run inside the
  CLISpecBench model: local files, CLI flags, no GUI, no hosted services, no
  manual scoring, and no network dependencies beyond the agent API.
- **Publicly distributable docs.** If the documentation corpus cannot be
  checked into the repo or otherwise redistributed cleanly, it is a poor
  candidate.

## Strong Preferences

- **Native behavioral contract.** The benchmark is strongest when the domain
  docs naturally define the behavior. If large parts of the real behavior have
  to be stuffed into `technical-requirements-prompt.md`, that is a warning
  sign.
- **Language-agnostic surface.** The core behavior should be testable through
  the same CLI contract across languages, even if the first reference
  implementation is only in C++.
- **Adversarial testability.** The domain should support hidden edge cases that
  reward genuine understanding rather than pattern-matching against a few
  happy-path examples.
- **Domain expertise available.** The best evals come from areas where someone
  with real domain knowledge can author test cases, spot ambiguity, and reject
  fake-but-plausible behavior.
- **Curated corpus size.** Dense is good; sprawling is not. A great eval often
  has one self-contained spec or a small number of tightly scoped documents
  rather than a pile of scattered references.
- **Natural extensions.** It is a plus if the task has plausible follow-on
  feature requests for future extension prompts, but this is optional.

## Bad Fits

- Web apps, CRUD apps, or UX-heavy tasks where correctness depends on design
  taste, browser behavior, or manual inspection.
- Tasks whose "spec" is mostly examples, existing code, or reverse-engineering
  a reference implementation.
- Thin wrappers around standard libraries or SDK tutorials.
- Problems that are mostly dependency wrangling, framework setup, or vendor
  integration rather than document comprehension and implementation.
- Domains with ambiguous, contradictory, or underspecified behavior unless the
  ambiguity can be resolved cleanly in the public prompt/docs corpus.
- Tasks with correctness tied to wall-clock timing, flaky concurrency, remote
  services, nondeterministic hardware, or platform-specific quirks.
- Tiny utilities or textbook exercises that do not force architecture, state
  management, or nontrivial reasoning.

## Sanity-Check Questions

Before investing in a new eval, answer "yes" to most of these:

- Can a strong agent theoretically pass using only the public prompt/docs
  artifacts?
- Can every hidden test be justified by a specific, defensible requirement?
- Can the task be scored through a stable CLI and structured output?
- Will failures be informative, or will one schema slip cause half the suite to
  fail for the same reason?
- Is the difficulty coming from real system-building and spec comprehension
  rather than incidental setup friction?
- Would a competent human engineer recognize this as a real implementation
  task, not a toy?
- Is contamination low enough that success probably reflects reasoning rather
  than recall?

## Rule of Thumb

If a candidate eval sounds good only after adding lots of harness-only
behavior, hand-waving ambiguities, or leaning on a known public
implementation, it is probably not a CLISpecBench eval.
