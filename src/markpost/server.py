# src/markpost/server.py
from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from markpost.config import load_config
from markpost.formatter import markdown_to_plain, markdown_to_html, split_into_thread
from markpost.publishers.twitter import post_to_twitter, TWITTER_CHAR_LIMIT
from markpost.publishers.threads import post_to_threads, THREADS_CHAR_LIMIT
from markpost.publishers.blog import publish_to_blog

mcp = FastMCP(name="Markpost")


@mcp.tool
def ping() -> str:
    """Health check tool."""
    return "pong"


@mcp.tool
async def publish_post(
    content: Annotated[str, Field(description="Markdown-formatted content to publish")],
    title: Annotated[str | None, Field(description="Post title (used for blog HTML <title>)")] = None,
    slug: Annotated[str | None, Field(description="URL slug for blog post (e.g. 'my-first-post')")] = None,
    platforms: Annotated[
        list[str],
        Field(description="Platforms to publish to: 'twitter', 'threads', 'blog'. Defaults to all."),
    ] = None,
) -> dict:
    """Publish Markdown content to social media and/or a static blog.

    Formats content appropriately for each platform:
    - Twitter/X: Converts to plain text, auto-splits into threads at 280 chars
    - Threads: Converts to plain text, auto-splits into threads at 500 chars
    - Blog: Renders full HTML and uploads to S3
    """
    if platforms is None:
        platforms = ["twitter", "threads", "blog"]

    config = load_config()
    results: dict = {}

    plain = markdown_to_plain(content)

    if "twitter" in platforms:
        parts = split_into_thread(plain, max_chars=TWITTER_CHAR_LIMIT)
        tweet_ids = post_to_twitter(parts, config.twitter)
        results["twitter"] = {"tweet_ids": tweet_ids, "parts": len(parts)}

    if "threads" in platforms:
        parts = split_into_thread(plain, max_chars=THREADS_CHAR_LIMIT)
        post_ids = await post_to_threads(parts, config.threads)
        results["threads"] = {"post_ids": post_ids, "parts": len(parts)}

    if "blog" in platforms:
        html = markdown_to_html(content, title=title)
        post_slug = slug or _slugify(title or "post")
        url = publish_to_blog(html, post_slug, config.blog)
        results["blog"] = {"url": url}

    return results


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    import re
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


if __name__ == "__main__":
    mcp.run()
