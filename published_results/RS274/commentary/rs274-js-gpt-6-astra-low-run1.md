# GPT-6 Astra low — RS274 JavaScript run 1

Astra completed voluntarily and reported the implementation finished, with syntax checks, own regression tests, and all three complete Appendix C programs verified. Its final transcript ends with `turn.completed`; the complete hidden test report records **482/546 (88.28%)**. Its own validation claims do not imply a perfect hidden-suite score.

The agent and grader both completed normally. Generated source was graded as-is. No timeout, authentication failure, interrupted grading, manual source repair, or infrastructure rerun was involved.

28 failures stop at a positive-feed-rate requirement, and eight stop at a probe-in-spindle requirement. Four failures stop at an M6 selected-tool requirement. Other failures involve cutter compensation, parameter files and values, coordinate/tool state, and traces. These are observed failure clusters; a shared precondition can stop several tests before their intended assertion. Specification/test interpretation review is needed before treating every failed test as an independent implementation defect.

This run passes **+5 tests** relative to the corresponding Astra Max run. Both runs used identical language-specific prompt and test-suite content hashes. This is a comparison of one run per configuration.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **low**, RS274 eval **3.2.0**, and **api-only** networking. The network audit contains allowed API-domain connections and denied external requests. Compare within that network condition.

Recorded usage is **1,394,409 input tokens** (including 1,294,208 cached), **18,468 output tokens** (including **2,592 reasoning**), and **1,412,877 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. There were **19 tool calls** under `underlying_tool_invocations_v2`. The full session, transcript, network audit, and complete grading report are retained. Estimated standard API-equivalent cost is **$3.219618**, rather than a measured subscription charge or invoice.
