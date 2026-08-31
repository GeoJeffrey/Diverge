"""
phylogeny_builder.py

Phase 6: Narrative Phylogeny Builder.

Tracks how narrative focus and metrics evolve from window to window for each ticker.
For each ticker, orders ticker_window_metrics rows chronologically and evaluates transitions:
  - 'composite_reversal': composite_score crossed 50 in either direction (> 50 to <= 50 or vice versa).
  - 'dominant_index_shift': dominant_index changed.
  - 'new_risk_flag': risk_flag present now that wasn't in previous window.
  - 'flag_resolved': risk_flag present before but gone now.
  - 'stable': no major structural changes.

Priority Order for multiple conditions:
  composite_reversal > dominant_index_shift > new_risk_flag > flag_resolved > stable.
Lower priority mutations are preserved inside mutation_detail under an 'also' key.
Skips null/insufficient_data windows when determining the parent window (gap skipping).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config, storage, utils

logger = utils.setup_logger("phylogeny_builder")


def build_phylogeny_for_ticker(
    ticker: str,
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Build narrative_phylogeny rows for a single ticker across all valid metrics windows.
    """
    conn = storage.get_connection(db_path)
    conn.row_factory = storage.sqlite3.Row
    query = """
        SELECT * FROM ticker_window_metrics
        WHERE ticker = ?
        ORDER BY window_start_utc ASC
    """
    rows = [dict(r) for r in conn.execute(query, (ticker.upper(),)).fetchall()]
    conn.close()

    # Filter only windows with valid non-null composite_score
    valid_rows = [r for r in rows if r.get("composite_score") is not None]
    if not valid_rows:
        return []

    phylogeny_records: List[Dict[str, Any]] = []

    # First valid window is the root (parent_window_start_utc = None)
    root = valid_rows[0]
    phylogeny_records.append({
        "ticker": ticker.upper(),
        "window_start_utc": root["window_start_utc"],
        "window_end_utc": root.get("window_end_utc"),
        "parent_window_start_utc": None,
        "mutation_type": "stable",
        "mutation_detail": json.dumps({"root": True, "dominant": root.get("dominant_index")}),
        "composite_delta": 0.0,
    })

    # Compare consecutive valid windows (gap-skipping built in by using valid_rows)
    for i in range(1, len(valid_rows)):
        prev = valid_rows[i - 1]
        curr = valid_rows[i]

        prev_score = float(prev["composite_score"])
        curr_score = float(curr["composite_score"])
        delta = round(curr_score - prev_score, 1)

        prev_dom = prev.get("dominant_index", "")
        curr_dom = curr.get("dominant_index", "")

        prev_flags_str = prev.get("risk_flags", "[]")
        curr_flags_str = curr.get("risk_flags", "[]")
        try:
            prev_flags = set(json.loads(prev_flags_str) if isinstance(prev_flags_str, str) else prev_flags_str)
        except Exception:
            prev_flags = set()

        try:
            curr_flags = set(json.loads(curr_flags_str) if isinstance(curr_flags_str, str) else curr_flags_str)
        except Exception:
            curr_flags = set()

        new_flags = list(curr_flags - prev_flags)
        resolved_flags = list(prev_flags - curr_flags)

        # Detect mutation conditions
        is_reversal = (prev_score > 50.0 and curr_score <= 50.0) or (prev_score <= 50.0 and curr_score > 50.0)
        is_dom_shift = (prev_dom != curr_dom)
        is_new_flag = len(new_flags) > 0
        is_flag_resolved = len(resolved_flags) > 0

        mutations: List[Tuple[str, Dict[str, Any]]] = []

        if is_reversal:
            mutations.append(("composite_reversal", {"from_score": prev_score, "to_score": curr_score}))
        if is_dom_shift:
            mutations.append(("dominant_index_shift", {"from": prev_dom, "to": curr_dom}))
        if is_new_flag:
            mutations.append(("new_risk_flag", {"flags_added": new_flags}))
        if is_flag_resolved:
            mutations.append(("flag_resolved", {"flags_removed": resolved_flags}))

        if not mutations:
            primary_mutation = "stable"
            detail = {"status": "stable"}
        else:
            primary_mutation = mutations[0][0]
            detail = mutations[0][1]
            if len(mutations) > 1:
                detail["also"] = [{"type": m[0], "detail": m[1]} for m in mutations[1:]]

        phylogeny_records.append({
            "ticker": ticker.upper(),
            "window_start_utc": curr["window_start_utc"],
            "window_end_utc": curr.get("window_end_utc"),
            "parent_window_start_utc": prev["window_start_utc"],
            "mutation_type": primary_mutation,
            "mutation_detail": json.dumps(detail),
            "composite_delta": delta,
        })

    return phylogeny_records
