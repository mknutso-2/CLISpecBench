# Reviewed Claude 5.5 collection, October 13-29, 2026 — las-js

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `d76704f6-4b13-45f0-a09e-0348d0081fe4`

- Score 215/223; status Complete.
- Failures: 8, identical to the C++ run: waveform packets outside the payload (4), missing GeoKeyDirectory / WKT records (2), legacy count vs return counters (2).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `777ff674-9bdc-4d67-8c93-3cbf71eb967e`

- Score 220/223; status Complete.
- Failures: 3: missing GeoKeyDirectory / WKT record should be rejected (2), rendering GeoTIFF triplet records (1).
- Network: none

### Sonnet 5.5 max — `138d1a68-9a81-437d-b078-6c211754968c`

- Score 215/223; status Complete.
- Failures: 8: waveform packet outside payload in inspect and render (4), missing GeoKeyDirectory in GeoTIFF mode and missing WKT record (2), and legacy-count vs return-counter consistency (2). All three families were disclosed as deliberate choices: the waveform offset is not checked, absent CRS records are accepted, and all-zero legacy fields are accepted.
- Network: pip-installed laspy, and downloaded public LAS test files from GitHub (laspy, PDAL, TerraScan data) (web-enabled condition; disclose).
- Harness 0.2.1 conditions; one same-model subagent, 23 ListAgents; modelUsage only claude-sonnet-5-5.

### Opus 5.5 max — `1c194f0a-7df4-474a-8579-18c0900c2829`

- Score 220/223; status Complete.
- Failures: 3: inspect and render should reject a waveform packet outside the waveform payload (2-4); render should reject a format-6 gps_time that does not fit the target binary float. Not mentioned; the agent chose to check waveform data only when a point refers to it.
- Network: 1 WebSearch (3 web requests) for the task's own JSON field names (wkt_coordinate_system, geo_key_directory, waveform_data_packets, las_b64), looking for a public reference using this schema; found only general LAS background (libLAS, GeoCue). The helper ran on claude-opus-5-5 only (web-enabled condition; disclose).
- Harness 0.2.2 conditions; no subagents and no stopped background tasks; modelUsage only claude-opus-5-5 despite WebSearch, confirming the 0.2.1 helper fix.
- Same score as Opus LAS JS high (220/223); 5 above Sonnet LAS JS max (215/223).
