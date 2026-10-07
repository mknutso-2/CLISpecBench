# Claude Sonnet 5.5 low — RS274 JS

Run UID: `fc078521-2fb1-4dcb-bea7-acd84f0b8389`. RS274 3.2.2; Claude Code 2.1.289; exact `claude-sonnet-5-5`; low effort; historical Claude web-enabled condition.

## Completion and claims

Claims simulator built and trace examples verified; acknowledges limited numeric checks and chosen tool-offset/parameter semantics. Trace tests pass, but CRC/TLO modal reporting, tool-offset/probe behavior and parameter-file edges remain incorrect.

## Substantive review

Completed voluntarily with a substantial five-module JavaScript simulator: build succeeded and 516/555 tests passed, including all 104 trace tests. The main failure is stale modal state reporting: execBlock updates CRC and tool-offset internals but never sets active_modal_g_codes groups 7/8 for G41/G42/G43. This causes 26 CRC cases plus the active-G41 and active-G43 tests to fail; CRC geometry is implemented, and the 26 geometry assertions are masked by the modal assertion. Other failures are three current-Z tool-length-offset cases and two TLC probe cases (G43 changes the offset but not current Z), two G10 raw-parameter persistence cases (output multiplies backing values by active unit conversion), two missing-required-parameter validations, bare G53 without any axes accepted, and probing with a spinning spindle accepted. The final message admits sparse parameter-file validation, its no-position-change G43 interpretation and limited expected-number checks; it does not acknowledge the remaining defects. No timeout, auth/network/quota failure or paid overflow occurred. Exact Sonnet 5.5 served at low effort throughout; Claude's web-enabled condition was retained, no personal MCP/skills or subagents were used, and only local Read/Bash calls occurred. Cost reconciles to $2.8964338 with 54 uncached input, 225435 one-hour cache writes, 3824929 cache reads and 122960 output tokens (including 85599 thinking tokens).

## Accounting and evidence

API-equivalent list-price estimate: $2.8964338; not a subscription or extra-usage charge. Full saved terminal message (2548 characters) was reviewed because raw result metadata retains only its first 2,000 characters. Exact model, effort, input/image provenance, canonical session/tool inventory, token accounting and natural completion were checked. No quota/auth/network termination or paid overflow occurred. All workers and graders were removed. Original attempts and scores are unchanged; private raw sessions, source and artifact paths are not published.
