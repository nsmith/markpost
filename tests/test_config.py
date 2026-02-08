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
