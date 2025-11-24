# PolyFuture Backend Template
# Pre-configured Python 3.12 with all required packages

FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install Python 3.12
RUN uv python install 3.12

# Create user home directory
RUN mkdir -p /home/user
WORKDIR /home/user

# Create virtual environment with Python 3.12
RUN uv venv /home/user/.venv --python 3.12

# Install all required packages
RUN uv pip install --python /home/user/.venv/bin/python \
    fastapi \
    uvicorn \
    e2b-code-interpreter \
    anthropic \
    httpx \
    pydantic \
    mcp \
    python-dotenv \
    mesa==2.1.5 \
    numpy \
    pandas \
    plotly

# Set PATH to use venv Python by default
ENV PATH="/home/user/.venv/bin:$PATH"

# Verify installation
RUN python --version && pip list | grep -E 'mcp|fastapi|anthropic'

# Set working directory for app
WORKDIR /home/user/app
