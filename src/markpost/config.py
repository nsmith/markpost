# src/markpost/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
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
