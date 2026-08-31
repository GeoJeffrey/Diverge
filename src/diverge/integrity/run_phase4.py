"""
run_phase4.py

Phase 4 Integrity & Coordination Scoring Orchestrator.

For every (ticker, window) that has data:
  1. Computes near-duplicate post ratio (duplicate_detection.py).
  2. Computes sentiment variance and baseline normalization (sentiment_variance.py).
  3. Checks for legitimate news events to apply news dampening (storage.check_news_event_in_window).
  4. Combines periodicity components + duplicate ratio + inverted sentiment variance into coordination_score (0-100).
  5. Assigns confidence_flag ('high_trust', 'moderate', 'low_trust', 'insufficient_data').

Stores raw scores in coordination_scores table (INSERT OR REPLACE).
Prints summary report of window trust classification per ticker.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure package root is importable
# sys.path manipulation removed: package installed via pip install -e .

from diverge import config, storage, utils
from diverge.integrity import coordination_score

logger = utils.setup_logger("run_phase4")


def run(db_path: Path = config.DB_PATH) -> int:
    """
    Run Phase 4 coordination scoring for all tickers and windows.
    Returns count of updated coordination_scores rows.
    """
    logger.info("=" * 60)
    logger.info("DIVERGE PHASE 4 â€” INTEGRITY & COORDINATION SCORING")
    logger.info("=" * 60)

    pstats = storage.get_periodicity_stats_for_window(db_path=db_path)
    if not pstats:
        logger.info("No periodicity_stats rows found. Computing coordination scores across tickers...")
        tickers = list(config.TICKERS.keys())
        pstats = [{"ticker": t, "window_start_utc": "", "window_end_utc": ""} for t in tickers]

    score_rows: List[Dict[str, Any]] = []

    for p in pstats:
        ticker = p["ticker"]
        start_utc = p.get("window_start_utc")
        end_utc = p.get("window_end_utc")

        try:
            res = coordination_score.compute_coordination_for_window(
                ticker=ticker,
                window_start_utc=start_utc,
                window_end_utc=end_utc,
                pstat=p,
                db_path=db_path,
            )
            score_rows.append(res)
            logger.info(
                f"  [{ticker}] Score: {res['coordination_score']} -> Flag: {res['confidence_flag']} "
                f"(Dups: {res['duplicate_ratio']}, SentVar: {res['sentiment_variance']})"
            )
        except Exception as e:
            logger.error(f"Failed coordination scoring for {ticker}: {e}")

    inserted = storage.insert_coordination_scores(score_rows, db_path=db_path)
    logger.info(f"Saved {inserted} coordination_scores rows to storage.")

    # â”€â”€ Print Phase 4 Summary Report â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_summary_report(score_rows)
    return inserted


def print_summary_report(rows: List[Dict[str, Any]]) -> None:
    """Print trust classification summary table per ticker."""
    print("\n" + "=" * 70)
    print("DIVERGE PHASE 4 â€” INTEGRITY & TRUST CLASSIFICATION SUMMARY")
    print("=" * 70)
    print(f"{'Ticker':<12} {'High Trust':<12} {'Moderate':<12} {'Low Trust':<12} {'Insufficient Data':<18}")
    print("-" * 70)

    # Group counts by ticker
    summary: Dict[str, Dict[str, int]] = {}
    for r in rows:
        t = r["ticker"]
        flag = r.get("confidence_flag", "insufficient_data")
        if t not in summary:
            summary[t] = {"high_trust": 0, "moderate": 0, "low_trust": 0, "insufficient_data": 0}
        summary[t][flag] = summary[t].get(flag, 0) + 1

    for ticker, counts in sorted(summary.items()):
        print(
            f"{ticker:<12} {counts['high_trust']:<12} {counts['moderate']:<12} "
            f"{counts['low_trust']:<12} {counts['insufficient_data']:<18}"
        )

    print("=" * 70 + "\n")


if __name__ == "__main__":
    run()

