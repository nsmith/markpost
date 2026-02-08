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
