"""
test_phase4.py

Unit tests for Phase 4 Integrity / Coordination Scoring:
  1. Duplicate Detection (MinHash Jaccard pairwise comparison across different accounts)
  2. Sentiment Variance (Low variance detection & baseline normalization)
  3. Coordination Score (Combiner, news dampening, and trust flag classification)
"""

import unittest

from diverge_scraper import coordination_score, duplicate_detection, sentiment_variance


class TestPhase4IntegrityScoring(unittest.TestCase):

    # ── 1. Duplicate Detection Tests ──────────────────────────
    def test_duplicate_detection_minhash(self):
        # 3 near-identical posts from different accounts
        near_identical = [
            {"post_id": "p1", "account_id": "user_a", "raw_text": "TATASTEEL target is 200 buy now breakout rocket"},
            {"post_id": "p2", "account_id": "user_b", "raw_text": "TATASTEEL target is 200 buy now breakout rocket moon"},
            {"post_id": "p3", "account_id": "user_c", "raw_text": "TATASTEEL target is 200 buy now breakout rocket rocket"},
        ]
        # 3 genuinely different posts
        different = [
            {"post_id": "p4", "account_id": "user_d", "raw_text": "Quarterly financial results for Tata Steel show decline in exports."},
            {"post_id": "p5", "account_id": "user_e", "raw_text": "Why is the steel sector underperforming global markets today?"},
            {"post_id": "p6", "account_id": "user_f", "raw_text": "RBI interest rate decision impacts industrial stocks heavy volume."},
        ]

        all_posts = near_identical + different
        ratio = duplicate_detection.compute_duplicate_ratio(all_posts, similarity_threshold=0.80)

        # 3 out of 6 posts are near-duplicates -> ratio should be 0.50
        self.assertAlmostEqual(ratio, 0.50, places=2)

    # ── 2. Sentiment Variance Tests ───────────────────────────
    def test_sentiment_variance_detection(self):
        # Near-identical sentiment values (suspiciously low variance)
        low_var_scores = [0.85, 0.85, 0.86, 0.85, 0.84, 0.85]
        var_low = sentiment_variance.compute_window_sentiment_variance(low_var_scores)
        norm_low = sentiment_variance.normalize_sentiment_variance(var_low)

        # Naturally spread sentiment values (high variance, normal)
        high_var_scores = [-0.80, 0.50, 0.10, -0.40, 0.90, -0.20]
        var_high = sentiment_variance.compute_window_sentiment_variance(high_var_scores)
        norm_high = sentiment_variance.normalize_sentiment_variance(var_high)

        self.assertLess(var_low, var_high)
        self.assertLess(norm_low, norm_high)

    # ── 3. Coordination Score Combiner Tests ──────────────────
    def test_coordination_score_organic_vs_manipulated(self):
        # Organic Case: low KS, low ACF, low dispersion, 0 duplicates, high sentiment variance -> high_trust (< 40)
        res_organic = coordination_score.calculate_coordination_score(
            ks_stat=0.10,
            acf_strength=0.10,
            onset_dispersion=0.10,
            duplicate_ratio=0.0,
            sentiment_var=0.25,
            total_posts=50,
            news_event_present=False,
        )
        self.assertEqual(res_organic["confidence_flag"], "high_trust")
        self.assertLess(res_organic["coordination_score"], 40.0)

        # Manipulated Case: high KS, high ACF, high dispersion, 80% duplicates, near-zero sentiment variance -> low_trust (>= 70)
        res_manipulated = coordination_score.calculate_coordination_score(
            ks_stat=0.95,
            acf_strength=0.95,
            onset_dispersion=0.95,
            duplicate_ratio=0.85,
            sentiment_var=0.001,
            total_posts=50,
            news_event_present=False,
        )
        self.assertEqual(res_manipulated["confidence_flag"], "low_trust")
        self.assertGreaterEqual(res_manipulated["coordination_score"], 70.0)

    def test_coordination_insufficient_data_guard(self):
        # < 20 posts guard check
        res_small = coordination_score.calculate_coordination_score(
            ks_stat=0.90,
            acf_strength=0.90,
            onset_dispersion=0.90,
            duplicate_ratio=0.90,
            sentiment_var=0.001,
            total_posts=10,  # < 20
        )
        self.assertEqual(res_small["confidence_flag"], "insufficient_data")
        self.assertEqual(res_small["coordination_score"], 0.0)

    def test_news_event_dampening(self):
        # High onset dispersion due to news event should yield a lower score than un-dampened onset
        res_normal = coordination_score.calculate_coordination_score(
            ks_stat=0.20,
            acf_strength=0.20,
            onset_dispersion=0.95,  # high onset spike
            duplicate_ratio=0.0,
            sentiment_var=0.20,
            total_posts=50,
            news_event_present=False,
        )
        res_dampened = coordination_score.calculate_coordination_score(
            ks_stat=0.20,
            acf_strength=0.20,
            onset_dispersion=0.95,  # high onset spike
            duplicate_ratio=0.0,
            sentiment_var=0.20,
            total_posts=50,
            news_event_present=True,  # News event present -> onset dampened
        )

        # Dampened score should be lower than normal score when onset is high
        self.assertLess(res_dampened["coordination_score"], res_normal["coordination_score"])


if __name__ == "__main__":
    unittest.main()

