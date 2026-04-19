---
name: eval-authoring
description: Add or modify SWE-BuildBench evals. Use when changing eval prompts, docs, tests, reference implementations, task registration, or per-eval version and changelog state, or when creating a new eval directory.
---

Meta: This file is a breathing document. If you read it and find that any of the following guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

# Eval authoring

- Use this skill for any change under `Evals/` or `src/swe_buildbench/harness/task.py` that affects eval behavior or registration.

## Eval structure

- Each eval is organized around `prompt/`, `tests/`, and one or more `reference-implementation-<lang>/` directories.
- Each eval `conftest.py` defines `EVAL_CONFIG`; tests should use the shared `submission_command` fixture exposed by `src/swe_buildbench/pytest_plugin.py`.
- New tasks must be registered in `src/swe_buildbench/harness/task.py` via `_KNOWN_TASKS`.
- New evals should include at least `Evals/<Name>/{prompt,tests,reference-implementation-cpp}/` unless there is a concrete reason to use a different reference-language layout.

## Authoring rules

- Treat `technical-requirements-prompt.md` as a harness contract only: language/tooling constraints, CLI flags, exit codes, and output schema or serialization details. Behavioral requirements belong in `base-prompt.md` or `prompt/docs/`.
- Only edit `technical-requirements-prompt.md` when the harness build/invoke/output contract changes. If a new test depends on behavior that is not derivable from `base-prompt.md`, `technical-requirements-prompt.md`, and `prompt/docs/`, fix those sources instead of smuggling behavior into the contract prompt. Agents should be able to pass in principle from those three sources alone.
- Do not edit `Evals/CNCSim/prompt/docs/RS274NGC.md` unless explicitly asked. CNCSim tests should only depend on behavior that is plainly stated there. If a desired test depends on multi-clause inference or needs clearer behavior, document it in `Evals/CNCSim/CNCSim-Design.md` or `Evals/CNCSim/prompt/base-prompt.md`, not in the spec mirror.
- Every reference-implementation bug fix must ship with an eval test that enforces the corrected behavior. Reference implementations exist to validate the tests, not the other way around.
- Keep test failure modes independent. A test named for behavior X should fail because of X — if many tests share a precondition (schema shape, a parse step, a preamble assertion), one bug cascades into all of them and the score measures that bug N times rather than measuring N independent behaviors. Gate shared preconditions once (e.g. a single `test_output_schema.py`) and keep behavioral assertions tolerant of detail they are not testing: prefer `payload.get("error") is None` to `payload["error"] is None` so a missing-key schema slip surfaces as one schema failure rather than as hundreds of duplicated `KeyError`s. See `Eval-Design.md` §7.4 for the worked example (sonnet-4-6 CNCSim cpp run 3 lost 55% of the suite to one such cascade).
- Keep `__init__.py` minimal. Do not add package-root re-exports unless they are part of a deliberate public API.

## Versioning

- Bump `Evals/<Task>/VERSION` and update `Evals/<Task>/CHANGELOG.md` for any contract-affecting change: prompts, docs, tests, harness contract, or reference implementation changes that alter observable behavior.
- Use a patch bump for clarifications and bug fixes, a minor bump for new behavior or expanded contract, and a major bump for breaking changes.
- Pure refactors that do not change observable behavior do not need a version bump.
- When bumping `VERSION`, date the new `CHANGELOG.md` header with today's date (`## vX.Y.Z — YYYY-MM-DD`) in the same commit. Do not use `— unreleased` as a deferred-date marker: eval runs stamp `eval_version` from the `VERSION` file immediately, so there is no pre-release state worth encoding. Describe pending-but-unlanded work in a PR description or a TODO, not in a dated `CHANGELOG.md` header.

## Validation

- Pyright is strict for both `src/` and the eval test directories, so validate Python test changes with Pyright as well as Ruff and pytest.
- After Python edits, use `skills/build-and-lint/SKILL.md`.
