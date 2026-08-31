# Phase 1 — Data Collection

Built the Diverge Phase 1 scraper module (`diverge_scraper/`).
Implemented five scrapers: Reddit (public JSON/RSS), StockTwits (public stream),
Telegram (public channel preview), RSS news feeds, and Google Trends.
Stored all raw posts in `raw_posts` table with platform, ticker, account, timestamp, text, and stable_id deduplication.
Added robots.txt compliance, rate-limit delays, retention purge, and a summary report.
