# Claude Sonnet 5.5 low — RS274 PY

Run UID: `3887f796-87f7-4c30-be5c-af0107fd4e5d`. RS274 3.2.2; Claude Code 2.1.289; exact `claude-sonnet-5-5`; low effort; historical Claude web-enabled condition.

## Completion and claims

Voluntarily delivered the simulator after ad-hoc checks, acknowledging untested CRC geometry and parameter assumptions. Passed 543/555; remaining failures concern parameter persistence/rotary entries and missing cycle, probing and G53 safety checks.

## Substantive review

Completed voluntarily without quota, auth, network or timeout interruption. The substantial standard-library Python simulator built and passed 543/555 tests, including all trace cases and CRC geometry cases. The 12 failures are concrete implementation/contract defects: missing P accepted in G86/G88/G89; G53 accepted while CRC is active; coordinate-system backing parameters converted across unit switches rather than preserved raw; overly permissive G-code rounding accepts G53.99998; required rotary parameter input/output entries omitted; probing allowed with spindle turning; and M2/M30 destroy stored G92 parameters. The final message candidly discloses untested geometry and parameter choices rather than claiming full correctness, but several choices contradict the benchmark's specified persistence contract. Full stream final message was reviewed because raw metadata is truncated at 2000 characters.

## Accounting and evidence

API-equivalent list-price estimate: $2.4254748; not a subscription or extra-usage charge. Full saved terminal message (2372 characters) was reviewed because raw result metadata retains only its first 2,000 characters. Exact model, effort, input/image provenance, canonical session/tool inventory, token accounting and natural completion were checked. No quota/auth/network termination or paid overflow occurred. All workers and graders were removed. Original attempts and scores are unchanged; private raw sessions, source and artifact paths are not published.
