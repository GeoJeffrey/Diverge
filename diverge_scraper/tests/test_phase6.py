"""
test_phase6.py

Unit test suite for Phase 6 Explainability & Narrative Lineage Engine:
  1. Duplicate Pairs recording in duplicate_detection.py
  2. Reasoning Trace Builder & empty-source guard
  3. Narrative Phylogeny Builder (5 mutation types & gap-window skipping)
  4. Render Prototype JSON contracts
"""

import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from diverge_scraper import duplicate_detection, phylogeny_builder, reasoning_trace_builder, render_prototype, storage


class TestPhase6Explainability(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_diverge.db"
        storage.get_connection(self.db_path)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # ── 1. Duplicate Pairs Storage Test ─────────────────────────
    def test_duplicate_pairs_storage(self):
        posts = [
            {"post_id": "p1", "account_id": "user_a", "raw_text": "TATASTEEL target is 200 buy now breakout rocket"},
            {"post_id": "p2", "account_id": "user_b", "raw_text": "TATASTEEL target is 200 buy now breakout rocket moon"},
            {"post_id": "p3", "account_id": "user_c", "raw_text": "Quarterly financial results show steel demand growth"},
        ]
        ratio = duplicate_detection.compute_duplicate_ratio(
            posts,
            similarity_threshold=0.80,
            ticker="TATASTEEL",
            window_start_utc="2026-01-01T00:00:00Z",
            db_path=self.db_path,
        )
        pairs = storage.get_duplicate_pairs_for_window("TATASTEEL", "2026-01-01T00:00:00Z", db_path=self.db_path)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["post_id_a"], "p1")
        self.assertEqual(pairs[0]["post_id_b"], "p2")

    # ── 2. Reasoning Trace Builder & Empty Guard Test ───────────
    def test_reasoning_trace_builder_rn_onset(self):
        # Insert raw post and timing row
        raw = [{
            "post_id": "post_onset_1",
            "account_id": "user_x",
            "timestamp_utc": "2026-01-01T00:05:00Z",
            "community": "wallstreetbets",
            "ticker": "AAPL",
            "raw_text": "AAPL first mention breakout onset",
            "upvotes": 10,
            "platform": "reddit",
        }]
        storage.insert_many(raw, db_path=self.db_path)
        storage.insert_timing_features([{
            "post_id": "post_onset_1",
            "ticker": "AAPL",
            "timestamp_utc": "2026-01-01T00:05:00Z",
            "delta_seconds": 60.0,
            "is_first_mention": 1,
            "computed_at": "2026-01-01T00:05:00Z",
        }], db_path=self.db_path)

        metric_row = {
            "ticker": "AAPL",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "window_end_utc": "2026-01-01T02:00:00Z",
            "dominant_index": "rn",
            "risk_flags": json.dumps([]),
            "confidence_flag": "high_trust",
        }
        traces = reasoning_trace_builder.build_traces_for_window(metric_row, db_path=self.db_path)
        self.assertTrue(any(t["post_id"] == "post_onset_1" and t["contributed_to"] == "rn_onset" for t in traces))

    def test_reasoning_trace_empty_source_guard(self):
        # Low trust window with no duplicate_pairs rows in DB -> must not crash
        metric_row = {
            "ticker": "NVDA",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "window_end_utc": "2026-01-01T02:00:00Z",
            "dominant_index": "rn",
            "risk_flags": json.dumps([]),
            "confidence_flag": "low_trust",
        }
        traces = reasoning_trace_builder.build_traces_for_window(metric_row, db_path=self.db_path)
        # Should complete gracefully without raising
        self.assertIsInstance(traces, list)

    # ── 3. Narrative Phylogeny Builder Test ─────────────────────
    def test_phylogeny_builder_5_mutations_and_gap(self):
        # Construct synthetic 5-window sequence covering all 5 mutation_types and gap skipping
        metrics = [
            # Root window
            {"ticker": "TSLA", "window_start_utc": "2026-01-01T00:00:00Z", "composite_score": 60.0, "dominant_index": "rn", "risk_flags": "[]"},
            # Window 2: dominant_index_shift (rn -> cassi)
            {"ticker": "TSLA", "window_start_utc": "2026-01-01T02:00:00Z", "composite_score": 65.0, "dominant_index": "cassi", "risk_flags": "[]"},
            # Window 3: GAP window (composite_score = None / insufficient_data) -> MUST BE SKIPPED
            {"ticker": "TSLA", "window_start_utc": "2026-01-01T04:00:00Z", "composite_score": None, "dominant_index": "insufficient_data", "risk_flags": "[]"},
            # Window 4: new_risk_flag (adds capitulation_signal)
            {"ticker": "TSLA", "window_start_utc": "2026-01-01T06:00:00Z", "composite_score": 55.0, "dominant_index": "cassi", "risk_flags": '["capitulation_signal"]'},
            # Window 5: flag_resolved (removes capitulation_signal)
            {"ticker": "TSLA", "window_start_utc": "2026-01-01T08:00:00Z", "composite_score": 52.0, "dominant_index": "cassi", "risk_flags": "[]"},
            # Window 6: composite_reversal (crosses 50: 52.0 -> 42.0)
            {"ticker": "TSLA", "window_start_utc": "2026-01-01T10:00:00Z", "composite_score": 42.0, "dominant_index": "cassi", "risk_flags": "[]"},
        ]
        storage.insert_ticker_window_metrics(metrics, db_path=self.db_path)

        phylo = phylogeny_builder.build_phylogeny_for_ticker("TSLA", db_path=self.db_path)
        self.assertEqual(len(phylo), 5)  # 5 valid non-null windows

        # Check gap skipping: Window 4 parent should link directly to Window 2 (2026-01-01T02:00:00Z)
        w4 = next(p for p in phylo if p["window_start_utc"] == "2026-01-01T06:00:00Z")
        self.assertEqual(w4["parent_window_start_utc"], "2026-01-01T02:00:00Z")
        self.assertEqual(w4["mutation_type"], "new_risk_flag")

        # Check reversal
        w6 = next(p for p in phylo if p["window_start_utc"] == "2026-01-01T10:00:00Z")
        self.assertEqual(w6["mutation_type"], "composite_reversal")

    # ── 4. Render Prototype Test ────────────────────────────────
    def test_render_prototype_contracts(self):
        panel = render_prototype.reasoning_trace_panel("AAPL", "2026-01-01T00:00:00Z", db_path=self.db_path)
        self.assertIn("categories", panel)
        self.assertEqual(panel["ticker"], "AAPL")

        tree = render_prototype.narrative_phylogeny_tree("AAPL", db_path=self.db_path)
        self.assertIn("nodes", tree)
        self.assertEqual(tree["ticker"], "AAPL")


if __name__ == "__main__":
    unittest.main()
