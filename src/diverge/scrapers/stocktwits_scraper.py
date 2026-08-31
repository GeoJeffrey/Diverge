"""
stocktwits_noapi_scraper.py

# HONESTY / LEGAL & TOS NOTICE:
# Scraped via StockTwits public symbol stream API endpoint:
#   GET https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json
# While public and requires no authentication token or key, fetching without an official
# developer partner agreement sits in a legal/ToS gray area. Unauthenticated access is
# subject to rate limits (~200 requests/hour) and schema modifications without notice.
# Check StockTwits robots.txt and Terms of Service before high-volume polling.
"""

import time
from typing import Any, Dict, List, Optional

import requests
import urllib3

from .. import config, storage, utils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = utils.setup_logger("stocktwits_noapi_scraper")


def fetch_symbol_stream(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch public stream message objects for a given stock symbol.
    """
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.warning(f"StockTwits HTTP {resp.status_code} for symbol {symbol}")
            return None
    except Exception as e:
        logger.error(f"Error fetching StockTwits stream for {symbol}: {e}")
        return None


def parse_stocktwits_messages(symbol: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse StockTwits stream message list into raw_posts schema format.
    """
    messages = data.get("messages", [])
    collected = []

    for msg in messages:
        msg_id = msg.get("id")
        body = msg.get("body", "")
        if not msg_id or not body:
            continue

        # Match ticker using utils.match_ticker (fallback to symbol if not matched by regex)
        ticker = utils.match_ticker(body)
        if not ticker:
            clean_sym = symbol.split(".")[0].upper()
            ticker = utils.match_ticker(clean_sym) or clean_sym

        user = msg.get("user", {})
        username = user.get("username", "anonymous")
        created_at = msg.get("created_at")
        likes = msg.get("likes", {}).get("total", 0) if isinstance(msg.get("likes"), dict) else 0

        collected.append({
            "post_id": f"stocktwits_{msg_id}",
            "account_id": f"stocktwits_{username}",
            "timestamp_utc": utils.to_iso_utc(created_at),
            "community": f"symbol/{symbol}",
            "ticker": ticker,
            "raw_text": body.strip(),
            "upvotes": likes,
            "platform": "stocktwits",
        })

    return collected


def scrape_symbol(symbol: str) -> List[Dict[str, Any]]:
    """Scrape stream for one symbol and return parsed posts list."""
    logger.info(f"Fetching StockTwits public stream for symbol {symbol}...")
    data = fetch_symbol_stream(symbol)
    if not data:
        return []
    posts = parse_stocktwits_messages(symbol, data)
    logger.info(f"Parsed {len(posts)} messages for symbol {symbol}")
    return posts


def run() -> int:
    """Execute StockTwits scraper across all configured symbols."""
    all_posts = []
    for symbol in config.STOCKTWITS_SYMBOLS:
        try:
            posts = scrape_symbol(symbol)
            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Failed scraping StockTwits symbol {symbol}: {e}")
        time.sleep(config.STOCKTWITS_DELAY)

    new_count = storage.insert_many(all_posts)
    logger.info(f"StockTwits scraper finished. Matched {len(all_posts)} items, {new_count} new rows inserted.")
    return new_count


if __name__ == "__main__":
    run()

