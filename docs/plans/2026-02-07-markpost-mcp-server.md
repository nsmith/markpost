# Markpost MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MCP server (via FastMCP) that receives Markdown content from an AI agent, formats it per platform, and syndicates to Twitter/X, Threads, and a static blog on S3.

**Architecture:** A single FastMCP server exposes tools for posting content. A `formatter` module parses Markdown and auto-splits into threads based on platform character limits and `---` markers. Platform-specific `publisher` modules handle API calls. A TOML config file stores API credentials and settings.

**Tech Stack:** Python 3.10+, FastMCP 2.x, tweepy (Twitter/X API v2), httpx (Threads Graph API), boto3 (S3), markdown (HTML rendering), tomli/tomllib (config), pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/markpost/__init__.py`
- Create: `src/markpost/server.py`
- Create: `tests/__init__.py`
- Create: `tests/test_server.py`
- Create: `.gitignore`

**Step 1: Initialize git repo**

Run: `git init`

**Step 2: Create pyproject.toml**

```toml
[project]
name = "markpost"
version = "0.1.0"
description = "MCP server for syndicating Markdown content to social media and static blogs"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.14,<3",
    "tweepy>=4.14",
    "httpx>=0.27",
    "boto3>=1.34",
    "markdown>=3.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/markpost"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 3: Create src/markpost/__init__.py**

```python
"""Markpost: MCP server for social media syndication."""
```

**Step 4: Create minimal server**

```python
# src/markpost/server.py
from fastmcp import FastMCP

mcp = FastMCP(name="Markpost")


@mcp.tool
def ping() -> str:
    """Health check tool."""
    return "pong"


if __name__ == "__main__":
    mcp.run()
```

**Step 5: Create test file**

```python
# tests/test_server.py
from markpost.server import mcp


def test_server_has_ping_tool():
    tool_names = [t.name for t in mcp._tool_manager.tools.values()]
    assert "ping" in tool_names
```

**Step 6: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.env
config.toml
```

**Step 7: Install project and run tests**

Run: `uv venv && uv pip install -e ".[dev]"`
Run: `uv run pytest tests/test_server.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add pyproject.toml src/ tests/ .gitignore
git commit -m "feat: scaffold markpost project with FastMCP server"
```

---

### Task 2: Configuration Module

**Files:**
- Create: `src/markpost/config.py`
- Create: `tests/test_config.py`
- Create: `config.example.toml`

**Step 1: Write the failing test**

```python
# tests/test_config.py
import tempfile
import os
from pathlib import Path


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[twitter]
api_key = "tk"
api_secret = "ts"
access_token = "at"
access_token_secret = "ats"

[threads]
access_token = "threads_token"
user_id = "123456"

[blog]
s3_bucket = "my-blog"
s3_prefix = "posts/"
base_url = "https://blog.example.com"

