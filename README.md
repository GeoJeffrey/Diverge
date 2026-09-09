# Diverge — Financial Narrative Sentiment, Timing, Indices, Integrity & Lineage Pipeline

A zero-API, zero-auth financial narrative sentiment intelligence system, feature extraction pipeline, index calculation engine, integrity/coordination scorer, composite aggregator, explainability audit trail, and real-time dual-mode dashboard framework.

Diverge monitors public social commentary, search trends, consumer app reviews, and market news across 16 major Indian and global equities (`TATASTEEL`, `RELIANCE`, `INFY`, `TCS`, `HDFCBANK`, `ICICIBANK`, `SBIN`, `BHARTIARTL`, `ITC`, `LT`, `WIPRO`, `AAPL`, `TSLA`, `NVDA`, `MSFT`, `AMZN`). It extracts temporal and NLP features, evaluates 5 distinct financial indices, benchmarks coordinated inorganic activity, collapses metrics into calibrated 0–100 composite confidence scores, and produces full post-level explainability traces with narrative evolution phylogeny trees.

---

## 🚀 Quick Start & Usage

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/GeoJeffrey/Diverge.git
cd Diverge
pip install -r requirements.txt
pip install -e .
```

### 2. Run the Full End-to-End Pipeline

Execute the master pipeline across all phases (Phase 1 Ingestion → Phase 2 Features → Phase 3 Indices → Phase 4 Integrity → Phase 5 Composite → Phase 6 Explainability):

```bash
python run_all.py
```

To run Phases 2 through 6 against existing live database records without re-scraping:

```bash
python run_all.py --skip-scrape
```

### 3. Launch Web Dashboard & REST API

Start the dashboard server:

```bash
python run_server.py [--port 8000]
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser:
- **Simple Mode**: Intuitive consumer-friendly cards, sentiment dial, dominant narrative driver, and qualitative risk indicators.
- **Advanced Mode**: Full audit view including 5-metric radar/table breakdown, coordination trust dampening, post-level reasoning traces, and narrative phylogeny tree.
- **REST APIs**: `/api/stats`, `/api/tickers`, `/api/simple`, `/api/advanced`, `/api/reasoning-trace`, `/api/phylogeny`.

---

## 🏗️ Architecture & Pipeline Phases

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           1. Ingestion Layer                              │
│   StockTwits  │  Reddit  │  Telegram  │  Google Trends  │  RSS Feeds     │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     2. Feature Extraction & NLP Track                     │
│  FinBERT Sentiment  │  Sarcasm Heuristic  │  Capitulation Continuous Signal │
│  Conviction/Hedge Ratio  │  FFT & Periodicity  │  MinHash Deduplication   │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        3. Financial Indices Engine                        │
│   • CLI   (Capitulation Leak Index)                                       │
│   • VDI   (Vernacular Divergence Index - Multilingual & Cross-Platform)    │
│   • CASSI (Cross-Asset Sentiment Spillover Index - VAR & Correlation)     │
│   • Rn    (Narrative Reproduction Number - Epidemic Viral Transmission)   │
│   • CIRG  (Consumer-Investor Rating Gap)                                  │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      4. Integrity & Coordination Scorer                   │
│   Periodicity KS-Stat  │  ACF Peak Strength  │  Duplicate Density Ratio   │
│   Sentiment Variance   │  News Reaction Dampening (High / Mod / Low Trust)│
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       5. Composite Aggregation Engine                     │
│   Normalized Core Weighted Combination  │  CIRG / CLI Asymmetric Modifiers │
│   Confidence Dampening (0–100 Score)    │  Dominant Index Identification  │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     6. Explainability & Lineage Audit                     │
│   Post-Level Reasoning Traces  │  Parent-Child Narrative Phylogeny Tree   │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       7. Output & Interactive Server                      │
│   Simple Mode UI  │  Advanced Diagnostics Mode  │  Fast REST Endpoints    │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Phase 3 Financial Indices Explained

1. **CLI (Capitulation Leak Index)**:
   Measures retail despair, liquidations, and stop-loss panic. Utilizes expanded capitulation phrase lexicons coupled with continuous soft confidence scoring and negative sentiment density to ensure sensitive, continuous tracking without artificial zero floors.

2. **VDI (Vernacular Divergence Index)**:
   Measures divergence in sentiment between language groups (e.g. English vs. Hinglish/Devanagari). Incorporates cross-platform vernacular divergence (retail social streams vs. institutional news feeds) as a robust proxy when bilingual post volumes are asymmetric.

3. **CASSI (Cross-Asset Sentiment Spillover Index)**:
   Measures how sentiment shocks in one asset propagate to other equities via Vector Autoregression (VAR) forecast-error variance decomposition, backed by pairwise cross-correlation spillover fallbacks.

4. **Rn (Narrative Reproduction Number)**:
   Epidemiological viral transmission modeling of narrative spread ($R_n = \beta / \gamma$). Tracks daily new first-mention posters against active decay curves across tiered sample windows.

5. **CIRG (Consumer-Investor Rating Gap)**:
   Quantifies the delta between retail/institutional investor sentiment and real-world consumer product/app ratings (`Z_investor - Z_consumer`), highlighting overhyped assets or underpriced consumer value.

---

## 🛡️ 100% Live Data Guarantee & Data Integrity

Diverge operates strictly on **verified live data**:
- **Zero synthetic/seeded posts**: All fake historical post generators have been permanently excised.
- **Database maintenance**: Use `python scripts/purge_seeded_data.py` to audit or purge any residual seed patterns.
- **Zero NULL / 0 Guarantees**: Robust statistical fallbacks ensure that sparse ticker windows still produce meaningful scores without crashing or generating uninformative NULL metrics.

---

## 📁 Repository Structure

```
Diverge/
├── dashboard.html             # Interactive web dashboard (Simple & Advanced modes)
├── server.py                  # HTTP server & REST API implementation
├── run_server.py              # Server launcher script
├── run_all.py                 # Master orchestrator (Phases 1–6)
├── pyproject.toml             # Python package configuration
├── requirements.txt           # Package dependencies
├── README.md                  # Project documentation
├── scripts/                   # Operator utilities & audit tools
│   ├── check_counts.py        # Database table row-count inspector
│   ├── check_distribution.py  # Platform & feature distribution validator
│   ├── daily_volume_report.py # 24-hour ingestion volume summary
│   ├── purge_seeded_data.py   # Database maintenance & seed-purging utility
│   ├── validate_endpoints.py  # End-to-end REST API health checker
│   └── view_data.py           # CLI browser for raw ingested posts
├── src/diverge/               # Core Diverge Python package
│   ├── config.py              # Configuration constants & ticker universe
│   ├── storage.py             # SQLite schema, queries, and connection handling
│   ├── utils.py               # Time parsing (ISO/RFC), deduplication & hashing
│   ├── scrapers/              # Phase 1: Public zero-API ingestion scrapers
│   ├── features/              # Phase 2: NLP sentiment, timing & periodicity
│   ├── indices/               # Phase 3: CLI, VDI, CASSI, Rn, CIRG engines
│   ├── integrity/             # Phase 4: Coordination scoring & trust flags
│   ├── aggregation/           # Phase 5: Composite 0–100 score engine
│   ├── explainability/        # Phase 6: Post-level traces & phylogeny tree
│   └── output/                # Phase 7: Dual-mode payload generation
└── tests/                     # Test suite (63 unit tests across all phases)
```

---

## 🧪 Testing

Run the full offline test suite across all feature extractors, index calculators, aggregation rules, and output payloads:

```bash
pytest tests/ -v
```
