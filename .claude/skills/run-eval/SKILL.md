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
- Claude Desktop sign-in does not guarantee headless `claude --print` eval auth. Refresh Claude Code CLI credentials on Windows with `/login` or `claude auth login`, then run `scripts/smoke-test-claude.sh`. For long unattended queues, `claude setup-token` can generate a one-year `CLAUDE_CODE_OAUTH_TOKEN`; use it only if the launcher can keep the token out of logs/history.

Example:

```bash
DOCKER_HOST=tcp://localhost:2375 uv run clispecbench run --task rs274-cpp --agent codex-cli --model gpt-5.2-codex --effort xhigh --runs 3
```

- On this Windows host, do not background evals via `Start-Process powershell ...`; use a hidden `cmd.exe` wrapper instead.
- Tested detached launcher pattern on this host:

```powershell
Start-Process cmd.exe -WindowStyle Hidden -ArgumentList '/d','/c','cd /d C:\Git\CLISpecBench && set DOCKER_HOST=tcp://localhost:2375 && uv run clispecbench run --task <task> --agent <agent> --model <model> [optional flags] 1>"<out.log>" 2>"<err.log>"'
```

- Do not rely on raw `docker` from PowerShell on this host; the harness uses the Python Docker SDK.

## Post-run inspection

- After every eval run completes, inspect the result JSON and `transcript.jsonl` before moving on. Do not batch review later.
- Use the `metadata.notes` field in the result JSON for root-cause observations when the file is still editable.
- For every run, classify the **failure-mode bucket** for `metadata.exit_class`. The bucket determines whether the run counts toward Best/Mean (see Reporting rules). Two top-level groups:
  - **`completed`** — the agent ran to its own self-terminated end. Score reflects what the agent built. Always included.
  - **Model-side failures (prefix `model_*`)** — the run produced a real, scorable submission but the agent CLI exited via something other than its own completion path. Score still reflects model behavior. **Included** in Best/Mean unless the submission was empty/stub. Sub-buckets:
    - `model_timeout`: agent was actively working when killed by the 24h backstop or a local timeout. Note whether source files exist and whether they build.
    - `model_context_exhausted`: agent hit context-window limits; note how far it got.
    - `model_no_code`: agent completed voluntarily but never wrote source files. Check whether it only planned or analyzed; flag as a false-completion if it claimed it shipped code.
    - `model_build_failure`: agent wrote source but it does not compile.
    - `model_agent_error`: agent crashed or threw an unhandled exception.
    - `model_output_cap`: agent's session ended because a single model response exceeded the per-message output-token ceiling. Diagnostic signal: `agent_last_message` contains "Claude's response exceeded the NNN output token maximum" (or `CLAUDE_CODE_MAX_OUTPUT_TOKENS` text). **Distinct from `infra_usage_cap`** — this is a model-behavior signal (the agent chose to emit a single huge response instead of chunking or stopping); the user's billing tier has nothing to do with it. Kept and included. NOTE: the claude-code adapter now sets `CLAUDE_CODE_MAX_OUTPUT_TOKENS=1000000` (the CLI clamps to each model's true max), removing the CLI's default 32k truncation — so this bucket should now be rare for claude-code. It was introduced because Opus 4.8 at `--effort max` hit the old 32k default on every run (dying mid-task with stub submissions). If you still see it, the model genuinely emitted a single response exceeding its own max output.
  - **User/environment failures (prefix `infra_*`)** — the run was cut off by something outside the model's control. Score does not measure model capability. **Always excluded** from Best/Mean and flagged for rerun, with **no exceptions for high scores or long wall-times** — the agent didn't get a fair chance to finish, so the result is not a model-capability data point. Sub-buckets:
    - `infra_usage_cap`: agent hit an Anthropic/operator-side usage cap, daily quota, or session limit. Diagnostic signal: `agent_last_message` contains "you've hit your limit" / "resets at X" / similar cap-reset text, OR the agent CLI exited 1 mid-session after long wall-time with no completion claim. **This bucket replaces the old `model_capped`. Even if the agent ran for 30 min, produced a working build, and scored 0.85, this is still scrapped** — the cap belongs to the operator's billing tier, not the model, and recording it would inflate the model's failure rate with non-model signal.
    - `infra_auth`: 401/403 errors or expired credentials; agent never started real work. Fast-fail signature (wall under a minute, no source files written).
    - `infra_rate_limit`: 429s or platform-side quota exhaustion encountered before any work happened. Same fast-fail signature as `infra_auth`.
    - `infra_other`: server errors, capacity errors, container startup crashes, or any other host/network issue not attributable to the model.
