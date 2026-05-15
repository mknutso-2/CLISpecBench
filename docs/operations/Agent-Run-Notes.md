# Agent Run Notes

This file records cross-agent operational findings that affect how CLISpecBench
runs should be interpreted. Eval-specific prompt, test, and version changes
still belong in each eval's `CHANGELOG.md`.

## Network Access Audit and Study Consistency

CLISpecBench's original design intent was that agent containers would only
reach the agent's required API endpoint, and would not browse the public web,
fetch packages, clone repositories, or contact unrelated services during a
benchmark run.

A May 2026 audit found that this intent was not fully enforced for historical
agent runs. Agent adapters exposed `allowed_hosts`, but the run path did not
wire those declarations into an active Docker network policy; agent containers
therefore ran on Docker's default bridge network. This allowed agent CLIs to
use their own built-in web-search facilities when those facilities were
available.

At this point in the current study, changing that access policy would create a
new experimental condition and make later results less comparable to the
already-published runs. For consistency, the current study should preserve the
same effective access level used by the existing published runs. A stricter
API-only/offline policy can be introduced only as a new, separately labeled
run series after the harness implements and verifies real egress controls.

### Codex CLI / OpenAI

Published Codex CLI transcripts contain structured `web_search` events in a
subset of OpenAI runs. Some are empty/non-query events, but others include
actual search queries or URL fetches. These runs should be interpreted as part
of the current web-access-enabled study condition, not as offline/API-only
runs.

The audit found this was not universal across all OpenAI published runs, but it
was common enough that OpenAI/Codex results should not be described as
network-isolated without checking the transcript and the run environment.

### Claude Code / Anthropic

Published Claude Code transcripts often list `WebSearch` and `WebFetch` as
available tools in the session initialization record. In the audited published
Anthropic runs, that was only tool advertisement: no actual `WebSearch` or
`WebFetch` tool-use events were found, and Claude's reported server tool-use
counters were zero.

These runs did not show evidence of web-search use, but the tool advertisement
and the historical lack of enforced container egress policy mean they should be
grouped under the same current study condition rather than presented as
strictly network-isolated runs.

### Publishing and Comparison Rule

For the current study, do not tighten network egress, disable CLI web-search
features, or omit otherwise valid runs solely because the transcript shows web
search or web fetch activity. Publish and compare runs only within the same
effective access condition, and keep noting observed web-search/web-fetch use
in audit notes or result metadata where practical.

If CLISpecBench later starts an offline/API-only study, that should be a new
run series with a clear label, verified network controls, and no mixing with
the current web-access-enabled results.
