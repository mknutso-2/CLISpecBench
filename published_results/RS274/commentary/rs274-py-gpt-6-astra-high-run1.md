# GPT-6 Astra high — RS274 Python run 1

Astra completed voluntarily and reported the implementation finished, with 42 own regression tests and Python compilation verified. Its final transcript ends with `turn.completed`; the complete hidden test report records **474/546 (86.81%)**. Its own validation claims do not imply a perfect hidden-suite score.

The agent and grader both completed normally. Generated source was graded as-is. No timeout, authentication failure, interrupted grading, manual source repair, or infrastructure rerun was involved.

28 failures stop at a positive-feed-rate requirement, and eight stop at a probe-in-spindle requirement. Other failures involve cutter compensation, canned cycles, probe contact, tool-length offsets, parameter files, spindle/tool state, and traces. These are observed failure clusters; a shared precondition can stop several tests before their intended assertion. Specification/test interpretation review is needed before treating every failed test as an independent implementation defect.

This run passes **-4 tests** relative to the corresponding Astra Max run. Both runs used identical language-specific prompt and test-suite content hashes. This is a comparison of one run per configuration.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **high**, RS274 eval **3.2.0**, and **api-only** networking. The network audit contains allowed API-domain connections and denied external requests. Compare within that network condition.

Recorded usage is **1,379,001 input tokens** (including 1,275,008 cached), **33,970 output tokens** (including **7,257 reasoning**), and **1,412,971 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. There were **26 tool calls** under `underlying_tool_invocations_v2`. The full session, transcript, network audit, and complete grading report are retained. Estimated standard API-equivalent cost is **$4.013438**, rather than a measured subscription charge or invoice.
