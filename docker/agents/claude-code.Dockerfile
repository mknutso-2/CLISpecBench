FROM swe-buildbench-base:latest

# Install Claude Code CLI (https://www.npmjs.com/package/@anthropic-ai/claude-code)
# Pin version for reproducibility — update when running new evaluations
ARG CLAUDE_CODE_VERSION=2.1.90
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/otel

WORKDIR /workspace
