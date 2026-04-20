FROM clispecbench-base:latest

# Install Claude Code CLI (https://www.npmjs.com/package/@anthropic-ai/claude-code)
# Pin version for reproducibility — update when running new evaluations
ARG CLAUDE_CODE_VERSION=2.1.90
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/otel

# Create non-root user — Claude Code refuses --dangerously-skip-permissions as root.
# The container starts as root so that copy_in can write to /workspace, then the
# invoke command uses `su agent` to drop privileges before running claude.
RUN useradd -m -s /bin/bash agent \
    && chown agent:agent /tmp/otel

WORKDIR /workspace
