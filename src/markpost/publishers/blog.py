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
