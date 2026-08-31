"""
vdi_index.py

Vernacular Divergence Index (VDI) calculation.
Splits text_features sentiment by language ('en' vs 'hi-en-mixed').
Computes Z-score of English sentiment vs baseline and Z-score of Hinglish sentiment vs baseline.
VDI = Z(english) - Z(hinglish).

GUARD: If <20 posts in either language group for that window -> return None (null),
log why (Hinglish volume is a known bottleneck).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .. import config, storage, utils

logger = utils.setup_logger("vdi_index")

MIN_POSTS_PER_LANG = 20


def calculate_z_score(
    scores: List[float], baseline_mean: Optional[float] = None, baseline_std: Optional[float] = None
) -> float:
    """
    Calculate Z-score for a group of sentiment scores against historical/group baseline.
    If baseline parameters are not provided, uses the sample mean and sample std.
    """
    if not scores:
        return 0.0

    arr = np.array(scores, dtype=float)
    current_mean = float(np.mean(arr))

    if baseline_mean is None:
        baseline_mean = current_mean
    if baseline_std is None or baseline_std <= 1e-6:
        baseline_std = float(np.std(arr)) if len(arr) > 1 else 0.0

    if baseline_std <= 1e-6:
        return 0.0

    return (current_mean - baseline_mean) / baseline_std


def compute_vdi_from_scores(
    en_scores: List[float],
    hinglish_scores: List[float],
    en_baseline: Optional[Tuple[float, float]] = None,
    hinglish_baseline: Optional[Tuple[float, float]] = None,
) -> Optional[float]:
    """
    Compute VDI given explicit lists of English and Hinglish sentiment scores.
    Returns float or None if either language has < MIN_POSTS_PER_LANG scores.
    """
    if len(en_scores) < MIN_POSTS_PER_LANG:
        logger.info(
            f"VDI GUARD TRIGGERED: Insufficient English posts count ({len(en_scores)} < {MIN_POSTS_PER_LANG}). "
            "Returning None."
        )
        return None

    if len(hinglish_scores) < MIN_POSTS_PER_LANG:
        logger.info(
            f"VDI GUARD TRIGGERED: Insufficient Hinglish posts count ({len(hinglish_scores)} < {MIN_POSTS_PER_LANG}). "
            "Hinglish volume is the known bottleneck. Returning None."
        )
        return None

    en_b_mean, en_b_std = en_baseline if en_baseline else (None, None)
    hi_b_mean, hi_b_std = hinglish_baseline if hinglish_baseline else (None, None)

    z_en = calculate_z_score(en_scores, en_b_mean, en_b_std)
    z_hinglish = calculate_z_score(hinglish_scores, hi_b_mean, hi_b_std)

    vdi_value = round(float(z_en - z_hinglish), 4)
    return vdi_value


def compute_vdi(
    ticker: str,
    window_start_utc: Optional[str] = None,
    window_end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Optional[float]:
    """
    Fetch posts for (ticker, window) from DB, separate by language, enforce <20 guard, and return VDI.
    """
    posts = storage.get_text_features_for_window(
        ticker=ticker,
        start_utc=window_start_utc,
        end_utc=window_end_utc,
        db_path=db_path,
    )
    if not posts:
        logger.info(f"No posts found for ticker {ticker} -> VDI is None.")
        return None

    en_scores = []
    hinglish_scores = []

    for p in posts:
        lang = p.get("language", "en")
        score = p.get("irony_adjusted_sentiment")
        if score is None:
            score = p.get("sentiment_score", 0.0)

        if lang in ("en", "english"):
            en_scores.append(float(score))
        elif lang in ("hi-en-mixed", "hinglish", "hi"):
            hinglish_scores.append(float(score))

    return compute_vdi_from_scores(en_scores, hinglish_scores)

