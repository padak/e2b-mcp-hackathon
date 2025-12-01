# E2B Template for LLM Prediction Arena
# Contains: Node.js 18 + Python 3.11 + claude-code-router

FROM e2bdev/code-interpreter:latest

# Install Node.js 18 (for claude-code-router)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    node --version && npm --version

# Install claude-code-router globally
RUN npm install -g @musistudio/claude-code-router && \
    which ccr || echo "ccr not found in PATH"

# Create router config directory (E2B runs as 'user', not root)
RUN mkdir -p /home/user/.claude-code-router

# Copy router config (will be overwritten with API key at runtime)
COPY router-config.json /home/user/.claude-code-router/config.json
RUN chown -R user:user /home/user/.claude-code-router

# Install Python dependencies for arena
RUN pip install --no-cache-dir \
    anthropic \
    openai \
    mesa==2.1.5 \
    numpy \
    pandas \
    scipy

# Verify installations
RUN python3 --version && \
    node --version && \
    pip show anthropic | grep Version

# Keep sandbox running
CMD ["sleep", "infinity"]
