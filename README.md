# Diverge — Financial Narrative Sentiment & Timing Pipeline

A zero-API, zero-auth financial narrative sentiment data collection, feature extraction, and real-time dashboard framework for **Diverge**.

This module gathers financial discussions, news, search trends, and social media commentary mentioning tracked Indian tickers (`TATASTEEL`, `RELIANCE`, `INFY`, `TCS`, `HDFCBANK`), extracts timing, periodicity, and sentiment features, and serves a live multi-tab web dashboard.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Data Collection (Phase 1)

Scrape public data across Reddit, StockTwits, Telegram channels, Google Trends, and RSS news feeds into `diverge_raw.db`:

```bash
python main.py
# OR
python -m diverge_scraper.main
```

### 3. Run Feature Extraction (Phase 2)

Extract posting frequency metrics, time-bin aggregated sentiment, periodicity statistics (KS-test, ACF peak lag, Fourier dominant frequencies), capitulation flags, sarcasm detection, and sentiment distributions:

```bash
python run_phase2.py
```

### 4. Launch the Web Dashboard

Start the local dashboard server and REST API:

```bash
python server.py [--port 8000]
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to view live stats, platform breakdown, sentiment distribution, and trigger pipeline executions on-demand.

---

## 🏗️ Project Architecture & Structure

```
Diverge/
├── dashboard.html                  # Multi-tab interactive web dashboard (HTML/JS/CSS)
├── server.py                        # HTTP dashboard server & REST API endpoints
├── run_phase2.py                    # Phase 2 pipeline orchestrator
├── main.py                          # Phase 1 scraper orchestrator
├── check_distribution.py            # Data distribution diagnostics script
├── view_data.py                     # Database preview utility script
├── diverge_raw.db                   # SQLite database (auto-generated)
├── requirements.txt                 # Project python dependencies
├── README.md                        # Documentation
└── diverge_scraper/                 # Core package
    ├── __init__.py
    ├── config.py                    # Central configuration (tickers, regex, retention limits)
    ├── utils.py                     # Helpers (ticker matching, UTC conversion, stable SHA-256 IDs)
    ├── storage.py                   # SQLite storage layer & schema migrations
    ├── reddit_noapi_scraper.py      # Reddit public JSON scraper
    ├── stocktwits_noapi_scraper.py    # StockTwits public stream scraper
    ├── telegram_noapi_scraper.py    # Telegram public HTML web preview scraper
    ├── trends_scraper.py            # Google Trends scraper (pytrends)
    ├── rss_news_scraper.py          # Financial RSS feed parser (feedparser)
    ├── timing_features.py           # Phase 2: Post interval & time-bin aggregator
    ├── periodicity_analysis.py      # Phase 2: KS-test, ACF peak lag, FFT periodicity
    ├── text_features.py             # Phase 2: Sentiment scoring, sarcasm & capitulation flags
    └── tests/
        ├── test_scrapers.py         # Phase 1 offline unit tests (mocked HTTP)
        └── test_phase2.py           # Phase 2 feature extraction unit tests
```

---

## 🛡️ Zero-Config & "No API" Principles

- **No Official API Keys / Credentials**: No API keys, OAuth credentials, or SDK dependencies (`praw`, `telethon`, `tweepy`) are required.
- **Raw Web Ingestion**: Uses standard HTTP requests, public JSON endpoints, RSS XML feeds, and HTML web previews.
- **Auto Database Initialization**: SQLite schema and tables are automatically initialized upon execution.

---

## 📊 Database Schema

All scrapers and feature engines write into a single SQLite database (`diverge_raw.db`):

| Table | Description | Key Fields |
| :--- | :--- | :--- |
| `raw_posts` | Stored raw scraped posts & news items | `post_id`, `ticker`, `platform`, `raw_text`, `upvotes`, `timestamp_utc` |
| `post_timing` | Calculated post time intervals & delays | `post_id`, `time_since_prev_sec`, `time_to_next_sec`, `is_burst_start` |
| `ticker_time_bins` | Aggregated metrics per time window | `ticker`, `bin_start_utc`, `post_count`, `avg_sentiment` |
| `text_features` | Sentiment, capitulation & sarcasm scores | `post_id`, `sentiment_score`, `sentiment_label`, `is_sarcastic`, `capitulation_flag` |
| `periodicity_stats` | Statistical periodicity & Fourier analysis | `ticker`, `ks_statistic`, `acf_peak_lag_minutes`, `onset_dispersion_index` |

---

## 🧪 Running Offline Unit Tests

To run the complete test suite without making external network requests:

```bash
python -m unittest discover -s diverge_scraper/tests
```

---

## 🌐 Server REST API Endpoints

- `GET /` or `/dashboard.html` — Serves the interactive web dashboard.
- `GET /api/stats` — Summary counts, platform distribution, and Phase 2 statistics.
- `GET /api/posts` — Filterable raw posts with pagination (`?ticker=...&platform=...&limit=50`).
- `GET /api/text-features` — Sentiment distribution, sarcasm flags, and capitulation indicators.
- `GET /api/periodicity` — Statistical analysis & periodicity metrics.
- `POST /api/run-scraper` — Triggers full Phase 1 scraping pipeline on-demand.
- `POST /api/run-phase2` — Triggers Phase 2 feature extraction pipeline on-demand.
