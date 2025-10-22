# Quick Start Guide

## Using Docker (Recommended)

### 1. Setup Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your credentials:
# - NEO4J_PASSWORD (required)
# - API_KEY (recommended - single shared key)
# - OPENAI_API_KEY (optional)
```

### 2. Build and Run

```bash
# Using docker-compose (easiest)
docker-compose up

# Or build and run manually
docker build -t sejmofil-neo4j-mcp .
docker run -it --rm \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  sejmofil-neo4j-mcp:latest
```

The server uses SSE transport on port 8000.

## Using uv (Development)

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
```

### 3. Run Server

```bash
# Set your API key (if API_KEY is configured in .env)
export API_KEY=your-key

# Run the server
uv run python -m sejmofil_mcp
```

## API Key Setup

Generate a secure key:

```bash
# Generate a random key
openssl rand -hex 16
```

Add to `.env`:

```env
API_KEY=<your-generated-key>
```

All users share the same `API_KEY` value.

## Integration with Claude Desktop

Add to `~/.config/claude/config.json` (or `%APPDATA%\Claude\config.json` on Windows):

```json
{
  "mcpServers": {
    "sejmofil": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-p", "8000:8000",
        "-e", "NEO4J_PASSWORD=your_password",
        "-e", "API_KEY=your_key",
        "sejmofil-neo4j-mcp:latest"
      ]
    }
  }
}
```

## Troubleshooting

**"Authorization failed"**: Check that `API_KEY` environment variable matches the configured key

**"Connection failed"**: Verify `NEO4J_HOST`, `NEO4J_USER`, and `NEO4J_PASSWORD` are correct

**Need more help?**: See [DOCKER.md](DOCKER.md) for detailed documentation

## Security Summary

✅ **No security vulnerabilities found** (verified with CodeQL)

Key security features:
- Simple API key authentication for access control
- TLS encryption for Neo4j connections (bolt+s://)
- Environment-based configuration (no hardcoded secrets)
- Comprehensive security best practices documented in DOCKER.md
