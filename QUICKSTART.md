# Quick Start Guide

## Using Docker (Recommended)

### 1. Setup Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your credentials:
# - NEO4J_PASSWORD (required)
# - API_KEYS (recommended - comma-separated list, e.g., "key1,key2,key3")
# - CLIENT_API_KEY (required if API_KEYS is set)
# - OPENAI_API_KEY (optional)
```

### 2. Build and Run

```bash
# Using docker-compose (easiest)
docker-compose up

# Or build and run manually
docker build -t sejmofil-neo4j-mcp .
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  sejmofil-neo4j-mcp:latest
```

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
# Set your API key (if API_KEYS is configured in .env)
export CLIENT_API_KEY=your-key

# Run the server
uv run python -m sejmofil_mcp
```

## API Key Setup (3 Users)

Generate secure keys:

```bash
# Generate 3 random keys
openssl rand -hex 16  # → user1 key
openssl rand -hex 16  # → user2 key  
openssl rand -hex 16  # → user3 key
```

Add to `.env`:

```env
API_KEYS=<user1-key>,<user2-key>,<user3-key>
CLIENT_API_KEY=<user1-key>
```

Each user should use their own `CLIENT_API_KEY` value.

## Integration with Claude Desktop

Add to `~/.config/claude/config.json` (or `%APPDATA%\Claude\config.json` on Windows):

```json
{
  "mcpServers": {
    "sejmofil": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "NEO4J_PASSWORD=your_password",
        "-e", "API_KEYS=key1,key2,key3",
        "-e", "CLIENT_API_KEY=your_key",
        "sejmofil-neo4j-mcp:latest"
      ]
    }
  }
}
```

## Troubleshooting

**"Authorization failed"**: Check that `CLIENT_API_KEY` matches one of the keys in `API_KEYS`

**"Connection failed"**: Verify `NEO4J_HOST`, `NEO4J_USER`, and `NEO4J_PASSWORD` are correct

**Need more help?**: See [DOCKER.md](DOCKER.md) for detailed documentation

## Security Summary

✅ **No security vulnerabilities found** (verified with CodeQL)

Key security features:
- API key authentication for access control
- TLS encryption for Neo4j connections (bolt+s://)
- Environment-based configuration (no hardcoded secrets)
- Comprehensive security best practices documented in DOCKER.md
