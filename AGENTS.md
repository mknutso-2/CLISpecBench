Meta: This file is a breathing document. If you read it and find that any of the following documentation or guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

## What this repo is

SWE-BuildBench is a benchmark for evaluating AI coding agents on doc-driven implementation tasks. An agent is given a domain spec + docs and must produce a buildable implementation that passes a hidden pytest suite. Current evals: `CNCSim` (full RS274 G-code interpreter), `IGES` (CAD interchange parser/writer), and `WordCount` (toy harness sanity-check).

## Architecture

- **`src/swe_buildbench/`** is the harness package. Key areas: `harness/` (task registry + run pipeline), `agents/` (per-agent CLI adapters and Docker invocation), `build/` (CMake/build helpers), `cncsim/` (task-specific scoring), `cli.py` (the `swe-buildbench` entrypoint), and `pytest_plugin.py` (shared fixtures re-exported by each eval's `conftest.py`).
- **Eval pipeline**: assemble prompt (`base-prompt.md` + `technical-requirements-prompt.md` + `docs/`) -> run agent CLI in Docker with prompt/docs mounted and network locked to the API host -> build the agent output -> run the hidden pytest suite via `pytest-json-report` -> write a `RunResult` JSON.
- **Multi-language refs**: each `Evals/<Task>/` may include `reference-implementation-cpp/` plus other language variants. Tests are language-agnostic and use the `submission_command` fixture from `pytest_plugin`; `--language=<lang>` is required, and `--implementation-root=<path>` selects an explicit target when you are not using a configured reference implementation for that language.
- **Task registration** lives in `src/swe_buildbench/harness/task.py` via `_KNOWN_TASKS`, with explicit language suffixes such as `cncsim-cpp` and `wordcount-rs`.
- **Agent credential mounting** happens at runtime. On Windows + WSL2 Docker, authenticate `claude`, `codex`, and `gemini` on Windows; `scripts/smoke-test-*.sh` is the source of truth for the mount strategy.

## Repo-wide rules

- **`skills/eval-authoring/SKILL.md` is authoritative** for prompt/docs/test/versioning rules, including `technical-requirements-prompt.md`, CNCSim spec edits, reference-implementation bug fixes, and `VERSION`/`CHANGELOG.md` bumps.
- **Keep `__init__.py` minimal.** Do not re-export from package roots unless it is an intentional public API. Import from the defining module instead.

## Key docs

- `Eval-Design.md` — benchmark-level design
- `Harness-Design.md` — harness architecture
- `Evals/CNCSim/CNCSim-Design.md` — CNCSim task design
- `Evals/CNCSim/tests/` — CNCSim tests run against submissions and reference implementations
- `Evals/CNCSim/prompt/base-prompt.md` — non-technical prompt shown to the coding agent
- `Evals/CNCSim/prompt/technical-requirements-prompt.md` — harness contract prompt
- `Evals/CNCSim/prompt/docs/RS274NGC.md` — RS274 spec mirror; do not edit unless explicitly asked
- `Evals/CNCSim/reference-implementation-cpp/` and `Evals/CNCSim/reference-implementation-py/` — reference implementations that should pass all tests for their language
