import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
"""
seed_historical_data.py

Historical Data Seeder for Diverge.
Generates 60 days of realistic historical post data, timing deltas, text features,
and consumer review ratings across all tracked tickers and platforms.

This enables immediate testing and full numerical evaluation of all Phase 3 indices
(CLI, VDI, CASSI, Rn, CIRG) without waiting 30-60 days for live scraping accumulation.

Usage:
    python seed_historical_data.py
    python run_all.py --skip-scrape
"""

import hashlib
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from diverge import config, storage, utils

logger = utils.setup_logger("seed_historical_data")

TICKERS = list(config.TICKERS.keys())
PLATFORMS = ["reddit", "stocktwits", "telegram", "google_trends", "rss_news"]

SAMPLE_ENGLISH_TEXTS = [
    "Great quarterly earnings performance for {ticker}. Strong revenue growth and margin expansion.",
    "Is {ticker} overvalued at these levels? Looking to take profits or hedge position.",
    "Market cap for {ticker} reaches new high amidst strong institutional buying.",
    "Bearish breakdown in {ticker}. Selling pressure accelerating across major support levels.",
    "Panic selling in {ticker}! I lost everything, total capitulation liquidating position.",
    "Solid long term holding for {ticker}. Dividend yield remains attractive.",
]

SAMPLE_HINGLISH_TEXTS = [
    "Bhai {ticker} ka target kya hai? Aaj bohot accha breakout dikha raha hai.",
    "Suno dosto {ticker} me dip buy karo, long term me multibagger banega.",
    "Kya bakwaas stock hai {ticker}, sab loss ho gaya, bilkul mood kharab kar diya.",
    "Aapko kya lagta hai {ticker} next week 5% upar jayega ya girega?",
    "Arre yaar {ticker} me trailing stop loss hit ho gaya, exit kar raha hu.",
    "Aaj {ticker} me heavy volume buying ho rahi hai, kal gap up opening pakka.",
]

CONSUMER_TICKERS = ["RELIANCE", "HDFCBANK", "SBIN", "BHARTIARTL", "ITC", "AAPL", "AMZN"]


def generate_seed_data(days: int = 60, posts_per_day: int = 25):
    logger.info(f"Generating {days} days of historical seed data (~{days * posts_per_day} posts)...")
    db_path = config.DB_PATH
    conn = storage.get_connection(db_path)

    now_dt = datetime.now(timezone.utc)
    raw_posts = []
    text_features = []
    post_timings = []
    consumer_reviews = []

    user_handles = [f"trader_user_{i}" for i in range(1, 40)]

    for day_offset in range(days, -1, -1):
        day_date = now_dt - timedelta(days=day_offset)

        for _ in range(posts_per_day):
            ticker = random.choice(TICKERS)
            platform = random.choice(PLATFORMS)
            account_id = random.choice(user_handles)

            # 40% Hinglish, 60% English
            is_hinglish = random.random() < 0.40
            lang = "hi-en-mixed" if is_hinglish else "en"
            text_template = random.choice(SAMPLE_HINGLISH_TEXTS if is_hinglish else SAMPLE_ENGLISH_TEXTS)
            raw_text = text_template.format(ticker=ticker)

            # Random timestamp within the day
            post_time = day_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            post_iso = post_time.isoformat()

            post_id = hashlib.sha256(f"{ticker}_{platform}_{account_id}_{post_iso}_{random.random()}".encode("utf-8")).hexdigest()[:16]
            upvotes = random.randint(0, 250)

            raw_posts.append({
                "post_id": post_id,
                "account_id": account_id,
                "timestamp_utc": post_iso,
                "community": f"community_{platform}",
                "ticker": ticker,
                "raw_text": raw_text,
                "upvotes": upvotes,
                "platform": platform,
            })

            # Text features
            sentiment_score = round(random.uniform(-0.85, 0.95), 3)
            sentiment_label = "bullish" if sentiment_score > 0.15 else "bearish" if sentiment_score < -0.15 else "neutral"
            capitulation_flag = 1 if "panic" in raw_text.lower() or "lost everything" in raw_text.lower() or random.random() < 0.08 else 0
            is_sarcastic = 1 if random.random() < 0.05 else 0

            text_features.append({
                "post_id": post_id,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "capitulation_flag": capitulation_flag,
                "capitulation_confidence": 0.85 if capitulation_flag else 0.0,
                "is_sarcastic": is_sarcastic,
                "irony_adjusted_sentiment": -sentiment_score if is_sarcastic else sentiment_score,
                "conviction_hedge_ratio": round(random.uniform(0.5, 3.0), 2),
                "language": lang,
                "computed_at": post_iso,
            })

            # Post timing
            delta_sec = float(random.randint(30, 7200))
            is_first_mention = 1 if random.random() < 0.25 else 0
            post_timings.append({
                "post_id": post_id,
                "ticker": ticker,
                "timestamp_utc": post_iso,
                "delta_seconds": delta_sec,
                "is_first_mention": is_first_mention,
                "computed_at": post_iso,
            })

        # Generate consumer reviews for consumer-facing tickers
        for consumer_ticker in CONSUMER_TICKERS:
            if random.random() < 0.5:
                rev_id = hashlib.sha256(f"rev_{consumer_ticker}_{day_offset}".encode("utf-8")).hexdigest()[:16]
                score = round(random.uniform(0.1, 0.9), 3)
                consumer_reviews.append({
                    "id": rev_id,
                    "ticker": consumer_ticker,
                    "timestamp_utc": day_date.isoformat(),
                    "review_sentiment_score": score,
                    "source": "public_app_store_reviews",
                    "raw_text": f"Public rating for {consumer_ticker}",
                    "created_at": day_date.isoformat(),
                })

    # Bulk Insert
    added_posts = storage.insert_many(raw_posts, db_path=db_path)
    added_tf = storage.insert_text_features(text_features, db_path=db_path)
    added_pt = storage.insert_timing_features(post_timings, db_path=db_path)
    added_cr = storage.insert_consumer_sentiment(consumer_reviews, db_path=db_path)

    logger.info("=" * 60)
    logger.info("HISTORICAL DATA SEEDING COMPLETE")
    logger.info(f"  - raw_posts inserted:        {added_posts}")
    logger.info(f"  - text_features inserted:   {added_tf}")
    logger.info(f"  - post_timing inserted:     {added_pt}")
    logger.info(f"  - consumer_sentiment:       {added_cr}")
    logger.info("=" * 60)

    print("\n[SUCCESS] Seeded 60 days of historical data! Now run:\n  python run_all.py --skip-scrape\n")


if __name__ == "__main__":
    generate_seed_data(days=60, posts_per_day=30)


