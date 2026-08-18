"""
view_data.py

Helper script to easily view and inspect raw scraped posts stored in `diverge_raw.db`.

Usage:
  python view_data.py             # View 10 most recent posts
  python view_data.py --limit 20  # View 20 most recent posts
  python view_data.py --ticker RELIANCE # Filter by ticker
  python view_data.py --platform telegram # Filter by platform
"""

import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "diverge_raw.db"


def view_posts(limit: int = 10, ticker: str = None, platform: str = None):
    if not DB_PATH.exists():
        print(f"Database file '{DB_PATH}' does not exist yet. Run 'python main.py' first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT post_id, platform, ticker, account_id, timestamp_utc, community, upvotes, raw_text FROM raw_posts WHERE 1=1"
    params = []

    if ticker:
        query += " AND ticker = ?"
        params.append(ticker.upper())

    if platform:
        query += " AND platform = ?"
        params.append(platform.lower())

    query += " ORDER BY scraped_at DESC LIMIT ?"
    params.append(limit)

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    print("\n" + "=" * 80)
    print(f"RAW POSTS DATA (Showing max {limit} rows)")
    print("=" * 80)

    if not rows:
        print("No matching rows found.")
        return

    for i, (post_id, plat, tick, account, ts, comm, upvotes, text) in enumerate(rows, 1):
        print(f"[{i}] ID: {post_id}")
        print(f"    Platform: {plat} | Ticker: {tick} | Community: {comm}")
        print(f"    Account: {account} | Timestamp UTC: {ts} | Upvotes/Score: {upvotes}")
        print(f"    Raw Text:\n      {text.strip()}\n")
        print("-" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View raw scraped data in diverge_raw.db")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent posts to show (default: 10)")
    parser.add_argument("--ticker", type=str, help="Filter by ticker symbol (e.g. RELIANCE, TATASTEEL)")
    parser.add_argument("--platform", type=str, help="Filter by platform (e.g. telegram, google_trends, rss_news)")
    args = parser.parse_args()

    view_posts(limit=args.limit, ticker=args.ticker, platform=args.platform)
