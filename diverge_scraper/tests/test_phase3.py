"""
test_phase3.py

Comprehensive unit tests for Phase 3 financial indices:
  1. CLI (Capitulation Leak Index)
  2. VDI (Vernacular Divergence Index)
  3. CASSI (Cross-Asset Sentiment Spillover Index)
  4. Rn (Effective Reproduction Number Index)
  5. CIRG (Consumer-Investor Rating Gap Index)
"""

import unittest
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from diverge_scraper import cassi_index, cirg_index, cli_index, consumer_reviews_scraper, rn_index, vdi_index


class TestPhase3Indices(unittest.TestCase):

    # ── 1. CLI Index Tests ────────────────────────────────────
    def test_cli_calculation(self):
        # 3 out of 10 posts have capitulation_flag = 1 -> ratio should be 0.30
        posts = [{"capitulation_flag": 1 if i < 3 else 0} for i in range(10)]
        cli_val = cli_index.compute_cli_for_posts(posts)
        self.assertEqual(cli_val, 0.3)

    def test_cli_null_guard_on_empty(self):
        cli_val = cli_index.compute_cli_for_posts([])
        self.assertIsNone(cli_val)

    # ── 2. VDI Index Tests ────────────────────────────────────
    def test_vdi_zscore_math_and_null_guard(self):
        # Enforce <20 posts guard
        small_en = [0.5] * 10
        small_hinglish = [0.2] * 10
        self.assertIsNone(vdi_index.compute_vdi_from_scores(small_en, small_hinglish))

        # Valid count >= 20
        en_scores = [0.8] * 25
        hinglish_scores = [0.2] * 25
        # Set distinct baselines
        en_baseline = (0.5, 0.1)
        hinglish_baseline = (0.5, 0.1)
        vdi_val = vdi_index.compute_vdi_from_scores(
            en_scores, hinglish_scores, en_baseline=en_baseline, hinglish_baseline=hinglish_baseline
        )
        self.assertIsNotNone(vdi_val)
        # Z_en = (0.8 - 0.5)/0.1 = 3.0, Z_hi = (0.2 - 0.5)/0.1 = -3.0 -> VDI = 6.0
        self.assertAlmostEqual(vdi_val, 6.0, places=2)

    # ── 3. CASSI Index Tests ──────────────────────────────────
    def test_cassi_cross_attribution(self):
        # Generate 40 days of synthetic data
        np.random.seed(42)
        dates = pd.date_range("2026-01-01", periods=40, freq="D")

        # Ticker B is random noise
        ticker_b = np.random.normal(0.0, 1.0, size=40)
        # Ticker A is a lagged copy of Ticker B + small noise (high spillover / cross-attribution)
        ticker_a = np.zeros(40)
        ticker_a[1:] = 0.8 * ticker_b[:-1] + np.random.normal(0.0, 0.1, size=39)

        df_coupled = pd.DataFrame({"TICKER_A": ticker_a, "TICKER_B": ticker_b}, index=dates)
        res_coupled = cassi_index.compute_cassi_from_dataframe(df_coupled)

        # Independent series
        df_indep = pd.DataFrame(
            {"TICKER_X": np.random.normal(0, 1, 40), "TICKER_Y": np.random.normal(0, 1, 40)}, index=dates
        )
        res_indep = cassi_index.compute_cassi_from_dataframe(df_indep)

        self.assertIsNotNone(res_coupled.get("TICKER_A"))
        self.assertIsNotNone(res_indep.get("TICKER_X"))
        # Coupled ticker A should show positive cross-attribution (> 0.10)
        self.assertGreater(res_coupled["TICKER_A"], 0.10)

    def test_cassi_guard_insufficient_points(self):
        dates = pd.date_range("2026-01-01", periods=10, freq="D")
        df_small = pd.DataFrame({"A": np.random.normal(0, 1, 10), "B": np.random.normal(0, 1, 10)}, index=dates)
        res = cassi_index.compute_cassi_from_dataframe(df_small)
        self.assertIsNone(res.get("A"))

    # ── 4. Rn Index Tests ─────────────────────────────────────
    def test_rn_accelerating_vs_decelerating(self):
        # Accelerating onset series (1, 2, 4, 8, 16, 32, 64) -> Rn > 1.0
        acc_onsets = [1, 2, 4, 8, 16, 32, 64]
        rn_acc, conf_acc = rn_index.compute_rn_from_onset_counts(acc_onsets)
        self.assertIsNotNone(rn_acc)
        self.assertGreater(rn_acc, 1.0)

        # Decelerating onset series (64, 32, 16, 8, 4, 2, 1) -> Rn < 1.0
        dec_onsets = [64, 32, 16, 8, 4, 2, 1]
        rn_dec, conf_dec = rn_index.compute_rn_from_onset_counts(dec_onsets)
        self.assertIsNotNone(rn_dec)
        self.assertLess(rn_dec, 1.0)

    def test_rn_guard_insufficient_days(self):
        short_onsets = [5, 10, 15]  # < 7 days
        rn_val, conf = rn_index.compute_rn_from_onset_counts(short_onsets)
        self.assertIsNone(rn_val)
        self.assertEqual(conf, 0.0)

    # ── 5. CIRG Index Tests ───────────────────────────────────
    def test_cirg_zscore_math_and_null_guard(self):
        # Guard: missing consumer review data returns None
        inv_scores = [0.8, 0.7, 0.9]
        self.assertIsNone(cirg_index.compute_cirg_from_scores(inv_scores, []))

        # Valid review data
        rev_scores = [0.2, 0.3, 0.1]
        cirg_val = cirg_index.compute_cirg_from_scores(
            inv_scores, rev_scores, investor_baseline=(0.5, 0.1), review_baseline=(0.5, 0.1)
        )
        self.assertIsNotNone(cirg_val)
        # Z_inv = (0.8 - 0.5)/0.1 = 3.0, Z_rev = (0.2 - 0.5)/0.1 = -3.0 -> CIRG = 6.0
        self.assertAlmostEqual(cirg_val, 6.0, places=2)


if __name__ == "__main__":
    unittest.main()
