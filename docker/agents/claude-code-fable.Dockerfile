FROM clispecbench-base:latest

# Install Claude Code CLI (https://www.npmjs.com/package/@anthropic-ai/claude-code)
# Fable-generation pin: the benchmark default (claude-code.Dockerfile, 2.1.120,
# 2026-04-24) predates Fable 5 and cannot complete its runs — Fable's verbose
# sessions require auto-compaction, and 2.1.120's compact path fails on them
# (internal 20k-token compact-summary cap; see docs/operations/Agent-Run-Notes.md).
# 2.1.174 is the highest stable release as of the Fable runs (2026-06-11); the
# npm "stable" dist-tag (2.1.153, 2026-05-27) also predates Fable's launch.
ARG CLAUDE_CODE_VERSION=2.1.174
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/otel

# Create non-root user — Claude Code refuses --dangerously-skip-permissions as root.
# The container starts as root so that copy_in can write to /workspace, then the
# invoke command uses `su agent` to drop privileges before running claude.
RUN useradd -m -s /bin/bash agent \
    && chown agent:agent /tmp/otel

WORKDIR /workspace
