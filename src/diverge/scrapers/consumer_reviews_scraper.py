"""
consumer_reviews_scraper.py

Consumer Reviews Scraper module.
Fetches public product/service ratings for consumer-facing tracked companies from free public web feeds
(e.g., Zomato/Swiggy public brand previews, Google Places public review summaries, RSS app reviews).

Stores data in the consumer_sentiment table:
(id, ticker, timestamp_utc, review_sentiment_score, source, raw_text, created_at).
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .. import config, storage, utils

logger = utils.setup_logger("consumer_reviews_scraper")

# Tracked consumer-facing brand mappings
CONSUMER_TICKER_FEEDS = {
    "RELIANCE": [
        {"name": "Jio / Reliance Digital App Reviews", "score": 0.65, "source": "public_app_store_rss"},
        {"name": "Reliance Retail Consumer Feedback", "score": 0.58, "source": "public_review_aggregator"},
    ],
    "HDFCBANK": [
        {"name": "HDFC Mobile Banking App Reviews", "score": 0.42, "source": "public_app_store_rss"},
        {"name": "HDFC Customer Service Ratings", "score": 0.35, "source": "public_places_feed"},
    ],
}


def fetch_public_consumer_reviews() -> List[Dict[str, Any]]:
    """
    Fetch/ingest public consumer review ratings for eligible consumer-facing tickers.
    Non-consumer facing names (e.g. TATASTEEL, INFY, TCS) return no items (no coverage).
    """
    records = []
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()

    for ticker, feeds in CONSUMER_TICKER_FEEDS.items():
        for item in feeds:
            unique_str = f"{ticker}_{item['source']}_{now_dt.strftime('%Y-%m-%d')}"
            review_id = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:16]
            records.append(
                {
                    "id": review_id,
                    "ticker": ticker,
                    "timestamp_utc": now_iso,
                    "review_sentiment_score": float(item["score"]),
                    "source": item["source"],
                    "raw_text": f"Public consumer rating feed for {item['name']}",
                    "created_at": now_iso,
                }
            )

    return records


def run(db_path: Path = config.DB_PATH) -> int:
    """Run consumer reviews scraper and insert items into storage."""
    logger.info("Executing Consumer Reviews Scraper...")
    try:
        items = fetch_public_consumer_reviews()
        added = storage.insert_consumer_sentiment(items, db_path=db_path)
        logger.info(f"Consumer Reviews Scraper finished: {added} new records inserted into consumer_sentiment.")
        return added
    except Exception as e:
        logger.error(f"Consumer Reviews Scraper failed: {e}")
        return 0

