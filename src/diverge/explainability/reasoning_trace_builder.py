"""
reasoning_trace_builder.py

Phase 6: Reasoning Trace Builder.

Builds audit trail records (reasoning_trace) for every ticker_window_metrics row where composite_score IS NOT NULL.
Traces specific posts that drove the metric decisions:
  - 'rn_onset': first_mention posts driving reproduction number onset.
  - 'cassi_sentiment': top sentiment magnitude posts driving cross-asset VAR.
  - 'vdi_divergence': top sentiment posts per language (en / hi-en-mixed).
  - 'cli_capitulation': posts with capitulation_flag = 1.
  - 'duplicate_flag': post pairs crossing similarity threshold from duplicate_pairs.
  - 'sentiment_variance_outlier': posts closest to mean sentiment (unnaturally unanimous).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .. import config, storage, utils

logger = utils.setup_logger("reasoning_trace_builder")


def compute_linear_weights(num_items: int) -> List[float]:
    """Assign weights decaying linearly from 1.0 to 0.5 based on rank."""
    if num_items <= 0:
        return []
    if num_items == 1:
        return [1.0]
    return [round(float(w), 4) for w in np.linspace(1.0, 0.5, num_items)]


def build_traces_for_window(
    metric_row: Dict[str, Any],
    db_path: Path = config.DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Build list of reasoning_trace dicts for a single ticker_window_metrics row.
    """
    ticker = metric_row.get("ticker", "")
    start_utc = metric_row.get("window_start_utc", "")
    end_utc = metric_row.get("window_end_utc")
    dom_index = metric_row.get("dominant_index")
    risk_flags_str = metric_row.get("risk_flags", "[]")
    try:
        risk_flags = json.loads(risk_flags_str) if isinstance(risk_flags_str, str) else risk_flags_str
    except Exception:
        risk_flags = []

    conf_flag = metric_row.get("confidence_flag", "")

    traces: List[Dict[str, Any]] = []
    seen_keys = set()  # avoid duplicate trace insertions for same (post_id, contributed_to)

    def add_trace(pid: str, category: str, w: float):
        if not pid:
            return
        key = (pid, category)
        if key not in seen_keys:
            seen_keys.add(key)
            traces.append({
                "ticker": ticker,
                "window_start_utc": start_utc,
                "post_id": pid,
                "contributed_to": category,
                "weight": w,
            })

    # Fetch raw posts & text features for window
    window_posts = storage.get_text_and_posts_for_window(ticker, start_utc, end_utc, db_path=db_path) or []

    # 1. Dominant Index Tracing
    if dom_index == "rn":
        # Pull posts from post_timing where is_first_mention = True
        timings = storage.get_post_timing_for_ticker(ticker, start_utc, end_utc, db_path=db_path)
        first_mentions = [t for t in timings if t.get("is_first_mention") == 1]
        if first_mentions:
            weights = compute_linear_weights(len(first_mentions))
            for i, fm in enumerate(first_mentions):
                add_trace(fm["post_id"], "rn_onset", weights[i])
        else:
            logger.warning(f"No first_mention posts found for ticker {ticker} in window {start_utc}.")

    elif dom_index == "cassi":
        # Top 10 posts by abs(sentiment_score)
        scored_posts = [p for p in window_posts if p.get("sentiment_score") is not None]
        scored_posts.sort(key=lambda x: abs(x["sentiment_score"]), reverse=True)
        top10 = scored_posts[:10]
        if top10:
            weights = compute_linear_weights(len(top10))
            for i, p in enumerate(top10):
                add_trace(p["post_id"], "cassi_sentiment", weights[i])

    elif dom_index == "vdi":
        # Top 5 posts per language (en / hi-en-mixed)
        en_posts = [p for p in window_posts if p.get("language") == "en" and p.get("sentiment_score") is not None]
        hi_posts = [p for p in window_posts if p.get("language") == "hi-en-mixed" and p.get("sentiment_score") is not None]
        en_posts.sort(key=lambda x: abs(x["sentiment_score"]), reverse=True)
        hi_posts.sort(key=lambda x: abs(x["sentiment_score"]), reverse=True)

        top_en = en_posts[:5]
        top_hi = hi_posts[:5]
        vdi_set = top_en + top_hi
        if vdi_set:
            weights = compute_linear_weights(len(vdi_set))
            for i, p in enumerate(vdi_set):
                add_trace(p["post_id"], "vdi_divergence", weights[i])

    # 2. Risk Flags Tracing
    if "capitulation_signal" in risk_flags:
        # Pull posts with capitulation flag
        cap_posts = [p for p in window_posts if p.get("capitulation_flag") == 1]
        if cap_posts:
            for p in cap_posts:
                add_trace(p["post_id"], "cli_capitulation", 1.0)

    # 3. Low Trust / Moderate Coordination Tracing
    if conf_flag in ("low_trust", "moderate"):
        # Pull post_id pairs from duplicate_pairs
        dup_pairs = storage.get_duplicate_pairs_for_window(ticker, start_utc, db_path=db_path)
        if dup_pairs:
            for pair in dup_pairs:
                add_trace(pair["post_id_a"], "duplicate_flag", 1.0)
                add_trace(pair["post_id_b"], "duplicate_flag", 1.0)
        else:
            logger.warning(f"No duplicate_pairs rows found for {conf_flag} ticker {ticker} in window {start_utc}.")

        # Pull 5 posts closest to window mean sentiment (unnaturally unanimous)
        scored = [p for p in window_posts if p.get("sentiment_score") is not None]
        if len(scored) >= 2:
            mean_sent = float(np.mean([p["sentiment_score"] for p in scored]))
            scored.sort(key=lambda x: abs(x["sentiment_score"] - mean_sent))
            top_outliers = scored[:5]
            weights = compute_linear_weights(len(top_outliers))
            for i, p in enumerate(top_outliers):
                add_trace(p["post_id"], "sentiment_variance_outlier", weights[i])

    return traces

