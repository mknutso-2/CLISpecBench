Meta: This file is a breathing document. If you read it and find that any of the following documentation or guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

## What this repo is

CLISpecBench is a benchmark for evaluating AI coding agents on doc-driven implementation tasks. An agent is given a domain spec + docs and must produce a buildable implementation that passes a hidden pytest suite. Registered evals currently include `BibTeX`, `GEDCOM`, `ICal`, `IGES`, `LAS`, `MARC21`, `RS274`, and `WordCount`.

## Architecture

- **`src/clispecbench/`** is the harness package. Key areas: `harness/` (task registry + run pipeline), `agents/` (per-agent CLI adapters and Docker invocation), `build/` (CMake/build helpers), `tests/` (repo-level harness/adapter/build tests), `cli.py` (the `clispecbench` entrypoint), and `pytest_plugin.py` (shared fixtures re-exported by each eval's `conftest.py`).
- **Eval pipeline**: assemble prompt (`base-prompt.md` + `technical-requirements-prompt.md` + `docs/`) -> run agent CLI in Docker with prompt/docs mounted under the network-access condition documented in `docs/operations/Agent-Run-Notes.md` -> build the agent output -> run the hidden pytest suite via `pytest-json-report` -> write a `RunResult` JSON.
- **Multi-language refs**: each `Evals/<Task>/` may include `reference-implementation-cpp/` plus other language variants. Tests are language-agnostic and use the `submission_command` fixture from `pytest_plugin`; `--language=<lang>` is required, and `--implementation-root=<path>` selects an explicit target when you are not using a configured reference implementation for that language.
- **Task registration** lives in `src/clispecbench/harness/task.py` via `_KNOWN_EVALS`; harness task IDs are generated as `<eval>-<language>` from the registered evals and shared language prompts, such as `rs274-cpp` and `wordcount-rs`.
- **Agent credential mounting** happens at runtime. On Windows + WSL2 Docker, authenticate `claude`, `codex`, and `gemini` on Windows; `scripts/smoke-test-*.sh` is the source of truth for the mount strategy. Antigravity CLI (`agy`) support is correctness-only experimental as of 1.0.5: Windows Credential Manager auth can be made portable to Linux Docker by seeding `~/.gemini/antigravity-cli/antigravity-oauth-token` from the `gemini:antigravity` credential, but that file contains a plaintext OAuth refresh token; `agy --model gemini-3.5-flash` can select the default Flash model, but effort/reasoning selection, token/cost accounting, and canonical transcript capture are not publication-ready; `agy --print` can still return exit 0 with empty captured stdout in non-TTY/subprocess mode.

## Repo-wide rules

- **The parallel author-eval skills are authoritative** for prompt/docs/test/versioning rules, including `technical-requirements-prompt.md`, RS274 spec edits, reference-implementation bug fixes, and `VERSION`/`CHANGELOG.md` bumps. Use `.codex/skills/author-eval/SKILL.md` in Codex and `.claude/skills/author-eval/SKILL.md` in Claude.
- **Keep `__init__.py` minimal.** Do not re-export from package roots unless it is an intentional public API. Import from the defining module instead.

## Key docs

- `docs/design/Eval-Design.md` — benchmark-level design
- `docs/design/Harness-Design.md` — harness architecture
- `docs/operations/Agent-Run-Notes.md` — cross-agent operational findings, including network-access audit and study-consistency notes
- `Evals/RS274/README.md` — RS274 task design
- `Evals/RS274/tests/` — RS274 tests run against submissions and reference implementations
- `Evals/RS274/prompt/base-prompt.md` — non-technical prompt shown to the coding agent
- `Evals/RS274/prompt/technical-requirements-prompt.md` — harness contract prompt
- `Evals/RS274/prompt/docs/RS274NGC.md` — RS274 spec mirror; do not edit unless explicitly asked
- `Evals/RS274/reference-implementation-cpp/` and `Evals/RS274/reference-implementation-py/` — reference implementations. The current C++ reference lacks the motion-trace CLI and passes the `-m "not trace"` baseline; do not treat its full-suite trace failures as a host setup regression.
