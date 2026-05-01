---
name: eval-runs
description: Run and analyze evals like WordCount, RS274, and IGES. Use when launching evals, detaching background runs, monitoring progress, inspecting transcripts and result JSON, classifying failures, or preparing official results tables and Last Message summaries.
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
- Use `clispecbench run ...` if the console script is available; otherwise use `uv run clispecbench run ...`.
- Use `clispecbench results` or `uv run clispecbench results` to inspect aggregate run output after completion.
- On Windows + WSL2 Docker, authenticate `claude`, `codex`, and `gemini` on Windows, not inside WSL. Credential paths under `C:\Users\<you>\.claude`, `.codex`, and `.gemini` are translated to `/mnt/c/...` for the WSL daemon; `scripts/smoke-test-*.sh` is the source of truth for the mount strategy.

Example:

```bash
DOCKER_HOST=tcp://localhost:2375 uv run clispecbench run --task rs274-cpp --agent codex-cli --model gpt-5.2-codex --effort xhigh --runs 3
```

- On this Windows host, do not background evals via `Start-Process powershell ...`; use a hidden `cmd.exe` wrapper instead.
- Tested detached launcher pattern on this host:

```powershell
Start-Process cmd.exe -WindowStyle Hidden -ArgumentList '/d','/c','cd /d C:\Git\CLISpecBench && DOCKER_HOST=tcp://localhost:2375 && uv run clispecbench run --task <task> --agent <agent> --model <model> [optional flags] 1>"<out.log>" 2>"<err.log>"'
```

- Do not rely on raw `docker` from PowerShell on this host; the harness uses the Python Docker SDK.

## Post-run inspection

- After every eval run completes, inspect the result JSON and `transcript.jsonl` before moving on. Do not batch review later.
- Use the `metadata.notes` field in the result JSON for root-cause observations when the file is still editable.
- For every run, classify the **failure-mode bucket** for `metadata.exit_class`. The bucket determines whether the run counts toward Best/Mean (see Reporting rules). Two top-level groups:
  - **`completed`** — the agent ran to its own self-terminated end. Score reflects what the agent built. Always included.
  - **Model-side failures (prefix `model_*`)** — the run produced a real, scorable submission but the agent CLI exited via something other than its own completion path. Score still reflects model behavior. **Included** in Best/Mean unless the submission was empty/stub. Sub-buckets:
    - `model_capped`: agent hit a usage cap, daily quota, or per-message output-token cap (e.g. "you've hit your limit", "Claude's response exceeded the 32000 output token maximum"). Distinguish from infra rate-limits by checking that the agent already did real work — wall time > a couple of minutes AND source files exist.
    - `model_timeout`: agent was actively working when killed by the 24h backstop or a local timeout. Note whether source files exist and whether they build.
    - `model_context_exhausted`: agent hit context-window limits; note how far it got.
    - `model_no_code`: agent completed voluntarily but never wrote source files. Check whether it only planned or analyzed; flag as a false-completion if it claimed it shipped code.
    - `model_build_failure`: agent wrote source but it does not compile.
    - `model_agent_error`: agent crashed or threw an unhandled exception.
  - **Infrastructure-side failures (prefix `infra_*`)** — the agent never got to do meaningful work because of an environment or API issue. Score does not measure model capability. **Excluded** from Best/Mean and flagged for rerun. Sub-buckets:
    - `infra_auth`: 401/403 errors or expired credentials; agent never started real work. Distinguish from `model_capped` by checking that the agent fast-failed (wall time under a minute, no source files written).
    - `infra_rate_limit`: 429s or quota exhaustion encountered before any work happened. Same fast-fail signature as `infra_auth`.
    - `infra_other`: server errors, capacity errors, container startup crashes, or any other host/network issue not attributable to the model.
- The line between `model_capped` and `infra_rate_limit` is wall-time + artifact presence. A "you've hit your limit" message at 5 seconds with no source files is `infra_rate_limit`. The same message at 50 minutes with 4,000 LOC of working code is `model_capped`.
- Record the bucket in `metadata.exit_class` and a brief prose explanation in `metadata.notes` (or report explicitly if the file is already finalized).
- For every run that scores above zero, confirm from the transcript whether the agent acknowledged it was done, voluntarily exited, was still working when killed, asked for input but got none, or hit an error/rate limit partway through.

## Reporting rules

- Every results report must include the language/task variant, the failure-mode bucket for every non-`completed` run, whether any included non-`completed` runs may have scored higher with more wall time, and any infrastructure-side failures requiring reruns.
- A run is **included** in official per-run tables and Best/Mean calculations if its `exit_class` is `completed` or starts with `model_*` AND `test_summary.total > 0` (tests actually ran). All other runs — anything `infra_*`, plus model-side runs where pytest never collected — are excluded and listed in a separate "Excluded runs" section.
- Annotate every included non-`completed` run inline (e.g. `0.747†` with a footnote: "agent hit `model_capped` at 3,076s; submission scorable"). The point is to make the reader see at a glance which numbers came from clean runs and which came from runs cut short.
- If a cell has zero included runs, show `- | -` for Best and Mean and explain the failure in the Status column.
- The model preparing or publishing the results is responsible for the Last Message summary: read the full `metadata.agent_last_message`, compare it against the run outcome and artifacts, and write a concise editorial summary instead of copying the first sentence.
- Do not include file counts or LOC in the Last Message summary unless they are needed to explain a contradiction, false completion claim, or other anomaly; the per-run table reports those fields separately.
- Surface these signals when present:
  - claims complete
  - incomplete and acknowledged
  - incomplete and asked to continue
  - incomplete but not acknowledged
  - asked a clarifying question
- `acknowledged` and `asked to continue` are not mutually exclusive; report both when both appear.
- Flag false completion claims explicitly. Example: if the message says the simulator is working but the run produced 0 files or only stubs, say so.

## Publishing rules

- Pass the bucket through to `clispecbench publish` so the dashboard surfaces it. Use these editorial `--status` labels:
  - `completed` → `--status "Complete"` (or `"Incomplete"` if the agent acknowledged gaps)
  - `model_capped` → `--status "Capped (model)"`
  - `model_timeout` → `--status "Timeout"`
  - `model_context_exhausted` → `--status "Context exhausted"`
  - `model_no_code` → `--status "No code written"`
  - `model_build_failure` → `--status "Build failure"`
  - `model_agent_error` → `--status "Agent error"`
- Do **not** publish `infra_*` runs. They contain no model-capability signal; rerun them instead.
- When publishing a `model_capped` or `model_timeout` run, include a Last Message summary that explicitly notes the cap/timeout and the wall-time at which it tripped, so the dashboard reader knows the agent was cut short and didn't choose to stop.
