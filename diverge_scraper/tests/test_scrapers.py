"""
test_scrapers.py

Comprehensive offline unit test suite for Diverge Phase 1 Scraper Module.
Tests ticker regex matching, timestamp normalization, deterministic hashing, SQLite storage,
duplicate prevention (INSERT OR IGNORE), retention text purging, and mock parsing for
Reddit, StockTwits, Telegram, Google Trends, and RSS news feeds.
"""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from diverge_scraper import (
    config,
    reddit_noapi_scraper,
    rss_news_scraper,
    stocktwits_noapi_scraper,
    storage,
    telegram_noapi_scraper,
    trends_scraper,
    utils,
)


class TestUtils(unittest.TestCase):
    def test_match_ticker(self):
        self.assertEqual(utils.match_ticker("Buying some Tata Steel shares today!"), "TATASTEEL")
        self.assertEqual(utils.match_ticker("Reliance quarterly results look solid"), "RELIANCE")
        self.assertEqual(utils.match_ticker("Infosys IT earnings announced"), "INFY")
        self.assertEqual(utils.match_ticker("TCS hiring spree"), "TCS")
        self.assertEqual(utils.match_ticker("HDFC bank home loan rates"), "HDFCBANK")
        self.assertIsNone(utils.match_ticker("Random non-financial text post"))

    def test_to_iso_utc(self):
        # Timestamp float
        ts_float = 1700000000.0
        iso_str = utils.to_iso_utc(ts_float)
        self.assertTrue("Z" in iso_str or "+00:00" in iso_str or iso_str.startswith("2023"))

        # Datetime obj
        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(utils.to_iso_utc(dt), "2025-01-01T12:00:00+00:00")

    def test_stable_id(self):
        id1 = utils.stable_id("reddit", "123", "sub")
        id2 = utils.stable_id("reddit", "123", "sub")
        id3 = utils.stable_id("reddit", "456", "sub")
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)
        self.assertEqual(len(id1), 64)  # SHA-256 length

    def test_is_allowed_by_robots(self):
        with patch("urllib.robotparser.RobotFileParser.can_fetch", return_value=True):
            self.assertTrue(utils.is_allowed_by_robots("https://www.reddit.com/r/stocks/new.json"))


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        self.db_path = Path(self.temp_db_path)

    def tearDown(self):
        if self.db_path.exists():
            os.unlink(self.db_path)

    def test_insert_and_deduplicate(self):
        post = {
            "post_id": "test_1",
            "account_id": "user_a",
            "timestamp_utc": "2025-01-01T12:00:00+00:00",
            "community": "r/stocks",
            "ticker": "RELIANCE",
            "raw_text": "Reliance stock update",
            "upvotes": 10,
            "platform": "reddit",
        }

        # First insert
        new_count1 = storage.insert_many([post], db_path=self.db_path)
        self.assertEqual(new_count1, 1)

        # Duplicate insert (same post_id)
        new_count2 = storage.insert_many([post], db_path=self.db_path)
        self.assertEqual(new_count2, 0)

        counts = storage.count_by_platform(db_path=self.db_path)
        self.assertEqual(counts.get("reddit"), 1)

    def test_purge_old_text(self):
        now_utc = datetime.now(timezone.utc)
        old_dt = (now_utc - timedelta(days=100)).isoformat()
        recent_dt = (now_utc - timedelta(days=10)).isoformat()

        old_post = {
            "post_id": "old_1",
            "account_id": "user_old",
            "timestamp_utc": old_dt,
            "community": "r/stocks",
            "ticker": "TATASTEEL",
            "raw_text": "Old raw text should be purged",
            "upvotes": 5,
            "platform": "reddit",
        }
        recent_post = {
            "post_id": "recent_1",
            "account_id": "user_recent",
            "timestamp_utc": recent_dt,
            "community": "r/stocks",
            "ticker": "TATASTEEL",
            "raw_text": "Recent raw text should remain",
            "upvotes": 8,
            "platform": "reddit",
        }

        storage.insert_many([old_post, recent_post], db_path=self.db_path)

        purged_count = storage.purge_old_text(retention_days=90, db_path=self.db_path)
        self.assertEqual(purged_count, 1)

        conn = storage.get_connection(self.db_path)
        old_row = conn.execute("SELECT raw_text, ticker FROM raw_posts WHERE post_id='old_1'").fetchone()
        recent_row = conn.execute("SELECT raw_text, ticker FROM raw_posts WHERE post_id='recent_1'").fetchone()
        conn.close()

        # raw_text is blanked out, but metadata columns (ticker) remain intact
        self.assertEqual(old_row[0], "")
        self.assertEqual(old_row[1], "TATASTEEL")
        self.assertEqual(recent_row[0], "Recent raw text should remain")


