# AGENTS.md

This file provides guidance to coding agents when working with code in this repository. `AGENTS.md` is the canonical repo-instruction file; `CLAUDE.md` mirrors overlapping guidance for Claude Code.

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

Single test: `pytest path/to/test_file.py::test_name`. Pytest markers `docker` and `prompts_agent` are strict; unmarked tests must stay pure-Python.

## Architecture

- **`src/swe_buildbench/`** is the harness package. Subpackages: `harness/` (task registry + run pipeline), `agents/` (per-agent CLI adapters and Docker invocation), `build/` (CMake/build helpers), `cncsim/` (task-specific scoring), `cli.py` (the `swe-buildbench` entrypoint), `pytest_plugin.py` (shared fixtures re-exported by each eval's `conftest.py`).
- **Eval pipeline** (per task): assemble prompt (`base-prompt.md` + `technical-requirements-prompt.md` + `docs/`) -> run agent CLI inside its Docker image with prompt + docs mounted and network locked to the agent's API host -> build the agent's output (CMake by default) -> run the hidden pytest suite via `pytest-json-report` -> write a `RunResult` JSON.
- **Multi-language refs.** Each `Evals/<task>/` may have `reference-implementation-cpp/` (C++, default) and `reference-implementation-py/` / `reference-implementation-js/` / `reference-implementation-rs/`. Tests are language-agnostic: they request the `submission_command` fixture from `pytest_plugin`, and `--language=<lang>` / `--implementation-root=<path>` select what gets built/run. Each eval's `conftest.py` defines an `EVAL_CONFIG` naming the task and its ref-impl layout.
- **Tasks are registered** in `src/swe_buildbench/harness/task.py` via `_KNOWN_TASKS`. Add a new eval there as well as creating `Evals/<Name>/{prompt,tests,reference-implementation-cpp}/`.
- **Agent credential mounting.** The harness mounts the host's CLI credentials into the container at runtime. On Windows + WSL2 Docker, log in to `claude` / `codex` / `gemini` on Windows, not inside WSL. Paths under `C:\Users\<you>\.claude` and similar get translated to `/mnt/c/...` for the WSL daemon. The `scripts/smoke-test-*.sh` scripts are the source of truth for the per-agent mount strategy.

## Repo-specific rules

- **`technical-requirements-prompt.md` is a harness contract**, not a behavior spec. Only edit it when the harness's build/invoke/output contract changes. It should contain only requirements the harness needs in order to build, invoke, and read results from the submission: language or tooling constraints, CLI flags, exit codes, and output schema or serialization details. New behavioral requirements belong in `base-prompt.md` or `docs/`. If a new test depends on behavior that is not derivable from those sources, fix those sources rather than `technical-requirements-prompt.md`. Agents must, in principle, be able to pass every test using only those three sources.
- **Do not edit `Evals/CNCSim/prompt/docs/RS274NGC.md`** unless explicitly asked. RS274 is the source of truth for CNCSim tests; only test behavior that is plainly stated there. If a desired test depends on multi-clause inference, document the requirement in `Evals/CNCSim/CNCSim-Design.md` or `Evals/CNCSim/prompt/base-prompt.md` instead, never by editing the spec.
- **Every ref-impl bug must have an eval test.** Reference implementations exist to validate the test suite, not the other way around. When a bug is found in a reference implementation, fix it and add or update a test that enforces the correct behavior. The test is what makes the fix visible to agent submissions.
- **Pyright is strict** for `src` and the eval test dirs. After editing Python, run Ruff and Pyright explicitly. `pyproject.toml` enables strict Pyright checking for both `src` and the eval tests, so Python test changes should be verified with Pyright too, not just Ruff and pytest. VS Code save actions do not fire on agent edits made via patches, shell commands, scripts, or other direct filesystem writes.
- **Keep `__init__.py` minimal.** Do not re-export from package roots unless it is an intentional public API. Import from the defining module instead.
- **Bump per-eval `VERSION` + `CHANGELOG.md` on any contract-affecting change.** Each `Evals/<Task>/` has a `VERSION` file (semver) and a `CHANGELOG.md`. Bump both whenever you change anything an agent or scoring run can observe: prompts, docs, tests, the harness contract, or reference implementations in a way that reflects a spec change. Patch bump for clarifications and bug fixes; minor for new behavior or expanded contract; major for breaking changes. Pure refactors that do not change observable behavior do not need a bump. See `README.md` -> "Versioning" for the full rule.

## Cross-validation requirement

- Before concluding any task and reporting completion, the agent must obtain adversarial cross-validation from a different AI system (see agent-specific sections below). Point the reviewer at the exact diff, commit, or files under review, and continue the review until the two agents agree that the changes have been cross-validated.
- This cross-validation requirement also applies to analysis and synthesis tasks, not just code changes. If the reviewing agent produced findings and you plan to omit, downgrade, reject, or contradict any of them in your response to the user, first do a targeted follow-up review on those exact points.
- When relaying cross-validation output, explicitly distinguish between:
  - the full superset of findings that were raised
  - the narrower consensus list you believe remains after reconciliation
  - findings rejected as stale, incorrect, already covered, or unobservable under the current harness
- If you and the reviewing agent do not agree, do not silently pick one opinion and move on. Create `ARGUMENT.md` at the repo root that records both positions, the relevant files or spec passages, and the unresolved disagreement.
- If the reviewing agent is unavailable, rate-limited, or otherwise cannot complete the needed reconciliation round, create `ARGUMENT.md` before answering and say that the disagreement remains unresolved due to that limitation.

## Running evals

### Launching eval runs

**There is no timeout flag.** Agent sessions run until the agent exits naturally. The harness has a 24-hour safety backstop for hung containers, but this should never be hit in practice. Killing a run mid-execution produces artificially low scores and wastes compute.

Run evals in the background and monitor them periodically. Do not block on them. The harness writes `progress.txt` in the eval directory as runs complete. Check that file and the Docker container status to track progress. You will be notified when the background command finishes.

Example launch:
```bash
DOCKER_HOST=tcp://localhost:2375 swe-buildbench run \
  --task cncsim-full --agent codex-cli --model gpt-5.2-codex --effort xhigh --runs 3
```

### Post-run log inspection (required)

After every eval run completes, inspect the result and transcript before moving on. Do not batch up runs and check later. The `metadata.notes` field in the result JSON exists for recording these observations.

**For every run that scores 0/N:**

Open `transcript.jsonl` in the run directory and classify the root cause:

- **timeout**: Agent still actively working when killed. Note whether source files exist and if they build.
- **auth_failure**: 401/403 errors or expired tokens in logs. The agent never started real work.
- **rate_limit**: 429 errors or quota exhaustion from the model API.
- **context_exhausted**: Agent hit context window limits. Note how far it got.
- **no_code_written**: Agent completed voluntarily but never wrote source files. Check whether it only planned or analyzed without implementing.
- **build_failure**: Agent wrote source but it does not compile. Check build diagnostics.
- **agent_error**: Agent crashed or threw an unhandled exception.
- **model_error**: The model API returned server errors or capacity issues unrelated to auth or rate limits.

Record the classification and a brief explanation in the result JSON's `metadata.notes` field, or if the harness has already written the file, note it in your report to the user.

**For every run that scores > 0:**

Confirm from the transcript that the agent acknowledged it was done. Check whether:
- Agent voluntarily exited (clean run)
- Agent was still working when timeout killed it (score may be artificially low)
- Agent asked for input but got no response (harness problem)
- Agent hit a rate limit or error partway through (partial result)

**Always include in results reports:**
1. The language/task variant (for example `cncsim-full` = C++, `cncsim-full-py` = Python)
2. Root cause for every zero-score run
3. Whether non-zero timed-out runs might have scored higher
4. Infrastructure issues requiring reruns

### Official results table rules

Only runs with `exit_reason: "completed"` appear in the per-run detail tables and are included in Best and Mean calculations. Runs that errored, timed out, or were rate-limited are excluded from the table and noted below it as needing reruns. If a model has zero completed runs, list it in the summary table with `- | -` for Best and Mean and describe the failure in the Status column.

### Last Message column

The "Last Message" column summarizes `metadata.agent_last_message` from the result JSON. **Do not copy the first sentence verbatim** because agents often sound confident even when they produced nothing. Instead, write a short editorial summary that surfaces the agent's actual completion state. The goal is to make it immediately obvious to a casual reader whether the agent considered the task done.

Key signals to surface (quote the agent's own words when possible):

- **Claims complete**: "Claims complete." / "Claims complete; built and tested."
- **Incomplete - acknowledged**: When the model explicitly acknowledges its implementation is incomplete, this must be surfaced. Look for: "remaining work" lists, "pending" / "TODO" items, future tense about core features ("will be implemented next"), progress-report framing ("began structuring..."), or explicit statements that the code does not build or run yet. Always quote or paraphrase the acknowledgment so a reader can see the model knew it was incomplete.
- **Incomplete - asked to continue**: When the model requests user input to continue, flag it. Direct questions ("Shall I proceed?", "Let me know if you want to continue") and indirect handoffs ("If you can break the problem into narrower slices...", numbered continuation plans) both count because the model treated the one-shot task as interactive.
- **Incomplete - not acknowledged**: "Claims complete but only wrote stubs (0 LOC)."
- **Asking a question**: "Asked for clarification on X."

`acknowledged` and `asked to continue` are not mutually exclusive. Surface whichever signals are present.

Read the full `agent_last_message`, not just the first line, and cross-reference it with Files or LOC to judge whether the agent's claim is credible. A message that says "simulator is working" with 0 files is a false claim and should be flagged.

## Environment notes

- **Use `python`, not `python3`**, for all shell commands. On this Windows system, `python3` is not available; `python` resolves to the correct interpreter.
- **Do not assume the host `docker` CLI is usable from PowerShell.** On this Windows machine, `Get-Command docker` resolves to a zero-byte `C:\Windows\System32\docker` file, which broke ad hoc PowerShell pipeline usage in local testing, made `cmd /c docker ...` unreliable in local testing, and can trigger Windows "Pick an app to open docker" prompts. The harness itself talks to Docker through the Python Docker SDK (`src/swe_buildbench/harness/docker.py`), so `swe-buildbench run ...` is fine even when manual `docker` shell commands are not.
- **Do not background eval runs via `Start-Process powershell ...` on this host.** That launch path opened visible external PowerShell windows during local testing. If you need a detached run, prefer a hidden `cmd.exe` wrapper or another non-windowed launcher; otherwise keep the eval in the current shell.
- **Tested detached eval launcher example on this host:** `Start-Process cmd.exe -WindowStyle Hidden -ArgumentList '/d','/c','cd /d <repo> && [optional host-specific env such as DOCKER_HOST=tcp://localhost:2375 &&] uv run swe-buildbench run --task <task> --agent <agent> --model <model> [optional agent-specific flags such as --effort <effort>] [optional --runs <n>] 1>\"<out.log>\" 2>\"<err.log>\"'`. This worked for CNCSim codex-cli runs here without opening visible PowerShell windows.

## Key docs

- `Eval-Design.md` - benchmark-level design
- `Harness-Design.md` - harness architecture
- `Evals/CNCSim/CNCSim-Design.md` - CNCSim task design
- `Evals/CNCSim/tests/` - CNCSim tests run against submissions and the reference implementations
- `Evals/CNCSim/prompt/base-prompt.md` - non-technical prompt shown to the coding agent
- `Evals/CNCSim/prompt/technical-requirements-prompt.md` - harness contract prompt
- `Evals/CNCSim/prompt/docs/RS274NGC.md` - RS274 spec mirror; do not edit unless explicitly asked
- `Evals/CNCSim/reference-implementation-cpp/` and `Evals/CNCSim/reference-implementation-py/` - running reference implementations; at each commit, each should pass all tests for its language
- `AGENTS.md` - full agent workflow and cross-validation protocol
