# Diverge — Phase 1 Data Collection Module

A zero-API, zero-auth financial narrative sentiment data collection pipeline for **Diverge**.

This module gathers financial discussions, news, search trends, and social media commentary mentioning tracked tickers (e.g. `TATASTEEL`, `RELIANCE`, `INFY`, `TCS`, `HDFCBANK`).

---

## Zero-Config Setup & Principles

### What "No API" Means
No official platform APIs, developer account registrations, OAuth credentials, or SDK libraries (`praw`, `telethon`, `tweepy`) are used. 

Instead, scrapers rely exclusively on **raw HTTP requests**, **public JSON endpoints**, **RSS XML feeds**, and **public web HTML parsing**.

### Zero API Key Configuration
No `.env` file or API key configuration is required to execute the pipeline. You can clone the project, install dependencies, and run immediately:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run data collection pipeline
python main.py
# OR
python -m diverge_scraper.main
```

---

## Source Architecture & ToS / Fragility Tradeoffs

> [!WARNING]  
> **Legal & ToS Gray Area Notice**  
> Fetching public web pages, preview HTML, or undocumented JSON endpoints without official API credentials sits in a legal/ToS gray area. While technically reachable without authentication, these methods can violate platform Terms of Service (ToS) and are significantly more fragile than official APIs. Platforms may introduce rate limits, IP blocks, CAPTCHA challenges, or structure changes without prior notice.

### 1. Reddit (Public JSON Endpoints)
- **Endpoint**: `https://www.reddit.com/r/{subreddit}/new.json?limit=100` and post comment endpoints.
- **Header**: Custom honest User-Agent (`DivergeResearchBot/0.1 (student project)`).
- **Tradeoffs & Fragility**: Undocumented public endpoint. Reddit strictly rate-limits or blocks unauthenticated user-agents or IPs without warning.

### 2. StockTwits (Public Stream API)
- **Endpoint**: `https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json`
- **Tradeoffs & Fragility**: Public stream endpoint capped at roughly 200 requests/hour for anonymous requests. Exceeding limits results in HTTP 429 errors.

### 3. Telegram (Public Channel HTML Web Previews)
- **Endpoint**: `https://t.me/s/{channel_username}`
- **Tradeoffs & Fragility**: Only works for **PUBLIC** Telegram channels. Displays only a limited recent-message window (no full historical backlog). Dependent on BeautifulSoup HTML class stability (`tgme_widget_message_text`, `tgme_widget_message_date time`).

### 4. Google Trends (`pytrends`)
- **Library**: `pytrends` querying Google Trends endpoints (`geo="IN"`).
- **Tradeoffs & Fragility**: Fetches search interest scores (0-100). Google frequently rate-limits unauthenticated traffic or issues CAPTCHAs under automated polling.

### 5. RSS News Feeds
- **Feeds**: Moneycontrol Top News, Economic Times Markets, Reuters Business via `feedparser`.
- **Tradeoffs & Fragility**: Feeds are officially intended for public syndication. Low fragility, but articles are limited to titles and summary descriptions. Uses deterministic SHA-256 hashes (`stable_id(link)`) for primary key generation.

---

## Project Structure

```
/diverge_scraper
  ├── __init__.py
  ├── config.py                 # Central config: tickers, synonym regexes, rate limits, retention
  ├── utils.py                  # Shared helpers: match_ticker, to_iso_utc, stable_id, robots.txt
  ├── storage.py                # SQLite storage: single `raw_posts` table with INSERT OR IGNORE
  ├── reddit_noapi_scraper.py   # Reddit public JSON scraper
  ├── stocktwits_noapi_scraper.py # StockTwits public stream scraper
  ├── telegram_noapi_scraper.py # Telegram public HTML preview scraper
  ├── trends_scraper.py         # Google Trends interest scraper (pytrends)
  ├── rss_news_scraper.py       # Financial RSS feeds scraper (feedparser)
  ├── main.py                   # Sequential orchestrator with error handling & text retention purge
  └── tests/
      └── test_scrapers.py      # Comprehensive offline unit tests with mocked HTTP responses
```

---

## Database Schema

All scrapers write into a single SQLite database (`diverge_raw.db`), table `raw_posts`:

| Column | Type | Description |
| :--- | :--- | :--- |
| `post_id` | `TEXT PRIMARY KEY` | Unique deterministic post/comment identifier |
| `account_id` | `TEXT NOT NULL` | Author username or platform channel handle |
| `timestamp_utc` | `TEXT NOT NULL` | Standardized ISO 8601 UTC timestamp |
| `community` | `TEXT` | Subreddit, stream, or channel name |
| `ticker` | `TEXT` | Matched ticker symbol (e.g. `TATASTEEL`) |
| `raw_text` | `TEXT` | Body text / headline description |
| `upvotes` | `INTEGER` | Likes, score, or Google Trends interest score (0-100) |
| `platform` | `TEXT NOT NULL` | Source (`reddit`, `stocktwits`, `telegram`, `google_trends`, `rss_news`) |
| `scraped_at` | `TEXT NOT NULL` | Ingestion timestamp in UTC ISO format |

`insert_many()` executes `INSERT OR IGNORE INTO raw_posts` to guarantee deduplication upon repeated runs.

---

## Running Offline Unit Tests

To verify parsers, storage deduplication, and retention logic without network access:

```bash
python -m unittest discover -s diverge_scraper/tests
```
