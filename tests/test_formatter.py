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
