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
        # If a single word exceeds max_chars, hard-split it
        while len(word) > max_chars:
            if current:
                parts.append(current)
                current = ""
            parts.append(word[:max_chars])
            word = word[max_chars:]

        if not word:
            continue

        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current = current + " " + word
        else:
            parts.append(current)
            current = word

    if current:
        parts.append(current)

    return parts


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