[blog.aws]
region = "us-east-1"
""")
    from markpost.config import load_config

    config = load_config(config_file)
    assert config.twitter.api_key == "tk"
    assert config.twitter.api_secret == "ts"
    assert config.twitter.access_token == "at"
    assert config.twitter.access_token_secret == "ats"
    assert config.threads.access_token == "threads_token"
    assert config.threads.user_id == "123456"
    assert config.blog.s3_bucket == "my-blog"
    assert config.blog.s3_prefix == "posts/"
    assert config.blog.base_url == "https://blog.example.com"
    assert config.blog.aws_region == "us-east-1"


def test_load_config_default_path(tmp_path, monkeypatch):
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
    monkeypatch.setenv("MARKPOST_CONFIG", str(config_file))
    from markpost.config import load_config

    config = load_config()
    assert config.twitter.api_key == "k"


def test_config_missing_optional_fields(tmp_path):
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
    from markpost.config import load_config

    config = load_config(config_file)
    assert config.blog.s3_prefix == ""
    assert config.blog.aws_region == "us-east-1"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with ModuleNotFoundError (config module doesn't exist)

**Step 3: Write minimal implementation**

```python
# src/markpost/config.py
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


@dataclass(frozen=True)
class TwitterConfig:
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str


@dataclass(frozen=True)
class ThreadsConfig:
    access_token: str
    user_id: str


@dataclass(frozen=True)
class BlogConfig:
    s3_bucket: str
    base_url: str
    s3_prefix: str = ""
    aws_region: str = "us-east-1"


@dataclass(frozen=True)
class MarkpostConfig:
    twitter: TwitterConfig
    threads: ThreadsConfig
    blog: BlogConfig


def load_config(path: Path | None = None) -> MarkpostConfig:
    """Load configuration from a TOML file.

    If no path is given, reads from MARKPOST_CONFIG env var,
    falling back to ~/.markpost/config.toml.
    """
    if path is None:
        env = os.environ.get("MARKPOST_CONFIG")
        if env:
            path = Path(env)
        else:
            path = Path.home() / ".markpost" / "config.toml"

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    twitter = TwitterConfig(**raw["twitter"])
    threads = ThreadsConfig(**raw["threads"])

    blog_raw = dict(raw["blog"])
    aws = blog_raw.pop("aws", {})
    blog = BlogConfig(
        s3_bucket=blog_raw["s3_bucket"],
        base_url=blog_raw["base_url"],
        s3_prefix=blog_raw.get("s3_prefix", ""),
        aws_region=aws.get("region", "us-east-1"),
    )

    return MarkpostConfig(twitter=twitter, threads=threads, blog=blog)
```

**Step 4: Create config.example.toml**

```toml
# config.example.toml — copy to ~/.markpost/config.toml and fill in values

[twitter]
api_key = ""
api_secret = ""
access_token = ""
access_token_secret = ""

[threads]
access_token = ""
user_id = ""

[blog]
s3_bucket = "my-blog-bucket"
s3_prefix = "posts/"
base_url = "https://blog.example.com"

[blog.aws]
region = "us-east-1"
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/markpost/config.py tests/test_config.py config.example.toml
git commit -m "feat: add TOML config loading for platform credentials"
```

---

### Task 3: Markdown Formatter — Plain Text Conversion

**Files:**
- Create: `src/markpost/formatter.py`
- Create: `tests/test_formatter.py`

**Step 1: Write the failing test**

```python
# tests/test_formatter.py


def test_strip_to_plain_text_basic():
    from markpost.formatter import markdown_to_plain

    md = "Hello **world** and *italic* text"
    result = markdown_to_plain(md)
    assert result == "Hello world and italic text"


def test_strip_links_to_text_and_url():
    from markpost.formatter import markdown_to_plain

    md = "Check out [Example](https://example.com) today"
    result = markdown_to_plain(md)
    assert result == "Check out Example (https://example.com) today"


def test_strip_headings():
    from markpost.formatter import markdown_to_plain

    md = "# Title\n\nSome paragraph."
    result = markdown_to_plain(md)
    assert "Title" in result
    assert "#" not in result


def test_strip_lists():
    from markpost.formatter import markdown_to_plain

    md = "- item one\n- item two"
    result = markdown_to_plain(md)
    assert "item one" in result
    assert "item two" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_formatter.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# src/markpost/formatter.py
from __future__ import annotations

import re
from html import unescape

import markdown


def markdown_to_plain(text: str) -> str:
    """Convert Markdown to plain text suitable for social media.

    Links become "text (url)" format. All other formatting is stripped.
    """
    # Convert links before stripping HTML so we can capture href
    # First handle markdown links: [text](url) -> text (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

    # Strip heading markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Strip bold/italic markers
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)

    # Strip list markers
    text = re.sub(r"^[\-\*\+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_formatter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/formatter.py tests/test_formatter.py
git commit -m "feat: add markdown to plain text conversion"
```

---

### Task 4: Markdown Formatter — Thread Splitting

**Files:**
- Modify: `src/markpost/formatter.py`
- Modify: `tests/test_formatter.py`

**Step 1: Write the failing test**

```python
# Append to tests/test_formatter.py


def test_split_by_separator():
    from markpost.formatter import split_into_thread

    md = "Part one content.\n\n---\n\nPart two content."
    parts = split_into_thread(md, max_chars=280)
    assert len(parts) == 2
    assert "Part one" in parts[0]
    assert "Part two" in parts[1]


def test_split_by_char_limit():
    from markpost.formatter import split_into_thread

    long_text = "A" * 300
    parts = split_into_thread(long_text, max_chars=280)
    assert len(parts) == 2
    assert all(len(p) <= 280 for p in parts)


def test_split_preserves_sentences():
    from markpost.formatter import split_into_thread

    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    # Force a split with a very small limit
    parts = split_into_thread(text, max_chars=40)
    # Each part should end at a sentence boundary where possible
    for part in parts:
        assert len(part) <= 40


def test_no_split_needed():
    from markpost.formatter import split_into_thread

    text = "Short post."
    parts = split_into_thread(text, max_chars=280)
    assert parts == ["Short post."]


def test_split_respects_separator_over_limit():
    from markpost.formatter import split_into_thread

    # Separator should always cause a split even if under char limit
    md = "Part A.\n\n---\n\nPart B."
    parts = split_into_thread(md, max_chars=5000)
    assert len(parts) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_formatter.py::test_split_by_separator -v`
Expected: FAIL with ImportError (split_into_thread doesn't exist)

**Step 3: Write minimal implementation**

```python
# Append to src/markpost/formatter.py

SEPARATOR_PATTERN = re.compile(r"\n\s*---\s*\n")


def split_into_thread(text: str, max_chars: int = 280) -> list[str]:
    """Split text into thread parts.

    First splits on --- separators, then splits any chunk that exceeds
    max_chars at sentence boundaries. Falls back to word boundaries
    if a single sentence exceeds the limit.
    """
    # Step 1: split on explicit separators
    raw_parts = SEPARATOR_PATTERN.split(text)
    raw_parts = [p.strip() for p in raw_parts if p.strip()]

    # Step 2: split any over-length parts
    result: list[str] = []
    for part in raw_parts:
        if len(part) <= max_chars:
            result.append(part)
        else:
            result.extend(_split_long_text(part, max_chars))

    return result


def _split_long_text(text: str, max_chars: int) -> list[str]:
    """Split text at sentence boundaries, falling back to word boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    current = ""

    for sentence in sentences:
        if not current:
            if len(sentence) <= max_chars:
                current = sentence
            else:
                # Sentence itself is too long — split on words
                parts.extend(_split_on_words(sentence, max_chars))
        elif len(current) + 1 + len(sentence) <= max_chars:
            current = current + " " + sentence
        else:
            parts.append(current)
            if len(sentence) <= max_chars:
                current = sentence
            else:
                parts.extend(_split_on_words(sentence, max_chars))
                current = ""

    if current:
        parts.append(current)

    return parts


