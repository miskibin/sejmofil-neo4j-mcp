# Sejmofil Neo4j MCP Server

Model Context Protocol server for querying Polish parliamentary data from Neo4j graph database.

**📚 [Quick Start Guide](QUICKSTART.md) | [Docker Guide](DOCKER.md)**

## Features

- 🔍 **Semantic Search**: Find legislative prints using AI-powered semantic search with flexible status filtering
- 🔗 **Graph Exploration**: Explore connections and relationships between any nodes in the database
- 📊 **Process Tracking**: Check status of legislative processes (active/finished)
- 👥 **MP Activity**: Query member of parliament legislative activity
- 🏛️ **Club Statistics**: Get comprehensive statistics about parliamentary clubs (parties)
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

**See [DOCKER.md](DOCKER.md) for detailed Docker usage instructions.**

## Configuration

Create a `.env` file (copy from `.env.example`):

```env
NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key  # Optional, for semantic search
EMBEDDINGS_MODEL=text-embedding-3-small

# API Key Authorization (optional but recommended)
API_KEY=your-secret-api-key
```

### API Key Authorization

The server supports simple API key authorization:

- **API_KEY**: A single shared API key for authorization
- If not set, authorization is disabled (not recommended for production)

**Example:**
```bash
# Set the API key
API_KEY=my-secret-key-12345

# All users use the same key
```

## Running the Server

### Using Docker (Recommended for Production)

```bash
# Using docker-compose (easiest)
docker-compose up

# Or run the container directly
docker run -it --rm \
  -p 8000:8000 \
  -e NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your_password \
  -e API_KEY=your-secret-key \
  -v $(pwd)/logs:/app/logs \
  sejmofil-neo4j-mcp:latest
```

The server uses SSE (Server-Sent Events) transport and listens on port 8000.

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
  "name": "search_prints",
  "arguments": {
    "query": "podatki",
    "status": "active",
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

// Example 4: Explore connections of a topic
{
  "name": "explore_node",
  "arguments": {
    "node_type": "Topic",
    "node_id": "Podatki",
    "limit": 10
  }
}

// Example 5: Get club statistics
{
  "name": "get_club_statistics",
  "arguments": {
    "club_name": "PiS"
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

### 1. `search_prints`
Search for parliamentary prints (legislative documents) by topic or keywords.

**Arguments:**
- `query` (str): Search query in Polish (e.g., "podatki", "obrona", "energia odnawialna")
- `limit` (int): Maximum number of results to return (default: 10, max: 50)
- `status` (str): Filter by status - 'active' (currently processed), 'finished' (published/withdrawn), or 'all' (default: 'all')

**Examples:**
```
search_prints("podatki", status="active") - finds active tax-related prints
search_prints("obrona narodowa") - finds all defense prints
search_prints("energia", status="finished") - finds completed energy prints
```

### 2. `explore_node`
Explore all connections (neighbors) of any node in the database.

**Arguments:**
- `node_type` (str): Type of node - 'Person', 'Print', 'Topic', 'Process', 'Club', 'Committee'
- `node_id` (str): Node identifier (Person: id number, Print: print number, Topic: topic name, Process: process number, Club: club name, Committee: committee code)
- `limit` (int): Maximum neighbors to show per relationship type (default: 50)

**Examples:**
```
explore_node("Person", "12345") - shows all connections for MP with ID 12345
explore_node("Print", "1234") - shows authors, topics, processes for print 1234
explore_node("Topic", "Podatki") - shows all prints related to tax topic
explore_node("Club", "PiS") - shows members and activity of PiS party
```

### 3. `get_print_details`
Get comprehensive information about a specific print.

**Arguments:**
- `print_number` (str): Print number (e.g., "1234")

**Returns:** Full metadata, authors, topics, organizations, current stage, comments

### 4. `get_process_status`
Check if a legislative process is active or finished.

**Arguments:**
- `process_number` (str): Process number

**Returns:** Status (active/finished), current stage, all stages with dates

### 5. `find_mp_by_name`
Find members of parliament by name.

**Arguments:**
- `name` (str): MP name or partial name

**Returns:** List of matching MPs with club and role info

### 6. `get_mp_activity`
Get legislative activity for a member of parliament.

**Arguments:**
- `person_id` (int): MP's ID number

**Returns:** Authored prints, speeches count, committee memberships

### 7. `get_similar_topics`
Find semantically similar topics.

**Arguments:**
- `topic_name` (str): Topic name
- `limit` (int): Max results (default: 5)

**Returns:** Similar topics with similarity scores

### 8. `get_topic_statistics`
Get statistics about a parliamentary topic.

**Arguments:**
- `topic_name` (str): Topic name

**Returns:** Total prints, active prints, finished prints

### 9. `get_club_statistics`
Get comprehensive statistics about a parliamentary club (political party/group).

**Arguments:**
- `club_name` (str): Club name to get statistics for (e.g., 'PiS', 'Platforma Obywatelska', 'Lewica')

**Returns:** Statistics including membership, legislative activity, voting, speeches, and committee involvement

### 10. `list_clubs`
List all parliamentary clubs (political parties/groups).

**Returns:** List of all clubs with member counts and active member information, ordered by membership size

### 11. `search_all`
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

### Search for prints about taxes (active only)
```python
search_prints(query="podatki", status="active", limit=5)
```

### Get details about a specific print
```python
get_print_details(print_number="1234")
```

### Explore all connections of a topic
```python
explore_node(node_type="Topic", node_id="Podatki", limit=50)
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

### Get statistics for a parliamentary club
```python
get_club_statistics(club_name="PiS")
```

### List all parliamentary clubs
```python
list_clubs()
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
        "API_KEY": "your-api-key-here"
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
        "-p",
        "8000:8000",
        "-e",
        "NEO4J_HOST=bolt+s://neo.msulawiak.pl:7687",
        "-e",
        "NEO4J_USER=neo4j",
        "-e",
        "NEO4J_PASSWORD=your_password",
        "-e",
        "API_KEY=your-api-key",
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
