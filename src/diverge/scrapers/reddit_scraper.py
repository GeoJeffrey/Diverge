"""
reddit_noapi_scraper.py

# HONESTY / LEGAL & TOS NOTICE:
# Fetching public Reddit endpoints without going through an official API (or OAuth)
# sits in a legal/ToS gray area. While technically reachable without login, scraping
# these public JSON/RSS endpoints can violate Reddit's Terms of Service and is far more
# fragile than official APIs since endpoints or rate limits can change without notice.
# Reddit can rate-limit or IP-block unauthenticated requests without warning.
# Always review Reddit's robots.txt before large-scale operations.

Pulls recent posts and comments directly from Reddit's public JSON and RSS endpoints:
  GET https://www.reddit.com/r/{subreddit}/new.json?limit=100
  GET https://www.reddit.com/r/{subreddit}/.rss
"""

import random
import time
from typing import Any, Dict, List, Optional

import feedparser
import requests
import urllib3

from .. import config, storage, utils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = utils.setup_logger("reddit_noapi_scraper")


def fetch_with_retry(url: str, headers: Dict[str, str], max_retries: int = 3) -> Optional[requests.Response]:
    """
    Execute HTTP GET request with retry backoff for rate limits (HTTP 429).
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=12, verify=False)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait_time = (attempt + 1) * 4.0
                logger.warning(f"Reddit HTTP 429 Rate Limit for {url}. Waiting {wait_time}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                logger.warning(f"Reddit HTTP {resp.status_code} for {url}")
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error fetching {url} (attempt {attempt+1}): {e}")
            time.sleep(2)
    return None


def fetch_subreddit_posts_json(subreddit: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch raw post JSON array for a subreddit using Reddit's public new.json endpoint.
    """
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={config.REDDIT_POST_LIMIT}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    resp = fetch_with_retry(url, headers=headers, max_retries=2)
    if resp and resp.status_code == 200:
        try:
            data = resp.json()
            return data.get("data", {}).get("children", [])
        except Exception:
            pass
    return None


def fetch_subreddit_rss(subreddit: str) -> List[Dict[str, Any]]:
    """
    Fetch and parse Reddit's public RSS feed for a subreddit.
    """
    rss_urls = [
        f"https://www.reddit.com/r/{subreddit}/new/.rss",
        f"https://www.reddit.com/r/{subreddit}/.rss",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/atom+xml,application/xml,text/xml",
    }
    collected = []

    for url in rss_urls:
        resp = fetch_with_retry(url, headers=headers, max_retries=2)
        if resp and resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                full_text = f"{title}\n{summary}".strip()

                ticker = utils.match_ticker(full_text)
                if not ticker:
                    continue

                link = entry.get("link", "")
                author = entry.get("author", "").replace("/u/", "").replace("u/", "")
                account_id = f"reddit_{author}" if author else "reddit_deleted_user"
                published = entry.get("published") or entry.get("updated")

                collected.append({
                    "post_id": f"reddit_rss_{utils.stable_id(link or title)}",
                    "account_id": account_id,
                    "timestamp_utc": utils.to_iso_utc(published),
                    "community": f"r/{subreddit}",
                    "ticker": ticker,
                    "raw_text": full_text,
                    "upvotes": 0,
                    "platform": "reddit",
                })

            if collected:
                break
        time.sleep(2)

    return collected


def parse_reddit_posts(subreddit: str, children: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse returned Reddit posts JSON structures into raw_posts schema format.
    """
    collected = []
    for item in children:
        post_data = item.get("data", {})
        item_id = post_data.get("id")
        if not item_id:
            continue

        title = post_data.get("title", "")
        selftext = post_data.get("selftext", "")
        full_text = f"{title}\n{selftext}".strip()
        ticker = utils.match_ticker(full_text)

        author = post_data.get("author")
        account_id = f"reddit_{author}" if author and author != "[deleted]" else "reddit_deleted_user"
        created_utc = post_data.get("created_utc", 0)

        if ticker:
            collected.append({
                "post_id": f"reddit_{item_id}",
                "account_id": account_id,
                "timestamp_utc": utils.to_iso_utc(created_utc),
                "community": f"r/{subreddit}",
                "ticker": ticker,
                "raw_text": full_text,
                "upvotes": post_data.get("score", 0),
                "platform": "reddit",
            })

    return collected


def scrape_subreddit(subreddit: str) -> List[Dict[str, Any]]:
    """Scrape recent posts for a single subreddit with JSON and RSS fallbacks."""
    logger.info(f"Scraping r/{subreddit} via public JSON/RSS endpoints...")
    
    # 1. Try JSON endpoint
    posts_raw = fetch_subreddit_posts_json(subreddit)
    if posts_raw:
        collected = parse_reddit_posts(subreddit, posts_raw)
        if collected:
            logger.info(f"Found {len(collected)} matching items in r/{subreddit} via JSON")
            return collected

    # 2. Try RSS fallback
    collected = fetch_subreddit_rss(subreddit)
    logger.info(f"Found {len(collected)} matching items in r/{subreddit} via RSS feed")
    return collected


def run() -> int:
    """Execute Reddit scraper for all configured subreddits."""
    all_posts = []
    for subreddit in config.REDDIT_SUBREDDITS:
        try:
            posts = scrape_subreddit(subreddit)
            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Failed scraping r/{subreddit}: {e}")
        delay = random.uniform(3.0, 5.0)
        time.sleep(delay)

    new_count = storage.insert_many(all_posts)
    logger.info(f"Reddit scraper finished. Matched {len(all_posts)} items, {new_count} new rows inserted.")
    return new_count


if __name__ == "__main__":
    run()

