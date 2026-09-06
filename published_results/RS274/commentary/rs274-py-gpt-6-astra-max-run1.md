# GPT-6 Astra max — RS274 Python run 1

Astra completed voluntarily and reported the implementation finished, with 48 own tests passing. The final transcript ends with `turn.completed`; the complete hidden test report records **478/546 (87.55%)**. The final message describes the submission's own validation, not a perfect hidden-suite score.

The agent and grader both completed normally. There was no timeout, authentication failure, interrupted grading, manual source repair, or rerun. This result uses the submission exactly as generated.

27 failures stop at a positive-feed-rate requirement. Eight failures stop at a probe-in-spindle requirement. Other failures involve cutter compensation, canned cycles, parameter files, spindle/tool state, and trace behavior. These are observed failure clusters; shared preconditions can stop several tests before they reach their intended assertion and should not be counted as independent implementation defects without specification/test interpretation review.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **max**, RS274 eval **3.2.0**, and **api-only** networking. The network audit records allowed API-domain connections and denied external requests. Compare within that network condition. The test-suite content hash matches the initial Astra C++ run; pulling the later historical telemetry backfill did not change the harness, prompts, or tests used here.

Recorded usage is **2,170,328 input tokens** (including 1,965,440 cached), **50,919 output tokens** (including **18,548 reasoning**), and **2,221,247 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. The run records **35 tool calls** under `underlying_tool_invocations_v2`, and retains its full session, transcript, network audit, and complete grading report. Estimated standard API-equivalent cost is **$6.560270**; this is not a measured subscription charge or invoice.
