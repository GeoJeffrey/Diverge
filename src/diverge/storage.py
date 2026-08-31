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

CREATE TABLE IF NOT EXISTS index_values (
    ticker           TEXT NOT NULL,
    window_start_utc TEXT NOT NULL,
    window_end_utc   TEXT,
    rn               REAL,
    rn_confidence    REAL,
    cirg             REAL,
    cli              REAL,
    cassi            REAL,
    vdi              REAL,
    computed_at      TEXT NOT NULL,
    PRIMARY KEY (ticker, window_start_utc)
);

CREATE TABLE IF NOT EXISTS consumer_sentiment (
    id                     TEXT PRIMARY KEY,
    ticker                 TEXT NOT NULL,
    timestamp_utc          TEXT NOT NULL,
    review_sentiment_score REAL NOT NULL,
    source                 TEXT NOT NULL,
    raw_text               TEXT,
    created_at             TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_consumer_ticker_time
    ON consumer_sentiment (ticker, timestamp_utc);

CREATE TABLE IF NOT EXISTS coordination_scores (
    ticker             TEXT NOT NULL,
    window_start_utc   TEXT NOT NULL,
    window_end_utc     TEXT,
    ks_component       REAL,           -- normalized 0-1, from periodicity_stats.ks_statistic
    acf_component      REAL,           -- normalized 0-1, from periodicity_stats.acf_peak_strength
    onset_component    REAL,           -- normalized 0-1, from periodicity_stats.onset_dispersion_index
    duplicate_ratio    REAL,           -- fraction of near-duplicate posts in window
    sentiment_variance REAL,           -- variance of sentiment_score in window (low = suspicious)
    coordination_score REAL,           -- 0-100 combined score
    confidence_flag    TEXT,           -- 'high_trust' / 'moderate' / 'low_trust' / 'insufficient_data'
    computed_at        TEXT NOT NULL,
    PRIMARY KEY (ticker, window_start_utc)
);

CREATE INDEX IF NOT EXISTS idx_coord_ticker_time
    ON coordination_scores (ticker, window_start_utc);

CREATE TABLE IF NOT EXISTS ticker_window_metrics (
    ticker                 TEXT NOT NULL,
    window_start_utc       TEXT NOT NULL,
    window_end_utc         TEXT,
    rn                     REAL,
    rn_confidence          REAL,
    cirg                   REAL,
    cli                    REAL,
    cassi                  REAL,
    vdi                    REAL,
    coordination_score     REAL,
    confidence_flag        TEXT,
    composite_score        REAL,       -- 0-100, nullable
    dominant_index         TEXT,       -- 'rn' / 'cassi' / 'vdi' / 'insufficient_data'
    risk_flags             TEXT,       -- JSON array string, e.g. '["hype_outrunning_reality"]'
    aggregation_confidence TEXT,       -- mirrors confidence_flag post-dampening
    computed_at            TEXT NOT NULL,
    PRIMARY KEY (ticker, window_start_utc)
);

CREATE INDEX IF NOT EXISTS idx_twm_ticker_time
    ON ticker_window_metrics (ticker, window_start_utc);

CREATE TABLE IF NOT EXISTS reasoning_trace (
    trace_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker             TEXT NOT NULL,
    window_start_utc   TEXT NOT NULL,
    post_id            TEXT NOT NULL,
    contributed_to     TEXT NOT NULL,
    weight             REAL NOT NULL,
    created_at         TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES raw_posts(post_id)
);

CREATE INDEX IF NOT EXISTS idx_trace_ticker_time
    ON reasoning_trace (ticker, window_start_utc);

CREATE TABLE IF NOT EXISTS duplicate_pairs (
    ticker             TEXT NOT NULL,
    window_start_utc   TEXT NOT NULL,
    post_id_a          TEXT NOT NULL,
    post_id_b          TEXT NOT NULL,
    similarity         REAL NOT NULL,
    PRIMARY KEY (ticker, window_start_utc, post_id_a, post_id_b)
);

CREATE TABLE IF NOT EXISTS narrative_phylogeny (
    ticker                  TEXT NOT NULL,
    window_start_utc        TEXT NOT NULL,
    window_end_utc          TEXT,
    parent_window_start_utc TEXT,
    mutation_type           TEXT NOT NULL,
    mutation_detail         TEXT,
    composite_delta         REAL,
    computed_at             TEXT NOT NULL,
    PRIMARY KEY (ticker, window_start_utc)
);

CREATE INDEX IF NOT EXISTS idx_phylogeny_ticker_time
    ON narrative_phylogeny (ticker, window_start_utc);
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


# --- Phase 3 Storage & Query Functions ---

def insert_index_values(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """
    Insert or replace rows in index_values table.
    Values get recomputed as data grows.
    """
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM index_values").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO index_values
                    (ticker, window_start_utc, window_end_utc, rn, rn_confidence,
                     cirg, cli, cassi, vdi, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r.get("window_end_utc"),
                    r.get("rn"),
                    r.get("rn_confidence"),
                    r.get("cirg"),
                    r.get("cli"),
                    r.get("cassi"),
                    r.get("vdi"),
                    r.get("computed_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM index_values").fetchone()[0]
    conn.close()
    return after - before


def insert_consumer_sentiment(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert rows into consumer_sentiment using INSERT OR IGNORE."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM consumer_sentiment").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO consumer_sentiment
                    (id, ticker, timestamp_utc, review_sentiment_score, source, raw_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["id"],
                    r["ticker"],
                    r["timestamp_utc"],
                    r["review_sentiment_score"],
                    r.get("source", "unknown"),
                    r.get("raw_text", ""),
                    r.get("created_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM consumer_sentiment").fetchone()[0]
    conn.close()
    return after - before


def get_text_features_for_window(
    ticker: str,
    start_utc: str = None,
    end_utc: str = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Fetch text_features joined with raw_posts for a given ticker and optional time window.
    Returns list of dicts with: post_id, ticker, timestamp_utc, sentiment_score,
    irony_adjusted_sentiment, capitulation_flag, language, etc.
    """
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT tf.post_id, rp.ticker, rp.timestamp_utc, tf.sentiment_score,
               tf.irony_adjusted_sentiment, tf.capitulation_flag, tf.language,
               tf.is_sarcastic, tf.conviction_hedge_ratio
        FROM text_features tf
        JOIN raw_posts rp ON tf.post_id = rp.post_id
        WHERE 1=1
    """
    params: List[Any] = []
    if ticker and ticker.upper() != "ALL":
        query += " AND rp.ticker = ?"
        params.append(ticker.upper())
    if start_utc:
        query += " AND rp.timestamp_utc >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND rp.timestamp_utc <= ?"
        params.append(end_utc)

    query += " ORDER BY rp.timestamp_utc ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_multi_ticker_sentiment_series(
    tickers: List[str] = None,
    start_utc: str = None,
    end_utc: str = None,
    db_path: Path = config.DB_PATH,
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Pull daily average sentiment per ticker for specified tickers within optional time window.
    Returns dictionary mapping ticker -> list of (date_str 'YYYY-MM-DD', avg_sentiment_score).
    """
    conn = get_connection(db_path)
    query = """
        SELECT rp.ticker,
               SUBSTR(rp.timestamp_utc, 1, 10) as post_date,
               AVG(COALESCE(tf.irony_adjusted_sentiment, tf.sentiment_score)) as avg_sentiment
        FROM text_features tf
        JOIN raw_posts rp ON tf.post_id = rp.post_id
        WHERE 1=1
    """
    params: List[Any] = []
    if tickers:
        placeholders = ",".join("?" for _ in tickers)
        query += f" AND rp.ticker IN ({placeholders})"
        params.extend([t.upper() for t in tickers])
    if start_utc:
        query += " AND rp.timestamp_utc >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND rp.timestamp_utc <= ?"
        params.append(end_utc)

    query += " GROUP BY rp.ticker, post_date ORDER BY post_date ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    result: Dict[str, List[Tuple[str, float]]] = {}
    for t, date_str, avg_sent in rows:
        if t not in result:
            result[t] = []
        result[t].append((date_str, float(avg_sent) if avg_sent is not None else 0.0))
    return result


def get_consumer_sentiment_for_ticker(
    ticker: str,
    start_utc: str = None,
    end_utc: str = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetch consumer_sentiment records for a ticker within an optional window."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM consumer_sentiment WHERE ticker = ?"
    params: List[Any] = [ticker.upper()]
    if start_utc:
        query += " AND timestamp_utc >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND timestamp_utc <= ?"
        params.append(end_utc)
    query += " ORDER BY timestamp_utc ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_post_timing_for_ticker(
    ticker: str,
    start_utc: str = None,
    end_utc: str = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetch post_timing rows joined with raw_posts account_id for a ticker."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT pt.post_id, pt.ticker, pt.timestamp_utc, pt.delta_seconds, pt.is_first_mention, rp.account_id
        FROM post_timing pt
        JOIN raw_posts rp ON pt.post_id = rp.post_id
        WHERE pt.ticker = ?
    """
    params: List[Any] = [ticker.upper()]
    if start_utc:
        query += " AND pt.timestamp_utc >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND pt.timestamp_utc <= ?"
        params.append(end_utc)
    query += " ORDER BY pt.timestamp_utc ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_all_tables(db_path: Path = config.DB_PATH) -> Dict[str, int]:
    """Return dictionary of row counts for all Phase 1-6 tables."""
    conn = get_connection(db_path)
    tables = [
        "raw_posts",
        "post_timing",
        "ticker_time_bins",
        "text_features",
        "periodicity_stats",
        "consumer_sentiment",
        "index_values",
        "coordination_scores",
        "ticker_window_metrics",
        "reasoning_trace",
        "duplicate_pairs",
        "narrative_phylogeny",
    ]
    counts = {}
    for t in tables:
        try:
            c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            counts[t] = c
        except Exception:
            counts[t] = 0
    conn.close()
    return counts


# --- Phase 4 Storage & Query Functions ---

def insert_coordination_scores(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """
    Insert or replace rows in coordination_scores table.
    """
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM coordination_scores").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO coordination_scores
                    (ticker, window_start_utc, window_end_utc, ks_component, acf_component,
                     onset_component, duplicate_ratio, sentiment_variance, coordination_score,
                     confidence_flag, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r.get("window_end_utc"),
                    r.get("ks_component"),
                    r.get("acf_component"),
                    r.get("onset_component"),
                    r.get("duplicate_ratio"),
                    r.get("sentiment_variance"),
                    r.get("coordination_score"),
                    r.get("confidence_flag", "insufficient_data"),
                    r.get("computed_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM coordination_scores").fetchone()[0]
    conn.close()
    return after - before


def get_periodicity_stats_for_window(
    ticker: Optional[str] = None,
    start_utc: Optional[str] = None,
    end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetch periodicity_stats rows for ticker and optional time window."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM periodicity_stats WHERE 1=1"
    params: List[Any] = []
    if ticker and ticker.upper() != "ALL":
        query += " AND ticker = ?"
        params.append(ticker.upper())
    if start_utc:
        query += " AND window_start_utc >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND window_end_utc <= ?"
        params.append(end_utc)
    query += " ORDER BY ticker ASC, window_start_utc ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_text_and_posts_for_window(
    ticker: str,
    start_utc: Optional[str] = None,
    end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Fetch joined raw_posts and text_features records for a given ticker and window.
    Returns post_id, account_id, raw_text, sentiment_score, platform, timestamp_utc, ticker.
    """
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT rp.post_id, rp.account_id, rp.ticker, rp.raw_text, rp.platform,
               rp.timestamp_utc, tf.sentiment_score, tf.irony_adjusted_sentiment, tf.language
        FROM raw_posts rp
        LEFT JOIN text_features tf ON rp.post_id = tf.post_id
        WHERE rp.ticker = ?
    """
    params: List[Any] = [ticker.upper()]
    if start_utc:
        query += " AND rp.timestamp_utc >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND rp.timestamp_utc <= ?"
        params.append(end_utc)
    query += " ORDER BY rp.timestamp_utc ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
def check_news_event_in_window(
    ticker: str,
    start_utc: str,
    end_utc: str,
    db_path: Path = config.DB_PATH,
) -> bool:
    """
    Check if an RSS news article or Google Trends spike exists for ticker in the given window.
    Used to dampen onset_component weight when legitimate news causes synchronized reactions.
    """
    conn = get_connection(db_path)
    query = """
        SELECT COUNT(*) FROM raw_posts
        WHERE ticker = ? AND platform IN ('rss_news', 'google_trends')
          AND timestamp_utc >= ? AND timestamp_utc <= ?
    """
    count = conn.execute(query, (ticker.upper(), start_utc, end_utc)).fetchone()[0]
    conn.close()
    return count > 0


# --- Phase 5 Storage & Query Functions ---

def insert_ticker_window_metrics(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert or replace rows in ticker_window_metrics table."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM ticker_window_metrics").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO ticker_window_metrics
                    (ticker, window_start_utc, window_end_utc, rn, rn_confidence, cirg, cli, cassi, vdi,
                     coordination_score, confidence_flag, composite_score, dominant_index, risk_flags,
                     aggregation_confidence, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r.get("window_end_utc"),
                    r.get("rn"),
                    r.get("rn_confidence"),
                    r.get("cirg"),
                    r.get("cli"),
                    r.get("cassi"),
                    r.get("vdi"),
                    r.get("coordination_score"),
                    r.get("confidence_flag"),
                    r.get("composite_score"),
                    r.get("dominant_index", "insufficient_data"),
                    r.get("risk_flags", "[]"),
                    r.get("aggregation_confidence", "insufficient_data"),
                    r.get("computed_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM ticker_window_metrics").fetchone()[0]
    conn.close()
    return after - before


def get_index_values_and_coordination_for_window(
    ticker: Optional[str] = None,
    start_utc: Optional[str] = None,
    end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Join index_values and coordination_scores on (ticker, window_start_utc).
    Returns a list of dicts with all raw inputs needed for Phase 5 composite aggregation.
    """
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row

    # Outer join approach to get all windows present in index_values OR coordination_scores
    query = """
        SELECT
            COALESCE(iv.ticker, cs.ticker) AS ticker,
            COALESCE(iv.window_start_utc, cs.window_start_utc) AS window_start_utc,
            COALESCE(iv.window_end_utc, cs.window_end_utc) AS window_end_utc,
            iv.rn,
            iv.rn_confidence,
            iv.cirg,
            iv.cli,
            iv.cassi,
            iv.vdi,
            cs.coordination_score,
            cs.confidence_flag
        FROM index_values iv
        LEFT JOIN coordination_scores cs
               ON iv.ticker = cs.ticker AND iv.window_start_utc = cs.window_start_utc
        WHERE 1=1
    """
    params: List[Any] = []
    if ticker and ticker.upper() != "ALL":
        query += " AND COALESCE(iv.ticker, cs.ticker) = ?"
        params.append(ticker.upper())
    if start_utc:
        query += " AND COALESCE(iv.window_start_utc, cs.window_start_utc) >= ?"
        params.append(start_utc)
    if end_utc:
        query += " AND COALESCE(iv.window_end_utc, cs.window_end_utc) <= ?"
        params.append(end_utc)
    query += " ORDER BY ticker ASC, window_start_utc ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Phase 6 Storage & Query Functions ---

def insert_duplicate_pairs(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert or replace rows into duplicate_pairs table."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM duplicate_pairs").fetchone()[0]
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO duplicate_pairs
                    (ticker, window_start_utc, post_id_a, post_id_b, similarity)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r["post_id_a"],
                    r["post_id_b"],
                    r.get("similarity", 1.0),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM duplicate_pairs").fetchone()[0]
    conn.close()
    return after - before


def get_duplicate_pairs_for_window(
    ticker: str,
    window_start_utc: str,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetch duplicate pairs for a given ticker and window."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT * FROM duplicate_pairs
        WHERE ticker = ? AND window_start_utc = ?
    """
    rows = conn.execute(query, (ticker.upper(), window_start_utc)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_reasoning_traces(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert rows into reasoning_trace table."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM reasoning_trace").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT INTO reasoning_trace
                    (ticker, window_start_utc, post_id, contributed_to, weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r["post_id"],
                    r["contributed_to"],
                    r.get("weight", 1.0),
                    r.get("created_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM reasoning_trace").fetchone()[0]
    conn.close()
    return after - before


def get_reasoning_traces_for_window(
    ticker: str,
    window_start_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetch reasoning_trace rows joined with raw_posts for a given ticker and window."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    if not window_start_utc:
        latest = conn.execute(
            "SELECT window_start_utc FROM reasoning_trace WHERE ticker = ? ORDER BY window_start_utc DESC LIMIT 1",
            (ticker.upper(),)
        ).fetchone()
        if latest:
            window_start_utc = latest[0]
        else:
            conn.close()
            return []
    query = """
        SELECT rt.trace_id, rt.ticker, rt.window_start_utc, rt.post_id, rt.contributed_to,
               rt.weight, rt.created_at, rp.raw_text, rp.account_id, rp.platform, rp.upvotes
        FROM reasoning_trace rt
        LEFT JOIN raw_posts rp ON rt.post_id = rp.post_id
        WHERE rt.ticker = ? AND rt.window_start_utc = ?
        ORDER BY rt.contributed_to ASC, rt.weight DESC
    """
    rows = conn.execute(query, (ticker.upper(), window_start_utc)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_narrative_phylogeny(rows: List[Dict[str, Any]], db_path: Path = config.DB_PATH) -> int:
    """Insert or replace rows into narrative_phylogeny table."""
    if not rows:
        return 0
    conn = get_connection(db_path)
    before = conn.execute("SELECT COUNT(*) FROM narrative_phylogeny").fetchone()[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO narrative_phylogeny
                    (ticker, window_start_utc, window_end_utc, parent_window_start_utc,
                     mutation_type, mutation_detail, composite_delta, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["ticker"],
                    r["window_start_utc"],
                    r.get("window_end_utc"),
                    r.get("parent_window_start_utc"),
                    r["mutation_type"],
                    r.get("mutation_detail", "{}"),
                    r.get("composite_delta"),
                    r.get("computed_at", now_iso),
                ),
            )
    after = conn.execute("SELECT COUNT(*) FROM narrative_phylogeny").fetchone()[0]
    conn.close()
    return after - before


def get_narrative_phylogeny_for_ticker(
    ticker: str,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetch narrative_phylogeny rows for a ticker ordered chronologically."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT * FROM narrative_phylogeny
        WHERE ticker = ?
        ORDER BY window_start_utc ASC
    """
    rows = conn.execute(query, (ticker.upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]




