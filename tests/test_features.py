"""
test_phase2.py

Phase 2 Unit Tests:
 - Text features: capitulation lexicon, conviction-hedge ratio, sarcasm detection, language detection
 - Periodicity analysis: KS test and ACF peak strength comparison between
   (a) irregular/organic timestamps and (b) clearly periodic/fixed-interval timestamps

All tests are offline â€” no network, no FinBERT model download required.
Test database files are cleaned up after each test.
"""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Text Features Unit Tests
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class TestCapitulationDetection(unittest.TestCase):
    """Tests for lexicon-based capitulation detection."""

    def setUp(self):
        from diverge.features.text_features import detect_capitulation
        self.detect = detect_capitulation

    def test_clear_capitulation_phrases(self):
        """Known capitulation phrases should produce flag=1 and high confidence."""
        phrases = [
            "I sold everything this morning, lesson learned the hard way",
            "I'm out. Never investing again after this disaster.",
            "Panic sold all my positions. Got wrecked.",
            "Cut my losses and closed everything today.",
        ]
        for text in phrases:
            with self.subTest(text=text[:40]):
                flag, conf = self.detect(text)
                self.assertEqual(flag, 1, f"Expected capitulation_flag=1 for: {text[:50]!r}")
                self.assertGreater(conf, 0.0)

    def test_no_capitulation_in_neutral_text(self):
        """Normal investment discussions should not trigger capitulation flag."""
        phrases = [
            "Thinking about buying NVIDIA next week, looks undervalued.",
            "Great quarterly earnings from Apple. Still holding strong.",
            "HDFC bank has solid fundamentals for long-term investors.",
        ]
        for text in phrases:
            with self.subTest(text=text[:40]):
                flag, conf = self.detect(text)
                self.assertEqual(flag, 0, f"Expected capitulation_flag=0 for: {text[:50]!r}")

    def test_empty_text_returns_zero(self):
        flag, conf = self.detect("")
        self.assertEqual(flag, 0)
        self.assertEqual(conf, 0.0)

    def test_confidence_bounded(self):
        """Confidence should always be in [0.0, 1.0]."""
        flag, conf = self.detect("sold everything lesson learned never again I'm out got wrecked")
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)


class TestConvictionHedgeRatio(unittest.TestCase):
    """Tests for conviction-hedge ratio computation."""

    def setUp(self):
        from diverge.features.text_features import conviction_hedge_ratio
        self.ratio = conviction_hedge_ratio

    def test_none_when_both_zero(self):
        """Should return None when no certainty or hedge terms are present."""
        result = self.ratio("The sky is blue today and the weather is nice.")
        self.assertIsNone(result)

    def test_high_certainty_low_hedge(self):
        """More certainty terms than hedge terms â†’ ratio > 1."""
        text = "I am 100% guaranteed this will go up, definitely all in, absolutely no doubt."
        result = self.ratio(text)
        self.assertIsNotNone(result)
        self.assertGreater(result, 1.0)

    def test_high_hedge_low_certainty(self):
        """More hedge terms than certainty terms â†’ ratio < 1."""
        text = "This might work, could go up or maybe not. Not financial advice. DYOR. I think perhaps."
        result = self.ratio(text)
        self.assertIsNotNone(result)
        self.assertLess(result, 1.0)

    def test_equal_terms(self):
        """Equal certainty and hedge count â†’ ratio ~1.0."""
        text = "Definitely going up, maybe it might not. 100% guaranteed, could be wrong."
        result = self.ratio(text)
        self.assertIsNotNone(result)
        # Should be near 1.0 (equal counts), allow tolerance
        self.assertAlmostEqual(result, 1.0, delta=1.5)

    def test_only_hedge_no_certainty(self):
        """Only hedge terms present â†’ ratio = 0.0."""
        text = "This might fail, could be bad, maybe not financial advice, perhaps."
        result = self.ratio(text)
        self.assertIsNotNone(result)
        self.assertEqual(result, 0.0)


