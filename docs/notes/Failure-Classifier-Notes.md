# Failure-Mode Classifier — Current State and Open Questions

Notes from a 2026-05-01 investigation into how the harness classifies the
end-state of an agent run (cap-hit, auth-failure, finished, etc.) and which
parts of the system act on that classification. Captures the current
architecture, identified gaps, and proposals that were considered but not
landed.

## Current state — three independent classifiers

Three places in the codebase classify run end-states. They share patterns
but each maintains its own taxonomy and runs at a different layer.

### 1. `src/clispecbench/harness/publish.py` — publish-time gate

- Function: `_unpublishable_stop_reason(source, result, status, last_message)`
- Buckets: `usage_limit | stream_disconnect | auth_failure | None`
- Used to **block** a result from being copied into `published_results/`.
- For codex runs, prefers structured signal: walks
  `transient_results/.../codex-events.jsonl` for the final
  `turn.failed.error.message` via `_final_codex_turn_failure_message()`.
- For non-codex runs, text-pattern over
  `agent_last_message + notes + status + last_message`.
- Result is not persisted anywhere — recomputed on every publish call.

### 2. `published_results/web/build_results_json.py` — dashboard data builder

- Function: `classify_agent_stop_message(message)` plus
  `codex_agent_stop()` and `agent_stop_info()`.
- Buckets (richer than #1):
  `finished | output_token_limit | context_window_exhausted | usage_limit | stream_disconnect | agent_turn_failed | unknown`
- Same structured-first / text-fallback pattern as `publish.py`.
- Emits **four fields per run** into `results-published.json`:
  `agent_stop_reason`, `agent_stop_label`, `agent_stop_message`,
  `agent_stop_source` (`codex-events` vs `result-json`).
- Read by the dashboard's "Agent Stop" column.

### 3. `metadata.exit_reason` on `result.json` — runner-level outcome

- Set in `harness/runner.py` from container exit signals.
- Values: `"completed" | "timeout" | "error" | "no_output"`.
- Crude — doesn't distinguish *why* the agent errored, just that it did.
- Persisted on every result file.

## Identified gaps

1. **Three classifiers, divergent taxonomies.** `publish.py` and
   `build_results_json.py` both pattern-match the same kinds of strings
   but track different bucket sets and don't share code. Risk: rules
   drift when new failure modes are added.
2. **No persistence on `result.json`.** The richer dashboard
   classification only reaches `published_results/web/results-published.json`.
   Anything else that wants to filter by failure mode (a markdown
   report, `clispecbench results`, ad-hoc Python over transient
   results, the `clispecbench results --breakdown` table) has to
   re-walk `codex-events.jsonl` and re-pattern-match.
3. **Best/Mean inclusion vs. publication gate are conflated.** The
   only place a "should this count" decision is encoded today is the
   publish/no-publish boolean. Conceptually these are two axes:
   - *Publication* — does the file appear in `published_results/`?
   - *Inclusion* — does its score count toward Best/Mean in a report
     of agent capability?
   They're related but not identical: a `model_capped` run with a
   real scorable submission might be publish-allowed but flagged
   in-table as `0.747†` rather than treated as a clean run.
4. **Two parallel SKILL.md files have drifted.** `.claude/skills/eval-runs/SKILL.md`
   and `.codex/skills/eval-runs/SKILL.md` describe different rules
   for what counts. The `.codex` version was updated 2026-05-01 to
   exclude account-usage-cap runs as environment failures; the
   `.claude` version still describes account-usage-cap runs as
   `model_capped` and includable. Whichever rule is canonical, the
   two files should be sync'd.

## Considered and rejected (this session)

A typed `metadata.exit_class` field with a unified classifier
(`harness/exit_class.py`), populated by the runner and backfillable
across historical results, was implemented and then reverted
(`baa5ada` → `6678e9f`). Reverted because it duplicated logic the
dashboard layer already does well, used a less-reliable text-only
signal extraction (no codex-events lookup), and disagreed with the
existing `publish.py` rule on the account-usage-cap case.

## What's worth doing later

These are observations, not commitments — sized roughly small to large.

- **Lift the dashboard's `classify_agent_stop_message` to a shared
  module** (e.g. `harness/agent_stop.py`) so `publish.py` and the
  dashboard call the same function. Single source of truth for
  pattern matching. Today there are two parallel implementations.
- **Sync `.claude/skills/eval-runs/SKILL.md` with
  `.codex/skills/eval-runs/SKILL.md`.** Pick one rule for what
  counts toward Best/Mean (most likely the `.codex` version's
  "exclude account/usage-cap as environment") and update both.
- **Optionally persist the dashboard's bucket on `result.json`** so
  non-dashboard consumers don't re-classify. Backfill via a new
  `clispecbench backfill-agent-stop` subcommand. Worth doing only
  if a non-dashboard consumer actually starts needing the data.
- **Distinguish account-usage-cap from per-message-output-token cap
  in the `usage_limit` bucket** — the latter is closer to model
  behavior ("the model emitted too much in one turn") and is
  arguably publishable per `.codex/skills/eval-runs/SKILL.md`,
  while the former is environment.
