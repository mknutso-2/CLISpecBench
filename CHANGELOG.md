# Harness Changelog

This file records changes to the `clispecbench` harness that can change how an
agent run behaves. Each result stamps the version in `metadata.harness_version`.
Eval prompt, doc and test changes belong in each eval's `Evals/<Task>/CHANGELOG.md`.

## v0.2.3 — 2026-10-29

- The API-only egress proxy writes a JSON `error` record when a connection
  fails mid-request (for example, a reset by the client). It used to print a
  Python traceback, which landed in `network-audit.jsonl` and broke readers
  that parse every line. The audit now holds only the proxy's stdout.
  Allow/deny decisions are unchanged.

## v0.2.2 — 2026-10-27

- Claude Code's refusal fallback is disabled. When the API flagged a request
  under a safety category, the CLI retried it on another model
  (`claude-opus-4-8` for the cyber category) and stayed there. That broke
  same-model delegation. A flagged request now ends as a refusal on the run's
  own model.

## v0.2.1 — 2026-10-21

- Claude Code's built-in helper model, which summarizes `WebFetch` pages and
  runs `WebSearch`, now uses the run's own model. It defaulted to Haiku 4.5,
  which broke same-model delegation for runs that used the web tools.

## v0.2.0 — 2026-10-17

- Claude Code no longer offers `ScheduleWakeup`, `CronCreate`, `CronDelete` or
  `CronList`. In headless runs the promised wake-up never comes, so the CLI
  exited and killed background subagents mid-task.
- Claude Code no longer offers `RemoteTrigger`, which creates scheduled cloud
  agents on the operator's account, outside the container and the run.
- Claude Code's agent shell keeps the image `PATH` across `su`. Before, Rust
  tasks started without `/usr/local/cargo/bin` on `PATH`.
- `--secret-env` passes secrets such as `CLAUDE_CODE_OAUTH_TOKEN` from the
  environment without putting them on the command line. A token in the
  container environment replaces the mounted `.credentials.json`.

See `docs/operations/Agent-Run-Notes.md` for affected runs.

## v0.1.0

- Baseline harness version for all results collected before 2026-10-17.
