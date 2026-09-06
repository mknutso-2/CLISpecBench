# GPT-6 Astra high — RS274 Rust run 1

Astra completed voluntarily and reported the implementation finished, with a release build, 21 own regression tests, and 14 CLI checks verified. Its final transcript ends with `turn.completed`; the complete hidden test report records **481/546 (88.10%)**. Its own validation claims do not imply a perfect hidden-suite score.

The agent and grader both completed normally. Generated source was graded as-is. No timeout, authentication failure, interrupted grading, manual source repair, or infrastructure rerun was involved.

28 failures stop at a positive-feed-rate requirement, and eight stop at a probe-in-spindle requirement. Four failures stop at an M6 selected-tool requirement. Other failures involve cutter compensation, canned cycles, parameter files and values, coordinate/tool state, and traces. These are observed failure clusters; a shared precondition can stop several tests before their intended assertion. Specification/test interpretation review is needed before treating every failed test as an independent implementation defect.

This run passes **-2 tests** relative to the corresponding Astra Max run. Both runs used identical language-specific prompt and test-suite content hashes. This is a comparison of one run per configuration.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **high**, RS274 eval **3.2.0**, and **api-only** networking. The network audit contains allowed API-domain connections and denied external requests. Compare within that network condition.

Recorded usage is **1,765,312 input tokens** (including 1,663,360 cached), **32,826 output tokens** (including **9,929 reasoning**), and **1,798,138 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. There were **23 tool calls** under `underlying_tool_invocations_v2`. The full session, transcript, network audit, and complete grading report are retained. Estimated standard API-equivalent cost is **$4.324180**, rather than a measured subscription charge or invoice.
