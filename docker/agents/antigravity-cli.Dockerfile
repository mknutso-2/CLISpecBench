FROM clispecbench-base:latest

# Install Google Antigravity CLI (https://antigravity.google/cli/install.sh)
# Pin version, download URL, and SHA512 for reproducibility.
ARG ANTIGRAVITY_CLI_VERSION=1.0.2
ARG ANTIGRAVITY_CLI_URL=https://storage.googleapis.com/antigravity-public/antigravity-cli/1.0.2-6109799369277440/linux-x64/cli_linux_x64.tar.gz
ARG ANTIGRAVITY_CLI_SHA512=131f5f38304082936f81ec8fda9aa3911231090f5aa3b27ead57c3de5d95c0ef95b281a6c02d81cb82beb8498455004fdbb62f0f09273d5c84bbb5e7a0f33086

RUN set -eux; \
    curl -fsSL "${ANTIGRAVITY_CLI_URL}" -o /tmp/antigravity-cli.tar.gz; \
    echo "${ANTIGRAVITY_CLI_SHA512}  /tmp/antigravity-cli.tar.gz" | sha512sum -c -; \
    tar -xzf /tmp/antigravity-cli.tar.gz -C /tmp antigravity; \
    install -m 0755 /tmp/antigravity /usr/local/bin/agy; \
    ln -sf /usr/local/bin/agy /usr/local/bin/antigravity; \
    rm -f /tmp/antigravity-cli.tar.gz /tmp/antigravity

WORKDIR /workspace