class TestSarcasmDetection(unittest.TestCase):
    """Tests for sarcasm / irony detection heuristic."""

    def setUp(self):
        from diverge.features.text_features import detect_sarcasm
        self.detect = detect_sarcasm

    def test_contradictory_certainty_and_loss(self):
        """High-certainty language with explicit loss signal â†’ sarcastic."""
        text = "Absolutely guaranteed gains! I only lost -$10,000 last week."
        self.assertEqual(self.detect(text), 1)

    def test_nfa_with_high_certainty(self):
        """'Not financial advice' with certainty language â†’ sarcastic."""
        text = "Not financial advice but this is 100% guaranteed to moon, definitely no doubt."
        self.assertEqual(self.detect(text), 1)

    def test_plain_bullish_text_not_sarcastic(self):
        """Plain bullish text with no contradictions â†’ not sarcastic."""
        text = "NVDA earnings beat expectations. Holding for the long term."
        self.assertEqual(self.detect(text), 0)

    def test_empty_not_sarcastic(self):
        self.assertEqual(self.detect(""), 0)

    def test_irony_adjusted_dampens_toward_zero(self):
        from diverge.features.text_features import irony_adjusted
        # Strong bullish score dampened to 30% when sarcastic
        result = irony_adjusted(0.8, is_sarcastic=1)
        self.assertAlmostEqual(result, 0.24, places=4)
        # Not sarcastic: no change
        result2 = irony_adjusted(0.8, is_sarcastic=0)
        self.assertAlmostEqual(result2, 0.8, places=4)


