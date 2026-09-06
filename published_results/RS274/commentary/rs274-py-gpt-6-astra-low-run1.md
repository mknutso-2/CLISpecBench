# GPT-6 Astra low — RS274 Python run 1

Astra completed voluntarily and reported the implementation finished, with 23 own regression tests, Python compilation, and the specification expression and canned-cycle sample programs verified. Its final transcript ends with `turn.completed`; the complete hidden test report records **485/546 (88.83%)**. Its own validation claims do not imply a perfect hidden-suite score.

The agent and grader both completed normally. Generated source was graded as-is. No timeout, authentication failure, interrupted grading, manual source repair, or infrastructure rerun was involved.

27 failures stop at a positive-feed-rate requirement, and eight stop at a probe-in-spindle requirement. Other failures involve cutter compensation, probe contact, parameter files, tool-length offsets, coordinate/tool state, and traces. These are observed failure clusters; a shared precondition can stop several tests before their intended assertion. Specification/test interpretation review is needed before treating every failed test as an independent implementation defect.

This run passes **+7 tests** relative to the corresponding Astra Max run. Both runs used identical language-specific prompt and test-suite content hashes. This is a comparison of one run per configuration.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **low**, RS274 eval **3.2.0**, and **api-only** networking. The network audit contains allowed API-domain connections and denied external requests. Compare within that network condition.

Recorded usage is **1,080,260 input tokens** (including 1,003,520 cached), **19,671 output tokens** (including **3,189 reasoning**), and **1,099,931 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. There were **17 tool calls** under `underlying_tool_invocations_v2`. The full session, transcript, network audit, and complete grading report are retained. Estimated standard API-equivalent cost is **$2.754470**, rather than a measured subscription charge or invoice.