- **How to distinguish a usage cap from anything else**: the agent CLI's "you've hit your limit" string is definitive for `infra_usage_cap` (account billing, scrap) — read `metadata.agent_last_message`. The string `"Claude's response exceeded the 32000 output token maximum"` is `model_output_cap` (model behavior, keep) and must not be confused with the billing cap. Account-cap messages reference a reset time ("resets 5:30pm UTC"); the output-cap message references the `CLAUDE_CODE_MAX_OUTPUT_TOKENS` env var.
- **Mid-session infra failures are NOT model signal even when partial scores look real.** An `infra_*` classification is independent of wall-time, tool-call count, or partial test score. If the agent ran 17 minutes, made 14 tool calls, and the harness extracted a submission scoring 89/220 — but the agent's last message is `"Failed to authenticate. API Error: 401 ..."` or `"API Error: Unable to connect to API (ConnectionRefused)"` — the score reflects WHEN the operator's token expired or the network blipped, not what the model could do. Scrap and rerun. The publish CLI's stoplist (`publish._classify_unpublishable_stop_message`) catches the known signatures; when a new mid-session infra signature appears, add it there so it can't be hand-published by mistake.
- **Silent model fallback (served ≠ requested).** The agent CLI can accept a `--model` it doesn't recognize and *silently* run its default model instead — no warning, no error, exit 0. This happened with the pinned claude-code CLI (2.1.120) and the deprecated 4.0 snapshots: requesting `claude-opus-4-20250514`/`claude-sonnet-4-20250514`/`claude-opus-4-1-20250805` was served `claude-opus-4-7`, producing ~86% scores that matched Opus 4.7, not the older model. **The harness guards this:** the runner records `metadata.served_model` from the transcript's `system/init` event and, on a positive mismatch with the requested model, forces `exit_reason="error"` and writes a `MODEL MISMATCH` note; `publish_result` hard-refuses to publish any run where `served_model` is incompatible with `model` (see `results.models_compatible`). Aliases resolving to their dated snapshot (e.g. `claude-opus-4-5` → `claude-opus-4-5-20251101`) are compatible.
- **CLI generations under one `claude-code` agent.** Rather than a separate agent id, `claude-code` spans multiple pinned CLI images via a *variant* (`src/clispecbench/agents/claude_code.py`): the default (2.1.120), a `legacy` (2.0.2) image that still serves the 4.0-gen snapshots, and a `fable` (2.1.174) image for Fable-family models — 2.1.120 predates Fable 5 and reproducibly dies on its long sessions (auto-compact fails on an internal 20k compact-summary cap that `CLAUDE_CODE_MAX_OUTPUT_TOKENS` does not govern, then every call errors "Prompt is too long" with no output written; see `docs/operations/Agent-Run-Notes.md`). The variant is chosen by `--cli-version` (`default`/`legacy`/`fable` or a version string) or, by default, **auto-routed by model** — the snapshots in `_LEGACY_MODELS` go to the legacy image and `claude-fable*` models to the fable image automatically. The fable variant also sets `API_TIMEOUT_MS=1800000` — Fable's 128k-token messages can legitimately stream for 20+ minutes, and the CLI's default request timeout killed an otherwise-healthy run. The CLI version is recorded in `metadata.agent_version` (2.0.2 vs 2.1.120) and surfaced on the dashboard (`CC 2.0.2 / O-4.0` vs `CC 2.1.120 / O-4.6`), so there is no `claude-code-legacy` agent name. The legacy variant omits `--effort` (absent in 2.0.x) and sets `MAX_THINKING_TOKENS=31999` as its max-reasoning setting, and disables OTEL (token/cost come from the stream-json result event). To collect a new deprecated model, add its id to `_LEGACY_MODELS`; the served-model guard backstops a wrong mapping. Legacy 4.0-gen queues: `scripts/_queue-legacy-rs274.sh` (`MODEL=… LABEL=… [SKIP=N]`).
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

- Pass the bucket through to `clispecbench publish` so the dashboard surfaces it. The canonical list of valid `--status` labels lives in `src/clispecbench/harness/status.py` (`VALID_STATUSES`); the publish CLI rejects anything not in that set and auto-populates `metadata.exit_class` from `STATUS_TO_EXIT_CLASS`. The current mapping is:
  - `completed` → `--status "Complete"` (or `"Incomplete"` if the agent acknowledged gaps)
  - `model_timeout` → `--status "Timeout"`
  - `model_context_exhausted` → `--status "Context exhausted"`
  - `model_no_code` → `--status "No code written"`
  - `model_build_failure` → `--status "Build failure"`
  - `model_agent_error` → `--status "Agent error"`
  - `model_output_cap` → `--status "Output cap"`
- Deprecated labels (e.g. `"Capped (model)"` from before the model_capped → infra_usage_cap + model_output_cap split) are rejected with a migration hint. See `DEPRECATED_STATUS_REPLACEMENTS` for the mapping.
- Do **not** publish `infra_*` runs — including `infra_usage_cap`. They contain no model-capability signal; delete the transient artifacts and rerun. This applies even when the agent did substantial work before the cap tripped: a capped run is the operator's billing tier showing up in the data, not the model, and publishing it would mislabel an operator failure as a model failure. The cap-hit transient (`result.json`, `transcript.jsonl`, `source/`) should be removed before relaunch so the harness doesn't accumulate stale eval directories.
- When publishing a `model_timeout` run, include a Last Message summary that explicitly notes the timeout and the wall-time at which it tripped, so the dashboard reader knows the agent was cut short and didn't choose to stop.
- The dashboard reads `published_results/web/results-published.json` and `published_results/web/test-results-published.json`, which are *not* updated by `clispecbench publish` itself. After publishing, regenerate them or the dashboard will silently drift behind the published files. Two ways:
  - One-shot publish: pass `--rebuild-dashboard` to `clispecbench publish` and the rebuild runs immediately.
  - Batch publish (multiple results in a row): omit the flag on each publish and run `clispecbench rebuild-dashboard` once after the whole batch — the rebuild walks every published file, so doing it per-publish is wasteful.
- Commit both `results-published.json` and `test-results-published.json` alongside the new `runN.json` files. They're regenerated artifacts but checked in so consumers don't have to rebuild before opening the dashboard.