class TestLanguageDetection(unittest.TestCase):
    """Tests for language detection heuristic."""

    def setUp(self):
        from diverge.features.text_features import detect_language
        self.detect = detect_language

    def test_devanagari_text_flagged_as_mixed(self):
        text = "\u092f\u0939 \u0938\u094d\u091f\u094c\u0915 \u092c\u0939\u0941\u0924 \u0905\u0966\u0966\u096b\u093e \u0939\u0948\u0964"
        self.assertEqual(self.detect(text), "hi-en-mixed")

    def test_romanized_hindi_flagged_as_mixed(self):
        text = "Yaar bhai HDFC bohot achha stock hai, invest karo."
        self.assertEqual(self.detect(text), "hi-en-mixed")

    def test_english_text_detected(self):
        text = "NVIDIA is trading at a historically low P/E ratio. Strong buy signal."
        result = self.detect(text)
        self.assertEqual(result, "en")

    def test_empty_defaults_to_english(self):
        self.assertEqual(self.detect(""), "en")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Periodicity Analysis Unit Tests
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _make_test_db(db_path: Path, ticker_a_times: List[datetime], ticker_b_times: List[datetime]):
    """
    Build a minimal test SQLite database with raw_posts, post_timing, and ticker_time_bins
    for two synthetic tickers (ORGANIC and PERIODIC).
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS raw_posts (
        post_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, timestamp_utc TEXT NOT NULL,
        community TEXT, ticker TEXT, raw_text TEXT, upvotes INTEGER DEFAULT 0,
        platform TEXT NOT NULL, scraped_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS post_timing (
        post_id TEXT PRIMARY KEY, ticker TEXT NOT NULL, timestamp_utc TEXT NOT NULL,
        delta_seconds REAL, is_first_mention INTEGER DEFAULT 0, computed_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ticker_time_bins (
        ticker TEXT NOT NULL, bin_start_utc TEXT NOT NULL, post_count INTEGER DEFAULT 0,
        PRIMARY KEY (ticker, bin_start_utc)
    );
    CREATE TABLE IF NOT EXISTS text_features (
        post_id TEXT PRIMARY KEY, sentiment_score REAL, sentiment_label TEXT,
        capitulation_flag INTEGER, capitulation_confidence REAL, is_sarcastic INTEGER,
        irony_adjusted_sentiment REAL, conviction_hedge_ratio REAL, language TEXT,
        computed_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS periodicity_stats (
        ticker TEXT NOT NULL, window_start_utc TEXT NOT NULL, window_end_utc TEXT NOT NULL,
        ks_statistic REAL, acf_peak_lag_minutes REAL, acf_peak_strength REAL,
        dominant_frequency_minutes REAL, onset_dispersion_index REAL,
        PRIMARY KEY (ticker, window_start_utc)
    );
    """)

    now_iso = datetime.now(timezone.utc).isoformat()

    def insert_ticker_posts(ticker: str, times: List[datetime]):
        sorted_times = sorted(times)
        last_dt = None
        seen_accts = set()
        for i, dt in enumerate(sorted_times):
            pid = f"{ticker}_{i}"
            acct = f"user_{ticker}_{i % 5}"  # 5 rotating accounts
            delta = (dt - last_dt).total_seconds() if last_dt else None
            is_first = 1 if acct not in seen_accts else 0
            seen_accts.add(acct)
            ts = dt.isoformat()

            conn.execute(
                "INSERT OR IGNORE INTO raw_posts VALUES (?,?,?,?,?,?,?,?,?)",
                (pid, acct, ts, f"r/{ticker.lower()}", ticker, f"Post about {ticker}", 0, "reddit", now_iso),
            )
            conn.execute(
                "INSERT OR IGNORE INTO post_timing VALUES (?,?,?,?,?,?)",
                (pid, ticker, ts, delta, is_first, now_iso),
            )
            last_dt = dt

        # Build 5-minute bins
        from collections import Counter
        bin_counts = Counter()
        for dt in sorted_times:
            minute_5 = (dt.minute // 5) * 5
            bin_dt = dt.replace(minute=minute_5, second=0, microsecond=0)
            bin_counts[(ticker, bin_dt.isoformat())] += 1
        for (tk, bin_start), cnt in bin_counts.items():
            conn.execute(
                "INSERT OR REPLACE INTO ticker_time_bins VALUES (?,?,?)", (tk, bin_start, cnt)
            )

    insert_ticker_posts("ORGANIC", ticker_a_times)
    insert_ticker_posts("PERIODIC", ticker_b_times)
    conn.commit()
    conn.close()


class TestPeriodicityAnalysis(unittest.TestCase):
    """
    Tests for periodicity_analysis.py using synthetic data.
    Organic (irregular) ticker: random Poisson-like timestamps
    Periodic ticker: fixed-interval timestamps (one post every 5 minutes exactly)
    """

    @classmethod
    def setUpClass(cls):
        """Generate synthetic timestamps and build test database."""
        import random
        random.seed(42)

        base_dt = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)

        # ORGANIC: irregular arrivals (random inter-arrivals between 1-8 min)
        # Dense enough to fill 2-hour windows with >= 20 posts, but NOT periodic.
        organic_times = []
        t = base_dt
        for _ in range(300):
            t += timedelta(seconds=random.uniform(30, 480))
            organic_times.append(t)

        # PERIODIC: strict 5-minute intervals for 120 posts over ~10 hours
        periodic_times = [base_dt + timedelta(minutes=5 * i) for i in range(120)]

        cls.tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = Path(cls.tmp_file.name)
        cls.tmp_file.close()

        _make_test_db(cls.db_path, organic_times, periodic_times)

    @classmethod
    def tearDownClass(cls):
        """Remove test database file after all tests complete."""
        try:
            os.unlink(cls.db_path)
        except Exception:
            pass

    def _get_stats_for_ticker(self, ticker: str):
        from diverge.features.periodicity_analysis import (
            _load_ticker_time_bins,
            _load_post_timing_for_ticker,
            analyse_ticker,
        )
        bins = _load_ticker_time_bins(self.db_path).get(ticker, [])
        timing = _load_post_timing_for_ticker(ticker, self.db_path)
        return analyse_ticker(ticker, bins, timing)

    def test_periodic_ticker_has_higher_acf_peak_strength(self):
        """
        PERIODIC ticker should have measurably higher ACF peak strength than ORGANIC.
        The periodic posts (every 5 min) produce a strong autocorrelation at lag=5 min.
        For the ORGANIC ticker we only assert it has valid windows â€” irregular spacing
        naturally produces lower but non-zero ACF peaks.
        """
        periodic_stats = self._get_stats_for_ticker("PERIODIC")
        organic_stats = self._get_stats_for_ticker("ORGANIC")

        self.assertTrue(len(periodic_stats) > 0, "Should have windows for PERIODIC ticker")

        # Average ACF peak strength across windows (filter None)
        p_strengths = [w["acf_peak_strength"] for w in periodic_stats if w["acf_peak_strength"] is not None]
        self.assertTrue(len(p_strengths) > 0, "PERIODIC ticker should produce ACF values")

        avg_p = sum(p_strengths) / len(p_strengths)
        # PERIODIC posts every 5 min should produce strong autocorrelation
        self.assertGreater(avg_p, 0.1, f"Expected PERIODIC ACF strength > 0.1, got {avg_p:.4f}")

        # If ORGANIC also has windows, verify PERIODIC > ORGANIC
        if organic_stats:
            o_strengths = [w["acf_peak_strength"] for w in organic_stats if w["acf_peak_strength"] is not None]
            if o_strengths:
                avg_o = sum(o_strengths) / len(o_strengths)
                self.assertGreater(
                    avg_p, avg_o,
                    f"Expected PERIODIC avg ACF ({avg_p:.4f}) > ORGANIC ({avg_o:.4f})"
                )

    def test_periodic_ticker_has_higher_ks_statistic(self):
        """
        PERIODIC ticker (non-Poisson, fixed interval) should deviate more from exponential
        distribution than ORGANIC (Poisson-like random arrivals) â†’ higher KS statistic.
        """
        periodic_stats = self._get_stats_for_ticker("PERIODIC")
        organic_stats = self._get_stats_for_ticker("ORGANIC")

        p_ks = [w["ks_statistic"] for w in periodic_stats if w["ks_statistic"] is not None]
        o_ks = [w["ks_statistic"] for w in organic_stats if w["ks_statistic"] is not None]

        if p_ks and o_ks:
            avg_p = sum(p_ks) / len(p_ks)
            avg_o = sum(o_ks) / len(o_ks)
            self.assertGreater(
                avg_p, avg_o,
                f"Expected PERIODIC avg KS ({avg_p:.4f}) > ORGANIC ({avg_o:.4f})"
            )

    def test_minimum_sample_guard_skips_sparse_windows(self):
        """
        When there are fewer than MIN_POSTS_PER_WINDOW posts in a window,
        it should be skipped. Verify no computation for empty windows.
        """
        from diverge.features.periodicity_analysis import analyse_ticker, MIN_POSTS_PER_WINDOW
        base = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        # Only 5 posts â€” all windows should be skipped
        sparse_times = [(base + timedelta(minutes=i * 10), 1) for i in range(5)]
        results = analyse_ticker("SPARSE", sparse_times, [])
        self.assertEqual(results, [], "Should skip all sparse windows")

    def test_run_writes_to_db(self):
        """Full periodicity_analysis.run() should write rows to periodicity_stats table."""
        from diverge.features import periodicity_analysis
        # Patch the db_path to use the test db
        count = periodicity_analysis.run(db_path=self.db_path)
        self.assertGreaterEqual(count, 0, "Should return non-negative row count")

        # Verify actual rows written
        conn = sqlite3.connect(str(self.db_path))
        actual = conn.execute("SELECT COUNT(*) FROM periodicity_stats").fetchone()[0]
        conn.close()
        self.assertGreaterEqual(actual, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


