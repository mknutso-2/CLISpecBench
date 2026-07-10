FROM clispecbench-base:latest

# Install Claude Code CLI (https://www.npmjs.com/package/@anthropic-ai/claude-code)
# Sonnet-5-generation pin: the benchmark default (claude-code.Dockerfile,
# 2.1.120, 2026-04-24) predates Claude Sonnet 5 (released 2026-06-30) and cannot
# serve it — an unrecognized --model silently falls back to the CLI's default,
# which the served-vs-requested guard rejects. 2.1.197 is the highest release
# available on the model's launch day; the npm "stable" dist-tag (2.1.185) is a
# few days older, so this pins the newest release to guarantee Sonnet 5 support.
ARG CLAUDE_CODE_VERSION=2.1.197
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/otel

# Create non-root user — Claude Code refuses --dangerously-skip-permissions as root.
# The container starts as root so that copy_in can write to /workspace, then the
# invoke command uses `su agent` to drop privileges before running claude.
RUN useradd -m -s /bin/bash agent \
    && chown agent:agent /tmp/otel

WORKDIR /workspace
