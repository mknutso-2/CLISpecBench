FROM clispecbench-base:latest

# Claude Code 2.1.293 adds Claude Haiku 5.5. This separate generation pin
# preserves the older Claude images and their CLI metadata.
# https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
ARG CLAUDE_CODE_VERSION=2.1.293
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

RUN mkdir -p /tmp/otel
RUN useradd -m -s /bin/bash agent \
    && chown agent:agent /tmp/otel

WORKDIR /workspace
