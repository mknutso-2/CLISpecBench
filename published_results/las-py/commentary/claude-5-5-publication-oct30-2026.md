# Reviewed Claude 5.5 collection, October 13-29, 2026 — las-py

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `f51083ba-85f8-4b21-ae9d-2d39cb0d21e4`

- Score 215/223; status Complete.
- Failures: 8, identical to C++ and JS: waveform packets outside the payload (4), missing GeoKeyDirectory / WKT records (2), legacy count vs return counters (2).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `abe5b3e5-0074-4f1c-86c7-91fe41857ed1`

- Score 221/223; status Complete.
- Failures: 2: missing GeoKeyDirectory / WKT record should be rejected.
- Network: none

### Sonnet 5.5 max — `ca96179e-069b-4430-bd28-7d36ebf71543`

- Score 215/223; status Complete.
- Failures: 8, the same set as Sonnet LAS JS max: waveform packet outside payload (4), missing GeoKeyDirectory/WKT record (2), legacy-count vs return-counter consistency (2). All disclosed as deliberate choices: the waveform offset is not validated, the CRS is not required, and legacy counts are zero for WKT files.
- Network: pip-installed laspy, numpy, pypdf and uv into a throwaway venv, and used uv to download a Python build for testing (web-enabled condition; disclose).
- Harness 0.2.1 conditions; two same-model subagents, 19 ListAgents, 2 SendMessage; modelUsage only claude-sonnet-5-5.

### Opus 5.5 max — `f0587983-eb05-4543-9484-3ef9505ac863`

- Score 221/223; status Complete.
- Failures: 2: missing GeoKeyDirectory in GeoTIFF mode and missing WKT coordinate-system record should be rejected. The last message says the agent deliberately did not treat a missing CRS record as an error.
- Network: pip-installed laspy and numpy into a throwaway /tmp venv for cross-checking only, and downloaded public LAS sample files (laspy test data) with curl (2 network commands; no WebFetch/WebSearch) (web-enabled condition; disclose).
- Harness 0.2.2 conditions. One foreground general-purpose subagent ('Independent spec-compliance review') ran on claude-opus-5-5; modelUsage only claude-opus-5-5. All 9 task notifications completed; none stopped.
- Same score as Opus LAS Python high (221/223); 6 above Sonnet LAS Python max (215/223).
