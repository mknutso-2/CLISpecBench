# Reviewed GPT-6.1 Terra collection, October 29, 2026 — iges-py

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `b299da8b-696a-4214-9742-017c9b3e0551`

- Score 248/249; status Complete.
- Failures: 1: test_reference_fixtures.py::test_appendix_file_parse_and_roundtrip[ex1.iges-21]. It passes the zero-count Hollerith case that the C++ run and the Claude runs fail. Not mentioned.
- Network: Two curl queries of the GitHub API for IGES sample files (OCCT data/iges and pythonocc-demos models), denied by the API-only proxy (api.github.com, 2 denials); nothing was retrieved. Audit otherwise: chatgpt.com 72 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted fetches.
- Session turn context shows only gpt-6.1-terra; 1 turn; 74 commands; files written through shell commands; non-partial token accounting.
- Compared with published max runs: GPT-6.1 Sol 248/249, GPT-5.6 Terra 247/249, GPT-6 Sol 243/249.

### GPT-6.1 Terra high — `67a04d7d-6b98-4d9e-8bf2-67f59fe89822`

- Score 181/249; status Incomplete.
- Failures: 68, across missing catalog entities and evaluators, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- One 13-line egress-proxy traceback in the network audit (tracked separately).
- Compared with published high runs: GPT-6 Sol 238/249, GPT-6.1 Sol 166/249.

### GPT-6.1 Terra low — `c7ed6e46-d36b-427a-8f69-9578ab857053`

- Score 142/249; status Incomplete.
- Failures: 107, across unimplemented entities, evaluators and validation, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
