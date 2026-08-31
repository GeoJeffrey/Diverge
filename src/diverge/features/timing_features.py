"""
timing_features.py

Phase 2 Timing Track: Feature Extraction
Computes inter-arrival time deltas, first-mention flags per user/ticker,
and 5-minute binned post counts. Stores metrics in `post_timing` and `ticker_time_bins`.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .. import config, storage, utils

logger = utils.setup_logger("timing_features")


def compute_timing_features(db_path: Path = config.DB_PATH) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Query raw_posts ordered by ticker and timestamp_utc.
    Compute inter-arrival delta_seconds, is_first_mention per account/ticker,
    and 5-minute binned counts per ticker.
    """
    conn = storage.get_connection(db_path)
    rows = conn.execute(
        """
        SELECT post_id, account_id, timestamp_utc, ticker
        FROM raw_posts
        ORDER BY ticker ASC, timestamp_utc ASC
        """
    ).fetchall()
    conn.close()

    timing_rows = []
    bin_counts = {}  # (ticker, bin_start_utc) -> count
    seen_accounts = set()  # (account_id, ticker)
    last_timestamps = {}  # ticker -> dt

    for post_id, account_id, ts_str, ticker in rows:
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)

        # Delta seconds computation
        delta_sec = None
        if ticker in last_timestamps:
            delta_sec = (dt - last_timestamps[ticker]).total_seconds()
            if delta_sec < 0:
                delta_sec = 0.0
        last_timestamps[ticker] = dt

        # First mention check
        acct_key = (account_id, ticker)
        if acct_key not in seen_accounts:
            is_first = 1
            seen_accounts.add(acct_key)
        else:
            is_first = 0

        timing_rows.append({
            "post_id": post_id,
            "ticker": ticker,
            "timestamp_utc": dt.isoformat(),
            "delta_seconds": delta_sec,
            "is_first_mention": is_first,
        })

        # 5-minute time binning (round down to nearest 5 minutes)
        minute_5 = (dt.minute // 5) * 5
        bin_dt = dt.replace(minute=minute_5, second=0, microsecond=0)
        bin_key = (ticker, bin_dt.isoformat())
        bin_counts[bin_key] = bin_counts.get(bin_key, 0) + 1

    time_bin_rows = [
        {"ticker": tk, "bin_start_utc": b_start, "post_count": cnt}
        for (tk, b_start), cnt in bin_counts.items()
    ]

    return timing_rows, time_bin_rows


def run(db_path: Path = config.DB_PATH) -> Dict[str, int]:
    """Execute timing features extraction and storage."""
    logger.info("Extracting timing features and 5-minute time bins...")
    timing_rows, time_bin_rows = compute_timing_features(db_path)

    new_timing = storage.insert_timing_features(timing_rows, db_path=db_path)
    new_bins = storage.insert_time_bins(time_bin_rows, db_path=db_path)

    logger.info(f"Timing extraction complete. Processed {len(timing_rows)} posts, {new_timing} timing rows added, {new_bins} time bins updated.")
    return {"timing_rows": new_timing, "time_bins": new_bins}


if __name__ == "__main__":
    run()

