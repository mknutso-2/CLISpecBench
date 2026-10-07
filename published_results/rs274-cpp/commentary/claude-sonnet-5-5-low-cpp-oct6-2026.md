# Claude Sonnet 5.5 low — RS274 CPP

Run UID: `fa6a0eb7-ef9f-4ec1-a8b6-5e38a19beecb`. RS274 3.2.2; Claude Code 2.1.289; exact `claude-sonnet-5-5`; low effort; historical Claude web-enabled condition.

## Completion and claims

Claims built and sample-tested; acknowledges unverified cutter compensation and interpretation choices. Remaining failures include CRC entry arcs, tool-length/probing state, parameter/reset semantics, and validation/trace edge cases.

## Substantive review

Completed voluntarily and built successfully, passing 534/555 tests. Residual model-implementation failures: 3 missing mandatory canned-cycle P checks (G86/G88/G89); 4 first radius-format CRC entry-arc cases with wrong endpoints or erroneous rejection; 2 raw backing coordinate-system parameter persistence failures across G20/G21 changes; overly permissive G-code tolerance accepts G53.99998; missing required rotary parameter entry accepted; 2 probe trips with tool-length compensation missed plus spinning-spindle probing accepted; M2/M30 improperly clear stored G92 parameters; 3 G43 current-position adjustment cases; and 2 zero-duration trace nonmodal-label cases. Source implements substantial parsing/state/geometry/cycles/probing/tracing rather than stubs. The final message explicitly acknowledges unverified CRC and interpretation choices; its self-test success claims do not establish full correctness. No quota/auth/network/operator interruption or infrastructure rerun is indicated. Costs are consistent API-equivalent list-price estimates. Historical web-enabled Claude condition is retained. Raw sessions contain private identifiers and remain local; curated publication removes artifacts.

## Accounting and evidence

API-equivalent list-price estimate: $2.2311180; not a subscription or extra-usage charge. Full saved terminal message (2148 characters) was reviewed because raw result metadata retains only its first 2,000 characters. Exact model, effort, input/image provenance, canonical session/tool inventory, token accounting and natural completion were checked. No quota/auth/network termination or paid overflow occurred. All workers and graders were removed. Original attempts and scores are unchanged; private raw sessions, source and artifact paths are not published.
