# Phase 5 — Composite Aggregation

Collapsed Phase 3 indices + Phase 4 trust into one composite score per (ticker, window).
Rules:
- Normalized Rn via tanh, CASSI to [-1,1], VDI clipped.
- Weighted core: Rn=0.55, CASSI=0.30, VDI=0.15 over available non-null indices.
- CLI and CIRG as modifiers (+/- adjustments on top of core).
- Low-trust dampening: abs(final-50) *= 0.6 for low_trust windows.
- cirg=-2.0 guard: if cirg sentinel detected, composite capped at 35.
Stored in `ticker_window_metrics`. Pure functions in `aggregate_composite.py` — no DB imports.
