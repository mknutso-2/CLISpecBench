FROM swe-buildbench-base:latest

# Install GitHub Copilot CLI (https://www.npmjs.com/package/@github/copilot)
# Pin version for reproducibility — update when running new evaluations
ARG COPILOT_CLI_VERSION=1.0.24
RUN npm install -g @github/copilot@${COPILOT_CLI_VERSION}

WORKDIR /workspace
