# Phase 3 — Financial Indices

Computed five proprietary indices per (ticker, window), stored in `index_values`:
- **Rn** (Narrative Reproduction Number): viral spread rate via generation-interval model.
- **CIRG** (Consumer-Investor Rating Gap): Z(investor sentiment) - Z(consumer review score).
- **CLI** (Capitulation Language Index): lexicon-weighted capitulation term density.
- **CASSI** (Cross-Asset Sentiment Spillover): VAR-modeled sentiment leakage between tickers.
- **VDI** (Vernacular Divergence Index): retail vs institutional vocabulary shift via KL divergence.
All indices return None when insufficient data — never substituting 0.
