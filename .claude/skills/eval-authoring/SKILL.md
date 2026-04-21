---
name: eval-authoring
description: Add or modify CLISpecBench evals. Use when changing eval prompts, docs, tests, reference implementations, task registration, or per-eval version and changelog state, or when creating a new eval directory.
---

Meta: This file is a breathing document. If you read it and find that any of the following guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

# Eval authoring

- Use this skill for any change under `Evals/` or `src/clispecbench/harness/task.py` that affects eval behavior or registration.

## Eval structure

- Each eval is organized around `prompt/`, `tests/`, and one or more `reference-implementation-<lang>/` directories.
- Each eval `conftest.py` defines `EVAL_CONFIG`; tests should use the shared `submission_command` fixture exposed by `src/clispecbench/pytest_plugin.py`.
- New tasks must be registered in `src/clispecbench/harness/task.py` via `_KNOWN_TASKS`.
- New evals should include at least `Evals/<Name>/{prompt,tests,reference-implementation-cpp}/` unless there is a concrete reason to use a different reference-language layout.

## Writing prompt artifacts

- **`base-prompt.md`** The base prompt is written from the perspective of a domain expert who is not a software developer — someone who knows exactly what they want to build but has no software engineering background. They would not think to specify test coverage, code quality standards, architectural patterns, or implementation strategy, just as they would not specify which sorting algorithm to use.
- **`prompt/docs/`** is for any documentation that a domain expert might reasonably provide to a software engineer to help them understand the problem and its constraints. Examples include a machinist providing the RS274 spec to specify how a CNC machine simulation should behave, a CAD engineer providing the IGES spec to specify how IGES files should be parsed and interpreted, a programming language official specification, a board or card game official rule book, etc.
- **`technical-requirements-prompt.md`** as a harness contract only: language/tooling constraints, CLI flags, exit codes, and output schema or serialization details. Behavioral requirements belong in `base-prompt.md` or `prompt/docs/`.

Everything else — whether to write tests, which architecture to choose, how to handle errors, what quality standards to follow — is left entirely to the agent's judgment. This framing serves two purposes: it measures genuine agent autonomy rather than instruction-following ability, and it emulates a realistic and increasingly common usage pattern where domain experts use coding agents to build real systems without software engineering backgrounds.

## Writing tests three golden rules

1. **Thorough coverage of the spec.** Every directive and requirement from a specification *must* have an associated test case in the eval.
2. **Unequivocally unambiguous tests.** The `docs` corpus associated with each eval may include some requirements that are clear and some that are ambiguous. The goal of CLISpecBench is that 100% success rate is possible for an agent that fully understands the spec. To achieve this, every test in an eval must only verify invariants that are unequivocally, unambiguously defined in the documentation corpus.
3. **Independent tests.** Tests should have independent failure modes. A test named for behavior X should only fail because of X. When many tests share a precondition — a schema assertion, a fixture that parses output, a preamble check — one bug in the submitted application violating that precondtion cascades and the score stops measuring N independent capabilities and starts measuring one thing N times. The rule of thumb: **if a test fails, the failure should tell you something you didn't learn from the other tests failing.**
Worked example: sonnet-4-6's RS274 cpp run 3 (see `published_results/CNCSIM/results-2_1_1.md`) built cleanly and claimed complete, but the agent emitted the required `error` output field only when non-empty, missing the spec's `null` on success. Because 259 behavioral tests asserted `payload["error"] is None` at the top, that single ~5-LOC mistake failed every one of them with `KeyError: 'error'` — costing the run ~55% of the suite before any of its actual RS274 logic was probed. A schema gate plus `.get("error")` in behavioral tests would have localized the failure to one schema test and let the rest of the suite measure what it was named for.

## Versioning

- Once the eval has been put in service, bump `Evals/<Task>/VERSION` and update `Evals/<Task>/CHANGELOG.md` for any contract-affecting change: prompts, docs, tests, harness contract, or reference implementation changes that alter observable behavior.
- Use a patch bump for clarifications and bug fixes, a minor bump for new behavior or expanded contract, and a major bump for breaking changes.
- Pure refactors that do not change observable behavior do not need a version bump.

## Validation

- Pyright is strict for both `src/` and the eval test directories, so validate Python test changes with Pyright as well as Ruff and pytest.
- After Python edits, use `skills/build-and-lint/SKILL.md`.
