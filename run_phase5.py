"""
run_phase5.py

Phase 5 Composite Aggregation Orchestrator.

Queries index_values and coordination_scores windows, passes raw inputs through
aggregate_composite_row(), and stores the final combined metrics into ticker_window_metrics.

Usage:
    python run_phase5.py [--recompute-all]
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diverge_scraper import aggregate_composite, config, storage, utils

logger = utils.setup_logger("run_phase5")


def run(db_path: Path = config.DB_PATH, recompute_all: bool = False) -> int:
    """
    Run Phase 5 composite aggregation across all available index windows.
    Returns count of inserted/updated ticker_window_metrics rows.
    """
    logger.info("=" * 60)
    logger.info("DIVERGE PHASE 5 — COMPOSITE AGGREGATION PIPELINE")
    logger.info("=" * 60)

    # Fetch joined index_values and coordination_scores
    raw_windows = storage.get_index_values_and_coordination_for_window(db_path=db_path)
    if not raw_windows:
        logger.warning("No index_values or coordination_scores found in storage. Skipping Phase 5 aggregation.")
        return 0

    logger.info(f"Loaded {len(raw_windows)} candidate index/coordination windows for Phase 5 aggregation.")

    metrics_rows: List[Dict[str, Any]] = []
    stats = {"insufficient_data": 0, "dampened": 0, "high_trust": 0}

    for w in raw_windows:
        ticker = w.get("ticker", "")
        start_utc = w.get("window_start_utc", "")

        try:
            res = aggregate_composite.aggregate_composite_row(w)
            metrics_rows.append(res)

            conf = res.get("aggregation_confidence", "insufficient_data")
            if conf == "insufficient_data" or res.get("composite_score") is None:
                stats["insufficient_data"] += 1
            elif conf in ["moderate", "low_trust"]:
                stats["dampened"] += 1
            elif conf == "high_trust":
                stats["high_trust"] += 1

            logger.info(
                f"  [{ticker}] Composite: {res['composite_score']} | Dominant: {res['dominant_index']} | "
                f"Flags: {res['risk_flags']} | Conf: {conf}"
            )
        except Exception as e:
            logger.error(f"Failed Phase 5 aggregation for ticker {ticker} at window {start_utc}: {e}")

    inserted = storage.insert_ticker_window_metrics(metrics_rows, db_path=db_path)
    logger.info(f"Saved {inserted} rows to ticker_window_metrics table.")

    # ── Summary Report ─────────────────────────────────────────
    print_summary_report(len(raw_windows), inserted, stats, metrics_rows)
    return inserted


def print_summary_report(total_processed: int, total_saved: int, stats: Dict[str, int], rows: List[Dict[str, Any]]) -> None:
    """Print Phase 5 Composite Aggregation Summary Table."""
    print("\n" + "=" * 70)
    print("DIVERGE PHASE 5 — COMPOSITE AGGREGATION SUMMARY")
    print("=" * 70)
    print(f"Total Windows Processed:    {total_processed}")
    print(f"Total Metrics Saved:        {total_saved}")
    print(f"  - Full High Trust:        {stats['high_trust']}")
    print(f"  - Dampened (Mod/LowTrust): {stats['dampened']}")
    print(f"  - Insufficient Data:      {stats['insufficient_data']}")
    print("-" * 70)
    print(f"{'Ticker':<12} {'Composite Score':<18} {'Dominant Index':<18} {'Risk Flags':<20}")
    print("-" * 70)

    # Print distinct sample per ticker
    seen_tickers = set()
    for r in rows:
        t = r["ticker"]
        if t not in seen_tickers:
            seen_tickers.add(t)
            score_str = str(r["composite_score"]) if r["composite_score"] is not None else "NULL"
            dom_str = r["dominant_index"]
            flags_str = r["risk_flags"]
            print(f"{t:<12} {score_str:<18} {dom_str:<18} {flags_str:<20}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    recompute = "--recompute-all" in sys.argv
    run(recompute_all=recompute)
