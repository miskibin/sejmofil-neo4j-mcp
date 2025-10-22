# Docker Build and Deployment Guide

This guide explains how to build and run the Sejmofil Neo4j MCP Server using Docker.

## Prerequisites

- Docker installed on your system
- Access to Neo4j database
- (Optional) OpenAI API key for semantic search features
- API keys for users who will access the server

## Building the Docker Image

The Dockerfile uses `uv` (a fast Python package installer) to install dependencies.

```bash
# Build the image
docker build -t sejmofil-neo4j-mcp:latest .

# Build with a specific tag
docker build -t sejmofil-neo4j-mcp:v1.0.0 .
```

## Running the Container

### Basic Run

```bash
docker run -it --rm \
  -e NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your_password \
  -e API_KEYS=user1-key,user2-key,user3-key \
  -e CLIENT_API_KEY=user1-key \
  sejmofil-neo4j-mcp:latest
```

### With Docker Compose

Create a `.env` file (use `.env.example` as template):

```bash
cp .env.example .env
# Edit .env with your credentials
```

Then run:

```bash
# Start the service
docker-compose up

# Run in background
docker-compose up -d

# Stop the service
docker-compose down
```

## API Key Configuration

### Setting Up API Keys

1. **Generate API Keys**: Create unique, secure API keys for each user
   ```bash
   # Example: Generate random keys
   openssl rand -hex 16  # user1-key
   openssl rand -hex 16  # user2-key
   openssl rand -hex 16  # user3-key
   ```

2. **Configure API_KEYS**: Set in environment or .env file
   ```env
   API_KEYS=user1-abc123,user2-def456,user3-ghi789
   ```

3. **Set CLIENT_API_KEY**: Each client uses their own key
   ```env
   CLIENT_API_KEY=user1-abc123
   ```

### Authorization Behavior

- **With API_KEYS set**: Server validates CLIENT_API_KEY on startup
  - Valid key → Server starts normally
  - Invalid/missing key → Server exits with error
  
- **Without API_KEYS set**: Authorization is disabled
  - Server starts without authentication (not recommended for production)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_HOST` | Yes | `bolt+s://neo.msulawiak.pl:7687` | Neo4j connection URL |
| `NEO4J_USER` | Yes | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | Yes | - | Neo4j password |
| `API_KEYS` | Recommended | - | Comma-separated list of valid API keys |
| `CLIENT_API_KEY` | If API_KEYS set | - | API key for this client |
| `OPENAI_API_KEY` | No | - | OpenAI API key for semantic search |
| `EMBEDDINGS_MODEL` | No | `text-embedding-3-small` | OpenAI embeddings model |

## Volume Mounts

Mount the logs directory to persist logs:

```bash
docker run -it --rm \
  -v $(pwd)/logs:/app/logs \
  -e NEO4J_PASSWORD=your_password \
  -e API_KEYS=key1,key2,key3 \
  -e CLIENT_API_KEY=key1 \
  sejmofil-neo4j-mcp:latest
```

## Integration with Claude Desktop

### Docker Configuration

Add this to your Claude Desktop config file:

**macOS/Linux**: `~/.config/claude/config.json`
**Windows**: `%APPDATA%\Claude\config.json`

```json
{
  "mcpServers": {
    "sejmofil": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687",
        "-e", "NEO4J_USER=neo4j",
        "-e", "NEO4J_PASSWORD=your_password",
        "-e", "API_KEYS=key1,key2,key3",
        "-e", "CLIENT_API_KEY=your-assigned-key",
        "-e", "OPENAI_API_KEY=your_openai_key",
        "sejmofil-neo4j-mcp:latest"
      ]
    }
  }
}
```

## Troubleshooting

### Build Issues

If the build fails due to network timeouts, try:

```bash
# Retry the build
docker build --no-cache -t sejmofil-neo4j-mcp:latest .

# Or use a different package index mirror (if available)
docker build --build-arg PIP_INDEX_URL=https://pypi.org/simple -t sejmofil-neo4j-mcp:latest .
```

### Authorization Errors

**Error: "Authorization required: CLIENT_API_KEY environment variable not set"**
- Make sure you set the CLIENT_API_KEY environment variable
- Check that the key matches one of the keys in API_KEYS

**Error: "Authorization failed: Invalid API key"**
- Verify the CLIENT_API_KEY matches exactly one of the keys in API_KEYS
- Check for extra spaces or typos in the keys

### Connection Issues

**Error: "Failed to connect to Neo4j"**
- Verify NEO4J_HOST, NEO4J_USER, and NEO4J_PASSWORD are correct
- Check network connectivity to the Neo4j server
- Ensure the Neo4j server is running and accessible

## Security Best Practices

1. **Use Strong API Keys**: Generate cryptographically random keys
   ```bash
   openssl rand -hex 32
   ```

2. **Keep Keys Secret**: Never commit API keys to version control
   - Use `.env` files (already in `.gitignore`)
   - Pass keys via environment variables
   - Use secrets management in production

3. **Rotate Keys Regularly**: Change API keys periodically

4. **Use HTTPS/TLS**: Ensure Neo4j connection uses TLS (`bolt+s://`)

5. **Limit Access**: Only give API keys to authorized users

## Production Deployment

For production environments:

1. Use a container orchestration platform (Kubernetes, Docker Swarm, etc.)
2. Store secrets in a secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
3. Enable API key authorization (set API_KEYS)
4. Use persistent volumes for logs
5. Monitor logs and set up alerts
6. Implement log rotation

Example Kubernetes deployment snippet:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sejmofil-secrets
type: Opaque
stringData:
  neo4j-password: your_password
  api-keys: user1-key,user2-key,user3-key
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sejmofil-mcp
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: sejmofil-mcp
        image: sejmofil-neo4j-mcp:latest
        env:
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: sejmofil-secrets
              key: neo4j-password
        - name: API_KEYS
          valueFrom:
            secretKeyRef:
              name: sejmofil-secrets
              key: api-keys
        - name: CLIENT_API_KEY
          valueFrom:
            secretKeyRef:
              name: sejmofil-secrets
              key: api-keys
```
