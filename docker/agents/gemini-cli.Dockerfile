FROM swe-buildbench-base:latest

# Install Gemini CLI (https://www.npmjs.com/package/@google/gemini-cli)
# Pin version for reproducibility — update when running new evaluations
ARG GEMINI_CLI_VERSION=0.36.0
RUN npm install -g @google/gemini-cli@${GEMINI_CLI_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/gemini-otel

WORKDIR /workspace
