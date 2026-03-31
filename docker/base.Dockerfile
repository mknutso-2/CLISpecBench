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
    && rm -rf /var/lib/apt/lists/*

# Pin compiler version for reproducibility
ENV CC=gcc-14 CXX=g++-14

# Install pytest and json-report plugin for test execution
RUN python3 -m pip install --break-system-packages \
    pytest \
    pytest-json-report

WORKDIR /workspace
