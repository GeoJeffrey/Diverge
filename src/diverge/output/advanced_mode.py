"""
advanced_mode.py

Phase 7: Advanced Output Mode Engine.

Provides exact, un-prettified technical diagnostic views (get_advanced_view) for any ticker_window_metrics row:
  - Exact index values (rn, cirg, cli, cassi, vdi) + confidence
  - Coordination score & trust flag
  - Reasoning trace audit panel (from Phase 6 render_prototype)
  - Recent narrative phylogeny history context (up to 3 most recent transitions)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .. import config, storage, utils
from ..explainability import render_prototype

logger = utils.setup_logger("advanced_mode")


def get_advanced_view(
    ticker: str,
    window_start_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Generate Advanced Mode technical breakdown dict for a (ticker, window_start_utc) pair.
    Returns None if (ticker, window_start_utc) does not exist in database at all.
    """
    conn = storage.get_connection(db_path)
    conn.row_factory = storage.sqlite3.Row
    if not window_start_utc:
        query = """
            SELECT * FROM ticker_window_metrics
            WHERE ticker = ?
            ORDER BY (composite_score IS NOT NULL) DESC, window_start_utc DESC
            LIMIT 1
        """
        row = conn.execute(query, (ticker.upper(),)).fetchone()
        if row:
            window_start_utc = row["window_start_utc"]
    else:
        query = """
            SELECT * FROM ticker_window_metrics
            WHERE ticker = ? AND window_start_utc = ?
        """
        row = conn.execute(query, (ticker.upper(), window_start_utc)).fetchone()

    if not row:
        conn.close()
        return None

    r = dict(row)

    try:
        risk_flags_raw = r.get("risk_flags", "[]")
        risk_flags = json.loads(risk_flags_raw) if isinstance(risk_flags_raw, str) else (risk_flags_raw or [])
    except Exception:
        risk_flags = []

    # Fetch 3 most recent narrative_phylogeny rows up to and including this window
    phylo_query = """
        SELECT * FROM narrative_phylogeny
        WHERE ticker = ? AND window_start_utc <= ?
        ORDER BY window_start_utc DESC
        LIMIT 3
    """
    phylo_rows = [dict(pr) for pr in conn.execute(phylo_query, (ticker.upper(), window_start_utc)).fetchall()]
    conn.close()

    # Reverse to keep chronological order (oldest to newest among the 3)
    phylo_rows.reverse()
    phylogeny_context = []
    for pr in phylo_rows:
        try:
            detail = json.loads(pr.get("mutation_detail", "{}"))
        except Exception:
            detail = {}
        phylogeny_context.append({
            "window_start_utc": pr["window_start_utc"],
            "mutation_type": pr["mutation_type"],
            "mutation_detail": detail,
            "composite_delta": pr.get("composite_delta"),
        })

    # Pull reasoning trace panel
    trace_panel = render_prototype.reasoning_trace_panel(ticker.upper(), window_start_utc, db_path=db_path)

    return {
        "ticker": ticker.upper(),
        "window_start_utc": window_start_utc,
        "window_end_utc": r.get("window_end_utc"),
        "composite_score": r.get("composite_score"),
        "dominant_index": r.get("dominant_index"),
        "risk_flags": risk_flags,
        "aggregation_confidence": r.get("aggregation_confidence"),
        "indices": {
            "rn": r.get("rn"),
            "rn_confidence": r.get("rn_confidence"),
            "cirg": r.get("cirg"),
            "cli": r.get("cli"),
            "cassi": r.get("cassi"),
            "vdi": r.get("vdi"),
        },
        "coordination": {
            "coordination_score": r.get("coordination_score"),
            "confidence_flag": r.get("confidence_flag"),
        },
        "trace": trace_panel,
        "phylogeny_context": phylogeny_context,
    }

