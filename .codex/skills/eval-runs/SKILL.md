---
name: eval-runs
description: Run and analyze evals like WordCount, CNCSim, and IGES. Use when launching evals, detaching background runs, monitoring progress, inspecting transcripts and result JSON, classifying failures, or preparing official results tables and Last Message summaries.
---

Meta: This file is a breathing document. If you read it and find that any of the following documentation or guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

# Eval runs

## Docker prerequisites

- On Windows, use the WSL2 daemon (this is the repo-supported setup for this host).
- Make sure Docker Engine is started in WSL and reachable from Windows:
  - `wsl -d Ubuntu -- service docker status`
  - If needed: `wsl -d Ubuntu -- sudo service docker start`
  - `DOCKER_HOST=tcp://localhost:2375 docker version`
- If the run cannot connect to Docker:
  - restart Docker in WSL: `wsl -d Ubuntu -- sudo service docker restart`
  - then re-run `DOCKER_HOST=tcp://localhost:2375 docker version`
- Proceed with eval commands only after a successful daemon check.

## Launching runs

- There is no timeout flag. Let agent sessions exit naturally; killing them early depresses scores and wastes compute.
- The harness has a 24-hour safety backstop for hung containers; treat that as an emergency stop, not a normal control.
- Prefer detached runs over blocking the shell. Monitor `progress.txt` in the eval directory as runs complete, and also check container status when you need to tell whether work is still active.
- Use `swe-buildbench run ...` if the console script is available; otherwise use `uv run swe-buildbench run ...`.
- Use `swe-buildbench results` or `uv run swe-buildbench results` to inspect aggregate run output after completion.
- On Windows + WSL2 Docker, authenticate `claude`, `codex`, and `gemini` on Windows, not inside WSL. Credential paths under `C:\Users\<you>\.claude`, `.codex`, and `.gemini` are translated to `/mnt/c/...` for the WSL daemon; `scripts/smoke-test-*.sh` is the source of truth for the mount strategy.

Example:

```bash
DOCKER_HOST=tcp://localhost:2375 uv run swe-buildbench run --task cncsim-cpp --agent codex-cli --model gpt-5.2-codex --effort xhigh --runs 3
```

- On this Windows host, do not background evals via `Start-Process powershell ...`; use a hidden `cmd.exe` wrapper instead.
- Tested detached launcher pattern on this host:

```powershell
Start-Process cmd.exe -WindowStyle Hidden -ArgumentList '/d','/c','cd /d C:\Git\SWE-BuildBench && DOCKER_HOST=tcp://localhost:2375 && uv run swe-buildbench run --task <task> --agent <agent> --model <model> [optional flags] 1>"<out.log>" 2>"<err.log>"'
```

- Do not rely on raw `docker` from PowerShell on this host; the harness uses the Python Docker SDK.

## Post-run inspection

- After every eval run completes, inspect the result JSON and `transcript.jsonl` before moving on. Do not batch review later.
- Use the `metadata.notes` field in the result JSON for root-cause observations when the file is still editable.
- For every run that scores `0/N`, classify the root cause as one of:
  - `timeout`: the agent was still actively working when killed; note whether source files exist and whether they build.
  - `auth_failure`: 401/403 errors or expired credentials; the agent never started real work.
  - `rate_limit`: 429 errors or quota exhaustion from the model API.
  - `context_exhausted`: the agent hit context-window limits; note how far it got.
  - `no_code_written`: the agent completed voluntarily but never wrote source files; check whether it only planned or analyzed.
  - `build_failure`: the agent wrote source but it does not compile; capture the build diagnostics.
  - `agent_error`: the agent crashed or threw an unhandled exception.
  - `model_error`: the model API returned server or capacity errors unrelated to auth or rate limits.
- Record the classification and a brief explanation in `metadata.notes`, or report it explicitly if the result file is already finalized.
- For every run that scores above zero, confirm from the transcript whether the agent acknowledged it was done, voluntarily exited, was still working when killed, asked for input but got none, or hit an error/rate limit partway through.

## Reporting rules

- Every results report must include the language/task variant, the root cause for every zero-score run, whether any non-zero timed-out runs may have scored higher, and any infrastructure issues requiring reruns.
- Only runs with `exit_reason: "completed"` belong in official per-run tables and Best/Mean calculations. Timed-out, errored, or rate-limited runs are excluded from those tables and called out separately.
- If a model has zero completed runs, show `- | -` for Best and Mean and explain the failure in the Status column.
- For the Last Message column, read the full `metadata.agent_last_message`, cross-check it against files/LOC, and summarize it editorially instead of copying the first sentence.
- Surface these signals when present:
  - claims complete
  - incomplete and acknowledged
  - incomplete and asked to continue
  - incomplete but not acknowledged
  - asked a clarifying question
- `acknowledged` and `asked to continue` are not mutually exclusive; report both when both appear.
- Flag false completion claims explicitly. Example: if the message says the simulator is working but the run produced 0 files or only stubs, say so.
