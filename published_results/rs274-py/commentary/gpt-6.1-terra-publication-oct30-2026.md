# Reviewed GPT-6.1 Terra collection, October 29, 2026 — rs274-py

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `2970090b-c5f1-47a0-8540-8a8527c34e15`

- Score 553/555; status Complete.
- Failures: 2: active G-code group 7 tracking for G41 (test_active_gcode_groups.py), and a parameter file missing a required rotary entry should be rejected (test_parameter_file_cli.py; the same failure as Terra RS274 JS). Not mentioned.
- Network: One attempted curl of LinuxCNC's interp_arc.cc from raw.githubusercontent.com, denied by the API-only proxy (curl exit 56); nothing was retrieved. Audit otherwise: chatgpt.com 86 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted reference-source fetch.
- Session turn context shows only gpt-6.1-terra; 1 turn; 77 commands and 22 file changes; non-partial token accounting.
- The network audit contains a 13-line Python traceback from the egress proxy (ConnectionResetError while relaying), not an audit event. Harmless here, but it is what made the first Terra app-connector smoke test fail its parse of the audit log.
- Compared with published max runs: GPT-6.1 Sol 555/555, GPT-5.6 Terra 545/555, GPT-6 Sol 538/555.

### GPT-6.1 Terra high — `0fb3fa50-cdcd-46aa-910d-d14cc8eec7b7`

- Score 490/555; status Incomplete.
- Failures: 65, concentrated in cutter radius compensation, error conditions and trace behavior, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 2 minutes, a dozen commands); the same model at max took 15-25 min and scored 553-555/555. Counted as a completed run; status Incomplete because the agent acknowledged the gaps.
- Compared with published high runs: GPT-6.1 Sol 555/555, GPT-6 Sol 538/555, GPT-5.6 Terra 470/555.

### GPT-6.1 Terra low — `f7bc29a2-629c-4ecd-9a10-0538b65bc176`

- Score 424/555; status Incomplete.
- Failures: 131, across canned cycles, probing, cutter compensation and validation rules, matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- Compared with published low runs: GPT-6.1 Sol 548/555, GPT-6 Sol 186/555.
