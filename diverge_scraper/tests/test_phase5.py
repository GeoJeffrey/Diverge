"""
test_phase5.py

Unit test suite for Phase 5 Composite Aggregation (aggregate_composite.py).
Tests all 9 required edge cases and mathematical guard assertions.
"""

import json
import math
import unittest

from diverge_scraper.aggregate_composite import aggregate_composite_row


class TestPhase5CompositeAggregation(unittest.TestCase):

    # ── Test 1: All 3 core indices present, high_trust ────────────────
    def test_all_core_indices_present_high_trust(self):
        data = {
            "ticker": "AAPL",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.5,      # Bullish
            "cassi": 0.8,   # Bullish
            "vdi": 1.0,     # Mildly Bullish
            "confidence_flag": "high_trust",
        }
        res = aggregate_composite_row(data)
        self.assertIsNotNone(res["composite_score"])
        self.assertGreater(res["composite_score"], 50.0)
        self.assertEqual(res["dominant_index"], "rn")

    # ── Test 2: Only Rn available (cassi/vdi null) ──────────────────
    def test_only_rn_available_not_diluted(self):
        data_single = {
            "ticker": "TCS",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.5,
            "cassi": None,
            "vdi": None,
            "confidence_flag": "high_trust",
        }
        res = aggregate_composite_row(data_single)
        # rn_norm = tanh(2 * 0.5) = tanh(1.0) = ~0.7616
        expected_raw = 50.0 + 50.0 * math.tanh(1.0)
        self.assertAlmostEqual(res["composite_score"], round(expected_raw, 1), places=1)
        self.assertEqual(res["dominant_index"], "rn")

    # ── Test 3: All 3 core indices null ──────────────────────────────
    def test_all_core_indices_null(self):
        data_null = {
            "ticker": "WIPRO",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": None,
            "cassi": None,
            "vdi": None,
            "confidence_flag": "high_trust",
        }
        res = aggregate_composite_row(data_null)
        self.assertIsNone(res["composite_score"])
        self.assertEqual(res["dominant_index"], "insufficient_data")
        self.assertEqual(json.loads(res["risk_flags"]), [])
        self.assertEqual(res["aggregation_confidence"], "insufficient_data")

    # ── Test 4: High CIRG (2.0) vs cirg=None baseline ────────────────
    def test_high_cirg_hype_outrunning_reality(self):
        base_data = {
            "ticker": "RELIANCE",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.5,
            "cassi": 0.5,
            "vdi": 0.0,
            "cirg": None,
            "confidence_flag": "high_trust",
        }
        res_base = aggregate_composite_row(base_data)

        high_cirg_data = dict(base_data, cirg=2.0)
        res_cirg = aggregate_composite_row(high_cirg_data)

        flags = json.loads(res_cirg["risk_flags"])
        self.assertIn("hype_outrunning_reality", flags)
        self.assertLess(res_cirg["composite_score"], res_base["composite_score"])

    # ── Test 5: Low CIRG (-2.0) informational-only check ────────────
    def test_low_cirg_informational_only(self):
        base_data = {
            "ticker": "HDFCBANK",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.2,
            "cassi": 0.5,
            "vdi": 0.0,
            "cirg": None,
            "confidence_flag": "high_trust",
        }
        res_base = aggregate_composite_row(base_data)

        low_cirg_data = dict(base_data, cirg=-2.0)
        res_low_cirg = aggregate_composite_row(low_cirg_data)

        flags = json.loads(res_low_cirg["risk_flags"])
        self.assertIn("consumer_reality_underpriced", flags)
        # Low CIRG MUST NOT adjust score (informational only)
        self.assertEqual(res_low_cirg["composite_score"], res_base["composite_score"])

    # ── Test 6: High CLI (0.8) vs cli=0.0 ─────────────────────────────
    def test_high_cli_capitulation_signal(self):
        base_data = {
            "ticker": "INFY",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.5,
            "cli": 0.0,
            "confidence_flag": "high_trust",
        }
        res_base = aggregate_composite_row(base_data)

        high_cli_data = dict(base_data, cli=0.8)
        res_cli = aggregate_composite_row(high_cli_data)

        flags = json.loads(res_cli["risk_flags"])
        self.assertIn("capitulation_signal", flags)
        self.assertLess(res_cli["composite_score"], res_base["composite_score"])

    # ── Test 7: Low trust confidence dampening ───────────────────────
    def test_low_trust_confidence_dampening(self):
        data_high = {
            "ticker": "NVDA",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.8,
            "cassi": 0.9,
            "confidence_flag": "high_trust",
        }
        res_high = aggregate_composite_row(data_high)

        data_low = dict(data_high, confidence_flag="low_trust")
        res_low = aggregate_composite_row(data_low)

        # Dampening pulls towards 50 (neutral), not towards 0!
        diff_high = abs(res_high["composite_score"] - 50.0)
        diff_low = abs(res_low["composite_score"] - 50.0)
        self.assertLess(diff_low, diff_high)

    # ── Test 8: Insufficient data guard check ────────────────────────
    def test_insufficient_data_forced_null(self):
        data = {
            "ticker": "TSLA",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": 1.5,
            "cassi": 0.8,
            "vdi": 1.0,
            "confidence_flag": "insufficient_data",
        }
        res = aggregate_composite_row(data)
        self.assertIsNone(res["composite_score"])

    # ── Test 9: Tie-break between rn and cassi ──────────────────────
    def test_tie_break_rn_vs_cassi(self):
        # Construct inputs where w_rn * abs(rn_norm) == w_cassi * abs(cassi_norm)
        # base weights: rn=0.55, cassi=0.30
        # If we set cassi_norm = 0.55 and rn_norm = 0.30:
        # w_rn * abs(rn_norm) = 0.55 * 0.30 = 0.165
        # w_cassi * abs(cassi_norm) = 0.30 * 0.55 = 0.165
        # With equal weighted magnitudes (0.165), tie-breaker chooses 'rn' (base weight 0.55 > 0.30)
        cassi_val = (0.55 + 1.0) / 2.0  # cassi_norm = 0.55
        # rn_norm = 0.30 -> tanh(2 * (rn - 1.0)) = 0.30 -> 2*(rn-1.0) = atanh(0.30)
        rn_val = 1.0 + math.atanh(0.30) / 2.0

        data_tie = {
            "ticker": "SBIN",
            "window_start_utc": "2026-01-01T00:00:00Z",
            "rn": rn_val,
            "cassi": cassi_val,
            "vdi": None,
            "confidence_flag": "high_trust",
        }
        res = aggregate_composite_row(data_tie)
        self.assertEqual(res["dominant_index"], "rn")


if __name__ == "__main__":
    unittest.main()
