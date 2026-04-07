FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++-14 \
    python3 \
    python3-pip \
    python3-venv \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 from NodeSource (Ubuntu 24.04 ships Node 18, too old for CLI agents)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Rust stable toolchain via rustup (for --language=rs eval variants)
ENV RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --default-toolchain stable --profile minimal --no-modify-path \
    && chmod -R a+w $RUSTUP_HOME $CARGO_HOME

# Pin compiler version for reproducibility
ENV CC=gcc-14 CXX=g++-14

# Install pytest and json-report plugin for test execution
RUN python3 -m pip install --break-system-packages \
    pytest \
    pytest-json-report

WORKDIR /workspace
