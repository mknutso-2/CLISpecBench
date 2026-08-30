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

## Claude Code CLI Version Pins

All Claude Code runs report the single agent identity `claude-code`; the pinned
CLI version actually used is recorded per-run in `metadata.agent_version` and
surfaced on the dashboard. Three pins exist (see the variant table in
`src/clispecbench/agents/claude_code.py`):

- **2.1.120** (default, 2026-04-24) — the benchmark's standard pin; all
  4.5/4.6/4.7/4.8-generation runs use it.
- **2.0.2** (legacy) — for the deprecated 4.0-generation snapshot IDs, which
  2.1.120 no longer serves faithfully (it silently falls back to its default
  model; the served-vs-requested guard fails such runs).
- **2.1.174** (fable, 2026-06-11) — for Fable-family models. 2.1.120 predates
  Fable 5 and reproducibly cannot complete its RS274 runs: Fable's verbosity
  (single messages up to its full 128k output max) forces auto-compaction
  mid-session, and 2.1.120's compact request fails — observed both as an
  internal 20k-token cap on the compact summary (not configurable via
  `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, which only governs normal generation) and
  as a spurious Usage Policy refusal. After the failed compact, every API call
  returns "Prompt is too long" and the CLI exits 1 with no output written
  (6/6 attempts on 2026-06-11, ~$11-13 each). The npm `stable` dist-tag
  (2.1.153, 2026-05-27) also predates Fable's launch, so the pin uses the
  highest stable release at collection time. Comparisons against Fable runs
  therefore cross a CLI-version boundary; the dashboard's version column makes
  this visible. The fable variant additionally sets `API_TIMEOUT_MS=1800000`
  (30 min per request): Fable's single messages run up to its full 128k output
  max and can legitimately stream for 20+ minutes, and a 2026-06-12 attempt
  died "Request timed out" after exhausting all API retries despite verified
  host- and container-level connectivity.

## Antigravity CLI Status

Antigravity CLI (`agy`) support is experimental as of 1.0.5. With a TTY and the
credential workaround below, `agy` can run CLISpecBench tasks end-to-end: it
writes implementation files under `/workspace/output`, the harness builds them,
runs hidden tests, and writes normal `result.json` correctness scores. This is
enough for diagnostic correctness-only experiments, but not yet enough for
counted CLISpecBench results.

The remaining blockers are first-class run control and publication-quality
artifacts. Version 1.0.5 adds `--model` and a `models` subcommand, so the
adapter now passes `--model gemini-3.5-flash` by default and can honor explicit
model overrides. Local 1.0.5 logs verify that `gemini-3.5-flash` resolves to
`Gemini 3.5 Flash (Medium)`. Antigravity still does not expose effort/reasoning,
prompt-file, JSON, or output-file flags. Unlike Gemini CLI, no documented
settings-file equivalent to `thinkingLevel` has been found for scripted
Antigravity reasoning selection; simple probes for `gemini-3.5-flash-low` and
`gemini-3.5-flash-high` still resolved to the Medium label. Antigravity does not
currently provide parseable token usage, so `token_usage` and estimated cost
remain `null`.

The Gemini CLI comparison matters: CLISpecBench can set Gemini CLI effort for
Gemini 3.x models even though `gemini --help` does not expose `--effort`,
because the adapter patches the copied `/root/.gemini/settings.json` with
`modelConfigs.customOverrides` and
`generateContentConfig.thinkingConfig.thinkingLevel` before invoking `gemini`.

Headless output capture is also still unreliable. Public issue reports and
local smoke tests show that `agy --print` can authenticate, complete the model
call, and then exit 0 while emitting zero bytes to captured stdout when invoked
from a non-TTY subprocess. Logs show the response is generated internally, so
this is an output-path problem rather than only an auth problem. The harness
uses a TTY to avoid this for correctness runs, but empty Antigravity outputs
from non-TTY smoke tests should still be treated as `infra_agent_cli` unless a
future upstream release provides a reliable headless mode such as stdout
capture, JSON, or `--output`.

Transcripts need separate handling before publication. The run directory's
`transcript.jsonl` is only captured TTY/stdout text. Antigravity writes richer
JSONL transcripts under
`~/.gemini/antigravity-cli/brain/<conversation-id>/.system_generated/logs/`,
including user input, tool calls, file views, command results, and `thinking`
fields, but the harness does not yet copy the matching conversation into each
run directory or scrub account/auth metadata from saved logs.

Credential behavior is also not equivalent to Gemini CLI. In Linux containers,
`agy` uses file-based token storage when it detects the container environment,
while a Windows host-side `agy` login stores OAuth state in Windows Credential
Manager under the `gemini:antigravity` target. A local workaround is to seed the
Credential Manager JSON into
`~/.gemini/antigravity-cli/antigravity-oauth-token` before mounting
`~/.gemini/antigravity-cli` into Docker; this passed the container smoke test
locally on 1.0.3 and 1.0.5 and lets `agy` authenticate inside the harness
container. That file contains a plaintext OAuth refresh token, so keep it out of
the repo, logs, and shared artifacts. The Antigravity smoke test remains
diagnostic and may still fail with an auth timeout if the token file is absent,
or empty output on current releases when stdout is captured without a TTY.

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

Those results remain a separate historical condition. Do not mix them with
new runs protected by the harness's Docker-level API-only egress controls.

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

### API-only restart and comparison rule

On August 30, 2026, the GPT-5.6 Codex collection restarted under an `api-only`
condition. Each agent container is attached only to a fresh Docker `--internal`
bridge network, which has no external route. A separate per-run CONNECT proxy
is attached to both that network and Docker's egress bridge; it permits only
port 443 to the adapter's declared API hostname (for Codex, `chatgpt.com`) and
rejects every other destination. The agent receives proxy variables pointing
to the proxy's internal IP and no usable DNS resolver. Codex runs in external-
sandbox mode inside that Docker boundary, and `web_search="disabled"` plus
`tools.web_search=false` removes the separate hosted search surface.

The container keeps Docker's default seccomp profile. Do not add
`seccomp=unconfined`: the Docker network is the isolation boundary, so Codex
does not need to create a nested bubblewrap namespace. The proxy records each
allow/deny decision in `network-audit.jsonl`, referenced by
`artifacts.network_audit` in the run result.

The required probes verify that direct IP egress, external DNS resolution, and
a proxy request to a non-allowlisted host all fail; a Luna/max model request
still reaches `chatgpt.com`; a model-invoked `curl` to `example.com` is denied;
and hosted web search is unavailable. Re-run `TestRestrictedEgress` and
`TestCodexNetworkIsolation` after changing Docker networking, the Codex CLI,
or its invocation flags.

All pre-change results remain `web-enabled`. New results record `api-only` in
`metadata.network_policy`. Publish and compare results only within the same
network condition; never combine the earlier web-enabled runs with this
restart series in Best/Mean calculations.
