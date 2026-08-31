"""
run_phase2.py

Phase 2 Feature Extraction Orchestrator.
Runs all three Phase 2 feature tracks in sequence, each crash-isolated:
  1. timing_features    -> post_timing + ticker_time_bins
  2. periodicity_analysis -> periodicity_stats
  3. text_features      -> text_features

Prints a summary table of row counts across all Phase 1 and Phase 2 tables.
"""

import sys
from pathlib import Path

# Ensure the package root is importable when run directly
# sys.path manipulation removed: package installed via pip install -e .

from diverge import storage, utils
from diverge.features import timing_features, periodicity_analysis, text_features

logger = utils.setup_logger("phase2_orchestrator")


def main():
    logger.info("=" * 60)
    logger.info("DIVERGE PHASE 2 â€” FEATURE EXTRACTION PIPELINE")
    logger.info("=" * 60)

    # â”€â”€ Track 1: Timing Features â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [1/3] Timing Features (inter-arrival deltas, first-mention flags, 5-min bins) ---")
    try:
        timing_counts = timing_features.run()
        logger.info(
            f"Timing OK: {timing_counts.get('timing_rows', 0)} post_timing rows added, "
            f"{timing_counts.get('time_bins', 0)} ticker_time_bins rows updated."
        )
    except Exception as e:
        logger.error(f"FAILED timing_features.run(): {e}")

    # â”€â”€ Track 2: Periodicity Analysis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [2/3] Periodicity Analysis (KS test, ACF, FFT, onset dispersion) ---")
    try:
        pstat_rows = periodicity_analysis.run()
        logger.info(f"Periodicity OK: {pstat_rows} periodicity_stats rows written.")
    except Exception as e:
        logger.error(f"FAILED periodicity_analysis.run(): {e}")

    # â”€â”€ Track 3: Text Features â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [3/3] Text Feature Extraction (FinBERT sentiment, capitulation, sarcasm, language) ---")
    try:
        text_rows = text_features.run()
        logger.info(f"Text OK: {text_rows} text_features rows inserted.")
    except Exception as e:
        logger.error(f"FAILED text_features.run(): {e}")

    # â”€â”€ Final Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("=" * 60)
    logger.info("DIVERGE PHASE 2 â€” DATABASE SUMMARY")
    logger.info("=" * 60)
    try:
        counts = storage.count_phase2_tables()
        col_w = 28
        logger.info(f"{'Table':<{col_w}} {'Rows':>8}")
        logger.info("-" * (col_w + 10))
        for table, count in counts.items():
            logger.info(f"  {table:<{col_w-2}} {count:>8,}")
        logger.info("=" * 60)
        print("\n" + "=" * 60)
        print("DIVERGE PHASE 2 - STORAGE SUMMARY")
        print("=" * 60)
        for table, count in counts.items():
            print(f"  {table:<30} {count:>8,} rows")
        print("=" * 60 + "\n")
    except Exception as e:
        logger.error(f"Failed to compute row counts: {e}")


if __name__ == "__main__":
    main()

