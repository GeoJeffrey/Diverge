"""
rn_index.py

Effective Reproduction Number Index (Rn) calculation.

Bins post_timing's is_first_mention flag into a per-ticker daily onset series
(count of new distinct posters per day). Estimates:
  - beta: transmission rate (growth rate of new onset users relative to active users).
  - gamma: decay/recovery rate derived from historical onset spike shapes (or default 0.20 if sparse).
Rn = beta / gamma.

NOTE & DISCLAIMER:
This is a lightweight viral transmission approximation using linear/exponential growth ratios,
NOT a full epidemiological serial-interval compartmental model fitting.

GUARD: Needs >= 7 distinct days of data for that ticker, else returns (None, 0.0).
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import config, storage, utils

logger = utils.setup_logger("rn_index")

MIN_DISTINCT_DAYS = 7
DEFAULT_GAMMA_DECAY = 0.20  # default 5-day narrative decay rate approximation


def compute_rn_from_onset_counts(daily_onsets: List[int]) -> Tuple[Optional[float], Optional[float]]:
    """
    Compute Rn and confidence score given an ordered list of daily new-onset poster counts.
    Returns (rn_value, confidence_score) or (None, 0.0) if guard fails.
    """
    if len(daily_onsets) < MIN_DISTINCT_DAYS:
        logger.info(
            f"Rn GUARD TRIGGERED: Only {len(daily_onsets)} distinct days of data (< {MIN_DISTINCT_DAYS}). Returning None."
        )
        return (None, 0.0)

    onsets = np.array(daily_onsets, dtype=float)
    if np.all(onsets == 0):
        return (0.0, 1.0)

    # Calculate transmission rate (beta) from average consecutive growth ratios
    prev_active = np.maximum(onsets[:-1], 1.0)
    next_onsets = onsets[1:]
    growth_ratios = next_onsets / prev_active
    beta = float(np.mean(growth_ratios))

    # Calculate decay rate (gamma) from historical peak-to-trough drops if available
    peak_diffs = np.diff(onsets)
    negative_diffs = -peak_diffs[peak_diffs < 0]

    if len(negative_diffs) > 0 and np.mean(onsets) > 0:
        gamma = float(np.mean(negative_diffs) / (np.mean(onsets) + 1e-5))
        gamma = max(0.05, min(1.0, gamma))
        confidence = 1.0
    else:
        gamma = DEFAULT_GAMMA_DECAY
        confidence = 0.5  # lower confidence due to default gamma fallback

    rn_value = round(float(beta / gamma), 4) if gamma > 0 else 0.0
    return (rn_value, confidence)


def compute_rn(
    ticker: str,
    window_start_utc: Optional[str] = None,
    window_end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Fetch timing records from DB for ticker, build daily onset count series, and return (Rn, confidence).
    """
    rows = storage.get_post_timing_for_ticker(
        ticker=ticker,
        start_utc=window_start_utc,
        end_utc=window_end_utc,
        db_path=db_path,
    )
    if not rows:
        logger.info(f"No post_timing rows for ticker {ticker} -> Rn is (None, 0.0).")
        return (None, 0.0)

    # Group first-mentions by date string 'YYYY-MM-DD'
    daily_counts: Dict[str, int] = {}
    for r in rows:
        if r.get("is_first_mention") == 1:
            date_str = str(r.get("timestamp_utc", ""))[:10]
            if date_str:
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

    sorted_dates = sorted(daily_counts.keys())
    daily_onsets = [daily_counts[d] for d in sorted_dates]

    return compute_rn_from_onset_counts(daily_onsets)
