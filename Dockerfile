# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Install uv - fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --system flag installs to system Python instead of creating a virtual environment
RUN uv sync --frozen --no-dev --system

# Copy application code
COPY sejmofil_mcp ./sejmofil_mcp/
COPY db_schema.json ./

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "-m", "sejmofil_mcp"]
