"""
daily_volume_report.py

Daily operator report: posts ingested per platform over the last 24 hours.
Usage: python scripts/daily_volume_report.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlite3
from diverge import config

conn = sqlite3.connect(config.DB_PATH)
since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
rows = conn.execute(
    "SELECT platform, COUNT(*) FROM raw_posts WHERE scraped_at >= ? GROUP BY platform ORDER BY platform",
    (since,)
).fetchall()
print(f"Posts ingested in the last 24 h (since {since[:16]} UTC):")
for platform, count in rows:
    print(f"  {platform:<22} {count:>6}")
conn.close()
