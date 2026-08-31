"""
run_all.py

Master Orchestrator for Diverge Pipeline (Phase 1 + Phase 2 + Phase 3).
Executes all three phases end-to-end in required order:
  1. Phase 1: Scraper data collection (Reddit, StockTwits, Telegram, RSS, Google Trends)
  2. Phase 2: Feature extraction (post_timing, ticker_time_bins, periodicity_stats, text_features)
  3. Phase 3: Financial indices calculation (CLI, VDI, CASSI, Rn, CIRG)

Includes:
  - Error isolation & data dependency checks before each phase.
  - CLI flag --skip-scrape to run Phase 2+3 only against existing database records.
  - Single combined summary table at the end (Phase 1 platforms, Phase 2 tables, Phase 3 index values).
"""

import argparse
import sys
from pathlib import Path

from diverge.features import run_phase2
from diverge.indices import run_phase3
from diverge import config, storage, utils
from diverge.scrapers import run_phase1 as phase1_main

logger = utils.setup_logger("run_all_master")


def main():
    parser = argparse.ArgumentParser(description="Diverge Pipeline Master Orchestrator (Phase 1 + 2 + 3)")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip Phase 1 live data scraping and run Phase 2 + Phase 3 on existing database records.",
    )
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("DIVERGE MASTER PIPELINE â€” END-TO-END EXECUTION")
    logger.info("=" * 70)

    db_path = config.DB_PATH

    # â”€â”€ Phase 1: Data Collection Scrapers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if getattr(args, "skip_scrape", False):
        logger.info("[PHASE 1] --skip-scrape flag set. Skipping live scrapers execution.")
    else:
        logger.info("--- [PHASE 1] Executing Scrapers Data Collection Pipeline ---")
        try:
            phase1_main.run_pipeline()
            logger.info("[PHASE 1] Data collection complete.")
        except Exception as e:
            logger.error(f"[PHASE 1 FAILED]: {e}")

    # Check raw_posts data presence before Phase 2
    raw_count = storage.count_by_platform(db_path=db_path)
    total_raw = sum(raw_count.values())
    if total_raw == 0:
        logger.warning("CRITICAL: raw_posts table is empty. Cannot proceed with Phase 2 feature extraction. STOPPING.")
        sys.exit(1)
    else:
        logger.info(f"Database contains {total_raw} raw posts across {len(raw_count)} platforms.")

    # â”€â”€ Phase 2: Feature Extraction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [PHASE 2] Executing Feature Extraction Pipeline ---")
    try:
        run_phase2.main()
        logger.info("[PHASE 2] Feature extraction complete.")
    except Exception as e:
        logger.error(f"[PHASE 2 FAILED]: {e}")

    # Check text_features/post_timing data presence before Phase 3
    phase2_counts = storage.count_phase2_tables(db_path=db_path)
    if phase2_counts.get("text_features", 0) == 0 and phase2_counts.get("post_timing", 0) == 0:
        logger.warning("WARNING: Phase 2 tables (text_features/post_timing) are empty. Phase 3 indices will return NULL.")

    # â”€â”€ Phase 3: Financial Indices â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [PHASE 3] Executing Financial Indices Pipeline ---")
    try:
        run_phase3.run(db_path=db_path)
        logger.info("[PHASE 3] Financial indices pipeline complete.")
    except Exception as e:
        logger.error(f"[PHASE 3 FAILED]: {e}")

    # â”€â”€ Phase 4: Integrity & Coordination Scoring â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [PHASE 4] Executing Integrity & Coordination Scoring Pipeline ---")
    try:
        from diverge.integrity import run_phase4
        run_phase4.run(db_path=db_path)
        logger.info("[PHASE 4] Integrity & coordination scoring pipeline complete.")
    except Exception as e:
        logger.error(f"[PHASE 4 FAILED]: {e}")

    # â”€â”€ Phase 5: Composite Aggregation Pipeline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [PHASE 5] Executing Composite Aggregation Pipeline ---")
    try:
        from diverge.aggregation import run_phase5
        run_phase5.run(db_path=db_path)
        logger.info("[PHASE 5] Composite aggregation pipeline complete.")
    except Exception as e:
        logger.error(f"[PHASE 5 FAILED]: {e}")

    # â”€â”€ Phase 6: Explainability & Narrative Lineage Pipeline 
    logger.info("--- [PHASE 6] Executing Explainability & Narrative Lineage Pipeline ---")
    try:
        from diverge.explainability import run_phase6
        run_phase6.run(db_path=db_path)
        logger.info("[PHASE 6] Explainability & narrative lineage pipeline complete.")
    except Exception as e:
        logger.error(f"[PHASE 6 FAILED]: {e}")

    # â”€â”€ Final Combined Summary Report â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_master_summary(db_path)


def print_master_summary(db_path: Path):
    """Print single unified summary report across all 6 phases."""
    print("\n" + "=" * 70)
    print("DIVERGE MASTER PIPELINE â€” COMBINED SUMMARY REPORT")
    print("=" * 70)

    # 1. Phase 1 Summary
    platform_counts = storage.count_by_platform(db_path=db_path)
    print("\n1. PHASE 1: RAW POSTS BY PLATFORM")
    print("-" * 40)
    if not platform_counts:
        print("  No records found.")
    else:
        for p, count in sorted(platform_counts.items()):
            print(f"  {p:<25} {count:>8,} rows")

    # 2. Phase 2 Summary
    all_table_counts = storage.count_all_tables(db_path=db_path)
    phase2_tables = ["post_timing", "ticker_time_bins", "text_features", "periodicity_stats"]
    print("\n2. PHASE 2: FEATURE EXTRACTION TABLES")
    print("-" * 40)
    for t in phase2_tables:
        print(f"  {t:<25} {all_table_counts.get(t, 0):>8,} rows")

    # 3. Phase 3-6 Summary
    print("\n3. PHASE 3 - 6: INDICES, INTEGRITY, COMPOSITE & EXPLAINABILITY STORAGE")
    print("-" * 40)
    print(f"  consumer_sentiment       {all_table_counts.get('consumer_sentiment', 0):>8,} rows")
    print(f"  index_values             {all_table_counts.get('index_values', 0):>8,} rows")
    print(f"  coordination_scores      {all_table_counts.get('coordination_scores', 0):>8,} rows")
    print(f"  ticker_window_metrics    {all_table_counts.get('ticker_window_metrics', 0):>8,} rows")
    print(f"  duplicate_pairs          {all_table_counts.get('duplicate_pairs', 0):>8,} rows")
    print(f"  reasoning_trace          {all_table_counts.get('reasoning_trace', 0):>8,} rows")
    print(f"  narrative_phylogeny      {all_table_counts.get('narrative_phylogeny', 0):>8,} rows")
    print("=" * 70)
    print("\nData pipeline complete. Run python run_server.py to view results.\n")


if __name__ == "__main__":
    main()

