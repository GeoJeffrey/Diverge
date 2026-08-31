"""
aggregate_composite.py

Phase 5 Aggregation: Composite Score & Narrative Alignment Engine.

Pure functions (no DB I/O, fully unit-testable in isolation).
Collapses Phase 3 indices (Rn, CIRG, CLI, CASSI, VDI) and Phase 4 trust scores
(coordination_score, confidence_flag) into one final composite row per (ticker, window).

Rules:
a) Normalize core narrative strength inputs to -1..1:
   - rn_norm = tanh(2 * (rn - 1.0))
   - cassi_norm = 2 * cassi - 1
   - vdi_norm = clip(vdi / 3.0, -1, 1)
   (Any None stays None; do not substitute 0)

b) Weighted core over available non-null indices (base weights: rn=0.55, cassi=0.30, vdi=0.15):
   core = sum(w_i * norm_i) / sum(w_i for available i)
   dominant_index = available index with largest (w_i * abs(norm_i)).
   If no core index is available -> composite_score = None, dominant_index = 'insufficient_data',
   risk_flags = '[]', aggregation_confidence = 'insufficient_data'.

c) Modifiers (CIRG & CLI):
   - if cirg > 1.5: risk_flags += 'hype_outrunning_reality'; core -= 0.10
   - if cirg < -1.5: risk_flags += 'consumer_reality_underpriced' (informational only, NO score change)
   - if cli > 0.5: risk_flags += 'capitulation_signal'; core -= 0.15 * cli
   (CRITICAL: CIRG & CLI only pull core DOWN, never up)

d) Map to 0-100 and dampen toward 50 (neutral) by confidence_flag:
   raw_0_100 = 50 + 50 * clip(core, -1, 1)
   multiplier = {'high_trust': 1.0, 'moderate': 0.7, 'low_trust': 0.4, 'insufficient_data': 0.0}
   composite_score = round(50 + (raw_0_100 - 50) * multiplier, 1)
   (CRITICAL: if confidence_flag == 'insufficient_data', force composite_score = None)
"""

import json
import math
from typing import Any, Dict, List, Optional


def aggregate_composite_row(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure aggregation function taking a dict of raw index_values and coordination_scores.
    Returns dict ready for insertion into ticker_window_metrics table.
    """
    ticker = input_data.get("ticker", "")
    window_start_utc = input_data.get("window_start_utc", "")
    window_end_utc = input_data.get("window_end_utc")

    rn = input_data.get("rn")
    rn_confidence = input_data.get("rn_confidence")
    cirg = input_data.get("cirg")
    cli = input_data.get("cli")
    cassi = input_data.get("cassi")
    vdi = input_data.get("vdi")

    coordination_score = input_data.get("coordination_score")
    confidence_flag = input_data.get("confidence_flag", "insufficient_data")
    if confidence_flag is None:
        confidence_flag = "high_trust" if (rn is not None or cassi is not None or vdi is not None) else "insufficient_data"

    # ── Step a: Normalize core narrative inputs (-1..1) ─────────────────
    rn_norm = math.tanh(2.0 * (rn - 1.0)) if (rn is not None) else None
    cassi_norm = (2.0 * cassi - 1.0) if (cassi is not None) else None
    vdi_norm = max(-1.0, min(1.0, vdi / 3.0)) if (vdi is not None) else None

    # ── Step b: Weighted Core Calculation ──────────────────────────────
    base_weights = {"rn": 0.55, "cassi": 0.30, "vdi": 0.15}
    norms = {"rn": rn_norm, "cassi": cassi_norm, "vdi": vdi_norm}

    available = {k: norm for k, norm in norms.items() if norm is not None}

    if not available:
        # NO core index is available -> stop here!
        return {
            "ticker": ticker,
            "window_start_utc": window_start_utc,
            "window_end_utc": window_end_utc,
            "rn": rn,
            "rn_confidence": rn_confidence,
            "cirg": cirg,
            "cli": cli,
            "cassi": cassi,
            "vdi": vdi,
            "coordination_score": coordination_score,
            "confidence_flag": confidence_flag,
            "composite_score": None,
            "dominant_index": "insufficient_data",
            "risk_flags": json.dumps([]),
            "aggregation_confidence": "insufficient_data",
        }

    sum_weights = sum(base_weights[k] for k in available)
    core = sum(base_weights[k] * norm for k, norm in available.items()) / sum_weights

    # Dominant Index Selection with Deterministic Tie-Breaking:
    # We rank candidates by (weight_i * abs(norm_i)).
    # TIE-BREAKING RULE: If two indices have identical weighted magnitude (w_i * abs(norm_i)),
    # we break ties deterministically by highest base weight rank ('rn' > 'cassi' > 'vdi').
    ranked_candidates = []
    for k, norm in available.items():
        w_mag = base_weights[k] * abs(norm)
        # Sort key: primary = weighted magnitude, secondary = base weight
        ranked_candidates.append((w_mag, base_weights[k], k))

    ranked_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    dominant_index = ranked_candidates[0][2]

    # ── Step c: Apply CIRG & CLI Modifiers ───────────────────────────────
    risk_flags: List[str] = []

    if cirg is not None:
        if cirg > 1.5:
            risk_flags.append("hype_outrunning_reality")
            core -= 0.10
        elif cirg < -1.5:
            risk_flags.append("consumer_reality_underpriced")
            # Informational flag only — NO core score adjustment!

    if cli is not None and cli > 0.5:
        risk_flags.append("capitulation_signal")
        core -= 0.15 * cli
        # CIRG & CLI only ever pull core DOWN, never up.

    # ── Step d: Map to 0-100 & Dampen by confidence_flag ───────────────
    # If confidence_flag is 'insufficient_data', force composite_score = None
    if confidence_flag == "insufficient_data":
        composite_score = None
    else:
        raw_0_100 = 50.0 + 50.0 * max(-1.0, min(1.0, core))
        multiplier_map = {
            "high_trust": 1.0,
            "moderate": 0.7,
            "low_trust": 0.4,
            "insufficient_data": 0.0,
        }
        multiplier = multiplier_map.get(confidence_flag, 1.0)
        composite_score = round(50.0 + (raw_0_100 - 50.0) * multiplier, 1)

    return {
        "ticker": ticker,
        "window_start_utc": window_start_utc,
        "window_end_utc": window_end_utc,
        "rn": rn,
        "rn_confidence": rn_confidence,
        "cirg": cirg,
        "cli": cli,
        "cassi": cassi,
        "vdi": vdi,
        "coordination_score": coordination_score,
        "confidence_flag": confidence_flag,
        "composite_score": composite_score,
        "dominant_index": dominant_index,
        "risk_flags": json.dumps(risk_flags),
        "aggregation_confidence": confidence_flag,
    }
