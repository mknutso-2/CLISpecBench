FROM clispecbench-base:latest

# Install OpenCode CLI (https://www.npmjs.com/package/opencode-ai)
# Pin version for reproducibility — update when running new evaluations.
ARG OPENCODE_VERSION=1.14.41
RUN npm install -g opencode-ai@${OPENCODE_VERSION}

WORKDIR /workspace
