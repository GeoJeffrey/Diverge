"""
run_phase6.py

Phase 6 Explainability & Narrative Lineage Orchestrator.

Execution Steps:
  1. Duplicate Pairs Backfill: Runs duplicate_detection.py to populate duplicate_pairs table.
  2. Reasoning Trace Builder: Generates audit trail records in reasoning_trace for all non-null composite windows.
  3. Narrative Phylogeny Builder: Tracks window-to-window narrative evolution in narrative_phylogeny for each ticker.

Usage:
    python run_phase6.py [--recompute-all]
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diverge_scraper import config, duplicate_detection, phylogeny_builder, reasoning_trace_builder, storage, utils

logger = utils.setup_logger("run_phase6")


def run(db_path: Path = config.DB_PATH, recompute_all: bool = False) -> int:
    """
    Run Phase 6 explainability and phylogeny builder.
    Returns total reasoning_trace rows inserted.
    """
    logger.info("=" * 60)
    logger.info("DIVERGE PHASE 6 — EXPLAINABILITY & NARRATIVE LINEAGE")
    logger.info("=" * 60)

    # ── 1. Duplicate Pairs Backfill ────────────────────────────────
    logger.info("--- [1/3] Backfilling duplicate_pairs table ---")
    windows = storage.get_index_values_and_coordination_for_window(db_path=db_path)
    dup_pairs_created = 0
    for w in windows:
        ticker = w.get("ticker", "")
        start_utc = w.get("window_start_utc", "")
        end_utc = w.get("window_end_utc")
        if ticker and start_utc:
            try:
                posts = storage.get_text_and_posts_for_window(ticker, start_utc, end_utc, db_path=db_path)
                if posts:
                    duplicate_detection.compute_duplicate_ratio(
                        posts,
                        similarity_threshold=0.90,
                        ticker=ticker,
                        window_start_utc=start_utc,
                        db_path=db_path,
                    )
            except Exception as e:
                logger.error(f"Failed duplicate pairs backfill for {ticker} at {start_utc}: {e}")

    conn = storage.get_connection(db_path)
    conn.row_factory = storage.sqlite3.Row
    dup_total = conn.execute("SELECT COUNT(*) FROM duplicate_pairs").fetchone()[0]
    logger.info(f"Duplicate pairs stored: {dup_total} rows.")

    # ── 2. Reasoning Trace Builder ─────────────────────────────────
    logger.info("--- [2/3] Building reasoning_trace audit records ---")
    metrics = [dict(r) for r in conn.execute("SELECT * FROM ticker_window_metrics WHERE composite_score IS NOT NULL").fetchall()]
    conn.close()

    total_traces = 0
    trace_rows_inserted = 0

    if not metrics:
        logger.warning("No populated composite metrics found. Skipping reasoning trace builder.")
    else:
        for m in metrics:
            ticker = m.get("ticker", "")
            start_utc = m.get("window_start_utc", "")

            try:
                traces = reasoning_trace_builder.build_traces_for_window(m, db_path=db_path)
                if traces:
                    num_saved = storage.insert_reasoning_traces(traces, db_path=db_path)
                    trace_rows_inserted += num_saved
                    total_traces += len(traces)
                    logger.info(f"  [{ticker}] Window {start_utc}: {len(traces)} reasoning traces generated.")
            except Exception as e:
                logger.error(f"Failed reasoning trace for {ticker} at {start_utc}: {e}")

    # ── 3. Narrative Phylogeny Builder ──────────────────────────────
    logger.info("--- [3/3] Building narrative_phylogeny lineage tree ---")
    tickers = list(config.TICKERS.keys())
    phylo_total = 0
    phylo_summary: Dict[str, int] = {}

    for t in tickers:
        try:
            records = phylogeny_builder.build_phylogeny_for_ticker(t, db_path=db_path)
            if records:
                num_saved = storage.insert_narrative_phylogeny(records, db_path=db_path)
                phylo_total += num_saved
                for r in records:
                    mtype = r.get("mutation_type", "stable")
                    phylo_summary[mtype] = phylo_summary.get(mtype, 0) + 1
        except Exception as e:
            logger.error(f"Failed narrative phylogeny for ticker {t}: {e}")

    logger.info(f"Saved {phylo_total} narrative_phylogeny rows across tickers.")

    # ── Print Summary Report ───────────────────────────────────────
    avg_posts_per_trace = round(total_traces / max(len(metrics), 1), 2)
    print_summary_report(len(metrics), total_traces, avg_posts_per_trace, phylo_summary)
    return trace_rows_inserted


def print_summary_report(
    total_metrics: int,
    total_traces: int,
    avg_posts_per_trace: float,
    phylo_summary: Dict[str, int],
) -> None:
    """Print Phase 6 Summary Report."""
    print("\n" + "=" * 70)
    print("DIVERGE PHASE 6 — EXPLAINABILITY & NARRATIVE LINEAGE SUMMARY")
    print("=" * 70)
    print(f"Total Traced Windows:       {total_metrics}")
    print(f"Total Reasoning Traces:     {total_traces}")
    print(f"Average Traces / Window:    {avg_posts_per_trace}")
    print("-" * 70)
    print("Phylogeny Mutation Types Count:")
    for mtype, count in sorted(phylo_summary.items()):
        print(f"  - {mtype:<25} {count:>6} transitions")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run()
