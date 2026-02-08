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
