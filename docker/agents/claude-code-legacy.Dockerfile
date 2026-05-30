FROM clispecbench-base:latest

# Legacy Claude Code CLI image — pins a mid-2025 (2.0.x line) version that still
# recognizes the deprecated Claude 4.0-generation snapshot IDs
# (claude-opus-4-20250514, claude-sonnet-4-20250514, claude-opus-4-1-20250805).
#
# WHY THIS EXISTS: the current pinned CLI (claude-code.Dockerfile, 2.1.120)
# silently falls back to its default model (Opus 4.7) when given those snapshot
# IDs — it no longer carries them in its model allowlist. claude-code 2.0.2
# (2025-09-30) serves them faithfully. See .claude/skills/run-eval/SKILL.md
# ("Silent model fallback") and the served-vs-requested model guard in the
# harness.
#
# CONFOUNDS (documented so results aren't misread):
#   * Different CLI generation (2.0.2 vs 2.1.120) = different agent scaffolding;
#     4.0-gen numbers are NOT a clean apples-to-apples vs 4.5/4.6/4.7 on the
#     newer CLI. Results are kept under the distinct agent id
#     "claude-code-legacy" to make this explicit.
#   * 2.0.2 has no --effort flag. The 4.0 generation controls reasoning via the
#     MAX_THINKING_TOKENS budget instead; the adapter sets it to 31999
#     ("ultrathink" ceiling) as the generation's maximum-reasoning setting.
ARG CLAUDE_CODE_VERSION=2.0.2
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/otel

# Create non-root user — Claude Code refuses --dangerously-skip-permissions as root.
RUN useradd -m -s /bin/bash agent \
    && chown agent:agent /tmp/otel

WORKDIR /workspace
