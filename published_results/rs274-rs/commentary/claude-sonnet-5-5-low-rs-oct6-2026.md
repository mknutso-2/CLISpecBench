# Claude Sonnet 5.5 low — RS274 RS

Run UID: `7754ce44-74db-4f59-b171-e4cde3b9f4c9`. RS274 3.2.2; Claude Code 2.1.289; exact `claude-sonnet-5-5`; low effort; historical Claude web-enabled condition.

## Completion and claims

Delivered a buildable simulator and confirmed the three published examples; explicitly acknowledged limited broader validation and approximate arc/cutter-compensation corners. Grading passed 494/555. A major unacknowledged omission is that parsed parameter assignments are never applied, causing cascading expression, home, offset and trace failures. Other gaps include unit-offset conversion, tool-length position updates and validation/probing edge cases.

## Substantive review

The substantial five-module Rust implementation completed voluntarily with end_turn and no cap/auth/network interruption. All 61 failures were inspected. parse.rs buffers assignments in Block.set, but exec_block never applies them; this explains six parameter-expression cases, three parameter-value cases, all eight G28/G30 parameter-home cases, missing sparse assignment trace and cascaded feed/tool/G92/arc failures. Additional defects: explicit modal G0/G1 without axes errors (six cases); G86/G88/G89 accept missing P; raw coordinate offsets are neither stored/converted consistently across unit changes; G43 changes tlo but never adjusts current position, breaking three position and two probe cases; missing spindle-turning probe rejection; parameter files omit required-entry validation; near-supported G-code tolerance accepts invalid values. The final message honestly cautions that broader tests were only plausible smoke checks and CRC arc corners are approximate, but does not acknowledge dropped parameter assignments. Hidden tests passed all 28 cutter compensation cases, so its disclosed CRC weakness should not be misreported as the main measured failure. Full final stream message is 2391 characters versus a 2000-character metadata prefix. Raw evidence is immutable; curated publication strips artifact paths and never includes canonical credential organization or Rust userEmail session context. No submitted code was executed/imported on the host.

## Accounting and evidence

API-equivalent list-price estimate: $2.8015848; not a subscription or extra-usage charge. Full saved terminal message (2391 characters) was reviewed because raw result metadata retains only its first 2,000 characters. Exact model, effort, input/image provenance, canonical session/tool inventory, token accounting and natural completion were checked. No quota/auth/network termination or paid overflow occurred. All workers and graders were removed. Original attempts and scores are unchanged; private raw sessions, source and artifact paths are not published.
