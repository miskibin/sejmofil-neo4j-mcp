# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Install uv - fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set environment variable for uv to use system Python
ENV UV_SYSTEM_PYTHON=1

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install dependencies using uv pip
# Using --no-cache to avoid cache issues
RUN uv pip install --no-cache \
    loguru>=0.7.3 \
    "mcp[cli]>=1.18.0" \
    neo4j>=6.0.2 \
    openai>=2.6.0 \
    pydantic-settings>=2.11.0 \
    pydantic>=2.12.3 \
    python-dotenv>=1.1.1

# Copy application code
COPY sejmofil_mcp ./sejmofil_mcp/
COPY db_schema.json ./

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "-m", "sejmofil_mcp"]
