# GPT-6 Astra low — RS274 Rust run 1

Astra completed voluntarily and reported the implementation finished, with a release build, 27 own tests, and Appendix C sample programs verified. Its final transcript ends with `turn.completed`; the complete hidden test report records **490/546 (89.74%)**. Its own validation claims do not imply a perfect hidden-suite score.

The agent and grader both completed normally. Generated source was graded as-is. No timeout, authentication failure, interrupted grading, manual source repair, or infrastructure rerun was involved.

28 failures stop at a positive-feed-rate requirement, and eight stop at a probe-in-spindle requirement. Other failures involve cutter compensation, canned cycles, parameter files, coordinate/tool state, probe error handling, and traces. These are observed failure clusters; a shared precondition can stop several tests before their intended assertion. Specification/test interpretation review is needed before treating every failed test as an independent implementation defect.

This run passes **+7 tests** relative to the corresponding Astra Max run. Both runs used identical language-specific prompt and test-suite content hashes. This is a comparison of one run per configuration.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **low**, RS274 eval **3.2.0**, and **api-only** networking. The network audit contains allowed API-domain connections and denied external requests. Compare within that network condition.

Recorded usage is **2,746,351 input tokens** (including 2,617,472 cached), **36,293 output tokens** (including **10,687 reasoning**), and **2,782,644 total tokens**. Cache-write tokens are explicitly zero. Counts match the retained session. There were **31 tool calls** under `underlying_tool_invocations_v2`. The full session, transcript, network audit, and complete grading report are retained. Estimated standard API-equivalent cost is **$5.720912**, rather than a measured subscription charge or invoice.
