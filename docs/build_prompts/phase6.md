# Phase 6 — Explainability

Produced three explainability artifacts for each populated window:
1. **duplicate_pairs**: MinHash near-duplicate pairs with similarity score.
2. **reasoning_trace**: per-post audit trail — which posts drove which index metric and how strongly.
3. **narrative_phylogeny**: window-to-window dominant narrative evolution with mutation_type classification
   (stable / composite_reversal / dominant_index_shift / sentiment_regime_change).
Added `reasoning_trace_panel()` and `narrative_phylogeny_tree()` JSON renderers in `render_prototype.py`.
