"""Entry point for running the MCP server"""
import sys
import uvicorn
from sejmofil_mcp.server import run_server


if __name__ == "__main__":
    # Run with Uvicorn by default
    # Use: python -m sejmofil_mcp
    uvicorn.run(
        "sejmofil_mcp.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
