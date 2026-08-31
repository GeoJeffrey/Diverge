"""
render_prototype.py

Phase 6 Data Contract Builders for Phase 7 UI Rendering.

Provides pure JSON/dict structure endpoints:
  - reasoning_trace_panel(): Groups reasoning_trace rows by category with post text previews.
  - narrative_phylogeny_tree(): Builds parent-child lineage tree for a ticker.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config, storage


def reasoning_trace_panel(
    ticker: str,
    window_start_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Dict[str, Any]:
    """
    Return plain JSON structure grouping reasoning_trace items by contributed_to.
    Includes post_id, weight, account_id, platform, upvotes, and raw_text preview (140 chars).
    """
    traces = storage.get_reasoning_traces_for_window(ticker, window_start_utc, db_path=db_path)

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for t in traces:
        cat = t.get("contributed_to", "unknown")
        if cat not in grouped:
            grouped[cat] = []

        raw_text = t.get("raw_text") or ""
        preview = raw_text[:140] + ("..." if len(raw_text) > 140 else "")

        grouped[cat].append({
            "trace_id": t.get("trace_id"),
            "post_id": t.get("post_id"),
            "account_id": t.get("account_id", "anonymous"),
            "platform": t.get("platform", "unknown"),
            "weight": round(float(t.get("weight", 1.0)), 3),
            "upvotes": t.get("upvotes", 0),
            "text_preview": preview,
        })

    return {
        "ticker": ticker.upper(),
        "window_start_utc": window_start_utc,
        "total_traces": len(traces),
        "categories": grouped,
    }


def narrative_phylogeny_tree(
    ticker: str,
    db_path: Path = config.DB_PATH,
) -> Dict[str, Any]:
    """
    Return chronological parent-child narrative phylogeny tree for a ticker.
    Root is the window with parent_window_start_utc IS NULL.
    """
    records = storage.get_narrative_phylogeny_for_ticker(ticker, db_path=db_path)
    if not records:
        return {"ticker": ticker.upper(), "total_nodes": 0, "root": None, "nodes": []}

    nodes: List[Dict[str, Any]] = []
    for r in records:
        try:
            detail = json.loads(r.get("mutation_detail", "{}"))
        except Exception:
            detail = {}

        nodes.append({
            "window_start_utc": r["window_start_utc"],
            "window_end_utc": r.get("window_end_utc"),
            "parent_window_start_utc": r.get("parent_window_start_utc"),
            "mutation_type": r["mutation_type"],
            "mutation_detail": detail,
            "composite_delta": r.get("composite_delta"),
        })

    return {
        "ticker": ticker.upper(),
        "total_nodes": len(nodes),
        "root_window": nodes[0]["window_start_utc"] if nodes else None,
        "nodes": nodes,
    }

