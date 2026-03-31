FROM swe-buildbench-base:latest

# Install Node.js (required for Gemini CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Gemini CLI (https://www.npmjs.com/package/@google/gemini-cli)
# Pin version for reproducibility — update when running new evaluations
ARG GEMINI_CLI_VERSION=0.35.3
RUN npm install -g @google/gemini-cli@${GEMINI_CLI_VERSION}

# Create directory for OpenTelemetry export
RUN mkdir -p /tmp/gemini-otel

WORKDIR /workspace
