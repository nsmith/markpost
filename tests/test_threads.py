# tests/test_threads.py
from unittest.mock import AsyncMock, patch, MagicMock
import pytest


@pytest.mark.asyncio
async def test_post_single_thread():
    from markpost.config import ThreadsConfig
    from markpost.publishers.threads import post_to_threads

    config = ThreadsConfig(access_token="tok", user_id="123")

    mock_response_create = MagicMock()
    mock_response_create.json.return_value = {"id": "container_1"}
    mock_response_create.raise_for_status = MagicMock()

    mock_response_publish = MagicMock()
    mock_response_publish.json.return_value = {"id": "post_1"}
    mock_response_publish.raise_for_status = MagicMock()

    with patch("markpost.publishers.threads.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.side_effect = [mock_response_create, mock_response_publish]
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await post_to_threads(["Hello Threads"], config)

    assert result == ["post_1"]


@pytest.mark.asyncio
async def test_post_thread_chain():
    from markpost.config import ThreadsConfig
    from markpost.publishers.threads import post_to_threads

    config = ThreadsConfig(access_token="tok", user_id="123")

    # Two posts = 4 API calls (create + publish each)
    responses = []
    for i in range(1, 3):
        create_resp = MagicMock()
        create_resp.json.return_value = {"id": f"container_{i}"}
        create_resp.raise_for_status = MagicMock()
        publish_resp = MagicMock()
        publish_resp.json.return_value = {"id": f"post_{i}"}
        publish_resp.raise_for_status = MagicMock()
        responses.extend([create_resp, publish_resp])

    with patch("markpost.publishers.threads.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.side_effect = responses
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await post_to_threads(["Part 1", "Part 2"], config)

    assert result == ["post_1", "post_2"]
    assert mock_client.post.call_count == 4
