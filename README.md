# Diverge Financial Narrative Sentiment, Timing, Indices, Integrity & Lineage Pipeline

A zero-API, zero-auth financial narrative sentiment data collection, feature extraction, index calculation, integrity/coordination scoring, composite aggregation, explainability audit trail, and real-time dashboard framework for **Diverge**.

This module gathers financial discussions, news, search trends, and social media commentary mentioning tracked Indian tickers (`TATASTEEL`, `RELIANCE`, `INFY`, `TCS`, `HDFCBANK`), extracts timing, periodicity, and sentiment features, computes 5 raw financial indices, evaluates 5-component integrity/coordination scores per window, aggregates 0-100 composite scores, generates post-level audit reasoning traces and narrative phylogeny lineage trees, and serves a live multi-tab web dashboard.

---

## ðŸš€ Quick Start & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Seed 60 Days of Historical Data

To populate 60 days of historical data for comprehensive offline testing across all 6 phases:

```bash
python seed_historical_data.py
```

### 3. Execute Master Pipeline (Phase 1 -> 2 -> 3 -> 4 -> 5 -> 6)

Run the full end-to-end data ingestion, feature extraction, indices calculation, integrity scoring, composite aggregation, and explainability pipeline in one command:

```bash
python run_all.py
```

To run Phase 2 -> 6 processing against existing database data without re-scraping live sources:

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
- **Phase 5 Composite Aggregation**:
  ```bash
  python run_phase5.py
  ```
- **Phase 6 Explainability & Lineage**:
  ```bash
  python run_phase6.py
  ```

### 5. Launch the Web Dashboard Server

Start the local dashboard server and REST API:

