# Reviewed Claude 5.5 collection, October 13-29, 2026 — rs274-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 max — `c4deee1c-c71c-4736-807f-5255e49bb0a2`

- Score 0/555; status Output cap.
- Failures: See the run's test report.
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 max — `db9f6f84-53a4-4ec2-a47b-6306e8052e96`

- Score 546/555; status Complete.
- Failures: 9: G43 current-Z adjustment (3), G38.2 trip points with tool length compensation (2), probing with spindle turning or probe already tripped accepted (2), G-code number not close enough to a supported value accepted (1), G4 P0 with a modal change should emit a state-only trace entry (1).
- Network: None (no network commands; no WebFetch/WebSearch).
