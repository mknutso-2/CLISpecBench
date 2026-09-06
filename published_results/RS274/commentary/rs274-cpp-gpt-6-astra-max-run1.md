# GPT-6 Astra max — RS274 C++ run 1

Astra completed voluntarily and produced a substantial implementation. Its final message claims the implementation and its own regression tests pass. The hidden suite passes **478/546 (87.55%)**: 381/440 non-trace tests and 97/106 trace tests. This is a completed run with remaining behavioral failures.

The first grading attempts selected the submission's self-test executable instead of its simulator. After fixing CMake executable discovery to prefer the application over CTest-registered test binaries, the unchanged submission scored 478/546 in two independent grading passes. The agent source, prompt, and hidden tests were unchanged; no source surgery or additional model generation was used.

Failures include feed-rate and probe preconditions, cutter compensation, parameter/tool state, and trace details. Twenty-eight failures stop at a positive-feed-rate requirement, including programs that omit F; eight stop at a probe-in-spindle precondition. Those clusters need specification/test interpretation review and should not be treated as independent defects for every failed test.

The run used Codex CLI **0.153.4**, model **gpt-6-astra**, effort **max**, and the **api-only** network condition. Compare within that condition. The GPT-5.6 restart runs used CLI 0.151.0. Their stored test-suite hashes differ from this run even though a Git comparison found no tracked test-file changes; that historical hash discrepancy remains unresolved.

Usage was audited against the saved session: **2,179,166 input tokens** (including 1,984,000 cached), **62,643 output tokens** (including **25,963 reasoning**), and **2,241,809 total tokens**. The standard API-equivalent estimate is **$7.06781**, not an invoice or measured subscription-credit charge. Corrected telemetry records **36 tool calls** under `underlying_tool_invocations_v2`; older published tool-call counts await backfill from their original transcripts.
