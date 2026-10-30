# Reviewed GPT-6.1 Terra collection, October 29, 2026 — iges-cpp

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `f74b6097-994a-4cc1-b3a0-2a93ca664680`

- Score 248/249; status Complete.
- Failures: 1: test_zero_count_hollerith_is_rejected_after_defaulted_string_control, the same single failure as the Claude 5.5 IGES runs. Not mentioned.
- Network: One Python urllib script that queried the GitHub API for IGES sample files in pythonocc-demos, CadQuery and FreeCAD, denied by the API-only proxy (api.github.com, 3 denials); nothing was retrieved, and the last message says so. Audit otherwise: chatgpt.com 111 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted fetch.
- Session turn context shows only gpt-6.1-terra; 1 turn; 94 commands; files written through shell commands; non-partial token accounting.
- The saved source includes the agent's build directory (most of the 222 files).
- Compared with published max runs: GPT-6.1 Sol 246/249, GPT-6 Sol 245/249, GPT-5.6 Terra 244/249.

### GPT-6.1 Terra high — `9392d810-e290-405a-a7ae-73b266bd3882`

- Score 143/249; status Incomplete.
- Failures: 106, across unsupported entity schemas and surface evaluators, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- Compared with published high runs: GPT-6 Sol 246/249, GPT-6.1 Sol 166/249.

### GPT-6.1 Terra low — `89d23865-816f-41cd-b4c4-7cc44f0b07c3`

- Score 70/249; status Incomplete.
- Failures: 179, across unimplemented write, entity schemas, evaluators and validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
