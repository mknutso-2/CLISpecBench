# Claude Sonnet 5.5 max — RS274 JS

Run UID: `c1ece4a3-58a7-4d5e-b1bd-6fb168a2bf9c`. RS274 3.2.2; Claude Code 2.1.289; exact `claude-sonnet-5-5`; max effort; historical Claude web-enabled condition. Launched October 13, 2026 as a single requested cell, not as part of a batch.

## Completion and claims

Claims a complete standard-library Node simulator with all CLI and trace modes, reproduced prompt and spec examples, about 40,000 crash-free random programs with trace/state replay agreement, and two subagent reviews. Lists its ambiguous modelling choices (G43 never moves the axes, sparse parameter reporting, defaults, composite CRC sub-motions, a missing F treated as zero time) and one known gap: `error_block_segment_index` is always null. These are self-checks, not independent conformance. The flagged G43 choice is one of the hidden-test failures.

## Substantive review

Completed voluntarily after 194 turns and 5,810 s. Build succeeded and 541/555 tests passed. The 14 failures:

- **Cutter compensation errors (6):** concave corners are accepted and handled with a retrace instead of being rejected (G41/G42, at 90° and after entry). Two zero-length R-format CRC arcs are also accepted.
- **Tool length compensation (3):** G43 and G43 offset changes do not adjust the reported current Z.
- **Probing (3):** two G38.2 trip points are wrong with tool length compensation active, and probing with the spindle turning is accepted.
- **Parameter files (2):** files missing a required linear or rotary entry are accepted.

Compared with the published Sonnet 5.5 high run (542/555, 27 min), seven failures are shared, seven are max-only and six are high-only. No timeout, auth, network, quota or rate-limit termination occurred. The five-hour account window stayed below 70% throughout.

## Model identity and accounting

The stream, native session and both subagent transcripts record only `claude-sonnet-5-5`, and `CLAUDE_CODE_SUBAGENT_MODEL` / `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` were set. The two subagents were general-purpose background reviewers. No MCP servers were configured and no web search or fetch requests occurred.

The CLI-reported model usage was 466 uncached input tokens, 1,333,616 cache-write tokens, 94,430,287 cache-read tokens and 852,838 output tokens (698,362 thinking). This gives a reported API-equivalent list price of $31.86 (harness estimate $32.75). That is not a subscription or extra-usage charge. The full saved terminal message was reviewed, because the result metadata keeps only its first 2,000 characters. The original attempt and score are unchanged. Private raw sessions, source and artifact paths are not published.
