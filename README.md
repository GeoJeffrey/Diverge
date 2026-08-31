# Diverge — Financial Narrative Sentiment, Timing, Indices & Integrity Pipeline

A zero-API, zero-auth financial narrative sentiment data collection, feature extraction, index calculation, integrity/coordination scoring, and real-time dashboard framework for **Diverge**.

This module gathers financial discussions, news, search trends, and social media commentary mentioning tracked Indian tickers (`TATASTEEL`, `RELIANCE`, `INFY`, `TCS`, `HDFCBANK`), extracts timing, periodicity, and sentiment features, computes 5 raw financial indices, evaluates 5-component integrity/coordination scores per window, and serves a live multi-tab web dashboard.

---

## 🚀 Quick Start & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Seed 60 Days of Historical Data

To populate 60 days of historical data for comprehensive offline testing across all 5 indices and integrity scoring:

```bash
python seed_historical_data.py
```

### 3. Execute Master Pipeline (Phase 1 -> 2 -> 3 -> 4)

Run the full end-to-end data ingestion, feature extraction, indices calculation, and integrity scoring pipeline in one command:

```bash
python run_all.py
```

To run Phase 2 + Phase 3 + Phase 4 feature processing against existing database data without re-scraping live sources:

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
- **Phase 4 Integrity & Coordination Scoring**:
  ```bash
  python run_phase4.py
  ```

### 5. Launch the Web Dashboard Server

Start the local dashboard server and REST API:

```bash
python server.py [--port 8000]
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to view live stats, platform breakdown, sentiment distribution, Phase 3 indices, and Phase 4 trust scores.

---

## 🛡️ Phase 4 Integrity & Coordination Scoring

Phase 4 computes a **0-100 combined coordination score** and trust classification per ticker window based on 5 normalized components:

1. **`ks_component`** (from `periodicity_stats.ks_statistic` normalized 0-1)
2. **`acf_component`** (from `periodicity_stats.acf_peak_strength` normalized 0-1)
3. **`onset_component`** (from `periodicity_stats.onset_dispersion_index` normalized 0-1)
4. **`duplicate_ratio`** (MinHash Jaccard pairwise similarity > 90% across different accounts via `datasketch`)
5. **`inverted_sentiment_variance`** (`1.0 - normalized_sentiment_variance`, since suspiciously low variance indicates coordination)

### 📰 News Event Cross-Check (Dampening)
If a legitimate RSS news article or Google Trends event is present in the same window, `onset_component` weight is dampened from `0.20` to `0.05` to prevent false-positive coordination flags on real news reactions (logged explicitly for auditability).

### 🏷️ Trust Classification
- `< 20` posts in window $\rightarrow$ `insufficient_data` (Guard)
- Coordination score $\ge 70$ $\rightarrow$ `low_trust`
- Coordination score $40 - 69$ $\rightarrow$ `moderate`
- Coordination score $< 40$ $\rightarrow$ `high_trust`

---

## 🏗️ Project Structure

```
Diverge/
├── dashboard.html                  # Multi-tab interactive web dashboard (HTML/JS/CSS)
├── server.py                        # HTTP dashboard server & REST API endpoints
├── run_all.py                       # Master orchestrator (Phase 1 -> 2 -> 3 -> 4)
├── run_phase4.py                    # Phase 4 integrity scoring orchestrator
├── run_phase3.py                    # Phase 3 financial indices orchestrator
├── run_phase2.py                    # Phase 2 feature extraction orchestrator
├── seed_historical_data.py          # 60-day historical data seeder script
├── main.py                          # Phase 1 scraper orchestrator
├── check_distribution.py            # Data distribution verification script
├── diverge_raw.db                   # SQLite database
├── requirements.txt                 # Project python dependencies
├── README.md                        # Documentation
└── diverge_scraper/                 # Core package
    ├── config.py                    # Central configuration
    ├── utils.py                     # Shared helpers
    ├── storage.py                   # SQLite storage layer & schema migrations
    ├── duplicate_detection.py       # Phase 4: MinHash near-duplicate post detection
    ├── sentiment_variance.py        # Phase 4: Sentiment variance & baseline normalization
    ├── coordination_score.py        # Phase 4: Combined coordination score calculator
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
        ├── test_phase3.py           # Phase 3 unit tests
        └── test_phase4.py           # Phase 4 unit tests
```

---

## 📊 Database Schema

All scrapers, feature engines, index calculators, and integrity scorers write into a single SQLite database (`diverge_raw.db`):

| Table | Description | Key Fields |
| :--- | :--- | :--- |
| `raw_posts` | Stored raw scraped posts & news items | `post_id`, `ticker`, `platform`, `raw_text`, `upvotes`, `timestamp_utc` |
| `post_timing` | Calculated post time intervals & delays | `post_id`, `delta_seconds`, `is_first_mention` |
| `ticker_time_bins` | Aggregated metrics per time window | `ticker`, `bin_start_utc`, `post_count` |
| `text_features` | Sentiment, capitulation & sarcasm scores | `post_id`, `sentiment_score`, `is_sarcastic`, `capitulation_flag`, `language` |
| `periodicity_stats` | Statistical periodicity & Fourier analysis | `ticker`, `window_start_utc`, `ks_statistic`, `acf_peak_lag_minutes` |
| `consumer_sentiment` | Public consumer brand/app review scores | `id`, `ticker`, `timestamp_utc`, `review_sentiment_score`, `source` |
| `index_values` | Computed raw Phase 3 financial indices | `ticker`, `window_start_utc`, `cli`, `vdi`, `cassi`, `rn`, `cirg` |
| `coordination_scores` | Phase 4 Integrity & trust scores | `ticker`, `window_start_utc`, `coordination_score`, `confidence_flag` |

---

## 🧪 Running Offline Unit Tests

To run the complete 45-test suite without making external network requests:

```bash
python -m unittest discover -s diverge_scraper/tests
```
