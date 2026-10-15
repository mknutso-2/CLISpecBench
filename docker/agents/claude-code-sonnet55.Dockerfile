FROM clispecbench-base:latest

# Sonnet 5.5 requires Claude Code >=2.1.284. This separate generation pin
# preserves the older Sonnet 5 image and its CLI metadata.
# https://code.claude.com/docs/en/model-config
ARG CLAUDE_CODE_VERSION=2.1.289
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

RUN mkdir -p /tmp/otel
RUN useradd -m -s /bin/bash agent \
    && chown agent:agent /tmp/otel

WORKDIR /workspace
