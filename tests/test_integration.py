# tests/test_integration.py
"""Integration tests verifying the MCP server exposes expected tools."""
from markpost.server import mcp


def test_server_exposes_all_tools():
    tool_names = [t.name for t in mcp._tool_manager._tools.values()]
    assert "ping" in tool_names
    assert "publish_post" in tool_names
    assert "preview_post" in tool_names


def test_server_name():
    assert mcp.name == "Markpost"