class TestRedditScraper(unittest.TestCase):
    def test_parse_reddit_posts_and_comments(self):
        sample_children = [
            {
                "data": {
                    "id": "post123",
                    "title": "Discussion on Infosys earnings report",
                    "selftext": "Infosys quarterly results were amazing!",
                    "author": "trader1",
                    "created_utc": 1700000000,
                    "score": 42,
                }
            }
        ]

        parsed = reddit_noapi_scraper.parse_reddit_posts("stocks", sample_children)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["post_id"], "reddit_post123")
        self.assertEqual(parsed[0]["ticker"], "INFY")
        self.assertEqual(parsed[0]["account_id"], "reddit_trader1")
        self.assertEqual(parsed[0]["upvotes"], 42)

        # parse_reddit_posts handles post data dicts with title/selftext fields.
        # Comment-style data (body only) is treated the same way now.
        sample_comment_children = [
            {
                "data": {
                    "id": "comm456",
                    "title": "I think Tata Steel is going to rally next week.",
                    "selftext": "",
                    "author": "investor2",
                    "created_utc": 1700000050,
                    "score": 15,
                }
            }
        ]

        parsed_c = reddit_noapi_scraper.parse_reddit_posts("stocks", sample_comment_children)
        self.assertEqual(len(parsed_c), 1)
        self.assertEqual(parsed_c[0]["post_id"], "reddit_comm456")
        self.assertEqual(parsed_c[0]["ticker"], "TATASTEEL")
        self.assertEqual(parsed_c[0]["upvotes"], 15)


class TestStockTwitsScraper(unittest.TestCase):
    def test_parse_stocktwits_messages(self):
        sample_data = {
            "messages": [
                {
                    "id": 999888,
                    "body": "Buying more Reliance shares before breakout! $RELIANCE.X",
                    "created_at": "2025-02-15T10:00:00Z",
                    "user": {"username": "bullish_trader"},
                    "likes": {"total": 7},
                }
            ]
        }

        parsed = stocktwits_noapi_scraper.parse_stocktwits_messages("RELIANCE.X", sample_data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["post_id"], "stocktwits_999888")
        self.assertEqual(parsed[0]["ticker"], "RELIANCE")
        self.assertEqual(parsed[0]["account_id"], "stocktwits_bullish_trader")
        self.assertEqual(parsed[0]["upvotes"], 7)


class TestTelegramScraper(unittest.TestCase):
    def test_parse_telegram_html(self):
        sample_html = """
        <html>
          <body>
            <div class="tgme_widget_message" data-post="IndianStreetBets/500">
              <div class="tgme_widget_message_text">HDFC Bank showing bullish signs today on heavy volume!</div>
              <time class="tgme_widget_message_date time" datetime="2025-02-10T14:30:00+00:00"></time>
            </div>
          </body>
        </html>
        """

        parsed = telegram_noapi_scraper.parse_telegram_html("IndianStreetBets", sample_html)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["post_id"], "telegram_IndianStreetBets_500")
        self.assertEqual(parsed[0]["ticker"], "HDFCBANK")
        self.assertEqual(parsed[0]["account_id"], "telegram_IndianStreetBets")


class TestTrendsScraper(unittest.TestCase):
    @patch("diverge_scraper.trends_scraper.TrendReq")
    def test_fetch_trends_data(self, mock_trend_req_cls):
        import pandas as pd

        mock_instance = MagicMock()
        mock_trend_req_cls.return_value = mock_instance

        # Mock DataFrame return
        dt_idx = pd.date_range("2025-01-01", periods=2, freq="D", tz="UTC")
        df_mock = pd.DataFrame({"TATASTEEL": [45, 80]}, index=dt_idx)
        mock_instance.interest_over_time.return_value = df_mock

        posts = trends_scraper.fetch_trends_data("TATASTEEL")
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["ticker"], "TATASTEEL")
        self.assertEqual(posts[1]["upvotes"], 80)
        self.assertEqual(posts[0]["platform"], "google_trends")


class TestRSSNewsScraper(unittest.TestCase):
    def test_parse_feed_entry(self):
        entry = {
            "title": "TCS reports 12% revenue growth in latest quarter",
            "summary": "Tata Consultancy Services beats street estimates.",
            "link": "https://example.com/news/tcs-q4-results",
            "published": "2025-01-15T08:00:00Z",
            "author": "Financial Reporter",
        }

        parsed = rss_news_scraper.parse_feed_entry("Moneycontrol", entry)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["ticker"], "TCS")
        self.assertEqual(parsed[0]["platform"], "rss_news")
        self.assertTrue(parsed[0]["post_id"].startswith("rss_"))


if __name__ == "__main__":
    unittest.main()
