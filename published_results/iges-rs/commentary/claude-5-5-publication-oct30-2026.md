# Reviewed Claude 5.5 collection, October 13-29, 2026 — iges-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `66685fbc-b089-4105-b82a-b4c127e91484`

- Score 248/249; status Complete.
- Failures: 1: zero-count Hollerith after a defaulted string control should be rejected (same as the other three languages).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `a14d5971-6f22-456d-a3e1-c634c4414138`

- Score 246/249; status Incomplete.
- Failures: 3: zero-count Hollerith after defaulted string control (1), spline surface write should include boundary/patch slots (1), empty start_lines should produce at least one blank Start record (1).
- Network: curl'd https://sh.rustup.rs to reinstall a Rust toolchain because cargo was not on the agent's PATH (see environment note); the install partially failed on permissions under /usr/local/rustup.
- ScheduleWakeup trap: called ScheduleWakeup and ended its turn while a same-model review subagent ran; the CLI killed the subagent (sequence ScheduleWakeup > killed > RESULT) and its findings were never processed.

### Sonnet 5.5 max — `7a5e92db-59a6-4a08-8744-1ab5ddaba394`

- Score 248/249; status Incomplete.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control (the same single failure as every Sonnet IGES high and max run).
- Network: Fetched public IGES sample files and reference material by curl (14 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness artifact, a variant of the ScheduleWakeup trap: in headless --print mode a turn that ends while a background Agent subagent is still running can end the session, and the CLI stops the subagent. The 0.2.0 tool block does not cover this; the agent used Agent with background execution, not ScheduleWakeup.
- Harness 0.2.1 conditions; cargo on PATH (28 invocations, none not found); one same-model subagent; modelUsage only claude-sonnet-5-5.
- The score equals every other Sonnet IGES run, so the cut-off pending refinements likely would not have changed it, but the run did not finish on its own terms.

### Opus 5.5 max — `bd41d708-7275-42d4-9fc7-57e984c6788a`

- Score 248/249; status not published.
- Not published: held: CLI refusal fallback served part of the run on claude-opus-4-8; the 0.2.2 rerun is published.
- Failures: 1: zero-count Hollerith should be rejected after a defaulted string control. Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- A background general-purpose subagent 'Fuzz binary for crashes' made 213 Opus 5.5 responses, then the CLI refusal fallback (cyber category -> claude-opus-4-8) moved it to Opus 4.8 for 25 responses. No refusal stop reason or system event marks the switch; only message.model changes.
- Fixed in harness 0.2.2 (CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1). User chose: let it finish, hold, rerun once at the end of the queue, keeping both attempts.
- 8 result events: the main agent was re-invoked by task notifications before the final stop.
- 2 above Opus IGES Rust high (246/249, itself Incomplete from a background stop).

### Sonnet 5.5 max (rerun) — `5055bc2b-b3d8-4788-8af1-dcae75c569d7`

- Score 248/249; status Complete.
- Failures: 1: test_data_types.py::test_zero_count_hollerith_is_rejected_after_defaulted_string_control. Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- Rerun of sonnet-iges-rs-max (Incomplete, background subagent stopped) under the 2026-10-24 'Keep, rerun at end' decision; both attempts kept. Same score as the first attempt.
- Harness 0.2.2 conditions. Two same-model subagents (spec-vs-code review and contract conformance review); modelUsage only claude-sonnet-5-5. The agent polled with ListAgents (15 calls) and used SendMessage once while waiting, so it never ended its turn with a subagent running: all 39 task notifications completed, none stopped. 1 result event.
- Two tool calls named lowercase 'bash' came from a subagent; they are harmless tool-name errors.
- cargo was available and used (16 cargo commands).

### Opus 5.5 max (rerun) — `07420fab-c75a-4be9-9272-c298b6c3c2a1`

- Score 248/249; status Complete.
- Failures: 1: test_data_types.py::test_zero_count_hollerith_is_rejected_after_defaulted_string_control, the same single failure as the other Claude 5.5 IGES runs. Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- Rerun of opus-iges-rs-max (248/249, held for the cross-model refusal fallback and Incomplete) under the 2026-10-27 decision to rerun it at the end; both attempts kept. Same score as the first attempt.
- Harness 0.2.2 conditions with the refusal fallback disabled; one background same-model review subagent; stream, native and modelUsage all claude-opus-5-5 only; no refusal stop_reason.
- The review subagent completed (task notification completed) and its findings were applied before the final summary. 37 task notifications completed; 1 stopped: a leftover Monitor ('wait for review agent activity/completion') cut off at session end after all work was done, not a background subagent.
- cargo was available and used (22 cargo commands).
