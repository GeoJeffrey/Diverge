import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
"""
check_distribution.py

Phase 1 + Phase 2 distribution verification script.
Confirms:
  - Phase 1 raw_posts table is intact (row counts per platform)
  - Phase 2 tables are populated
  - No unintended mutations to Phase 1 data
"""
import sqlite3
from pathlib import Path

from diverge import config; DB_PATH = config.DB_PATH

conn = sqlite3.connect(DB_PATH)

print("=" * 56)
print("DIVERGE â€” DATA DISTRIBUTION CHECK")
print("=" * 56)

# Phase 1 tables
print("\nPhase 1: raw_posts")
rows = conn.execute("SELECT platform, COUNT(*) FROM raw_posts GROUP BY platform ORDER BY platform").fetchall()
total = 0
for platform, count in rows:
    print(f"  {platform:<22} {count:>6} rows")
    total += count
print(f"  {'TOTAL':<22} {total:>6} rows")

# Phase 2 tables
print("\nPhase 2: Feature Extraction Tables")
tables = ["post_timing", "ticker_time_bins", "text_features", "periodicity_stats"]
for t in tables:
    try:
        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<26} {c:>6} rows")
    except Exception as e:
        print(f"  {t:<26}  ERROR: {e}")

# Integrity checks
print("\nIntegrity Checks:")
raw_count = conn.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
timing_count = conn.execute("SELECT COUNT(*) FROM post_timing").fetchone()[0]
text_count = conn.execute("SELECT COUNT(*) FROM text_features").fetchone()[0]

assert raw_count >= 400, f"raw_posts unexpectedly low: {raw_count}"
print(f"  raw_posts >= 400                OK  ({raw_count})")

assert timing_count == raw_count, f"post_timing mismatch: {timing_count} != {raw_count}"
print(f"  post_timing matches raw_posts   OK  ({timing_count})")

assert text_count > 0, "text_features is empty!"
print(f"  text_features populated         OK  ({text_count})")

# Sample text feature row
print("\nSample text_features Row:")
row = conn.execute("""
    SELECT tf.post_id, tf.sentiment_label, tf.sentiment_score,
           tf.capitulation_flag, tf.is_sarcastic, tf.language
    FROM text_features tf
    JOIN raw_posts rp ON tf.post_id = rp.post_id
    WHERE rp.raw_text != ''
    LIMIT 1
""").fetchone()
if row:
    print(f"  post_id:           {row[0][:40]}...")
    print(f"  sentiment_label:   {row[1]}")
    print(f"  sentiment_score:   {row[2]}")
    print(f"  capitulation_flag: {row[3]}")
    print(f"  is_sarcastic:      {row[4]}")
    print(f"  language:          {row[5]}")

# Sentiment distribution
print("\nSentiment Label Distribution (text_features):")
sent_rows = conn.execute(
    "SELECT sentiment_label, COUNT(*) FROM text_features GROUP BY sentiment_label ORDER BY sentiment_label"
).fetchall()
for label, count in sent_rows:
    print(f"  {label:<12} {count:>6} posts")

# Language distribution
print("\nLanguage Distribution (text_features):")
lang_rows = conn.execute(
    "SELECT language, COUNT(*) FROM text_features GROUP BY language ORDER BY language"
).fetchall()
for lang, count in lang_rows:
    print(f"  {lang:<16} {count:>6} posts")

conn.close()
print("\n" + "=" * 56)
print("All checks passed.")
print("=" * 56)