def _split_on_words(text: str, max_chars: int) -> list[str]:
    """Last-resort split on word boundaries."""
    words = text.split()
    parts: list[str] = []
    current = ""

    for word in words:
        if not current:
            current = word[:max_chars]
        elif len(current) + 1 + len(word) <= max_chars:
            current = current + " " + word
        else:
            parts.append(current)
            current = word[:max_chars]

    if current:
        parts.append(current)

    return parts
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_formatter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/formatter.py tests/test_formatter.py
git commit -m "feat: add thread splitting with separator and char limit support"
```

---

### Task 5: Markdown to HTML Conversion (for Blog)

**Files:**
- Modify: `src/markpost/formatter.py`
- Modify: `tests/test_formatter.py`

**Step 1: Write the failing test**

```python
# Append to tests/test_formatter.py


def test_markdown_to_html_basic():
    from markpost.formatter import markdown_to_html

    md = "# Hello\n\nA **bold** paragraph."
    html = markdown_to_html(md)
    assert "<h1>Hello</h1>" in html
    assert "<strong>bold</strong>" in html


def test_markdown_to_html_wraps_in_template():
    from markpost.formatter import markdown_to_html

    md = "# Title\n\nBody."
    html = markdown_to_html(md, title="My Post")
    assert "<title>My Post</title>" in html
    assert "<!DOCTYPE html>" in html
    assert "<h1>Title</h1>" in html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_formatter.py::test_markdown_to_html_basic -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# Append to src/markpost/formatter.py


