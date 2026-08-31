# Diverge — Architecture Reference

> **One-page onboarding.** Everything a new contributor needs to understand the system before reading code.

## What is Diverge?

Diverge is a seven-phase narrative sentiment analysis pipeline for financial markets.
It detects when retail investor language around a stock diverges from fundamentals —
using proprietary indices that measure virality, capitulation, vocabulary drift,
cross-asset spillover, and consumer-investor rating gaps.

---

## The 7-Phase Pipeline

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7
Scraping   Features   Indices    Integrity   Composite  Explain    Output
```

| Phase | Package | What it does |
|---|---|---|
| **1** | `scrapers/` | Collects raw posts from Reddit, StockTwits, Telegram, RSS, Google Trends, consumer reviews |
| **2** | `features/` | Extracts timing features, periodicity stats, and FinBERT text features per post |
| **3** | `indices/` | Computes five proprietary financial narrative indices per (ticker, window) |
| **4** | `integrity/` | Detects duplicate bursts, measures sentiment variance, assigns coordination trust scores |
| **5** | `aggregation/` | Collapses Phase 3 indices + Phase 4 trust into one composite score per (ticker, window) |
| **6** | `explainability/` | Generates per-post reasoning traces, duplicate pairs, and window-to-window narrative phylogeny |
| **7** | `output/` | Exposes Simple Mode cards and Advanced Mode diagnostics via REST API |

---

## Proprietary Indices (Phase 3)

| Index | File | Measures |
|---|---|---|
| **Rn** — Narrative Reproduction Number | `narrative_reproduction.py` | Viral spread rate of a narrative across platforms |
| **CIRG** — Consumer-Investor Rating Gap | `reality_gap.py` | Gap between investor sentiment and consumer review tone |
| **CLI** — Capitulation Language Index | `capitulation_language.py` | Concentration of surrender/panic language in posts |
| **CASSI** — Cross-Asset Sentiment Spillover | `cross_asset_spillover.py` | VAR-modeled sentiment leakage between tickers |
| **VDI** — Vernacular Divergence Index | `vernacular_divergence.py` | Shift from retail to institutional vocabulary |

---

## Database Schema (12 Tables)

```
raw_posts              Phase 1 — raw scraped posts (post_id PK)
post_timing            Phase 2 — inter-arrival deltas, first_mention flags
ticker_time_bins       Phase 2 — 5-min binned volume per ticker
text_features          Phase 2 — sentiment label/score, capitulation, sarcasm, language
periodicity_stats      Phase 2 — KS test, ACF peak, FFT, onset dispersion per window
consumer_sentiment     Phase 3 — scraped consumer review scores (feeds CIRG)
index_values           Phase 3 — Rn, CIRG, CLI, CASSI, VDI per (ticker, window)
coordination_scores    Phase 4 — duplicate ratio, sentiment variance, trust flag
ticker_window_metrics  Phase 5 — composite_score, dominant_index, risk_flags
duplicate_pairs        Phase 6 — near-duplicate post pairs (MinHash 0.90 threshold)
reasoning_trace        Phase 6 — per-post audit trail (post_id, contributed_to, weight)
narrative_phylogeny    Phase 6 — window-to-window dominant narrative evolution
```

---

## Running the Pipeline

```bash
# Install package (editable mode)
pip install -e .

# Run all 6 data phases end-to-end
python run_all.py

# Skip scraping, recompute Phases 2-6 on existing data
python run_all.py --skip-scrape

# Start Phase 7 API server (port 8000)
python run_server.py
```

Then open:
- **Simple Mode:** http://localhost:8000/ui/simple.html
- **Advanced Mode:** http://localhost:8000/ui/advanced.html?ticker=INFY&window=...
- **Dashboard:** http://localhost:8000/dashboard.html

---

## API Endpoints (Phase 7)

| Method | Path | Description |
|---|---|---|
| GET | `/api/tickers` | All tickers with at least one non-null composite score |
| GET | `/api/simple?ticker=X&window=Y` | Simple Mode view for one (ticker, window) |
| GET | `/api/advanced?ticker=X&window=Y` | Advanced Mode diagnostics for one (ticker, window) |
| GET | `/api/phylogeny?ticker=X` | Full narrative phylogeny history for a ticker |
