# Reviewed GPT-6.1 Terra collection, October 29, 2026 — iges-js

GPT-6.1 Terra at low, high and max effort under the API-only Codex CLI 0.165.0 condition, one run per cell. See the [collection note](../../collection-notes/gpt-6-1-terra-oct30.md). Dollar amounts are API-equivalent estimates, not subscription charges.

## Runs

### GPT-6.1 Terra max — `9e445c9f-5074-493f-929b-2a96287773d6`

- Score 227/249; status Complete.
- Failures: 22. 20 are surface evaluations (ruled, revolution, tabulated cylinder, offset, plane, cylinder, cone, sphere, torus and spline surfaces) where the CLI exits 1 before evaluating: the tool requires --output to be the last flag, and the hidden-suite helper (Evals/IGES/tests/iges_support.py, eval command builder) appends --s after --output. The other 2 are real: Boolean property values serialize with a non-standard suffix instead of a logical, and the ex1.iges appendix file fails to parse. Not mentioned.
- Network: Two curl probes (GitHub API for OCCT IGES samples; raw.githubusercontent.com), denied by the API-only proxy; nothing was retrieved. Audit otherwise: chatgpt.com 70 and ab.chatgpt.com 1 allowed; 11 denied startup requests to oaiusercontent.com content CDNs. Disclose the attempted fetches.
- EVAL CONTRACT/TEST MISMATCH: technical-requirements-prompt.md section 1 says 'All subcommands take a final --output <path> flag' and its synopsis shows 'iges eval --input <file.iges> --de <n> --t <f> [--s <f>] --output <point.json>', but the IGES 1.0.21 hidden suite passes '--t <f> --output <path> --s <f>'. A submission that enforces the documented order loses every two-parameter (surface) evaluation test. 20 of this run's 22 failures come from that. The score is kept as graded under the frozen suite, but publication needs a note and the eval needs an author-eval decision (accept any flag order in the contract, or put --s before --output in the helper).
- Session turn context shows only gpt-6.1-terra; 1 turn; 86 commands; files written through shell commands; non-partial token accounting.
- Compared with published max runs: GPT-6.1 Sol 249/249, GPT-6 Sol 246/249, GPT-5.6 Terra 228/249.

### GPT-6.1 Terra high — `7231d8fb-a646-4d4b-bb2a-5a1b4c5c70c1`

- Score 178/249; status Incomplete.
- Failures: 71, across unimplemented entity layouts and evaluators (and the eval-only --s/--output order mismatch), matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at high effort (about 1-3 minutes); counted as a completed run.
- The IGES 1.0.21 --s-after---output test-helper issue (task card filed) may also affect this run's surface-evaluation tests.
- Compared with published high runs: GPT-6 Sol 242/249, GPT-6.1 Sol 164/249.

### GPT-6.1 Terra low — `07784ced-83da-479a-a988-3c628dfc01d5`

- Score 153/249; status Incomplete.
- Failures: 96, across unimplemented entities and evaluators (and possibly the --s/--output order mismatch), matching the gaps the last message lists.
- Network: None by the agent. API-only audit: chatgpt.com and ab.chatgpt.com allowed; 11 denied startup requests to oaiusercontent.com content CDNs.
- Session turn context shows only gpt-6.1-terra; 1 turn; non-partial token accounting.
- Model-side early stop at low effort (about 0.5-2 minutes); counted as a completed run.
- The IGES 1.0.21 --s-after---output test-helper issue (task card filed) may also affect this run's surface-evaluation tests.
- Compared with published low runs: GPT-6.1 Sol and GPT-6 Sol low are in published_results for reference.
