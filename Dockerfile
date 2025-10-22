# Use Python 3.13 slim image as base

# Stage 1: Build dependencies and project in editable mode
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies only (not the project)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy project files
COPY . /app

# Install the project (non-editable)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Stage 2: Minimal runtime image
FROM python:3.13-slim
WORKDIR /app
# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
# Copy only necessary source files (for static assets, config, etc.)
COPY --from=builder /app/sejmofil_mcp /app/sejmofil_mcp

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
# Expose port 8000 for SSE transport
EXPOSE 8000
# Run the MCP server
CMD ["python", "-m", "sejmofil_mcp"]
