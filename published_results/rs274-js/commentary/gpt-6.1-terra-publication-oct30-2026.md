# Reviewed GPT-6.1 Terra collection, October 29, 2026 — rs274-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `4fb22ddd-0547-469e-8357-9d5c45b4b100`

- Score 553/555; status Complete.
- Failures: 2: a parameter file missing a required rotary entry should be rejected (test_parameter_file_cli.py), and G4 P0 with a modal change should emit a state-only trace entry (test_trace_nonmodal.py). Not mentioned.
- Network: None by the agent (no network commands). API-only audit: chatgpt.com 70 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs, as in earlier Codex runs.
- Session turn context shows only gpt-6.1-terra; 1 turn; 47 commands and 20 file changes; non-partial token accounting.
- Compared with published max runs: GPT-6.1 Sol 555/555 (37.7 min), GPT-5.6 Terra 552/555, GPT-6 Sol 546/555.

### GPT-6.1 Terra high — `f894dd13-1285-4ba1-86d3-71225ab8f95d`

- Score 521/555; status Incomplete.
- Failures: 34, mainly cutter compensation geometry, canned-cycle transitions and error trace segments, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 2 minutes, a dozen commands); the same model at max took 15-25 min and scored 553-555/555. Counted as a completed run; status Incomplete because the agent acknowledged the gaps.
- Compared with published high runs: GPT-6.1 Sol 555/555, GPT-6 Sol 535/555, GPT-5.6 Terra 490/555.

### GPT-6.1 Terra low — `333ae23f-6ec4-429b-aeaf-b4c28e03a574`

- Score 414/555; status Incomplete.
- Failures: 141, across canned cycles, probing, cutter compensation and edge cases, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 548/555, GPT-6 Sol 528/555.
