FROM swe-buildbench-base:latest

# Install Node.js (required for Codex CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Codex CLI (https://www.npmjs.com/package/@openai/codex)
# Pin version for reproducibility — update when running new evaluations
ARG CODEX_CLI_VERSION=0.1.0
RUN npm install -g @openai/codex@${CODEX_CLI_VERSION}

WORKDIR /workspace
