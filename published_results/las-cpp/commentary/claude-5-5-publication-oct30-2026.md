# Reviewed Claude 5.5 collection, October 13-29, 2026 — las-cpp

Sonnet 5.5 and Opus 5.5 at high and max effort under the web-enabled Claude Code condition, one run per cell; six cells also have one rerun, and both attempts are kept. See the [collection note](../../collection-notes/claude-5-5-oct30.md) for scope, harness versions, reruns and exclusions. Dollar amounts are CLI-reported or API-equivalent estimates, not subscription charges.

## Runs

### Sonnet 5.5 high — `868d83dc-570d-4929-8526-10e8da41f08d`

- Score 215/223; status Complete.
- Failures: 8: waveform packets outside the payload in inspect and render (4), missing GeoKeyDirectory in GeoTIFF mode (1), missing coordinate-system WKT record (1), legacy point count vs return counters consistency (2).
- Network: None (no network commands; no WebFetch/WebSearch).

### Opus 5.5 high — `685f5715-3600-4f33-8495-fca6b1579dcb`

- Score 222/223; status Complete.
- Failures: 1: render should reject a GPS time that does not fit the target binary float (point format 6).
- Network: none

### Sonnet 5.5 max — `4741a366-0f69-4029-9485-cec9227c179c`

- Score 212/223; status Complete.
- Failures: 11: waveform point payloads for formats 4/5/9/10 (4), external waveform mode not requiring the waveform EVLR (1), waveform packet outside payload in inspect and render (4), missing GeoKeyDirectory in GeoTIFF mode (1), missing coordinate-system WKT record (1). The last two were disclosed as a deliberate choice (absent records accepted); the waveform-bit rule was disclosed in a form that conflicts with the external-waveform test.
- Network: pip-installed laspy, numpy and pytest into a throwaway venv as an oracle (web-enabled condition; disclose).
- Harness 0.2.1 conditions; one same-model subagent, 21 ListAgents; modelUsage only claude-sonnet-5-5.
- Scored below Sonnet LAS C++ high (215/223).

### Opus 5.5 max — `705cf27a-789a-4e2b-8a9a-efd1d36b041b`

- Score 221/223; status Complete.
- Failures: 2: inspect and render should reject a waveform packet that lies outside the waveform payload (case 2-4). Not mentioned.
- Network: None (no network commands; no WebFetch/WebSearch).
- First run under harness 0.2.2; CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1 confirmed on the agent's claude process. No subagents and no stopped background tasks; modelUsage only claude-opus-5-5.
- 1 below Opus LAS C++ high (222/223); 9 above Sonnet LAS C++ max (212/223).
