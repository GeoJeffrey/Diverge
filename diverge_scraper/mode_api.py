"""
mode_api.py

Phase 7 API Handler Module.

Framework-agnostic handler functions for Simple Mode, Advanced Mode, Tickers Landing, and Phylogeny Tree.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import advanced_mode, config, render_prototype, simple_mode, storage, utils

logger = utils.setup_logger("mode_api")


def handle_get_simple(
    ticker: str,
    window_start_utc: str,
    db_path: Path = config.DB_PATH,
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle GET /api/simple/<ticker>/<window_start_utc>.
    Returns (status_code, payload_dict).
    """
    view = simple_mode.get_simple_view(ticker, window_start_utc, db_path=db_path)
    if view is None:
        return 404, {"error": f"No ticker_window_metrics record for {ticker} at {window_start_utc}"}
    return 200, view


def handle_get_advanced(
    ticker: str,
    window_start_utc: str,
    db_path: Path = config.DB_PATH,
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle GET /api/advanced/<ticker>/<window_start_utc>.
    Returns (status_code, payload_dict).
    """
    view = advanced_mode.get_advanced_view(ticker, window_start_utc, db_path=db_path)
    if view is None:
        return 404, {"error": f"No ticker_window_metrics record for {ticker} at {window_start_utc}"}
    return 200, view


def handle_get_tickers(
    db_path: Path = config.DB_PATH,
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle GET /api/tickers.
    Returns list of distinct tickers with at least one non-null composite score,
    each with its MOST RECENT window's score + verdict_label + simple view.
    """
    conn = storage.get_connection(db_path)
    conn.row_factory = storage.sqlite3.Row

    # Find tickers with at least one non-null composite score
    query_tickers = """
        SELECT DISTINCT ticker FROM ticker_window_metrics
        WHERE composite_score IS NOT NULL
        ORDER BY ticker ASC
    """
    tickers = [r[0] for r in conn.execute(query_tickers).fetchall()]

    landing_items: List[Dict[str, Any]] = []

    for t in tickers:
        most_recent_query = """
            SELECT window_start_utc FROM ticker_window_metrics
            WHERE ticker = ? AND composite_score IS NOT NULL
            ORDER BY window_start_utc DESC
            LIMIT 1
        """
        row = conn.execute(most_recent_query, (t,)).fetchone()
        if row:
            wstart = row[0]
            sview = simple_mode.get_simple_view(t, wstart, db_path=db_path)
            if sview:
                landing_items.append(sview)

    conn.close()
    return 200, {"tickers": landing_items, "total": len(landing_items)}


def handle_get_phylogeny(
    ticker: str,
    db_path: Path = config.DB_PATH,
) -> Tuple[int, Dict[str, Any]]:
    """
    Handle GET /api/phylogeny/<ticker>.
    """
    tree = render_prototype.narrative_phylogeny_tree(ticker, db_path=db_path)
    return 200, tree
