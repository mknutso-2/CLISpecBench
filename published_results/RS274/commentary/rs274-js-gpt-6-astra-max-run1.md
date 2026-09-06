# GPT-6 Astra max — RS274 JavaScript run 1

Astra completed voluntarily and reported the implementation finished, with 143 own tests passing. The final transcript ends with `turn.completed`; the complete hidden test report records **477/546 (87.36%)**. The final message describes the submission's own validation, not a perfect hidden-suite score.

The agent and grader both completed normally. There was no timeout, authentication failure, interrupted grading, manual source repair, or rerun. This result uses the submission exactly as generated.

27 failures stop at a positive-feed-rate requirement. Eight failures stop at a probe-in-spindle requirement; four stop at an M6 selected-tool requirement. Other failures involve cutter compensation, probe contact, tool-length offsets, parameter files, and trace behavior. These are observed failure clusters; shared preconditions can stop several tests before they reach their intended assertion and should not be counted as independent implementation defects without specification/test interpretation review.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **max**, RS274 eval **3.2.0**, and **api-only** networking. The network audit records allowed API-domain connections and denied external requests. Compare within that network condition. The test-suite content hash matches the initial Astra C++ run; pulling the later historical telemetry backfill did not change the harness, prompts, or tests used here.

Recorded usage is **1,529,665 input tokens** (including 1,383,936 cached), **54,933 output tokens** (including **22,225 reasoning**), and **1,584,598 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. The run records **29 tool calls** under `underlying_tool_invocations_v2`, and retains its full session, transcript, network audit, and complete grading report. Estimated standard API-equivalent cost is **$5.587876**; this is not a measured subscription charge or invoice.
