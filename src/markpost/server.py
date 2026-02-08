# src/markpost/server.py
from fastmcp import FastMCP

mcp = FastMCP(name="Markpost")


@mcp.tool
def ping() -> str:
    """Health check tool."""
    return "pong"


if __name__ == "__main__":
    mcp.run()
