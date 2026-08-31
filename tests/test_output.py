"""
test_phase7.py

Unit test suite for Phase 7 Output Modes & Mode API:
  1. Simple Mode view generation, verdict buckets, why_sentence risk flag appends & insufficient_data guard.
  2. Advanced Mode technical diagnostic breakdown, raw null preserving & phylogeny history context.
  3. Mode API status codes (404 for missing vs 200 for null score windows) & payload validation.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from diverge import storage
from diverge.output import advanced_mode, mode_api, simple_mode


class TestPhase7OutputModes(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_diverge.db"
        storage.get_connection(self.db_path)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # â”€â”€ 1. Simple Mode Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def test_simple_mode_buckets_and_sentences(self):
        metrics = [
            # Building window (>= 65) with hype flag
            {
                "ticker": "INFY", "window_start_utc": "2026-01-01T00:00:00Z",
                "composite_score": 72.0, "dominant_index": "rn", "rn": 1.4,
                "risk_flags": json.dumps(["hype_outrunning_reality"]), "confidence_flag": "high_trust",
            },
            # Building window (>= 65) WITHOUT hype flag (same score 72.0)
            {
                "ticker": "INFY", "window_start_utc": "2026-01-01T02:00:00Z",
                "composite_score": 72.0, "dominant_index": "rn", "rn": 1.4,
                "risk_flags": json.dumps([]), "confidence_flag": "high_trust",
            },
            # Fading window (< 35)
            {
                "ticker": "INFY", "window_start_utc": "2026-01-01T04:00:00Z",
                "composite_score": 25.0, "dominant_index": "cassi", "cassi": 0.2,
                "risk_flags": json.dumps([]), "confidence_flag": "moderate",
            },
            # Insufficient Data window (composite_score = None)
            {
                "ticker": "INFY", "window_start_utc": "2026-01-01T06:00:00Z",
                "composite_score": None, "dominant_index": "insufficient_data",
                "risk_flags": json.dumps([]), "confidence_flag": "insufficient_data",
            },
        ]
        storage.insert_ticker_window_metrics(metrics, db_path=self.db_path)

        # 1. Building + Hype flag
        view1 = simple_mode.get_simple_view("INFY", "2026-01-01T00:00:00Z", db_path=self.db_path)
        self.assertEqual(view1["verdict_label"], "building")
        self.assertIn("hype currently outrunning consumer reality", view1["why_sentence"])

        # 2. Building WITHOUT flag -> why_sentence MUST differ!
        view2 = simple_mode.get_simple_view("INFY", "2026-01-01T02:00:00Z", db_path=self.db_path)
        self.assertEqual(view2["verdict_label"], "building")
        self.assertNotIn("hype currently outrunning consumer reality", view2["why_sentence"])
        self.assertNotEqual(view1["why_sentence"], view2["why_sentence"])

        # 3. Fading
        view3 = simple_mode.get_simple_view("INFY", "2026-01-01T04:00:00Z", db_path=self.db_path)
        self.assertEqual(view3["verdict_label"], "fading")

        # 4. Insufficient Data Guard
        view4 = simple_mode.get_simple_view("INFY", "2026-01-01T06:00:00Z", db_path=self.db_path)
        self.assertIsNone(view4["score"])
        self.assertEqual(view4["verdict_label"], "insufficient_data")
        self.assertEqual(view4["why_sentence"], "Not enough data yet for a reliable reading.")

    # â”€â”€ 2. Advanced Mode Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def test_advanced_mode_raw_preservation(self):
        metrics = [{
            "ticker": "TCS", "window_start_utc": "2026-01-01T00:00:00Z",
            "composite_score": 85.0, "dominant_index": "rn", "rn": 1.5,
            "cirg": None, "cli": 0.12, "cassi": None, "vdi": None,
            "coordination_score": 92.5, "confidence_flag": "high_trust",
            "risk_flags": json.dumps([]), "aggregation_confidence": "high_trust",
        }]
        storage.insert_ticker_window_metrics(metrics, db_path=self.db_path)

        adv = advanced_mode.get_advanced_view("TCS", "2026-01-01T00:00:00Z", db_path=self.db_path)
        self.assertIsNotNone(adv)
        self.assertEqual(adv["indices"]["rn"], 1.5)
        # Assert null indices are preserved as None, not omitted, not zeroed
        self.assertIn("cassi", adv["indices"])
        self.assertIsNone(adv["indices"]["cassi"])
        self.assertIsNone(adv["indices"]["cirg"])
        self.assertEqual(adv["indices"]["cli"], 0.12)

    # â”€â”€ 3. Mode API Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def test_mode_api_status_codes(self):
        metrics = [
            {"ticker": "AAPL", "window_start_utc": "2026-01-01T00:00:00Z", "composite_score": 88.0, "dominant_index": "rn", "risk_flags": "[]"},
            {"ticker": "AAPL", "window_start_utc": "2026-01-01T02:00:00Z", "composite_score": None, "dominant_index": "insufficient_data", "risk_flags": "[]"},
        ]
        storage.insert_ticker_window_metrics(metrics, db_path=self.db_path)

        # 1. Known populated row -> 200 OK
        status_s, data_s = mode_api.handle_get_simple("AAPL", "2026-01-01T00:00:00Z", db_path=self.db_path)
        self.assertEqual(status_s, 200)
        self.assertEqual(data_s["score"], 88.0)

        # 2. Known null score window -> 200 OK with insufficient_data payload (NOT 404!)
        status_null, data_null = mode_api.handle_get_simple("AAPL", "2026-01-01T02:00:00Z", db_path=self.db_path)
        self.assertEqual(status_null, 200)
        self.assertEqual(data_null["verdict_label"], "insufficient_data")

        # 3. Missing window -> 404 Not Found
        status_404, data_404 = mode_api.handle_get_simple("AAPL", "2099-01-01T00:00:00Z", db_path=self.db_path)
        self.assertEqual(status_404, 404)
        self.assertIn("error", data_404)

        # 4. GET /api/tickers -> returns distinct populated tickers
        status_t, data_t = mode_api.handle_get_tickers(db_path=self.db_path)
        self.assertEqual(status_t, 200)
        self.assertTrue(any(item["ticker"] == "AAPL" for item in data_t["tickers"]))


if __name__ == "__main__":
    unittest.main()

