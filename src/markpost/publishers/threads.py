from __future__ import annotations

import httpx

from markpost.config import ThreadsConfig

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_CHAR_LIMIT = 500


async def post_to_threads(parts: list[str], config: ThreadsConfig) -> list[str]:
    """Post a single post or reply chain to Threads.

    Uses the two-step create-then-publish flow.
    Returns a list of post IDs.
    """
    post_ids: list[str] = []
    previous_id: str | None = None

    async with httpx.AsyncClient() as client:
        for part in parts:
            # Step 1: Create media container
            create_params: dict = {
                "text": part,
                "media_type": "TEXT",
                "access_token": config.access_token,
            }
            if previous_id is not None:
                create_params["reply_to_id"] = previous_id

            create_resp = await client.post(
                f"{THREADS_API_BASE}/{config.user_id}/threads",
                params=create_params,
            )
            create_resp.raise_for_status()
            container_id = create_resp.json()["id"]

            # Step 2: Publish
            publish_resp = await client.post(
                f"{THREADS_API_BASE}/{config.user_id}/threads_publish",
                params={
                    "creation_id": container_id,
                    "access_token": config.access_token,
                },
            )
            publish_resp.raise_for_status()
            post_id = publish_resp.json()["id"]

            post_ids.append(post_id)
            previous_id = post_id

    return post_ids
