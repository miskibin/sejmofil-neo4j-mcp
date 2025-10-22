"""Entry point for running the MCP server"""

# Use absolute package import so all imports consistently start with `sejmofil_mcp`.
from sejmofil_mcp.server import run_server


if __name__ == "__main__":
    run_server()
