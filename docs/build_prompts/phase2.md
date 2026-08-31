# Phase 2 — Feature Extraction

Extended Phase 1 with three feature extraction tracks:
1. Timing features: inter-arrival deltas, first-mention flags, 5-min ticker_time_bins.
2. Periodicity analysis: KS uniformity test, ACF peak strength, FFT dominant frequency, onset dispersion score — stored in `periodicity_stats`.
3. Text features: FinBERT sentiment (label + score), lexicon-based capitulation detection, sarcasm heuristic, langdetect language — stored in `text_features`.
All tracks run in crash-isolated try/except blocks.
