# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

SWE-BuildBench is a benchmark for evaluating AI coding agents on doc-driven implementation tasks. An agent is given a domain spec + docs and must produce a buildable implementation that passes a hidden pytest suite. Currently two evals: `CNCSim` (full RS274 G-code interpreter) and `WordCount` (toy harness sanity-check).

## Common commands

```bash
uv sync                                   # install deps
uv run ruff check                         # lint
uv run ruff format                        # format
uv run pyright                            # type-check (strict; covers src + eval tests)

# Eval reference tests (no API cost; needs C++ toolchain, or --language=python)
pytest Evals/CNCSim/tests
pytest Evals/WordCount/tests --language=python
pytest Evals/WordCount/tests --implementation-root /path/to/agent-output

# Harness tests, by marker
uv run pytest src/swe_buildbench/tests -m "not docker and not prompts_agent"   # unit
uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent"       # container
# On Windows, if container tests can't find the daemon:
DOCKER_HOST=tcp://localhost:2375 uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent"

# Build Docker images (base + per-agent); required for container/auth tests
MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh

# Run an eval end-to-end
swe-buildbench run --task wordcount --agent claude-code
swe-buildbench run --task cncsim-full --agent codex-cli
swe-buildbench results
```

Single test: `pytest path/to/test_file.py::test_name`. Pytest markers `docker` and `prompts_agent` are strict — unmarked tests must stay pure-Python.

## Architecture

- **`src/swe_buildbench/`** is the harness package. Subpackages: `harness/` (task registry + run pipeline), `agents/` (per-agent CLI adapters and Docker invocation), `build/` (CMake/build helpers), `cncsim/` (task-specific scoring), `cli.py` (the `swe-buildbench` entrypoint), `pytest_plugin.py` (shared fixtures re-exported by each eval's `conftest.py`).
- **Eval pipeline** (per task): assemble prompt (`base-prompt.md` + `technical-requirements-prompt.md` + `docs/`) → run agent CLI inside its Docker image with prompt + docs mounted and network locked to the agent's API host → build the agent's output (CMake by default) → run the hidden pytest suite via `pytest-json-report` → write a `RunResult` JSON.
- **Multi-language refs.** Each `Evals/<task>/` may have `reference-implementation-cpp/` (C++, default) and `reference-implementation-python/` etc. Tests are language-agnostic: they request the `submission_command` fixture from `pytest_plugin`, and `--language=<lang>` / `--implementation-root=<path>` select what gets built/run. Each eval's `conftest.py` defines an `EVAL_CONFIG` naming the task and its ref-impl layout.
- **Tasks are registered** in `src/swe_buildbench/harness/task.py` via `_KNOWN_TASKS`. Add a new eval there as well as creating `Evals/<Name>/{prompt,tests,reference-implementation-cpp}/`.
- **Agent credential mounting.** The harness mounts the *host's* CLI credentials into the container at runtime. On Windows + WSL2 Docker, log in to `claude` / `codex` / `gemini` on **Windows** (not inside WSL) — paths under `C:\Users\<you>\.claude` etc. get translated to `/mnt/c/...` for the WSL daemon. The `scripts/smoke-test-*.sh` scripts are the source of truth for the per-agent mount strategy.

## Repo-specific rules (from AGENTS.md)

- **`technical-requirements-prompt.md` is a harness contract**, not a behavior spec. Only edit it when the harness's build/invoke/output contract changes. New behavioral requirements belong in `base-prompt.md` or `docs/`. Agents must, in principle, be able to pass every test using only those three sources.
- **Do not edit `Evals/CNCSim/prompt/docs/RS274NGC.md`** unless explicitly asked. RS274 is the source of truth for CNCSim tests; only test behavior that is plainly stated there. If a desired test depends on multi-clause inference, document the requirement in `CNCSim-Design.md` or `base-prompt.md` instead — never by editing the spec.
- **Pyright is strict** for `src` and the eval test dirs. After editing Python, run Ruff *and* Pyright explicitly — VS Code save actions don't fire on agent edits.
- **Keep `__init__.py` minimal.** Don't re-export from package roots unless it's an intentional public API; import from the defining module.
- **Cross-validation is required.** Use `/codex:adversarial-review` to invoke Codex as an adversarial reviewer.

Workflow:

1. Before calling the review, prepare the review target (working-tree changes, a commit hash, or specific files).
2. Invoke `/codex:adversarial-review` with a focus prompt that includes:
   - what code to inspect (e.g. "Review the working-tree changes" or "Review commit abc1234")
   - which docs define correctness (e.g. AGENTS.md, CNCSim-Design.md, base-prompt.md, RS274NGC.md)
   - the instruction to be skeptical and surface concrete findings with file references
3. Codex's review output is returned verbatim into the Claude Code conversation, so the user can see the full exchange.
4. Evaluate Codex's findings. For each finding, either accept it and fix the issue, or prepare a counterargument grounded in the spec/code.
5. If findings remain disputed after one follow-up round, create `ARGUMENT.md` as described above.

Example invocation:
```
/codex:adversarial-review Review the working-tree changes. Check alignment with AGENTS.md, Evals/CNCSim/CNCSim-Design.md, Evals/CNCSim/prompt/base-prompt.md, Evals/CNCSim/prompt/technical-requirements-prompt.md, and the RS274 docs. Be skeptical. Focus on concrete findings with file references, not style.
```

## Key docs

- `Eval-Design.md` — benchmark-level design
- `Harness-Design.md` — harness architecture
- `Evals/CNCSim/CNCSim-Design.md` — CNCSim task design
- `AGENTS.md` — full agent workflow + cross-validation protocol
