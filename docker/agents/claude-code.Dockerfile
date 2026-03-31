FROM swe-buildbench-base:latest

# Install Node.js (required for Claude Code CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI (https://www.npmjs.com/package/@anthropic-ai/claude-code)
# Pin version for reproducibility — update when running new evaluations
ARG CLAUDE_CODE_VERSION=1.0.16
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/otel

WORKDIR /workspace
