"""
check_counts.py

Quick operator utility: prints row counts for all Diverge database tables.
Usage: python scripts/check_counts.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlite3
from diverge import config

conn = sqlite3.connect(config.DB_PATH)
tables = [
    "raw_posts", "post_timing", "ticker_time_bins", "text_features",
    "periodicity_stats", "consumer_sentiment", "index_values",
    "coordination_scores", "ticker_window_metrics",
    "duplicate_pairs", "reasoning_trace", "narrative_phylogeny",
]
print("=" * 45)
print("DIVERGE — TABLE ROW COUNTS")
print("=" * 45)
total = 0
for t in tables:
    try:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<28} {n:>8,}")
        total += n
    except Exception as e:
        print(f"  {t:<28} ERROR: {e}")
print("-" * 45)
print(f"  {'TOTAL':<28} {total:>8,}")
print("=" * 45)
conn.close()