```bash
python server.py [--port 8000]
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to view live stats, platform breakdown, sentiment distribution, Phase 3 indices, Phase 5 composite scores, and Phase 6 narrative lineage & reasoning trace audit logs.

---

## ðŸ” Phase 6 Explainability & Lineage Engine

Phase 6 produces a complete **post-level audit trail** (`reasoning_trace`) and **narrative evolution lineage tree** (`narrative_phylogeny`) for every aggregated metric window:

1. **Reasoning Trace Audit Trail (`reasoning_trace`)**:
   - `rn_onset`: First-mention posts driving reproduction rate onset.
   - `cassi_sentiment`: Top sentiment magnitude posts driving cross-asset VAR.
   - `vdi_divergence`: Top sentiment posts per language (`en` / `hi-en-mixed`).
   - `cli_capitulation`: Posts flagged with capitulation.
   - `duplicate_flag`: MinHash post pairs crossing >90% similarity from `duplicate_pairs`.
   - `sentiment_variance_outlier`: Posts closest to window mean sentiment (unnaturally unanimous).
2. **Narrative Phylogeny Lineage Tree (`narrative_phylogeny`)**:
   - Tracks window-to-window narrative transitions: `composite_reversal`, `dominant_index_shift`, `new_risk_flag`, `flag_resolved`, `stable`.
   - Handles data gaps automatically by linking to the most recent prior valid window.
3. **Phase 7 Data Contracts (`render_prototype.py`)**:
   - `reasoning_trace_panel(ticker, window_start)`: Grouped JSON audit trail items with 140-char text previews.
   - `narrative_phylogeny_tree(ticker)`: Chronological parent-child lineage tree for UI rendering.

---

## ðŸ—ï¸ Project Structure

```
Diverge/
â”œâ”€â”€ dashboard.html                  # Multi-tab interactive web dashboard (HTML/JS/CSS)
â”œâ”€â”€ server.py                        # HTTP dashboard server & REST API endpoints
â”œâ”€â”€ run_all.py                       # Master orchestrator (Phase 1 -> 2 -> 3 -> 4 -> 5 -> 6)
â”œâ”€â”€ run_phase6.py                    # Phase 6 explainability orchestrator
â”œâ”€â”€ run_phase5.py                    # Phase 5 composite aggregation orchestrator
â”œâ”€â”€ run_phase4.py                    # Phase 4 integrity scoring orchestrator
â”œâ”€â”€ run_phase3.py                    # Phase 3 financial indices orchestrator
â”œâ”€â”€ run_phase2.py                    # Phase 2 feature extraction orchestrator
â”œâ”€â”€ seed_historical_data.py          # 60-day historical data seeder script
â”œâ”€â”€ main.py                          # Phase 1 scraper orchestrator
â”œâ”€â”€ check_distribution.py            # Data distribution verification script
â”œâ”€â”€ diverge_raw.db                   # SQLite database
â”œâ”€â”€ requirements.txt                 # Project python dependencies
â”œâ”€â”€ README.md                        # Documentation
â””â”€â”€ src/diverge/                 # Core package
    â”œâ”€â”€ config.py                    # Central configuration
    â”œâ”€â”€ utils.py                     # Shared helpers
    â”œâ”€â”€ storage.py                   # SQLite storage layer & schema migrations
    â”œâ”€â”€ reasoning_trace_builder.py   # Phase 6: Post-level audit trail builder
    â”œâ”€â”€ phylogeny_builder.py         # Phase 6: Narrative evolution lineage builder
    â”œâ”€â”€ render_prototype.py          # Phase 6: Data contract JSON structure builders
    â”œâ”€â”€ aggregate_composite.py       # Phase 5: Composite aggregation engine
    â”œâ”€â”€ duplicate_detection.py       # Phase 4: MinHash near-duplicate post & pairs detection
    â”œâ”€â”€ sentiment_variance.py        # Phase 4: Sentiment variance & baseline normalization
    â”œâ”€â”€ coordination_score.py        # Phase 4: Combined coordination score calculator
    â”œâ”€â”€ reddit_noapi_scraper.py      # Reddit public JSON scraper
    â”œâ”€â”€ stocktwits_noapi_scraper.py    # StockTwits public stream scraper
    â”œâ”€â”€ telegram_noapi_scraper.py    # Telegram public HTML web preview scraper
    â”œâ”€â”€ trends_scraper.py            # Google Trends scraper (pytrends)
    â”œâ”€â”€ rss_news_scraper.py          # Financial RSS feed parser
    â”œâ”€â”€ consumer_reviews_scraper.py  # Consumer reviews rating scraper
    â”œâ”€â”€ timing_features.py           # Phase 2: Post interval & time-bin aggregator
    â”œâ”€â”€ periodicity_analysis.py      # Phase 2: KS-test, ACF peak lag, FFT periodicity
    â”œâ”€â”€ text_features.py             # Phase 2: Sentiment scoring, sarcasm & capitulation flags
    â”œâ”€â”€ cli_index.py                 # Phase 3: Capitulation Leak Index
    â”œâ”€â”€ vdi_index.py                 # Phase 3: Vernacular Divergence Index
    â”œâ”€â”€ cassi_index.py               # Phase 3: Cross-Asset Sentiment Spillover Index
    â”œâ”€â”€ rn_index.py                  # Phase 3: Effective Reproduction Number Index
    â”œâ”€â”€ cirg_index.py                # Phase 3: Consumer-Investor Rating Gap Index
    â””â”€â”€ tests/
        â”œâ”€â”€ test_scrapers.py         # Phase 1 offline unit tests
        â”œâ”€â”€ test_phase2.py           # Phase 2 unit tests
        â”œâ”€â”€ test_phase3.py           # Phase 3 unit tests
        â”œâ”€â”€ test_phase4.py           # Phase 4 unit tests
        â”œâ”€â”€ test_phase5.py           # Phase 5 unit tests
        â””â”€â”€ test_phase6.py           # Phase 6 unit tests
```

---

## ðŸ“Š Database Schema

All scrapers, feature engines, index calculators, integrity scorers, composite aggregators, and explainability builders write into a single SQLite database (`diverge_raw.db`):

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
| `ticker_window_metrics` | Phase 5 Aggregated composite metrics | `ticker`, `window_start_utc`, `composite_score`, `dominant_index`, `risk_flags` |
| `duplicate_pairs` | Phase 4/6 Flagged near-duplicate post pairs | `ticker`, `window_start_utc`, `post_id_a`, `post_id_b`, `similarity` |
| `reasoning_trace` | Phase 6 Post-level audit trail records | `trace_id`, `ticker`, `window_start_utc`, `post_id`, `contributed_to`, `weight` |
| `narrative_phylogeny` | Phase 6 Narrative evolution lineage tree | `ticker`, `window_start_utc`, `parent_window_start_utc`, `mutation_type` |

---

## ðŸ§ª Running Offline Unit Tests

To run the complete 60-test suite without making external network requests:

```bash
python -m unittest discover -s src/diverge/tests
```

