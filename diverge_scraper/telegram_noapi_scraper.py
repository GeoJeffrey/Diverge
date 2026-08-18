"""
telegram_noapi_scraper.py

# HONESTY / LEGAL & TOS NOTICE:
# Scrapes Telegram public channel web preview pages (https://t.me/s/{channel_username}).
# This approach uses plain HTML web parsing without any Telegram API, login, or api_id/api_hash.
# NOTE: This only works for PUBLIC Telegram channels, and preview pages display a limited
# recent-message window (not full historical message backlog). Scraping public HTML pages
# sits in a legal/ToS gray area — verify channel privacy and check robots.txt.
"""

import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from . import config, storage, utils

logger = utils.setup_logger("telegram_noapi_scraper")


def fetch_channel_html(channel_username: str) -> Optional[str]:
    """
    Fetch public HTML preview page for a Telegram channel.
    """
    url = f"https://t.me/s/{channel_username}"
    if not utils.is_allowed_by_robots(url):
        logger.warning(f"Robots.txt disallows scraping {url}. Skipping.")
        return None

    headers = {"User-Agent": config.USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.text
        else:
            logger.warning(f"Telegram HTTP {resp.status_code} for t.me/s/{channel_username}")
            return None
    except Exception as e:
        logger.error(f"Error fetching Telegram preview for {channel_username}: {e}")
        return None


def parse_telegram_html(channel_username: str, html_content: str) -> List[Dict[str, Any]]:
    """
    Parse HTML content of Telegram public web preview page using BeautifulSoup.
    Matches text with tgme_widget_message_text class and timestamps with tgme_widget_message_date time.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    message_wrappers = soup.find_all("div", class_=lambda c: c and "tgme_widget_message" in c)
    collected = []

    for idx, wrapper in enumerate(message_wrappers):
        text_el = wrapper.find(class_=lambda c: c and "tgme_widget_message_text" in c)
        if not text_el:
            continue

        raw_text = text_el.get_text(separator="\n", strip=True)
        ticker = utils.match_ticker(raw_text)
        if not ticker:
            continue

        # Extract timestamp from date time element attribute
        date_el = wrapper.find("time")
        timestamp_raw = None
        if date_el and date_el.has_attr("datetime"):
            timestamp_raw = date_el["datetime"]

        timestamp_utc = utils.to_iso_utc(timestamp_raw)

        # Extract post ID attribute or generate deterministic stable ID
        post_data_attr = wrapper.get("data-post")
        if post_data_attr:
            post_id = f"telegram_{post_data_attr.replace('/', '_')}"
        else:
            post_id = f"telegram_{utils.stable_id(channel_username, raw_text, timestamp_utc)}"

        collected.append({
            "post_id": post_id,
            "account_id": f"telegram_{channel_username}",
            "timestamp_utc": timestamp_utc,
            "community": f"t.me/{channel_username}",
            "ticker": ticker,
            "raw_text": raw_text,
            "upvotes": 0,
            "platform": "telegram",
        })

    return collected


def scrape_channel(channel_username: str) -> List[Dict[str, Any]]:
    """Scrape and parse recent preview messages for a single Telegram channel."""
    logger.info(f"Fetching Telegram web preview for channel t.me/s/{channel_username}...")
    html_content = fetch_channel_html(channel_username)
    if not html_content:
        return []
    posts = parse_telegram_html(channel_username, html_content)
    logger.info(f"Parsed {len(posts)} ticker-relevant messages for channel {channel_username}")
    return posts


def run() -> int:
    """Execute Telegram preview scraper across all configured public channels."""
    all_posts = []
    for channel in config.TELEGRAM_CHANNELS:
        try:
            posts = scrape_channel(channel)
            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Failed scraping Telegram channel {channel}: {e}")
        time.sleep(config.TELEGRAM_DELAY)

    new_count = storage.insert_many(all_posts)
    logger.info(f"Telegram scraper finished. Matched {len(all_posts)} items, {new_count} new rows inserted.")
    return new_count


if __name__ == "__main__":
    run()
