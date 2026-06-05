FROM clispecbench-base:latest

# Install Google Antigravity CLI (https://antigravity.google/cli/install.sh)
# Pin version, download URL, and SHA512 for reproducibility.
ARG ANTIGRAVITY_CLI_VERSION=1.0.5
ARG ANTIGRAVITY_CLI_URL=https://github.com/google-antigravity/antigravity-cli/releases/download/1.0.5/agy_cli_linux_x64.tar.gz
ARG ANTIGRAVITY_CLI_SHA512=72082d89ea71e101c7beb1630241428d53f68c702995897a2bbf55f162a9f71c8d2d7f98e7b310449cfbdb0b053f6e1b869c1f8d9fb23c95851e980d563d8924

RUN set -eux; \
    curl -fsSL "${ANTIGRAVITY_CLI_URL}" -o /tmp/antigravity-cli.tar.gz; \
    echo "${ANTIGRAVITY_CLI_SHA512}  /tmp/antigravity-cli.tar.gz" | sha512sum -c -; \
    tar -xzf /tmp/antigravity-cli.tar.gz -C /tmp antigravity; \
    install -m 0755 /tmp/antigravity /usr/local/bin/agy; \
    ln -sf /usr/local/bin/agy /usr/local/bin/antigravity; \
    rm -f /tmp/antigravity-cli.tar.gz /tmp/antigravity

WORKDIR /workspace
