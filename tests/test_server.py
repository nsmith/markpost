# tests/test_server.py
from markpost.server import mcp


def test_server_has_ping_tool():
    tool_names = [t.name for t in mcp._tool_manager._tools.values()]
    assert "ping" in tool_names
