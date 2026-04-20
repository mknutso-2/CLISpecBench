---
name: build-and-lint
description: Run SWE-BuildBench setup, build, lint, type-check, and test workflows. Use when installing dependencies, formatting or linting Python, running Pyright, choosing the right pytest target, or building Docker images for harness and container tests.
---

Meta: This file is a breathing document. If you read it and find that any of the following documentation or guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

# Build and lint

- Start with the narrowest validation that covers the changed files, then expand only if needed.
- After editing Python, run Ruff and Pyright explicitly; editor save hooks do not fire on agent-written changes.
- Use `python`, not `python3`, for shell commands on this Windows host.
- Pyright is strict for both `src/` and the eval test directories; `pyproject.toml` enables that scope, so Python test edits need Pyright too, not just Ruff and pytest.

## Core commands

```bash
uv sync
uv run ruff format
uv run ruff check
uv run pyright
```

## Targeted tests

```bash
pytest path/to/test_file.py::test_name
pytest Evals/RS274/tests --language=cpp
pytest Evals/WordCount/tests --language=py
pytest Evals/WordCount/tests --language=cpp --implementation-root /path/to/agent-output
uv run pytest src/swe_buildbench/tests -m "not docker and not prompts_agent"
uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent"
```

- Eval reference tests do not consume API tokens. C++ reference variants generally need the host C++ toolchain unless you select a supported alternate language such as `--language=py`.
- Pytest markers `docker` and `prompts_agent` are strict; unmarked harness tests must stay pure Python.
- If Windows container tests cannot reach the daemon, retry with `DOCKER_HOST=tcp://localhost:2375`.

## Docker images

```bash
MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh
```

- Build these images before container smoke tests or auth smoke tests.
- Prefer repo scripts or harness commands over raw `docker` from PowerShell on this host.
