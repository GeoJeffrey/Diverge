"""
storage.py

Unified SQLite storage layer for raw scraped posts and Phase 2 extracted features.
Tables:
  - raw_posts: Ingested raw post/comment metadata.
  - post_timing: Per-post inter-arrival deltas & first-mention flags.
  - ticker_time_bins: Aggregated 5-minute post counts per ticker.
  - text_features: Sentiment scores, capitulation flags, sarcasm calibration, conviction-hedge ratios.
  - periodicity_stats: Rolling window KS tests, autocorrelation peaks, FFT dominant frequencies, onset dispersion.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_posts (
    post_id       TEXT PRIMARY KEY,
    account_id    TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,   -- ISO 8601 string, always UTC
    community     TEXT,            -- e.g. r/wallstreetbets, t.me/channel, RSS feed
    ticker        TEXT,            -- e.g. TATASTEEL, RELIANCE
    raw_text      TEXT,
    upvotes       INTEGER DEFAULT 0,
    platform      TEXT NOT NULL,   -- 'reddit', 'stocktwits', 'telegram', 'google_trends', 'rss_news'
    scraped_at    TEXT NOT NULL    -- when OUR scraper collected it
);

CREATE INDEX IF NOT EXISTS idx_ticker_time
    ON raw_posts (ticker, timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_account_ticker
    ON raw_posts (account_id, ticker);

CREATE TABLE IF NOT EXISTS post_timing (
    post_id          TEXT PRIMARY KEY REFERENCES raw_posts(post_id),
    ticker           TEXT NOT NULL,
    timestamp_utc    TEXT NOT NULL,
    delta_seconds    REAL,            -- time in seconds since previous post for this ticker
    is_first_mention INTEGER DEFAULT 0, -- 1 if account's first post on this ticker, else 0
    computed_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_timing_ticker_time
    ON post_timing (ticker, timestamp_utc);

CREATE TABLE IF NOT EXISTS ticker_time_bins (
    ticker        TEXT NOT NULL,
    bin_start_utc TEXT NOT NULL,
    post_count    INTEGER DEFAULT 0,
    PRIMARY KEY (ticker, bin_start_utc)
);

CREATE TABLE IF NOT EXISTS text_features (
    post_id                    TEXT PRIMARY KEY REFERENCES raw_posts(post_id),
    sentiment_score            REAL,            -- -1.0 to 1.0
    sentiment_label            TEXT,            -- 'bullish' / 'bearish' / 'neutral'
    capitulation_flag          INTEGER,         -- 0 or 1
    capitulation_confidence    REAL,            -- 0.0 to 1.0
    is_sarcastic               INTEGER,         -- 0 or 1
    irony_adjusted_sentiment   REAL,            -- sentiment_score after sarcasm correction
    conviction_hedge_ratio     REAL,            -- certainty word count / hedge word count
    language                   TEXT,            -- 'en', 'hi-en-mixed', etc.
    computed_at                TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS periodicity_stats (
    ticker                     TEXT NOT NULL,
    window_start_utc           TEXT NOT NULL,
    window_end_utc             TEXT NOT NULL,
    ks_statistic               REAL,            -- Kolmogorov-Smirnov vs exponential fit
    acf_peak_lag_minutes       REAL,            -- lag of strongest autocorrelation peak
    acf_peak_strength           REAL,            -- 0.0 to 1.0
    dominant_frequency_minutes REAL,            -- from FFT, null if no clear peak
    onset_dispersion_index     REAL,            -- variance-to-mean ratio of first-mentions
    PRIMARY KEY (ticker, window_start_utc)
);
"""


def get_connection(db_path: Path = config.DB_PATH) -> sqlite3.Connection:
    """Open and initialize SQLite database with SCHEMA."""
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def insert_post(conn: sqlite3.Connection, post: Dict[str, Any]) -> None:
    """
    Insert one raw post into raw_posts. Silently ignores duplicates (same post_id)
    so re-running a scraper on overlapping time windows never creates duplicates.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO raw_posts
            (post_id, account_id, timestamp_utc, community,
             ticker, raw_text, upvotes, platform, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            post["post_id"],
            post["account_id"],
            post["timestamp_utc"],
            post.get("community"),
            post.get("ticker"),
            post.get("raw_text", ""),
            post.get("upvotes", 0),
            post["platform"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def insert_many(posts: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """
    Batch insert posts list into SQLite database.
    Returns the number of newly inserted rows.
    """
    if not posts:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
    with conn:
        for post in posts:
            insert_post(conn, post)
    after = conn.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
    conn.close()
    return after - before


def purge_old_text(retention_days: int = config.RETENTION_DAYS, db_path: Path = config.DB_PATH) -> int:
    """
    Blank out raw_text for records older than retention_days (keeping metadata columns intact).
    Returns count of updated rows.
    """
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff_dt.isoformat()

    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            UPDATE raw_posts
            SET raw_text = ''
            WHERE timestamp_utc < ? AND raw_text != '' AND raw_text IS NOT NULL
            """,
            (cutoff_iso,),
        )
        updated_count = cursor.rowcount
    conn.close()
    return updated_count


