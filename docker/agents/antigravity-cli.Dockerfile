FROM clispecbench-base:latest

# Install Google Antigravity CLI (https://antigravity.google/cli/install.sh)
# Pin version, download URL, and SHA512 for reproducibility.
ARG ANTIGRAVITY_CLI_VERSION=1.0.3
ARG ANTIGRAVITY_CLI_URL=https://storage.googleapis.com/antigravity-public/antigravity-cli/1.0.3-6260531212976128/linux-x64/cli_linux_x64.tar.gz
ARG ANTIGRAVITY_CLI_SHA512=f6cf890d494f5fd00c696b4d2e541c894d5b10ff50bfd9f6dc02b915386e08b61c56140f17115898fc49f4aa4534581393098f35db70be9aae20dfde3ba5787c

RUN set -eux; \
    curl -fsSL "${ANTIGRAVITY_CLI_URL}" -o /tmp/antigravity-cli.tar.gz; \
    echo "${ANTIGRAVITY_CLI_SHA512}  /tmp/antigravity-cli.tar.gz" | sha512sum -c -; \
    tar -xzf /tmp/antigravity-cli.tar.gz -C /tmp antigravity; \
    install -m 0755 /tmp/antigravity /usr/local/bin/agy; \
    ln -sf /usr/local/bin/agy /usr/local/bin/antigravity; \
    rm -f /tmp/antigravity-cli.tar.gz /tmp/antigravity

WORKDIR /workspace
