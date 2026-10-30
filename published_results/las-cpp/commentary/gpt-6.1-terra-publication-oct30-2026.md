# Reviewed GPT-6.1 Terra collection, October 29, 2026 — las-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `de7d9741-0341-4e03-b433-585623794f5a`

- Score 223/223; status Complete.
- Failures: None.
- Network: One attempted 'pip install clang-format' into /tmp, denied by the API-only proxy (pypi.org, 6 denials; exit 1); nothing was installed. Audit otherwise: chatgpt.com 80 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted install.
- Session turn context shows only gpt-6.1-terra; 1 turn; 66 commands and 11 file changes; non-partial token accounting.
- The saved source includes the agent's build directory (most of the 242 files).
- Perfect score; same as published GPT-6.1 Sol and GPT-6 Sol max (223/223); GPT-5.6 Terra 222/223.

### GPT-6.1 Terra high — `c179f3f6-08f3-4ad5-ad38-a7ec394dd86a`

- Score 217/223; status Incomplete.
- Failures: 6, including WKT validation edge cases, matching the gap the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6.1 Sol 223/223, GPT-6 Sol 220/223.

### GPT-6.1 Terra low — `fcb53227-9b24-44de-88c7-e7b934c6c61a`

- Score 189/223; status Incomplete.
- Failures: 34, in CRS, waveform, extra-bytes and header-extent validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
