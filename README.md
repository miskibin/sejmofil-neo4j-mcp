# Sejmofil Neo4j MCP Server

Model Context Protocol server for querying Polish parliamentary data from Neo4j graph database.

## Features

- 🔍 **Semantic Search**: Find legislative prints using AI-powered semantic search
- 📊 **Process Tracking**: Check status of legislative processes (active/finished)
- 👥 **MP Activity**: Query member of parliament legislative activity
- 🏷️ **Topic Analysis**: Find similar topics and get statistics
- 📝 **Detailed Information**: Get comprehensive details about prints, processes, and MPs

## Installation

### Option 1: Using uv (Recommended for Development)

```bash
# Install dependencies using uv
uv sync

# Or with pip
pip install -e .
```

### Option 2: Using Docker (Recommended for Production)

```bash
# Build the Docker image
docker build -t sejmofil-neo4j-mcp .

# Or use docker-compose
docker-compose build
```

## Configuration

Create a `.env` file (copy from `.env.example`):

```env
NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key  # Optional, for semantic search
EMBEDDINGS_MODEL=text-embedding-3-small

# API Key Authorization (optional but recommended)
# Comma-separated list of valid API keys
API_KEYS=user1-secret-key,user2-secret-key,user3-secret-key

# When running the server, set this to one of the API keys from API_KEYS
CLIENT_API_KEY=user1-secret-key
```

### API Key Authorization

The server supports simple but effective API key authorization:

- **API_KEYS**: Comma-separated list of valid API keys (one for each user)
- **CLIENT_API_KEY**: The API key used by the client to authenticate

If `API_KEYS` is not set, authorization is disabled (not recommended for production).

**Example:**
```bash
# Set up 3 API keys for 3 users
API_KEYS=abc123,def456,ghi789

# User 1 connects with:
CLIENT_API_KEY=abc123

# User 2 connects with:
CLIENT_API_KEY=def456

# User 3 connects with:
CLIENT_API_KEY=ghi789
```

## Running the Server

### Using Docker (Recommended for Production)

```bash
# Using docker-compose (easiest)
docker-compose up

# Or run the container directly
docker run -it --rm \
  -e NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your_password \
  -e API_KEYS=key1,key2,key3 \
  -e CLIENT_API_KEY=key1 \
  -v $(pwd)/logs:/app/logs \
  sejmofil-neo4j-mcp:latest
```

### Using MCP Inspector (Recommended for testing)

```bash
# Install MCP Inspector globally if you haven't
npx @modelcontextprotocol/inspector

# Run the server with inspector
uv run mcp dev sejmofil_mcp/server.py
```

The inspector will open in your browser. Try these example tool calls:

```json
// Example 1: Search active prints about taxes
{
  "name": "search_active_prints_by_topic",
  "arguments": {
    "topic": "podatki",
    "limit": 5
  }
}

// Example 2: Get print details
{
  "name": "get_print_details",
  "arguments": {
    "print_number": "1"
  }
}

// Example 3: Find MP by name
{
  "name": "find_mp_by_name",
  "arguments": {
    "name": "Tusk"
  }
}
```

### Running directly

```bash
uv run python -m sejmofil_mcp
```

## Testing

### Quick connection test
```bash
uv run python test_connection.py
```

### Test embeddings (requires OPENAI_API_KEY)
```bash
uv run python test_embeddings.py
```

### Test all workflows
```bash
uv run python test_workflows.py
```

### Comprehensive debug tests
```bash
uv run python debug_queries.py
```

## Available Tools

### 1. `search_active_prints_by_topic`
Find currently processed parliamentary prints on a specific topic.

**Arguments:**
- `topic` (str): Topic in Polish (e.g., "podatki", "obrona narodowa")
- `limit` (int): Max results (default: 10)

**Example:**
```
Topic: "podatki"
Returns: Active tax-related legislative prints
```

### 2. `get_print_details`
Get comprehensive information about a specific print.

**Arguments:**
- `print_number` (str): Print number (e.g., "1234")

**Returns:** Full metadata, authors, topics, organizations, current stage, comments

### 3. `get_process_status`
Check if a legislative process is active or finished.

**Arguments:**
- `process_number` (str): Process number

**Returns:** Status (active/finished), current stage, all stages with dates

### 4. `find_mp_by_name`
Find members of parliament by name.

**Arguments:**
- `name` (str): MP name or partial name

**Returns:** List of matching MPs with club and role info

### 5. `get_mp_activity`
Get legislative activity for a member of parliament.

**Arguments:**
- `person_id` (int): MP's ID number

**Returns:** Authored prints, speeches count, committee memberships

### 6. `get_similar_topics`
Find semantically similar topics.

**Arguments:**
- `topic_name` (str): Topic name
- `limit` (int): Max results (default: 5)

**Returns:** Similar topics with similarity scores

### 7. `get_topic_statistics`
Get statistics about a parliamentary topic.

**Arguments:**
- `topic_name` (str): Topic name

**Returns:** Total prints, active prints, finished prints

### 8. `search_all`
Search across all entity types.

**Arguments:**
- `query` (str): Search query in Polish
- `limit` (int): Results per category (default: 10)

**Returns:** Prints and MPs matching the query

## Architecture

```
sejmofil_mcp/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── server.py            # MCP server with tool definitions
├── config.py            # Configuration from environment
├── neo4j_client.py      # Neo4j database client
├── embeddings.py        # OpenAI embeddings service
├── models.py            # Pydantic data models
└── queries.py           # Cypher query service
```

## Example Queries

### Find active prints about taxes
```python
search_active_prints_by_topic(topic="podatki", limit=5)
```

### Get details about a specific print
```python
get_print_details(print_number="1234")
```

### Check if a process is still active
```python
get_process_status(process_number="567")
```

### Find MP and their activity
```python
# First find by name
mps = find_mp_by_name(name="Kowalski")

# Then get their activity
activity = get_mp_activity(person_id=mps[0].id)
```

## Database Schema

The server queries a Neo4j database with the following main entities:

- **Print** - Parliamentary documents (druki sejmowe)
- **Process** - Legislative processes
- **Stage** - Process stages
- **Person** - Members of parliament
- **Topic** - Thematic categories
- **Organization** - Institutions
- **Committee** - Parliamentary committees
- **Voting** - Voting records

## Logging

Logs are written to:
- Console (INFO level)
- `logs/sejmofil_mcp_{time}.log` (DEBUG level, rotated daily)
- `logs/debug_{time}.log` (for debug scripts)

## Integration with Claude Desktop

Add to Claude Desktop config:

### Without Docker

```json
{
  "mcpServers": {
    "sejmofil": {
      "command": "uv",
      "args": [
        "--directory",
        "E:\\neo4j-mcp",
        "run",
        "python",
        "-m",
        "sejmofil_mcp"
      ],
      "env": {
        "CLIENT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### With Docker

```json
{
  "mcpServers": {
    "sejmofil": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687",
        "-e",
        "NEO4J_USER=neo4j",
        "-e",
        "NEO4J_PASSWORD=your_password",
        "-e",
        "API_KEYS=key1,key2,key3",
        "-e",
        "CLIENT_API_KEY=your-api-key",
        "sejmofil-neo4j-mcp:latest"
      ]
    }
  }
}
```

## License

MIT

## Author

Built for Sejmofil.pl
