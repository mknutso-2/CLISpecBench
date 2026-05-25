# Agent Run Notes

This file records cross-agent operational findings that affect how CLISpecBench
runs should be interpreted. Eval-specific prompt, test, and version changes
still belong in each eval's `CHANGELOG.md`.

## Claude Code Authentication for Unattended Runs

Claude Desktop being open and signed in is not sufficient evidence that
headless Claude Code evals will authenticate. The eval harness runs the
standalone `claude --print` CLI inside Docker and mounts only the host
`~/.claude/.credentials.json` and `~/.claude/settings.json` files into the
container. On Windows + WSL2 Docker, those files must be refreshed from the
Windows host profile (`C:\Users\<you>\.claude`), not from WSL.

If Claude Code evals fast-fail with 401/403 errors and no source artifacts,
treat the run as `infra_auth`: rerun only after refreshing the CLI credentials
with `/login` or `claude auth login` on the Windows host and passing
`scripts/smoke-test-claude.sh`.

For long unattended Claude queues, Anthropic documents `claude setup-token` as
the non-interactive path: it generates a one-year OAuth token for scripts and
CI, which can be supplied to Claude Code through `CLAUDE_CODE_OAUTH_TOKEN`.
Use that only when the run launcher can keep the token out of logs and shell
history, and verify the behavior with the Claude smoke test before counting
the runs.

## Antigravity CLI Status

Antigravity CLI (`agy`) support is experimental as of 1.0.2. The upstream
1.0.1 changelog says OAuth token persistence and authentication hangs were
fixed, and public WSL reports indicate 1.0.2 improves some credential
persistence cases. This does not yet make `agy` suitable for counted
CLISpecBench runs.

The remaining blocker is headless output capture. Public issue reports and
local smoke tests show that `agy --print` can authenticate, complete the model
call, and then exit 0 while emitting zero bytes to captured stdout when invoked
from a non-TTY subprocess. Logs show the response is generated internally, so
this is an output-path problem rather than only an auth problem. Treat empty
Antigravity outputs as `infra_agent_cli` unless a future upstream release
provides a reliable headless mode such as stdout capture, JSON, or `--output`.

Credential behavior is also not equivalent to Gemini CLI. In Linux containers,
`agy` uses file-based token storage when it detects the container environment,
but Windows Credential Manager state from a host-side `agy` login is not
portable into Docker by mounting `~/.gemini/antigravity-cli` alone. The
Antigravity smoke test remains diagnostic and may fail with an auth timeout or
empty output on current releases.

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
