# Reviewed GPT-6.1 Terra collection, October 29, 2026 — rs274-rs

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `eed317d8-6dce-493a-bf04-56490d3fb92a`

- Score 553/555; status Complete.
- Failures: 2: a parameter file missing a required rotary entry should be rejected (the same failure as Terra RS274 JS and Python), and G84 with G99 should show the spindle reversal in the trace (test_trace_stepping.py). Not mentioned.
- Network: One attempted 'rustup component add rustfmt', denied by the API-only proxy (static.rust-lang.org, 2 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 107 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 72 commands and 27 file changes; non-partial token accounting.
- The saved source includes the agent's target/ build directory (249 of 258 files); the authored code is under src/.
- The network audit again contains a 13-line egress-proxy traceback (ConnectionResetError), not an audit event; tracked separately.
- Compared with published max runs: GPT-6.1 Sol 550/555, GPT-6 Sol 542/555, GPT-5.6 Terra 541/555.

### GPT-6.1 Terra high — `71366245-09a6-46a1-b496-abf9936c7aa6`

- Score 454/555; status Incomplete.
- Failures: 101, including cutter compensation, G87, canned-cycle behavior and validation/error handling, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 2 minutes, a dozen commands); the same model at max took 15-25 min and scored 553-555/555. Counted as a completed run; status Incomplete because the agent acknowledged the gaps.
- Compared with published high runs: GPT-6.1 Sol 550/555, GPT-6 Sol 537/555, GPT-5.6 Terra 317/555.

### GPT-6.1 Terra low — `4594aae2-fdb4-46b0-b9a0-9ca3e5a11eb7`

- Score 438/555; status Incomplete.
- Failures: 117, across cutter compensation, canned cycles and error conditions, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 550/555, GPT-6 Sol 184/555.
