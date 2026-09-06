FROM clispecbench-base:latest

# Install Codex CLI (https://www.npmjs.com/package/@openai/codex)
# Pin version for reproducibility — update when running new evaluations
ARG CODEX_CLI_VERSION=0.153.4
RUN npm install -g @openai/codex@${CODEX_CLI_VERSION}

WORKDIR /workspace
