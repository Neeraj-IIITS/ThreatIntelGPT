import requests
import feedparser
from typing import List, Dict


def fetch_rss_entries(rss_url: str, max_items: int = 5) -> List[Dict]:
    """
    Fetch entries from an RSS feed and return as list of dicts.
    Each dict contains: title, published date, link, summary/description.
    """
    feed = feedparser.parse(rss_url)

    items = []
    for entry in feed.entries[:max_items]:
        items.append({
            "title": entry.get("title"),
            "published": entry.get("published", ""),
            "link": entry.get("link"),
            "summary": entry.get("summary", "") or entry.get("description", "")
        })

    return items


def collect_rss_items(rss_url: str, max_items: int = 5) -> List[Dict]:
    """
    Alias wrapper for compatibility with api.py
    """
    return fetch_rss_entries(rss_url, max_items)


def fetch_page_text(url: str) -> str:
    """
    Fetch the raw HTML/text of a webpage.
    Used when RSS summary is short.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return ""
