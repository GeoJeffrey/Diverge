# Diverge — Financial Narrative Sentiment, Timing & Indices Pipeline

A zero-API, zero-auth financial narrative sentiment data collection, feature extraction, index calculation, and real-time dashboard framework for **Diverge**.

This module gathers financial discussions, news, search trends, and social media commentary mentioning tracked Indian tickers (`TATASTEEL`, `RELIANCE`, `INFY`, `TCS`, `HDFCBANK`), extracts timing, periodicity, and sentiment features, computes 5 raw financial indices, and serves a live multi-tab web dashboard.

---

## 🚀 Quick Start & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Seed 60 Days of Historical Data

To immediately populate 60 days of historical data for comprehensive offline testing of all 5 indices across all tickers and languages:

```bash
python seed_historical_data.py
```

### 3. Execute End-to-End Master Pipeline (Phase 1 + 2 + 3)

Run the full end-to-end data ingestion, feature extraction, and financial indices pipeline in one command:

```bash
python run_all.py
```

To run Phase 2 + Phase 3 feature processing against existing database data without re-scraping live sources:

```bash
python run_all.py --skip-scrape
```

### 4. Run Individual Phase Modules

- **Phase 1 Data Collection**:
  ```bash
  python main.py
  ```
- **Phase 2 Feature Extraction**:
  ```bash
  python run_phase2.py
  ```
- **Phase 3 Financial Indices**:
  ```bash
  python run_phase3.py
  ```

### 5. Launch the Web Dashboard Server

Start the local dashboard server and REST API:

```bash
python server.py [--port 8000]
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to view live stats, platform breakdown, sentiment distribution, and Phase 3 indices.

---

## 📈 Phase 3 Financial Indices Overview

| Index | Name | Formula / Logic | Guard Conditions |
| :--- | :--- | :--- | :--- |
| **CLI** | Capitulation Leak Index | `(posts with capitulation_flag=1) / (total posts)` | Returns `NULL` if window post count = 0 |
| **VDI** | Vernacular Divergence Index | `Z(English sentiment) - Z(Hinglish sentiment)` | Returns `NULL` if <20 posts in either language (Hinglish volume bottleneck) |
| **CASSI** | Cross-Asset Sentiment Spillover | Forecast-error variance decomposition (VAR `.fevd()`) | Returns `NULL` if <30 daily points across <2 tickers |
| **Rn** | Effective Reproduction Number | $\beta / \gamma$ from daily new-onset discussant growth & decay | Returns `NULL` if <7 distinct days of data |
| **CIRG** | Consumer-Investor Rating Gap | `Z(investor sentiment) - Z(consumer review score)` | Returns `NULL` if no review data available for ticker (e.g. B2B / IT) |

---

## 🏗️ Project Structure

```
Diverge/
├── dashboard.html                  # Multi-tab interactive web dashboard (HTML/JS/CSS)
├── server.py                        # HTTP dashboard server & REST API endpoints
├── run_all.py                       # Master orchestrator (Phase 1 -> 2 -> 3)
├── run_phase3.py                    # Phase 3 financial indices orchestrator
├── run_phase2.py                    # Phase 2 feature extraction orchestrator
├── seed_historical_data.py          # 60-day historical data seeder script
├── main.py                          # Phase 1 scraper orchestrator
├── check_distribution.py            # Phase 1 & 2 data distribution verification script
├── diverge_raw.db                   # SQLite database
├── requirements.txt                 # Project python dependencies
├── README.md                        # Documentation
└── diverge_scraper/                 # Core package
    ├── config.py                    # Central configuration
    ├── utils.py                     # Shared helpers
    ├── storage.py                   # SQLite storage layer & schema migrations
    ├── reddit_noapi_scraper.py      # Reddit public JSON scraper
    ├── stocktwits_noapi_scraper.py    # StockTwits public stream scraper
    ├── telegram_noapi_scraper.py    # Telegram public HTML web preview scraper
    ├── trends_scraper.py            # Google Trends scraper (pytrends)
    ├── rss_news_scraper.py          # Financial RSS feed parser
    ├── consumer_reviews_scraper.py  # Consumer reviews rating scraper
    ├── timing_features.py           # Phase 2: Post interval & time-bin aggregator
    ├── periodicity_analysis.py      # Phase 2: KS-test, ACF peak lag, FFT periodicity
    ├── text_features.py             # Phase 2: Sentiment scoring, sarcasm & capitulation flags
    ├── cli_index.py                 # Phase 3: Capitulation Leak Index
    ├── vdi_index.py                 # Phase 3: Vernacular Divergence Index
    ├── cassi_index.py               # Phase 3: Cross-Asset Sentiment Spillover Index
    ├── rn_index.py                  # Phase 3: Effective Reproduction Number Index
    ├── cirg_index.py                # Phase 3: Consumer-Investor Rating Gap Index
    └── tests/
        ├── test_scrapers.py         # Phase 1 offline unit tests
        ├── test_phase2.py           # Phase 2 unit tests
        └── test_phase3.py           # Phase 3 unit tests
```

---

## 📊 Database Schema

All scrapers, feature engines, and index calculators write into a single SQLite database (`diverge_raw.db`):

| Table | Description | Key Fields |
| :--- | :--- | :--- |
| `raw_posts` | Stored raw scraped posts & news items | `post_id`, `ticker`, `platform`, `raw_text`, `upvotes`, `timestamp_utc` |
| `post_timing` | Calculated post time intervals & delays | `post_id`, `delta_seconds`, `is_first_mention` |
| `ticker_time_bins` | Aggregated metrics per time window | `ticker`, `bin_start_utc`, `post_count` |
| `text_features` | Sentiment, capitulation & sarcasm scores | `post_id`, `sentiment_score`, `is_sarcastic`, `capitulation_flag`, `language` |
| `periodicity_stats` | Statistical periodicity & Fourier analysis | `ticker`, `window_start_utc`, `ks_statistic`, `acf_peak_lag_minutes` |
| `consumer_sentiment` | Public consumer brand/app review scores | `id`, `ticker`, `timestamp_utc`, `review_sentiment_score`, `source` |
| `index_values` | Computed raw Phase 3 financial indices | `ticker`, `window_start_utc`, `cli`, `vdi`, `cassi`, `rn`, `cirg` |

---

## 🧪 Running Offline Unit Tests

To run the complete 41-test suite without making external network requests:

```bash
python -m unittest discover -s diverge_scraper/tests
```
