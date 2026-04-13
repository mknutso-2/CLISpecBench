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

# Eval reference tests (no API cost; needs C++ toolchain, or --language=py)
pytest Evals/CNCSim/tests
pytest Evals/WordCount/tests --language=py
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
- **Multi-language refs.** Each `Evals/<task>/` may have `reference-implementation-cpp/` (C++, default) and `reference-implementation-py/` / `reference-implementation-js/` / `reference-implementation-rs/`. Tests are language-agnostic: they request the `submission_command` fixture from `pytest_plugin`, and `--language=<lang>` / `--implementation-root=<path>` select what gets built/run. Each eval's `conftest.py` defines an `EVAL_CONFIG` naming the task and its ref-impl layout.
- **Tasks are registered** in `src/swe_buildbench/harness/task.py` via `_KNOWN_TASKS`. Add a new eval there as well as creating `Evals/<Name>/{prompt,tests,reference-implementation-cpp}/`.
- **Agent credential mounting.** The harness mounts the *host's* CLI credentials into the container at runtime. On Windows + WSL2 Docker, log in to `claude` / `codex` / `gemini` on **Windows** (not inside WSL) — paths under `C:\Users\<you>\.claude` etc. get translated to `/mnt/c/...` for the WSL daemon. The `scripts/smoke-test-*.sh` scripts are the source of truth for the per-agent mount strategy.

## Repo-specific rules (from AGENTS.md)

- **`technical-requirements-prompt.md` is a harness contract**, not a behavior spec. Only edit it when the harness's build/invoke/output contract changes. New behavioral requirements belong in `base-prompt.md` or `docs/`. Agents must, in principle, be able to pass every test using only those three sources.
- **Do not edit `Evals/CNCSim/prompt/docs/RS274NGC.md`** unless explicitly asked. RS274 is the source of truth for CNCSim tests; only test behavior that is plainly stated there. If a desired test depends on multi-clause inference, document the requirement in `CNCSim-Design.md` or `base-prompt.md` instead — never by editing the spec.
- **Every ref-impl bug must have an eval test.** When a bug is found in a reference implementation, fix it AND add/update a test that enforces the correct behavior. The test is what makes the fix visible to agent submissions.
- **Pyright is strict** for `src` and the eval test dirs. After editing Python, run Ruff *and* Pyright explicitly — VS Code save actions don't fire on agent edits.
- **Keep `__init__.py` minimal.** Don't re-export from package roots unless it's an intentional public API; import from the defining module.
- **Bump per-eval `VERSION` + `CHANGELOG.md` on any contract-affecting change.** Each `Evals/<Task>/` has a `VERSION` file (semver) and a `CHANGELOG.md`. Bump both whenever you change anything an agent or scoring run can observe (prompts, docs, tests, harness contract, reference impls reflecting a spec change). See README.md → "Versioning" for patch/minor/major guidance and the full rule.
## Running evals

### Post-run log inspection (required)

After every eval run completes, inspect the result and transcript before moving on. Do not batch up runs and check later.

**For every run that scores 0/N:**

Open `transcript.jsonl` in the run directory and classify the root cause:

- **timeout**: Agent still actively working when killed. Note whether source files exist and if they build.
- **auth_failure**: 401/403 errors or expired tokens in logs. Agent never started real work.
- **rate_limit**: 429 errors or quota exhaustion from the model API.
- **context_exhausted**: Agent hit context window limits. Note how far it got.
- **no_code_written**: Agent completed voluntarily but never wrote source files (only planned/analyzed).
- **build_failure**: Agent wrote source but it doesn't compile.
- **agent_error**: Agent crashed or threw an unhandled exception.
- **model_error**: Model API returned server errors or capacity issues.

Record the classification in your report to the user. If possible, update the result JSON's `metadata.notes` field.

**For every run that scores > 0:**

Confirm from the transcript that the agent acknowledged it was done. Check whether:
- Agent voluntarily exited (clean run)
- Agent was still working when timeout killed it (score may be artificially low)
- Agent asked for input but got no response (harness problem)
- Agent hit a rate limit/error partway through (partial result)

**Always include in results reports:**
1. The language/task variant (e.g. `cncsim-full` = C++, `cncsim-full-py` = Python)
2. Root cause for every zero-score run
3. Whether non-zero timed-out runs might have scored higher
4. Infrastructure issues requiring reruns

### Official results table rules

Only runs with `exit_reason: "completed"` appear in the per-run detail tables and
are included in Best/Mean calculations. Runs that errored, timed out, or were
rate-limited are excluded from the table and noted below it as needing reruns.
If a model has zero completed runs, list it in the summary table with `- | -` for
Best/Mean and describe the failure in the Status column.

### Last Message column

The "Last Message" column summarizes `metadata.agent_last_message` from the result
JSON. **Do not copy the first sentence verbatim** — agents often sound confident
even when they produced nothing. Instead, write a short editorial summary that
surfaces the agent's actual completion state. The goal is to make it immediately
obvious to a casual reader whether the agent considered the task done.

Key signals to surface (quote the agent's own words when possible):

- **Claims complete**: "Claims complete." / "Claims complete; built and tested."
- **Incomplete — asked to continue**: "Incomplete; wrote no code. Asked 'Shall I
  proceed with building the simulator?'" / "Incomplete; scaffolded only. Asked
  'Let me know if you want to proceed.'"
- **Incomplete — acknowledged but didn't ask**: "Incomplete; scaffolded only.
  Acknowledged 'core logic will be implemented next.'"
- **Incomplete — not acknowledged**: "Claims complete but only wrote stubs (0 LOC)."
- **Asking a question**: "Asked for clarification on X."

Read the full `agent_last_message` (not just the first line) and cross-reference
with Files/LOC to judge whether the agent's claim is credible. A message that says
"simulator is working" with 0 files is a false claim — flag it. Always check for
questions directed at the user ("Should I proceed?", "Let me know if you want to
continue", "Shall I...?") — these are strong signals that the agent treated the
task as interactive despite the one-shot prompt.

## Environment notes

- **Use `python`, not `python3`**, for all shell commands. On this Windows system, `python3` is not available; `python` resolves to the correct interpreter.

## Key docs

- `Eval-Design.md` — benchmark-level design
- `Harness-Design.md` — harness architecture
- `Evals/CNCSim/CNCSim-Design.md` — CNCSim task design
- `AGENTS.md` — full agent workflow + cross-validation protocol
