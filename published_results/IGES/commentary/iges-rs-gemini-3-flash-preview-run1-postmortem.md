# Postmortem: `iges-rs` run 1 on gemini-cli / gemini-3-flash-preview

**Score:** 0/258 (0.0%) — `build_failure`.
**Session:** 2026-04-18 21:19:06Z → 21:34:27Z (15 min 21 s).
**Container exit:** `exit_code=0`, `timed_out=False`, `wall=927.5s` — clean exit from the harness's perspective.
**Session envelope:** `type: result, status: "success"` — clean exit from gemini-cli's perspective.

Despite two `status: success` signals, the agent produced a single 510-line `src/main.rs` that never compiled, and its last assistant message was a forward-looking plan rather than a completion claim. This page reconstructs what actually happened and assigns root cause.

Back-link: [`results.md`](../results.md) · [related sub-10% commentary](iges-gemini-3-flash-preview-sub-10pct.md) · [related high-scorer commentary](iges-gemini-3-flash-preview-high-scorers.md).

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 21:19:06 | Session starts. 510-entry transcript begins. |
| 21:19:49 | **Rate-limit hiccup**: gemini-cli stderr emits `Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 0s. Retrying after 5416ms...`. Retry succeeds; no further rate-limit events in the run. |
| 21:20:14 | Agent calls `enter_plan_mode` with reason *"Implementing a complete IGES 5.3 parser, writer, and evaluator is a complex task involving 87 entity types... I need to design the architecture and strategy before..."* Self-imposed, not policy-imposed. |
| 21:20:26 | Agent tries `write_file` on `output/src/main.rs` → policy-denied: `"You are in Plan Mode and cannot modify source code. You may ONLY use write_file or replace to save plans to the designated plans directory as .md files."` Four such denials in quick succession. |
| 21:20:33 | Agent calls `exit_plan_mode` after realizing its own plan-mode entry was blocking it from writing code. |
| 21:25:16 | `[LocalAgentExecutor] Blocked call: Unauthorized tool call: 'generalist' is not available to this agent.` The model tries to delegate entity-table work to gemini-cli's `generalist` sub-agent; the CLI's recursion guard (`"Skipping subagent tool 'generalist' for agent 'generalist' to prevent recursion"`) blocks it. Agent comments in the next message: *"I'll check the current main.rs file and continue implementing the remaining entities that the 'generalist' didn't finish."* |
| 21:31:37 | **First `cargo build`** (12.5 min into the session). Fails: `error: 5 positional arguments in format string, but there are 4 arguments → src/main.rs:98:30`. |
| 21:32:29 | Agent rewrites `main.rs` (rewrite #1 after build failure). |
| 21:33:23 | Agent rewrites `main.rs` (rewrite #2, same file). |
| 21:34:16 | Agent rewrites `main.rs` (rewrite #3, same file). Never attempts another `cargo build`. |
| 21:34:16.472 | `tool_result: success` for rewrite #3. |
| 21:34:27.829 | **`type: result, status: success`**. Session ends. Eleven seconds of silence between the final tool_result and the session-end envelope, with no model output in between. |

## What terminated the session?

Between the final `tool_result` (21:34:16.472) and the `result` envelope (21:34:27.829) there's an 11-second gap and **zero transcript entries**:

- No streamed assistant text.
- No new tool_use.
- No stderr line (no rate-limit retry, no error).
- No `stop_reason` field in the `result` envelope — gemini-cli doesn't record one.

The harness sees a container that exited cleanly with `exit_code=0`. The CLI reports `status: "success"`. So whatever made gemini-cli stop, it considered the stop normal.

The most plausible interpretation is that **the model returned a response with no content and no tool_use**, which gemini-cli treats as "agent is done" and shuts down the session. That matches the 11-second latency (one more API round-trip), the absence of any visible output, and the lack of an error path in either the CLI or the harness. It is inference from circumstantial evidence, not a confirmed fact — the transcript has no direct signal.

Alternative explanations that don't fit:

- **Harness timeout**: none. The harness has no time cap, only a 24-hour safety backstop for hung containers. Container wall was 927.5 s.
- **Rate-limit kill**: the only rate-limit event (21:19:49) was handled by gemini-cli's retry loop 14 minutes before the session ended.
- **gemini-cli turn cap**: no fixed cap exists — other runs in the same sweep reach 132 (rs r3) and 166 (cpp r1) tool calls. rs r1 stopped at 73.
- **Context-window exhaustion**: 8.34M input tokens total but 6.08M of that is cached; non-cached input is 2.25M spread across 73 calls (~31K/call average). gemini-3-flash-preview's 1M context window would see ~31K fresh tokens per request — well under the ceiling.

## Contributing factors

Even if the proximate cause is "model emitted an empty response," the session had accumulated problems that plausibly led the model to that state:

1. **Self-imposed plan mode.** The agent voluntarily entered plan mode at 21:20:14, then spent ~20 seconds and four denied `write_file` calls realizing this had blocked its own editing. It exited plan mode correctly, but the episode produced confused reasoning about file paths (*"must save my implementation plan to the designated directory: `/root/.gemini/tmp/workspace/78ab315c-...`"*) that appears nowhere else in the sweep.
2. **`generalist` sub-agent blocked.** The model repeatedly attempted to delegate entity-table implementation work to gemini-cli's built-in `generalist` sub-agent. Every call was blocked by the CLI's recursion guard. rs r1 has **10** `LocalAgentExecutor` blocks, including an explicit `Unauthorized tool call` event; rs r2 has 13 blocks but also 7 successful `cargo build` iterations and a sibling file layout, suggesting r2's model activity was less dependent on delegation. The rs r1 model plainly expected `generalist` to finish entity variants (*"continue implementing the remaining entities that the 'generalist' didn't finish"*) and never got that help.
3. **No build feedback between rewrites.** After the first (and only) `cargo build` failed at 21:31:37, the model issued three full rewrites of `main.rs` in the next 2 min 39 s with no intervening build. With no new compile error to react to, each rewrite was blind.
4. **Monolithic file layout.** rs r2 and rs r3 both produced 8-file modular trees (parser / writer / entities / eval / json_parser / model / error / main), with `entities.rs` reaching 2408 lines and `eval.rs` reaching 696. rs r1 never got past a single 510-line `main.rs`, so any rewrite had to be the whole file.

## Root cause and classification

- **Not a harness bug.** The harness faithfully recorded the container's exit. No harness-level retry, timeout, or kill was involved.
- **Not a clear gemini-cli bug.** Every policy block observed (Plan Mode, `generalist` recursion guard) is intentional. The rate-limit retry worked. Interpreting an empty model response as end-of-session is a reasonable default for a CLI that does not expose a "finish" tool to the agent.
- **Most defensibly an agent-stuck run.** gemini-3-flash-preview self-entered plan mode it didn't need, repeatedly tried an unavailable sub-agent, thrashed on a single file without running the compiler, and then emitted a response the CLI read as "done." The same model on the same prompt produced 0.527 and 0.589 in the two other runs in this eval, so the failure mode is run-level, not a capability ceiling.

Suggested exit classification: **`agent_error`** — specifically an "agent got stuck" variant. The run was scored as `build_failure` because `cargo build` never succeeded, but the underlying behavior is closer to the model giving up silently than to an ordinary compilation failure with the agent still trying to fix it.

## What would have changed the outcome

- **Earlier first build.** rs r2 ran 7 `cargo build` iterations through its session; rs r1 ran 1 late attempt. Building after the scaffold is in place, not after the whole implementation is drafted, would have surfaced the format-string error much earlier and given the model ~12 more minutes of feedback-driven iteration.
- **Modular split up front.** Both successful rs runs produced an 8-file tree before filling in `entities.rs` and `eval.rs`. rs r1's monolithic `main.rs` meant every rewrite was full-file and every build covered the same blast radius.
- **Harness surfacing of stuck state.** The harness currently has no signal for "model emitted empty response" — the transcript records it as an 11-second gap followed by a session-end envelope. A follow-up change worth considering: detect the `tool_result → result` adjacency with no intervening assistant text, and flag it in `metadata.notes` so postmortems don't need to reconstruct this from the transcript.
