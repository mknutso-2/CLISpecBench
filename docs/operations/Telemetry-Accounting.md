# Telemetry accounting and historical backfills

Result schema 2.3 preserves Codex reasoning-output and cache-write counts,
records the tool-count definition, lists retained telemetry artifacts, and
separates agent completion from grading completion.

## Token accounting

`reasoning_output_tokens` is a subset of `output_tokens`. Do not add it to
total tokens or cost. Explicit zero cache-read/write counts remain zero;
missing fields remain null. Codex `cache_write_input_tokens` maps to the
normalized `cache_creation_input_tokens` field.

The completed exec event supplies aggregate usage. If it omits a breakdown,
the parser may supplement it from session usage with matching input, output,
and cache-read totals. Session-only usage remains marked partial when the
agent has no completed-turn usage record. Historical absent reasoning counts
mean unknown, not zero.

## Tool calls

The field and display name remain `tool_calls` / Tool calls. Codex results
produced by the corrected parser have
`tool_calls_definition: "underlying_tool_invocations_v2"`.

Count each underlying command, patch, search, MCP or collaboration tool call
once, including calls that fail or start without completing. A patch editing
multiple files is one call. A shell command running several programs is one
call. Code-mode `exec` wrappers are not counted again. Item IDs deduplicate
the start/update/completion lifecycle. The stdout transcript and its tee log
are alternative records, not additive counts.

Plan updates have a special lifecycle: the first `todo_list` start and each
update represent plan-tool invocations; its automatic completion at turn end
does not. This follows Codex's JSONL event processor. Agent messages,
reasoning summaries, and error notifications are not tools. Unknown event
item types make the count unavailable rather than silently undercounting.

Before this correction, the Codex adapter counted only completed command
events. Missing definition markers identify those historical measurements.
Other adapters retain their existing provider-specific accounting; this
migration changes Codex results only.

## Preserved evidence and grading validity

Before grading starts, the runner saves source, stdout/stderr, network audit,
and extracted telemetry files **and directory trees**. All Codex session
shards are retained under the run's `sessions/` directory. Their relative
paths are recorded in `artifacts.telemetry`. Failed scorer attempts retain
their logs and any partial reports as separate attempt artifacts.

A valid grader run needs pytest exit 0 or 1 plus a complete, matching JSON
report. Ordinary failed tests (exit 1) still produce valid benchmark scores.
Interrupted runs, collection errors, timeouts, missing/malformed reports,
and exhausted retries do not. Every retry uses a new report directory to
prevent stale-report reuse.

`metadata.agent_exit_reason` records the agent outcome independently.
`metadata.grading_status` is `completed`, `failed`, or `not_started`;
historical records may omit it. Failed grading sets overall `exit_reason`
to `error`, `exit_class` to `infra_scoring`, and scores to null, retaining
the completed agent's usage and artifacts. Publishing and dashboard building
reject explicitly incomplete grading even if another field says completed.

## Backfill on the original machine

Run these commands from the repository root after updating the harness.
No model calls or regrading are performed.

Preview:

```bash
uv run clispecbench backfill-telemetry --runs-root transient_results --published-root published_results --report telemetry-preview.json
```

Apply and save an audit of old/new values:

```bash
uv run clispecbench backfill-telemetry --runs-root transient_results --published-root published_results --apply --report telemetry-applied.json
uv run clispecbench rebuild-dashboard
```

The command matches original `result.json` and published `run*.json` files
by `run_uid`, validating identifying metadata and core token totals. It
preserves scores, costs, editorial fields, and original run metadata. It
updates tool counts and any evidenced reasoning/zero-cache details; recovered
nonzero cache counts requiring cost reconciliation are not changed by this
migration. Run it again to verify `unchanged` entries.

Missing transcripts, unsupported items, duplicate identities, and mismatched
results are reported as skipped. The command does not guess counts from
generated source files. For Codex command/file/search counts, the ordinary
`transcript.jsonl` or `codex-events.jsonl` is sufficient. The richer session
is useful for older streams missing token breakdowns.

Reference: [Codex non-interactive JSON events](https://developers.openai.com/codex/noninteractive)
and the official [JSONL event processor](https://github.com/openai/codex/blob/main/codex-rs/exec/src/event_processor_with_jsonl_output.rs).
