"""
trends_scraper.py

# HONESTY / LEGAL & TOS NOTICE:
# Uses `pytrends` to fetch search interest data from Google Trends without API keys.
# Google Trends endpoints are unauthenticated public web endpoints. Excessive request
# frequencies can result in temporary HTTP 429 rate limit responses or CAPTCHA blocks.
# Introduce delay between queries and limit request frequencies.
"""

import time
from typing import Any, Dict, List

from pytrends.request import TrendReq

from .. import config, storage, utils

logger = utils.setup_logger("trends_scraper")


def fetch_trends_data(keyword: str, geo: str = config.TRENDS_GEO, timeframe: str = config.TRENDS_TIMEFRAME) -> List[Dict[str, Any]]:
    """
    Fetch Google Trends interest-over-time for a keyword using pytrends.
    Returns list of dicts matching raw_posts schema format.
    """
    logger.info(f"Fetching Google Trends data for keyword '{keyword}' (geo={geo})...")
    pytrend = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
    pytrend.build_payload(kw_list=[keyword], geo=geo, timeframe=timeframe)

    df = pytrend.interest_over_time()
    if df.empty:
        logger.warning(f"No Google Trends data returned for '{keyword}'")
        return []

    ticker = utils.match_ticker(keyword) or keyword.upper()
    collected = []

    for timestamp, row in df.iterrows():
        score = row.get(keyword)
        if score is None:
            continue

        score_int = int(score)
        ts_utc = utils.to_iso_utc(timestamp)
        post_id = f"trends_{utils.stable_id(ticker, ts_utc, geo)}"

        raw_text = f"Google Trends search interest score: {score_int}/100 for {ticker} (geo={geo}, timeframe={timeframe})"

        collected.append({
            "post_id": post_id,
            "account_id": f"google_trends_{geo.lower()}",
            "timestamp_utc": ts_utc,
            "community": "google_trends_search",
            "ticker": ticker,
            "raw_text": raw_text,
            "upvotes": score_int,
            "platform": "google_trends",
        })

    return collected


def run() -> int:
    """Execute Google Trends scraper for all configured keywords."""
    all_posts = []
    for kw in config.TRENDS_KEYWORDS:
        try:
            posts = fetch_trends_data(kw)
            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Failed fetching Google Trends for '{kw}': {e}")
        time.sleep(config.TRENDS_DELAY)

    new_count = storage.insert_many(all_posts)
    logger.info(f"Google Trends scraper finished. Generated {len(all_posts)} data points, {new_count} new rows inserted.")
    return new_count


if __name__ == "__main__":
    run()

