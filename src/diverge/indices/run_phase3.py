"""
run_phase3.py

Phase 3 Financial Indices Orchestrator.
Runs all five Phase 3 indices in order, each wrapped in a try/except block so one failure
does not halt execution of remaining indices:
  1. CLI (Capitulation Leak Index)
  2. VDI (Vernacular Divergence Index)
  3. CASSI (Cross-Asset Sentiment Spillover Index)
  4. Rn (Effective Reproduction Number Index)
  5. CIRG (Consumer-Investor Rating Gap Index - runs consumer_reviews_scraper first)

Stores raw index values in index_values table (INSERT OR REPLACE).
Prints a summary table (ticker x index) showing real values vs NULL so data gaps are visible.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure package root is importable
# sys.path manipulation removed: package installed via pip install -e .

from diverge import config, storage, utils
from diverge.scrapers import consumer_reviews_scraper
from diverge.indices import (
    cross_asset_spillover as cassi_index,
    reality_gap as cirg_index,
    capitulation_language as cli_index,
    narrative_reproduction as rn_index,
    vernacular_divergence as vdi_index,
)

logger = utils.setup_logger("run_phase3")


def run(db_path: Path = config.DB_PATH) -> int:
    """
    Run Phase 3 indices calculation for all configured tickers and store in index_values.
    Returns count of updated index_values rows.
    """
    logger.info("=" * 60)
    logger.info("DIVERGE PHASE 3 â€” FINANCIAL INDICES PIPELINE")
    logger.info("=" * 60)

    tickers = list(config.TICKERS.keys())
    now_iso = datetime.now(timezone.utc).isoformat()
    window_start = (datetime.now(timezone.utc) - timedelta(days=config.RETENTION_DAYS)).isoformat()

    # Dictionary to collect results per ticker
    index_results: Dict[str, Dict[str, Any]] = {
        t: {
            "ticker": t,
            "window_start_utc": window_start,
            "window_end_utc": now_iso,
            "cli": None,
            "vdi": None,
            "cassi": None,
            "rn": None,
            "rn_confidence": None,
            "cirg": None,
            "computed_at": now_iso,
        }
        for t in tickers
    }

    # â”€â”€ 1. CLI (Capitulation Leak Index) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [1/5] Calculating CLI (Capitulation Leak Index) ---")
    for t in tickers:
        try:
            cli_val = cli_index.compute_cli(t, window_start_utc=window_start, window_end_utc=now_iso, db_path=db_path)
            index_results[t]["cli"] = cli_val
            logger.info(f"  CLI [{t}]: {cli_val if cli_val is not None else 'NULL'}")
        except Exception as e:
            logger.error(f"Failed CLI for {t}: {e}")

    # â”€â”€ 2. VDI (Vernacular Divergence Index) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [2/5] Calculating VDI (Vernacular Divergence Index) ---")
    for t in tickers:
        try:
            vdi_val = vdi_index.compute_vdi(t, window_start_utc=window_start, window_end_utc=now_iso, db_path=db_path)
            index_results[t]["vdi"] = vdi_val
            logger.info(f"  VDI [{t}]: {vdi_val if vdi_val is not None else 'NULL'}")
        except Exception as e:
            logger.error(f"Failed VDI for {t}: {e}")

    # â”€â”€ 3. CASSI (Cross-Asset Sentiment Spillover Index) â”€â”€â”€â”€â”€â”€
    logger.info("--- [3/5] Calculating CASSI (Cross-Asset Sentiment Spillover Index) ---")
    try:
        cassi_dict = cassi_index.compute_cassi(tickers, window_start_utc=None, window_end_utc=now_iso, db_path=db_path)
        for t, cassi_val in cassi_dict.items():
            if t in index_results:
                index_results[t]["cassi"] = cassi_val
                logger.info(f"  CASSI [{t}]: {cassi_val if cassi_val is not None else 'NULL'}")
    except Exception as e:
        logger.error(f"Failed CASSI calculation: {e}")

    # â”€â”€ 4. Rn (Effective Reproduction Number Index) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [4/5] Calculating Rn (Effective Reproduction Number Index) ---")
    for t in tickers:
        try:
            rn_val, rn_conf = rn_index.compute_rn(t, window_start_utc=None, window_end_utc=now_iso, db_path=db_path)
            index_results[t]["rn"] = rn_val
            index_results[t]["rn_confidence"] = rn_conf
            logger.info(f"  Rn [{t}]: {rn_val if rn_val is not None else 'NULL'} (conf: {rn_conf})")
        except Exception as e:
            logger.error(f"Failed Rn for {t}: {e}")

    # â”€â”€ 5. CIRG (Consumer-Investor Rating Gap Index) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("--- [5/5] Executing Consumer Reviews Scraper & Calculating CIRG ---")
    try:
        consumer_reviews_scraper.run(db_path=db_path)
    except Exception as e:
        logger.error(f"Consumer Reviews Scraper failed: {e}")

    for t in tickers:
        try:
            cirg_val = cirg_index.compute_cirg(t, window_start_utc=None, window_end_utc=now_iso, db_path=db_path)
            index_results[t]["cirg"] = cirg_val
            logger.info(f"  CIRG [{t}]: {cirg_val if cirg_val is not None else 'NULL'}")
        except Exception as e:
            logger.error(f"Failed CIRG for {t}: {e}")

    # Save all index values to storage
    rows_to_insert = list(index_results.values())
    inserted = storage.insert_index_values(rows_to_insert, db_path=db_path)
    logger.info(f"Saved {inserted} index_values rows to storage.")

    # â”€â”€ Print Phase 3 Summary Table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_summary_table(index_results)
    return inserted


def print_summary_table(results: Dict[str, Dict[str, Any]]) -> None:
    """Print clean formatted ticker x index summary table showing real values vs NULL."""
    print("\n" + "=" * 70)
    print("DIVERGE PHASE 3 â€” INDEX VALUES SUMMARY (REAL VS NULL)")
    print("=" * 70)
    header = f"{'Ticker':<12} {'CLI':<10} {'VDI':<10} {'CASSI':<10} {'Rn (Conf)':<14} {'CIRG':<10}"
    print(header)
    print("-" * 70)

    for ticker, res in sorted(results.items()):
        cli_str = f"{res['cli']:.4f}" if res['cli'] is not None else "NULL"
        vdi_str = f"{res['vdi']:.4f}" if res['vdi'] is not None else "NULL"
        cassi_str = f"{res['cassi']:.4f}" if res['cassi'] is not None else "NULL"

        if res['rn'] is not None:
            rn_str = f"{res['rn']:.2f} ({res['rn_confidence']:.1f})"
        else:
            rn_str = "NULL"

        cirg_str = f"{res['cirg']:.4f}" if res['cirg'] is not None else "NULL"

        print(f"{ticker:<12} {cli_str:<10} {vdi_str:<10} {cassi_str:<10} {rn_str:<14} {cirg_str:<10}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    run()

