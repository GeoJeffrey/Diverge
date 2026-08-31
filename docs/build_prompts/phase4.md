# Phase 4 — Integrity & Coordination Scoring

For each (ticker, window):
1. Computed near-duplicate post ratio via MinHash (0.90 similarity threshold).
2. Computed sentiment variance and baseline normalization.
3. Combined periodicity score + duplicate ratio + inverted sentiment variance into `coordination_score` (0-100).
4. Assigned `confidence_flag`: high_trust / moderate / low_trust / insufficient_data.
Stored in `coordination_scores`. Phase 4 data feeds Phase 5 trust dampening.
