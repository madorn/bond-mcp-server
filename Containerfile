# Multi-stage build for Bond MCP Server
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as runtime

# Set environment variables for stdio and unbuffered output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Create non-root user for security
RUN groupadd -r bond && useradd -r -g bond bond

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Install the package in development mode (as root)
RUN pip install -e .

# Set ownership to non-root user
RUN chown -R bond:bond /app /opt/venv

# Switch to non-root user
USER bond

# Health check to ensure the server can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from bond_mcp.config import get_config; get_config(); sys.exit(0)" || exit 1

# Default environment variables
ENV BOND_TOKEN="" \
    BOND_HOST="" \
    LOG_LEVEL="INFO" \
    BOND_TIMEOUT="10.0"

# Expose port for documentation (not used for stdio communication)
EXPOSE 8080

# Set the entrypoint to the MCP server
# Using exec form to ensure proper signal handling
ENTRYPOINT ["python", "-m", "bond_mcp.server"]

# Add labels for metadata
LABEL org.opencontainers.image.title="Bond MCP Server" \
      org.opencontainers.image.description="Model Context Protocol server for Bond Bridge smart home devices" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="Bond MCP Server" \
      org.opencontainers.image.source="https://github.com/madorn/bond-mcp-server" \
      org.opencontainers.image.documentation="https://github.com/madorn/bond-mcp-server/blob/main/README.md"
