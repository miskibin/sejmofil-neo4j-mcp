# Docker Build and Deployment Guide

This guide explains how to build and run the Sejmofil Neo4j MCP Server using Docker.

## Prerequisites

- Docker installed on your system
- Access to Neo4j database
- (Optional) OpenAI API key for semantic search features
- (Optional) API key for server authorization

## Building the Docker Image

The Dockerfile follows the [official uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/#installing-a-project) for optimal caching and build performance.

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
  -e API_KEY=your-secret-key \
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

### Setting Up API Key

1. **Generate API Key**: Create a secure API key
   ```bash
   # Example: Generate random key
   openssl rand -hex 16
   ```

2. **Configure API_KEY**: Set in environment or .env file
   ```env
   API_KEY=your-generated-secret-key
   ```

### Authorization Behavior

- **With API_KEY set**: Server validates the API_KEY on startup
  - Valid key → Server starts normally
  - Invalid/missing key → Server exits with error
  
- **Without API_KEY set**: Authorization is disabled
  - Server starts without authentication (not recommended for production)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_HOST` | Yes | `bolt+s://neo.msulawiak.pl:7687` | Neo4j connection URL |
| `NEO4J_USER` | Yes | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | Yes | - | Neo4j password |
| `API_KEY` | Recommended | - | API key for authorization (shared by all users) |
| `OPENAI_API_KEY` | No | - | OpenAI API key for semantic search |
| `EMBEDDINGS_MODEL` | No | `text-embedding-3-small` | OpenAI embeddings model |

## Volume Mounts

Mount the logs directory to persist logs:

```bash
docker run -it --rm \
  -v $(pwd)/logs:/app/logs \
  -e NEO4J_PASSWORD=your_password \
  -e API_KEY=your-secret-key \
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
        "-e", "API_KEY=your-secret-key",
        "-e", "OPENAI_API_KEY=your_openai_key",
        "sejmofil-neo4j-mcp:latest"
      ]
    }
  }
}
```

## Troubleshooting

### Build Issues

If the build fails, try:

```bash
# Clean rebuild
docker build --no-cache -t sejmofil-neo4j-mcp:latest .
```

### Authorization Errors

**Error: "Authorization required: API_KEY environment variable not set"**
- Make sure you set the API_KEY environment variable
- Check that the key matches the configured API_KEY

**Error: "Authorization failed: Invalid API key"**
- Verify the API_KEY matches exactly
- Check for extra spaces or typos

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

5. **Limit Access**: Only share the API key with authorized users

## Production Deployment

For production environments:

1. Use a container orchestration platform (Kubernetes, Docker Swarm, etc.)
2. Store secrets in a secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
3. Enable API key authorization (set API_KEY)
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
  api-key: your-secret-key
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
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: sejmofil-secrets
              key: api-key
```
