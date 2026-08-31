"""
simple_mode.py

Phase 7: Simple Output Mode Engine.

Provides an accessible, plain-English summary (get_simple_view) for any ticker_window_metrics row:
  - composite_score (0-100 or null)
  - verdict_label ('insufficient_data' / 'fading' [0-35] / 'mixed' [35-65] / 'building' [65-100])
  - why_sentence (templated plain-English explanation based on dominant_index + risk_flags)
  - trust_label (plain-English confidence rating)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from . import config, storage, utils

logger = utils.setup_logger("simple_mode")

TRUST_LABEL_MAP = {
    "high_trust": "High confidence",
    "moderate": "Moderate confidence — treat with caution",
    "low_trust": "Low confidence — possible manipulation detected",
    "insufficient_data": "Not enough data",
}


def get_simple_view(
    ticker: str,
    window_start_utc: str,
    db_path: Path = config.DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Generate Simple Mode summary dict for a (ticker, window_start_utc) pair.
    Returns None if (ticker, window_start_utc) does not exist in database at all.
    """
    conn = storage.get_connection(db_path)
    conn.row_factory = storage.sqlite3.Row
    query = """
        SELECT * FROM ticker_window_metrics
        WHERE ticker = ? AND window_start_utc = ?
    """
    row = conn.execute(query, (ticker.upper(), window_start_utc)).fetchone()
    conn.close()

    if not row:
        return None

    r = dict(row)
    score = r.get("composite_score")
    dom_index = r.get("dominant_index", "insufficient_data")
    conf_flag = r.get("confidence_flag", "insufficient_data")

    try:
        risk_flags_raw = r.get("risk_flags", "[]")
        risk_flags = json.loads(risk_flags_raw) if isinstance(risk_flags_raw, str) else (risk_flags_raw or [])
    except Exception:
        risk_flags = []

    # 1. Guard for NULL composite_score or insufficient_data
    if score is None or dom_index == "insufficient_data":
        return {
            "ticker": ticker.upper(),
            "window_start_utc": window_start_utc,
            "score": None,
            "verdict_label": "insufficient_data",
            "why_sentence": "Not enough data yet for a reliable reading.",
            "trust_label": TRUST_LABEL_MAP.get(conf_flag, "Not enough data"),
        }

    # 2. Verdict Label Bucket
    score_val = float(score)
    if score_val < 35.0:
        verdict_label = "fading"
    elif score_val < 65.0:
        verdict_label = "mixed"
    else:
        verdict_label = "building"

    # 3. Why Sentence Construction
    rn_val = r.get("rn")
    cirg_val = r.get("cirg")
    cli_val = r.get("cli")
    cassi_val = r.get("cassi")
    vdi_val = r.get("vdi")

    if dom_index == "rn":
        rn_str = f" ({rn_val:.2f})" if rn_val is not None else ""
        base_clause = f"Narrative momentum driven by virality rate (Rn{rn_str})."
    elif dom_index == "cassi":
        cassi_str = f" ({cassi_val:.2f})" if cassi_val is not None else ""
        base_clause = f"Cross-asset sentiment spillover (CASSI{cassi_str}) driving retail interest."
    elif dom_index == "vdi":
        vdi_str = f" ({vdi_val:.2f})" if vdi_val is not None else ""
        base_clause = f"Language divergence between English and regional commentary (VDI{vdi_str})."
    else:
        base_clause = f"Narrative score driven by {dom_index} index."

    # Risk Flags clauses
    flag_clauses = []
    if "hype_outrunning_reality" in risk_flags:
        flag_clauses.append("hype currently outrunning consumer reality")
    if "consumer_reality_underpriced" in risk_flags:
        flag_clauses.append("consumer sentiment indicates market may be underpricing reality")
    if "capitulation_signal" in risk_flags:
        flag_clauses.append("capitulation signals detected across social channels")

    if flag_clauses:
        why_sentence = f"{base_clause} — {'; '.join(flag_clauses)}."
    else:
        why_sentence = base_clause

    # 4. Trust Label
    trust_label = TRUST_LABEL_MAP.get(conf_flag, "Moderate confidence — treat with caution")

    return {
        "ticker": ticker.upper(),
        "window_start_utc": window_start_utc,
        "score": round(score_val, 1),
        "verdict_label": verdict_label,
        "why_sentence": why_sentence,
        "trust_label": trust_label,
    }