def markdown_to_html(text: str, title: str | None = None) -> str:
    """Convert Markdown to HTML.

    If title is provided, wraps in a full HTML document.
    Otherwise returns just the body HTML fragment.
    """
    body = markdown.markdown(text)

    if title is None:
        return body

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>"""
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_formatter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/formatter.py tests/test_formatter.py
git commit -m "feat: add markdown to HTML conversion with optional template"
```

---

### Task 6: Twitter Publisher

**Files:**
- Create: `src/markpost/publishers/__init__.py`
- Create: `src/markpost/publishers/twitter.py`
- Create: `tests/test_twitter.py`

**Step 1: Write the failing test**

```python
# tests/test_twitter.py
from unittest.mock import MagicMock, patch, call


def test_post_single_tweet():
    from markpost.config import TwitterConfig
    from markpost.publishers.twitter import post_to_twitter

    mock_response = MagicMock()
    mock_response.data = {"id": "111"}

    with patch("markpost.publishers.twitter.tweepy.Client") as MockClient:
        client = MockClient.return_value
        client.create_tweet.return_value = mock_response

        config = TwitterConfig(
            api_key="k", api_secret="s",
            access_token="a", access_token_secret="as",
        )
        result = post_to_twitter(["Hello world"], config)

    client.create_tweet.assert_called_once_with(text="Hello world")
    assert result == ["111"]


def test_post_thread():
    from markpost.config import TwitterConfig
    from markpost.publishers.twitter import post_to_twitter

    responses = []
    for tweet_id in ["111", "222", "333"]:
        r = MagicMock()
        r.data = {"id": tweet_id}
        responses.append(r)

    with patch("markpost.publishers.twitter.tweepy.Client") as MockClient:
        client = MockClient.return_value
        client.create_tweet.side_effect = responses

        config = TwitterConfig(
            api_key="k", api_secret="s",
            access_token="a", access_token_secret="as",
        )
        result = post_to_twitter(["Part 1", "Part 2", "Part 3"], config)

    assert client.create_tweet.call_count == 3
    # First tweet has no reply
    client.create_tweet.assert_any_call(text="Part 1")
    # Subsequent tweets reply to the previous
    client.create_tweet.assert_any_call(text="Part 2", in_reply_to_tweet_id="111")
    client.create_tweet.assert_any_call(text="Part 3", in_reply_to_tweet_id="222")
    assert result == ["111", "222", "333"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_twitter.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# src/markpost/publishers/__init__.py
"""Platform publishers for markpost."""
```

```python
# src/markpost/publishers/twitter.py
from __future__ import annotations

import tweepy

from markpost.config import TwitterConfig

TWITTER_CHAR_LIMIT = 280


def post_to_twitter(parts: list[str], config: TwitterConfig) -> list[str]:
    """Post a single tweet or a thread to Twitter/X.

    Returns a list of tweet IDs.
    """
    client = tweepy.Client(
        consumer_key=config.api_key,
        consumer_secret=config.api_secret,
        access_token=config.access_token,
        access_token_secret=config.access_token_secret,
    )

    tweet_ids: list[str] = []
    previous_id: str | None = None

    for part in parts:
        kwargs: dict = {"text": part}
        if previous_id is not None:
            kwargs["in_reply_to_tweet_id"] = previous_id

        response = client.create_tweet(**kwargs)
        tweet_id = response.data["id"]
        tweet_ids.append(tweet_id)
        previous_id = tweet_id

    return tweet_ids
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_twitter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/publishers/ tests/test_twitter.py
git commit -m "feat: add Twitter/X publisher with thread support"
```

---

### Task 7: Threads Publisher

**Files:**
- Create: `src/markpost/publishers/threads.py`
- Create: `tests/test_threads.py`

The Threads API uses a two-step process: (1) create a media container via `POST /{user_id}/threads`, (2) publish it via `POST /{user_id}/threads_publish`. For reply chains, the `reply_to_id` field references a previous post's ID.

**Step 1: Write the failing test**

```python
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
        client = MockClient.return_value.__aenter__ = AsyncMock()
        mock_client = AsyncMock()
        mock_client.post.side_effect = [mock_response_create, mock_response_publish]
        MockClient.return_value.__aenter__.return_value = mock_client
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_threads.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# src/markpost/publishers/threads.py
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_threads.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/publishers/threads.py tests/test_threads.py
git commit -m "feat: add Threads publisher with reply chain support"
```

---

### Task 8: Blog Publisher (S3)

**Files:**
- Create: `src/markpost/publishers/blog.py`
- Create: `tests/test_blog.py`

**Step 1: Write the failing test**

```python
# tests/test_blog.py
from unittest.mock import patch, MagicMock
from datetime import date


def test_publish_to_blog():
    from markpost.config import BlogConfig
    from markpost.publishers.blog import publish_to_blog

    config = BlogConfig(
        s3_bucket="my-blog",
        base_url="https://blog.example.com",
        s3_prefix="posts/",
        aws_region="us-east-1",
    )

    with patch("markpost.publishers.blog.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        url = publish_to_blog(
            html="<h1>Test</h1>",
            slug="my-first-post",
            config=config,
        )

    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args[1]
    assert call_kwargs["Bucket"] == "my-blog"
    assert call_kwargs["Key"].startswith("posts/")
    assert call_kwargs["Key"].endswith("my-first-post.html")
    assert call_kwargs["ContentType"] == "text/html"
    assert call_kwargs["Body"] == "<h1>Test</h1>"
    assert "blog.example.com" in url


def test_publish_to_blog_generates_slug_from_title():
    from markpost.config import BlogConfig
    from markpost.publishers.blog import publish_to_blog

    config = BlogConfig(
        s3_bucket="b",
        base_url="https://example.com",
    )

    with patch("markpost.publishers.blog.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        url = publish_to_blog(
            html="<h1>Test</h1>",
            slug="hello-world",
            config=config,
        )

    call_kwargs = mock_s3.put_object.call_args[1]
    assert "hello-world.html" in call_kwargs["Key"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_blog.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# src/markpost/publishers/blog.py
from __future__ import annotations

from datetime import date

import boto3

from markpost.config import BlogConfig


def publish_to_blog(html: str, slug: str, config: BlogConfig) -> str:
    """Upload rendered HTML to S3 and return the public URL."""
    s3 = boto3.client("s3", region_name=config.aws_region)

    today = date.today().isoformat()
    key = f"{config.s3_prefix}{today}-{slug}.html"

    s3.put_object(
        Bucket=config.s3_bucket,
        Key=key,
        Body=html,
        ContentType="text/html",
    )

    base = config.base_url.rstrip("/")
    return f"{base}/{key}"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_blog.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/publishers/blog.py tests/test_blog.py
git commit -m "feat: add S3 blog publisher"
```

---

### Task 9: MCP Server — publish_post Tool

**Files:**
- Modify: `src/markpost/server.py`
- Create: `tests/test_publish_tool.py`

This is the main tool that the AI agent will call. It receives Markdown content, formats it per platform, and syndicates to all configured platforms.

**Step 1: Write the failing test**

```python
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

        result = await publish_post(
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

        result = await publish_post(
            content="Short tweet.",
            platforms=["twitter"],
        )

    assert "twitter" in result
    assert "threads" not in result
    assert "blog" not in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_publish_tool.py -v`
Expected: FAIL with ImportError (publish_post doesn't exist)

**Step 3: Write the implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_publish_tool.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/server.py tests/test_publish_tool.py
git commit -m "feat: add publish_post MCP tool with multi-platform syndication"
```

---

### Task 10: MCP Server — preview_post Tool

**Files:**
- Modify: `src/markpost/server.py`
- Modify: `tests/test_publish_tool.py`

A dry-run tool so the agent can preview how content will be formatted and split before publishing.

**Step 1: Write the failing test**

```python
# Append to tests/test_publish_tool.py


def test_preview_post():
    from markpost.server import preview_post

    result = preview_post(
        content="# Title\n\nHello **world**.\n\n---\n\nSecond part.",
        platforms=["twitter", "threads"],
    )

    assert "twitter" in result
    assert "threads" in result
    assert len(result["twitter"]["parts"]) == 2
    assert len(result["threads"]["parts"]) == 2
    assert "**" not in result["twitter"]["parts"][0]


def test_preview_post_blog():
    from markpost.server import preview_post

    result = preview_post(
        content="# Title\n\nBody.",
        title="My Post",
        platforms=["blog"],
    )

    assert "blog" in result
    assert "<h1>Title</h1>" in result["blog"]["html"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_publish_tool.py::test_preview_post -v`
Expected: FAIL with ImportError

**Step 3: Write the implementation**

```python
# Add to src/markpost/server.py, before the if __name__ block


@mcp.tool
def preview_post(
    content: Annotated[str, Field(description="Markdown-formatted content to preview")],
    title: Annotated[str | None, Field(description="Post title (for blog preview)")] = None,
    platforms: Annotated[
        list[str],
        Field(description="Platforms to preview for: 'twitter', 'threads', 'blog'. Defaults to all."),
    ] = None,
) -> dict:
    """Preview how content will be formatted for each platform.

    Returns the formatted text and thread splits without actually publishing.
    Use this to verify formatting before calling publish_post.
    """
    if platforms is None:
        platforms = ["twitter", "threads", "blog"]

    results: dict = {}
    plain = markdown_to_plain(content)

    if "twitter" in platforms:
        parts = split_into_thread(plain, max_chars=TWITTER_CHAR_LIMIT)
        results["twitter"] = {
            "parts": parts,
            "char_counts": [len(p) for p in parts],
        }

    if "threads" in platforms:
        parts = split_into_thread(plain, max_chars=THREADS_CHAR_LIMIT)
        results["threads"] = {
            "parts": parts,
            "char_counts": [len(p) for p in parts],
        }

    if "blog" in platforms:
        html = markdown_to_html(content, title=title)
        results["blog"] = {"html": html}

    return results
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_publish_tool.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markpost/server.py tests/test_publish_tool.py
git commit -m "feat: add preview_post tool for dry-run formatting"
```

---

### Task 11: Integration Test and Claude Code Registration

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration tests verifying the MCP server exposes expected tools."""
from markpost.server import mcp


def test_server_exposes_all_tools():
    tool_names = [t.name for t in mcp._tool_manager.tools.values()]
    assert "ping" in tool_names
    assert "publish_post" in tool_names
    assert "preview_post" in tool_names


def test_server_name():
    assert mcp.name == "Markpost"
```

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 3: Register with Claude Code**

Run: `claude mcp add markpost -- uv run --with fastmcp fastmcp run src/markpost/server.py`

Verify: `claude mcp list` should show the markpost server

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add integration tests and Claude Code registration"
```

---

### Task 12: Final Verification

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 2: Verify MCP server starts**

Run: `echo '{}' | uv run python src/markpost/server.py`
Expected: Server starts without error (will wait for input on stdin)

**Step 3: Verify config example is complete**

Review: `config.example.toml` has all required fields documented

**Step 4: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```
