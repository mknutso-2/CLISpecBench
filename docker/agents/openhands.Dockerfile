FROM clispecbench-base:latest

# Install OpenHands CLI (https://pypi.org/project/openhands/)
# Pin version for reproducibility — update when running new evaluations.
ARG OPENHANDS_VERSION=1.16.0
RUN python3 -m pip install --break-system-packages \
    "opentelemetry-instrumentation==0.60b1" \
    "opentelemetry-instrumentation-threading==0.60b1" \
    "openhands==${OPENHANDS_VERSION}"

WORKDIR /workspace
