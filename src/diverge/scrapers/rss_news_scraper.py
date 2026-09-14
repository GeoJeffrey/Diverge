"""
rss_news_scraper.py

# HONESTY / LEGAL & TOS NOTICE:
# Scrapes public financial news feeds via RSS XML endpoints using `feedparser`.
# RSS feeds are explicitly intended for public syndication and consumption without API keys.
# However, redistributing full text or polling at excessive frequencies may violate
# provider usage terms. Check each publisher's syndication terms and robots.txt.
"""

import time
from typing import Any, Dict, List

import feedparser

from .. import config, storage, utils

logger = utils.setup_logger("rss_news_scraper")


def parse_feed_entry(feed_name: str, entry: Any) -> List[Dict[str, Any]]:
    """
    Parse a single feedparser entry into raw_posts schema format if a ticker matches.
    """
    title = entry.get("title", "")
    summary = entry.get("summary", "") or entry.get("description", "")
    full_text = f"{title}\n{summary}".strip()

    ticker = utils.match_ticker(full_text)
    if not ticker:
        return []

    link = entry.get("link", "")
    post_id = f"rss_{utils.stable_id(link or (title + summary))}"

    published = entry.get("published") or entry.get("updated")
    timestamp_utc = utils.to_iso_utc(published)

    publisher_id = entry.get("author") or feed_name

    return [{
        "post_id": post_id,
        "account_id": f"rss_{publisher_id}",
        "timestamp_utc": timestamp_utc,
        "community": feed_name,
        "ticker": ticker,
        "raw_text": full_text,
        "upvotes": 0,
        "platform": "rss_news",
    }]


def scrape_rss_feed(feed_cfg: Dict[str, str], max_retries: int = 3) -> List[Dict[str, Any]]:
    """Scrape and parse one RSS feed with retry/backoff."""
    feed_name = feed_cfg["name"]
    url = feed_cfg["url"]
    logger.info(f"Parsing RSS feed '{feed_name}' at {url}...")

    if not utils.is_allowed_by_robots(url):
        logger.warning(f"Robots.txt disallows scraping feed URL {url}. Skipping.")
        return []

    feed = None
    for attempt in range(max_retries):
        try:
            feed = feedparser.parse(url)
            if getattr(feed, "status", None) == 429:
                wait_time = (attempt + 1) * 3.0
                logger.warning(
                    f"RSS HTTP 429 rate limit for '{feed_name}'. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(wait_time)
                continue
            if feed and hasattr(feed, "entries"):
                break
        except Exception as e:
            logger.error(f"Error parsing RSS feed '{feed_name}' (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2.0)

    if not feed or not hasattr(feed, "entries"):
        return []

    collected = []
    for entry in feed.entries:
        parsed = parse_feed_entry(feed_name, entry)
        collected.extend(parsed)

    logger.info(f"Matched {len(collected)} ticker-relevant news items from '{feed_name}'")
    return collected


def run() -> int:
    """Execute RSS news scraper across all configured feeds."""
    all_posts = []
    for feed_cfg in config.RSS_FEEDS:
        try:
            posts = scrape_rss_feed(feed_cfg)
            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Failed parsing RSS feed '{feed_cfg.get('name')}': {e}")
        time.sleep(config.RSS_DELAY)

    new_count = storage.insert_many(all_posts)
    logger.info(f"RSS news scraper finished. Matched {len(all_posts)} items, {new_count} new rows inserted.")
    return new_count


if __name__ == "__main__":
    run()

