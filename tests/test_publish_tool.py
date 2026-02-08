# tests/test_publish_tool.py
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


@pytest.fixture
def mock_config(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[twitter]
api_key = "k"
api_secret = "s"
access_token = "a"
access_token_secret = "as"

[threads]
access_token = "t"
user_id = "1"

[blog]
s3_bucket = "b"
base_url = "https://example.com"
""")
    return str(config_file)


@pytest.mark.asyncio
async def test_publish_post_all_platforms(mock_config, monkeypatch):
    monkeypatch.setenv("MARKPOST_CONFIG", mock_config)

    with (
        patch("markpost.server.post_to_twitter", return_value=["tw1"]) as mock_tw,
        patch("markpost.server.post_to_threads", new_callable=AsyncMock, return_value=["th1"]) as mock_th,
        patch("markpost.server.publish_to_blog", return_value="https://example.com/post.html") as mock_blog,
    ):
        from markpost.server import publish_post

        result = await publish_post.fn(
            content="# Hello\n\nThis is my post.",
            title="Hello",
            platforms=["twitter", "threads", "blog"],
        )

    assert "twitter" in result
    assert "threads" in result
    assert "blog" in result
    mock_tw.assert_called_once()
    mock_th.assert_called_once()
    mock_blog.assert_called_once()


@pytest.mark.asyncio
async def test_publish_post_single_platform(mock_config, monkeypatch):
    monkeypatch.setenv("MARKPOST_CONFIG", mock_config)

    with patch("markpost.server.post_to_twitter", return_value=["tw1"]):
        from markpost.server import publish_post

        result = await publish_post.fn(
            content="Short tweet.",
            platforms=["twitter"],
        )

    assert "twitter" in result
    assert "threads" not in result
    assert "blog" not in result
