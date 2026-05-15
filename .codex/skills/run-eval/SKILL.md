---
name: run-eval
description: Run and analyze CLISpecBench evals like WordCount, RS274, and IGES. Use when launching evals, detaching background runs, monitoring progress, inspecting transcripts and result JSON, classifying failures, or preparing official results tables and Last Message summaries.
---

Meta: This file is a breathing document. If you read it and find that any of the following documentation or guidance is out of date or you find a way to do any of the following in a strictly better or more efficient way, please update it.

# Run eval

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
- Gemini CLI headless runs must bypass the workspace trust prompt (`--skip-trust`, currently handled by the adapter). If Gemini exits immediately with "not running in a trusted directory", treat those results as operator/environment failures and rerun after fixing the adapter or smoke-test command.

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
- For every run that scores `0/N`, classify the root cause as one of:
  - `timeout`: the agent was still actively working when killed; note whether source files exist and whether they build.
  - `auth_failure`: 401/403 errors or expired credentials; the agent never started real work.
  - `rate_limit`: 429 errors or quota exhaustion from the model API.
  - `context_exhausted`: the agent hit context-window limits; note how far it got.
  - `no_code_written`: the agent completed voluntarily but never wrote source files; check whether it only planned or analyzed.
  - `build_failure`: the agent wrote source but it does not compile; capture the build diagnostics.
  - `agent_error`: the agent crashed or threw an unhandled exception.
  - `model_error`: the model API returned server or capacity errors unrelated to auth or rate limits.
- Use the `metadata.notes` field in the result JSON for root-cause observations when the file is still editable.
- Record the classification and a substantive explanation in `metadata.notes`, or report it explicitly if the result file is already finalized. The notes should be comprehensive enough to explain the submission's concrete shortcomings, the evidence supporting the diagnosis, and whether the failure reflects missing code, incomplete behavior, schema/contract mismatch, infrastructure, or another cause.
- For every run that scores above zero, confirm from the transcript whether the agent acknowledged it was done, voluntarily exited, was still working when killed, asked for input but got none, or hit an error/rate limit partway through.
- For unexpectedly low nonzero scores, use `metadata.notes` for a specific root-cause analysis. Call out whether the implementation was substantial or incomplete, identify the dominant failure class, and include concrete evidence from both the test report and source. Good example:
  `Unexpected low score root cause: The run was completed voluntarily and produced a substantial C++ implementation (~3K nonblank LOC, 10 published files) that built successfully, but it failed the eval largely because its observable JSON contract did not match the test suite. It emitted axis values as arrays instead of {x,y,z,a,b,c} objects, used g_modal/m_modal instead of active_modal_g_codes/active_modal_m_codes, used coord_system_offsets instead of coordinate_system_offsets, emitted lowercase spindle directions, and omitted the required top-level error string on failing inputs. These schema issues alone caused broad failures across position tracking, modal state, output schema, error, and trace suites. Additional semantic gaps were incomplete cutter-radius compensation (CRC arcs explicitly unsupported and corner lookahead skipped), trace entries using source_line/position instead of line_number/machine_position with missing top-level trace error fields, weak invalid-input validation (duplicate A/B/C accepted, noninteger D/H rounded, negative spindle speed accepted, some invalid TLO/tool/G53/linear-motion cases accepted), missing canned-cycle P/negative-P checks, simplified probing behavior, and parameter output that only wrote nonzero params instead of the required parameter set. The agent's final 'fully functional' claim is therefore grossly overstated, but the failure is not no_code_written or near-empty code; it is a substantial implementation with major public-contract and edge-case completeness failures.`

## Reporting rules

- Every results report must include the language/task variant, the root cause for every zero-score run, whether any non-zero timed-out runs may have scored higher, and any infrastructure issues requiring reruns.
- Only runs with `exit_reason: "completed"` belong in official per-run tables and Best/Mean calculations. Timed-out, errored, or rate-limited runs are excluded from those tables and called out separately.
- Do not publish runs whose failure or early termination was caused by user/environment issues rather than the model or harness. Omit runs stopped by account/usage limits, expired or missing credentials, local network or stream disconnects, local machine interruptions, or other operator/environment failures. These runs can be reported as omitted with the concrete stop reason, but they should not appear in `published_results`.
- Model-side limits or model/harness behavior can be publishable when they are the thing being measured: for example model context-window exhaustion, model output-token caps, adapter/model API errors, or harness timeouts. If the root cause is ambiguous, inspect the transcript and event logs before publishing.
- If a model has zero completed runs, show `- | -` for Best and Mean and explain the failure in the Status column.
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
