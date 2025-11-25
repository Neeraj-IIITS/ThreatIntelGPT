# src/preprocess.py

import re
from html import unescape

# Regex to remove HTML tags
TAG_RE = re.compile(r"<[^>]+>")


def clean_html(raw_html: str) -> str:
    """
    Removes HTML tags, scripts, unwanted characters,
    and compresses whitespace.
    """
    if not raw_html:
        return ""

    # Remove HTML tags
    text = TAG_RE.sub(" ", raw_html)

    # Decode HTML entities (&amp; etc.)
    text = unescape(text)

    # Remove URLs inside the text if needed
    text = re.sub(r"http\S+", " ", text)

    # Remove non-English symbols
    text = re.sub(r"[^a-zA-Z0-9.,!?;:/()\-\s]", " ", text)

    # Remove excess whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()
