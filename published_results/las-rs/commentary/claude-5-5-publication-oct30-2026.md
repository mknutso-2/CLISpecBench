# Reviewed Claude 5.5 collection, October 13-29, 2026 — las-rs

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `8d86924c-16d2-4bba-8419-4e2b64643543`

- Score 217/223; status Complete.
- Failures: 6: waveform packets outside the payload (4), missing GeoKeyDirectory / WKT records (2). Unlike the other languages it handles the legacy-count consistency checks.
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `4448faee-b0eb-4edf-b484-1968b8cf0bde`

- Score 220/223; status Complete.
- Failures: 3: missing GeoKeyDirectory / WKT record should be rejected (2), GPS time that does not fit the target float should be rejected on render (1).
- Network: none

### Sonnet 5.5 max — `4ca245d7-6cae-4c61-a105-12ca0a694e14`

- Score 217/223; status Complete.
- Failures: 6: waveform packet outside payload in inspect and render (4) and missing GeoKeyDirectory/WKT record (2). It passed the legacy-count consistency tests the JS and Python runs failed. The CRS choice was disclosed; the waveform-offset check was not specifically mentioned.
- Network: None detected.
- Harness 0.2.1 conditions; cargo on PATH (22 invocations, none not found); no stopped background subagents; modelUsage only claude-sonnet-5-5.
- Best Sonnet LAS score in either cohort (high Rust was 217 too).

### Opus 5.5 max — `2cb617f9-45ab-4b6c-af7b-0ab78231a6e1`

- Score 221/223; status Complete.
- Failures: 2: missing GeoKeyDirectory in GeoTIFF mode and missing WKT coordinate-system record should be rejected. Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- Harness 0.2.2 conditions. One background general-purpose review subagent ran on claude-opus-5-5; modelUsage only claude-opus-5-5. The agent kept a background 'backup timer' shell task running so task notifications re-invoked it while it waited; all 15 task notifications completed, none stopped, no [Request interrupted]. 4 result events.
- cargo was available and used (18 cargo build/test mentions).
- Same score as Opus LAS Python max; 1 above Opus LAS Rust high (220/223); 4 above Sonnet LAS Rust max (217/223).