def count_by_platform(db_path: Path = config.DB_PATH) -> Dict[str, int]:
    """Return dictionary of row counts grouped by platform."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT platform, COUNT(*) FROM raw_posts GROUP BY platform"
    ).fetchall()
    conn.close()
    return dict(rows)


def recent_posts(limit: int = 5, db_path: Path = config.DB_PATH) -> List[Tuple[Any, ...]]:
    """Return most recently scraped rows."""
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT platform, ticker, account_id, timestamp_utc, raw_text
        FROM raw_posts ORDER BY scraped_at DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows


# --- Phase 2 Storage Functions ---

def insert_timing_features(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert rows into post_timing table using INSERT OR IGNORE."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM post_timing").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO post_timing
                    (post_id, ticker, timestamp_utc, delta_seconds, is_first_mention, computed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    r["post_id"],
                    r["ticker"],
                    r["timestamp_utc"],
                    r.get("delta_seconds"),
                    r.get("is_first_mention", 0),
                    r.get("computed_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM post_timing").fetchone()[0]
    conn.close()
    return after - before


def insert_time_bins(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert or update rows into ticker_time_bins using INSERT OR REPLACE."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM ticker_time_bins").fetchone()[0]
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO ticker_time_bins
                    (ticker, bin_start_utc, post_count)
                VALUES (?, ?, ?)
                """,
                (r["ticker"], r["bin_start_utc"], r.get("post_count", 0)),
            )
    after = conn.execute("SELECT COUNT(*) FROM ticker_time_bins").fetchone()[0]
    conn.close()
    return after - before


def insert_text_features(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert rows into text_features using INSERT OR IGNORE."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM text_features").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO text_features
                    (post_id, sentiment_score, sentiment_label, capitulation_flag,
                     capitulation_confidence, is_sarcastic, irony_adjusted_sentiment,
                     conviction_hedge_ratio, language, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["post_id"],
                    r.get("sentiment_score"),
                    r.get("sentiment_label"),
                    r.get("capitulation_flag", 0),
                    r.get("capitulation_confidence", 0.0),
                    r.get("is_sarcastic", 0),
                    r.get("irony_adjusted_sentiment"),
                    r.get("conviction_hedge_ratio"),
                    r.get("language", "en"),
                    r.get("computed_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM text_features").fetchone()[0]
    conn.close()
    return after - before


def get_all_posts_for_text(db_path: Path = config.DB_PATH) -> List[Tuple[str, str, str]]:
    """
    Select post_id, raw_text, ticker from raw_posts for text feature extraction.
    Deliberately omits account_id and timestamp_utc to keep the text track blind to timing data.
    """
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT post_id, raw_text, ticker
        FROM raw_posts
        WHERE raw_text IS NOT NULL AND raw_text != ''
        """
    ).fetchall()
    conn.close()
    return rows


def insert_periodicity_stats(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert or replace rows in periodicity_stats table."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM periodicity_stats").fetchone()[0]
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO periodicity_stats
                    (ticker, window_start_utc, window_end_utc, ks_statistic,
                     acf_peak_lag_minutes, acf_peak_strength, dominant_frequency_minutes,
                     onset_dispersion_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r["window_end_utc"],
                    r.get("ks_statistic"),
                    r.get("acf_peak_lag_minutes"),
                    r.get("acf_peak_strength"),
                    r.get("dominant_frequency_minutes"),
                    r.get("onset_dispersion_index"),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM periodicity_stats").fetchone()[0]
    conn.close()
    return after - before


def count_phase2_tables(db_path: Path = config.DB_PATH) -> Dict[str, int]:
    """Return dictionary of row counts for all Phase 1 and Phase 2 tables."""
    conn = get_connection(db_path)
    tables = ["raw_posts", "post_timing", "ticker_time_bins", "text_features", "periodicity_stats"]
    counts = {}
    for t in tables:
        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        counts[t] = c
    conn.close()
    return counts
