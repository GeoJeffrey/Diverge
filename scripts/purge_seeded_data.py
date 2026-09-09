"""
purge_seeded_data.py

Removes all fake/seeded data from the Diverge database and recomputes
all derived tables from live data only.

Seeded data is identified by:
  - raw_posts with account_id LIKE 'trader_user_%' (from seed_historical_data.py)
  - consumer_sentiment with raw_text LIKE 'Public rating for %' (seed pattern)

After purging seeded raw data, all derived tables (text_features, post_timing,
index_values, etc.) are wiped and recomputed from live data only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlite3
from diverge import config

DB_PATH = config.DB_PATH


def purge():
    conn = sqlite3.connect(DB_PATH)

    # --- Before counts ---
    print("=" * 60)
    print("PURGE SEEDED DATA — BEFORE")
    print("=" * 60)

    total_raw = conn.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
    seeded_raw = conn.execute(
        "SELECT COUNT(*) FROM raw_posts WHERE account_id LIKE 'trader_user_%'"
    ).fetchone()[0]
    print(f"raw_posts:           total={total_raw}, seeded={seeded_raw}, live={total_raw - seeded_raw}")

    total_cs = conn.execute("SELECT COUNT(*) FROM consumer_sentiment").fetchone()[0]
    seeded_cs = conn.execute(
        "SELECT COUNT(*) FROM consumer_sentiment WHERE raw_text LIKE 'Public rating for %'"
    ).fetchone()[0]
    print(f"consumer_sentiment:  total={total_cs}, seeded={seeded_cs}, live={total_cs - seeded_cs}")

    for tbl in [
        "text_features", "post_timing", "ticker_time_bins", "periodicity_stats",
        "index_values", "coordination_scores", "ticker_window_metrics",
        "reasoning_trace", "duplicate_pairs", "narrative_phylogeny",
    ]:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"{tbl}: {cnt}")
        except Exception:
            print(f"{tbl}: table not found")

    # --- Purge seeded raw_posts and their dependent features ---
    print("\n" + "=" * 60)
    print("PURGING...")
    print("=" * 60)

    # 1. Delete text_features linked to seeded posts
    conn.execute("""
        DELETE FROM text_features WHERE post_id IN (
            SELECT post_id FROM raw_posts WHERE account_id LIKE 'trader_user_%'
        )
    """)
    print(f"  Deleted seeded text_features: {conn.total_changes}")

    # 2. Delete post_timing linked to seeded posts
    conn.execute("""
        DELETE FROM post_timing WHERE post_id IN (
            SELECT post_id FROM raw_posts WHERE account_id LIKE 'trader_user_%'
        )
    """)
    print(f"  Deleted seeded post_timing: {conn.total_changes}")

    # 3. Delete seeded raw_posts themselves
    conn.execute("DELETE FROM raw_posts WHERE account_id LIKE 'trader_user_%'")
    print(f"  Deleted seeded raw_posts: {conn.total_changes}")

    # 4. Delete seeded consumer_sentiment
    conn.execute("DELETE FROM consumer_sentiment WHERE raw_text LIKE 'Public rating for %'")
    print(f"  Deleted seeded consumer_sentiment: {conn.total_changes}")

    # 5. Wipe all derived/computed tables — they'll be recomputed from live data
    for tbl in [
        "ticker_time_bins", "periodicity_stats",
        "index_values", "coordination_scores", "ticker_window_metrics",
        "reasoning_trace", "duplicate_pairs", "narrative_phylogeny",
    ]:
        try:
            conn.execute(f"DELETE FROM {tbl}")
            print(f"  Cleared derived table: {tbl}")
        except Exception:
            pass

    conn.commit()

    # --- After counts ---
    print("\n" + "=" * 60)
    print("AFTER PURGE")
    print("=" * 60)
    remaining_raw = conn.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
    remaining_seeded = conn.execute(
        "SELECT COUNT(*) FROM raw_posts WHERE account_id LIKE 'trader_user_%'"
    ).fetchone()[0]
    remaining_cs = conn.execute("SELECT COUNT(*) FROM consumer_sentiment").fetchone()[0]
    remaining_tf = conn.execute("SELECT COUNT(*) FROM text_features").fetchone()[0]
    remaining_pt = conn.execute("SELECT COUNT(*) FROM post_timing").fetchone()[0]

    print(f"raw_posts:           {remaining_raw} (seeded remaining: {remaining_seeded})")
    print(f"text_features:       {remaining_tf}")
    print(f"post_timing:         {remaining_pt}")
    print(f"consumer_sentiment:  {remaining_cs}")

    # VACUUM to reclaim space
    conn.execute("VACUUM")
    conn.close()

    print("\n[SUCCESS] All seeded/fake data purged. Database contains only live data.")
    print("Now run: python run_all.py  (full pipeline with live scraping + recompute)")


if __name__ == "__main__":
    purge()
