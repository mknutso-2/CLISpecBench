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
generated source files. Exact Codex tool counts require the canonical event log and preserved sessions.
The session records can expose rejected requests omitted from canonical items;
an event log alone supplies only the canonical baseline.

Reference: [Codex non-interactive JSON events](https://developers.openai.com/codex/noninteractive)
and the official [JSONL event processor](https://github.com/openai/codex/blob/main/codex-rs/exec/src/event_processor_with_jsonl_output.rs).

## September 12, 2026: requests rejected before canonical items

CLI 0.153.4 can emit a runtime `exec_command` rejection inside `functions.exec`
without creating a `command_execution` item. Such attempts already belong to
`underlying_tool_invocations_v2`; this corrects its implementation, not its meaning.
The adapter now pairs preserved session requests and runtime outputs by call ID,
deduplicates identical evidence, and supplements only a single proven attempted
call absent from canonical command items. It never counts JavaScript call sites
as runtime invocations. Printed error text from successful scripts is not evidence.

The bundled syntax inspector parses a narrow direct-awaited-call form with Node's
Acorn parser; it never evaluates generated JavaScript. Node with its bundled Acorn
(currently verified with Node 22) must be available on the **host** for these rare
failed-wrapper checks. The inspector is included in the Python package, has a
five-second timeout, and degrades to unavailable if missing or unsupported.
Unpaired requests, conflicting duplicates, ambiguous failed wrappers, missing
sessions, and possible canonical overlap yield null `tool_calls` and null
`tool_calls_definition`. Token totals, reasoning counts, cost, and `is_partial`
remain independent. A syntax rejection counts zero only when parsing independently
confirms that the whole script could not start.

The backfill command reports uncertain cases as skipped instead of assigning an
exact count. For the September non-RS274 cohort, separate publication audits retain
original result hashes, original usage, complete prior publication bytes, and
per-request evidence; raw generation results and prior regrade records remain
unchanged. Unknown tool metrics do not invalidate a completed correctness score.

## September 17, 2026: rejected patch requests

The same conservative recovery now covers `apply_patch` verification failures
that report "Failed to find expected lines" in a failed runtime wrapper without
creating a canonical `file_change` item. The static inspector accepts one directly
awaited patch call with a literal string, optionally stored first in a `const`.
It rejects computed arguments, control flow, multiple calls, and shadowed bindings.
Successful stdout containing error-like text is not rejection evidence.

A patch supplement is unavailable if any canonical file-change item is failed,
in progress, or lacks a completed status: those items do not carry enough request
identity to rule out overlap. An accepted supplement records the patch SHA-256 and
the preserved request/output locations. Identical duplicated evidence counts once.
All outputs are compared by call ID before failure classification: conflicting
successful or unclassified outputs also make the count unavailable.

The Sol Max LAS JavaScript run `2afb5142-8c8a-4e36-b7a9-323a7116324b` exposed
this case: 62 canonical tool items plus one proven rejected patch give 63 tool
calls. Its original null metric remains in the immutable raw result; publication
correction evidence records the recovered count separately. This implements the
existing `underlying_tool_invocations_v2` definition. Token totals, reasoning
tokens, estimated cost, and correctness score are unaffected.

Validation: 188 relevant harness tests and 20 subtests pass, including twelve
success/unclassified-output conflict cases across patch, process and syntax
rejections in both orders. Identical session copies remain count-once. Ruff,
strict Pyright and Node syntax checks pass. The actual preserved LAS evidence
contains one request and one failed output for the recovered patch call ID.

## September 22, 2026: duplicate-target patch rejections

The runtime can also reject a single patch with `invalid patch: multiple
operations target ...` before creating a canonical file-change item. This
diagnostic now follows the same conservative recovery path. Two operations in
one rejected patch count as one attempted tool call. The accepted wrapper
syntax, runtime-envelope requirement, deduplication and canonical-overlap
guards are unchanged; no generated JavaScript is executed.

Sol Max ICal Rust run `0ca96516-ffc9-44c0-a15b-56718bae72c7` exposed this case.
Its 185 canonical actions (105 commands and 80 file changes) plus three proven
rejected patches give **188 tool calls**. A separate malformed wrapper is
confirmed by syntax parsing to have failed before execution and adds zero.
The raw unavailable count and the complete initial publication remain in the
linked correction audit; token totals, reasoning, costs and scores are unchanged.

The new regression fails on the prior detector and passes after this narrow
change. Relevant rejection/telemetry tests pass **71 tests and 42 subtests**,
including duplicate evidence, overlapping failed/incomplete canonical patches,
printed error text, unrecognized diagnostics, multi-call/loop wrappers and a
mismatched tool. Independent session census and static review confirm the
count and the unchanged uncertainty guards. This is an accounting correction
under the existing v2 definition; no eval version, test suite or model input changes.

## September 22, 2026: exit-code display after a rejected command

The narrow wrapper parser now accepts exactly `` text(`exit=${r.exit_code}`) ``,
where `r` is the existing result binding of one directly awaited `exec_command`.
This untagged template display adds no invocation.
Arbitrary interpolation, calls, computed access, getters, changed bindings and
control flow remain unsupported; runtime rejection and canonical-overlap checks
still determine whether the attempted command can be counted. JavaScript is
parsed as data, never executed.

Sol Max ICal Python retry `01d6a652-c853-4e4c-82e6-675c1624cbe6` has 229
canonical actions and one explicitly rejected command with this suffix, yielding
230 tool calls under the unchanged v2 definition. Its raw null metric is preserved;
any published correction must retain the recomputed audit and leave all token,
reasoning, cost and correctness fields unchanged.
