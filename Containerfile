# Bond MCP Server - Single stage build
FROM fedora-minimal:latest

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python runtime and clean up
RUN dnf update -y && dnf install -y \
    python3 \
    python3-pip \
    && dnf clean all \
    && rm -rf /var/cache/dnf/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create non-root user for security
RUN groupadd -r bond && useradd -r -g bond bond

# Create app directory and copy application files
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/

# Install the package
RUN python3 -m pip install --no-cache-dir .

# Set ownership and switch to non-root user
RUN chown -R bond:bond /app
USER bond

# Health check to ensure the server can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; from bond_mcp.config import get_config; get_config(); sys.exit(0)" || exit 1

# Default environment variables
ENV BOND_TOKEN="" \
    BOND_HOST="" \
    LOG_LEVEL="INFO" \
    BOND_TIMEOUT="10.0"

# Set the entrypoint to the MCP server
# Using exec form to ensure proper signal handling
ENTRYPOINT ["python3", "-m", "bond_mcp.server"]

# Add labels for metadata
LABEL org.opencontainers.image.title="Bond MCP Server" \
      org.opencontainers.image.description="Model Context Protocol server for Bond Bridge smart home devices" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="Bond MCP Server" \
      org.opencontainers.image.source="https://github.com/madorn/bond-mcp-server" \
      org.opencontainers.image.documentation="https://github.com/madorn/bond-mcp-server/blob/main/README.md"
