FROM clispecbench-base:latest

# Install Google Antigravity CLI (https://antigravity.google/cli/install.sh)
# Pin version, download URL, and SHA512 for reproducibility.
ARG ANTIGRAVITY_CLI_VERSION=1.4.10
ARG ANTIGRAVITY_CLI_URL=https://github.com/google-antigravity/antigravity-cli/releases/download/1.4.10/agy_cli_linux_x64.tar.gz
ARG ANTIGRAVITY_CLI_SHA512=3a14c21697e86349ce8402e0b1889cbd1d3a5f4e2cb4dc43aae1c48c404240c2ccff9f775eec277e1f759234a33ec026645c63ed22ab6f6ebede561eda7c38b6

RUN set -eux; \
    curl -fsSL "${ANTIGRAVITY_CLI_URL}" -o /tmp/antigravity-cli.tar.gz; \
    echo "${ANTIGRAVITY_CLI_SHA512}  /tmp/antigravity-cli.tar.gz" | sha512sum -c -; \
    tar -xzf /tmp/antigravity-cli.tar.gz -C /tmp antigravity; \
    install -m 0755 /tmp/antigravity /usr/local/bin/agy; \
    ln -sf /usr/local/bin/agy /usr/local/bin/antigravity; \
    rm -f /tmp/antigravity-cli.tar.gz /tmp/antigravity

WORKDIR /workspace
