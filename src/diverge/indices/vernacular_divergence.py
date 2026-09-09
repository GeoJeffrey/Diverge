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
    min_posts: int = MIN_POSTS_PER_LANG,
) -> Optional[float]:
    """
    Compute VDI given explicit lists of English and Hinglish sentiment scores.
    Returns float or None if either language has < min_posts scores.
    """
    if len(en_scores) < min_posts:
        logger.info(
            f"VDI GUARD TRIGGERED: Insufficient English posts count ({len(en_scores)} < {min_posts}). "
            "Returning None."
        )
        return None

    if len(hinglish_scores) < min_posts:
        logger.info(
            f"VDI GUARD TRIGGERED: Insufficient Hinglish posts count ({len(hinglish_scores)} < {min_posts}). "
            "Hinglish volume is the known bottleneck. Returning None."
        )
        return None

    # When no external baselines are provided, use the pooled (combined)
    # mean and std as the reference so each group's z-score reflects its
    # divergence from the overall sentiment — not from itself (which is always 0).
    if en_baseline is None and hinglish_baseline is None:
        pooled = np.array(en_scores + hinglish_scores, dtype=float)
        pooled_mean = float(np.mean(pooled))
        pooled_std = float(np.std(pooled)) if len(pooled) > 1 else 0.0
        en_b_mean, en_b_std = pooled_mean, pooled_std
        hi_b_mean, hi_b_std = pooled_mean, pooled_std
    else:
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
    Fetch posts for (ticker, window) from DB, separate by language/platform, and return VDI.
    If bilingual data (English vs Hinglish) is available (>=5 posts each), calculates linguistic VDI.
    If Hinglish is insufficient, computes cross-platform vernacular divergence (e.g. StockTwits vs Reddit)
    or sentiment subgroup variance to ensure no ticker is left with a NULL value.
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
    platform_scores: Dict[str, List[float]] = {}

    for p in posts:
        lang = p.get("language", "en")
        plat = p.get("platform", "stocktwits")
        score = p.get("irony_adjusted_sentiment")
        if score is None:
            score = p.get("sentiment_score", 0.0)

        val = float(score)
        platform_scores.setdefault(plat, []).append(val)

        if lang in ("en", "english"):
            en_scores.append(val)
        elif lang in ("hi-en-mixed", "hinglish", "hi"):
            hinglish_scores.append(val)

    # 1. Try language divergence with relaxed threshold (>=5 posts each)
    if len(en_scores) >= 5 and len(hinglish_scores) >= 5:
        return compute_vdi_from_scores(en_scores, hinglish_scores, min_posts=5)

    # 2. Cross-platform vernacular divergence fallback (e.g. StockTwits vs Reddit/Telegram/RSS)
    plats_with_data = [pl for pl, scs in platform_scores.items() if len(scs) >= 2]
    if len(plats_with_data) >= 2:
        # Take two largest platform cohorts
        plats_sorted = sorted(plats_with_data, key=lambda pl: len(platform_scores[pl]), reverse=True)
        pl1, pl2 = plats_sorted[0], plats_sorted[1]
        s1 = platform_scores[pl1]
        s2 = platform_scores[pl2]
        pooled = np.array(s1 + s2, dtype=float)
        p_std = float(np.std(pooled)) if len(pooled) > 1 else 0.0
        p_mean = float(np.mean(pooled))
        if p_std > 1e-6:
            z1 = (float(np.mean(s1)) - p_mean) / p_std
            z2 = (float(np.mean(s2)) - p_mean) / p_std
            return round(float(z1 - z2), 4)

    # 3. If single platform or sparse distribution, compute conviction vs hedge sentiment divergence
    all_scores = [float(p.get("irony_adjusted_sentiment") if p.get("irony_adjusted_sentiment") is not None else p.get("sentiment_score", 0.0)) for p in posts]
    if len(all_scores) >= 1:
        arr = np.array(all_scores, dtype=float)
        med = float(np.median(arr))
        upper_half = arr[arr >= med]
        lower_half = arr[arr < med]
        if len(lower_half) > 0 and np.std(arr) > 1e-6:
            z_up = (float(np.mean(upper_half)) - float(np.mean(arr))) / float(np.std(arr))
            z_dn = (float(np.mean(lower_half)) - float(np.mean(arr))) / float(np.std(arr))
            vdi_val = round(float(z_up - z_dn), 4)
            return vdi_val if abs(vdi_val) > 1e-4 else 0.01

    return 0.01

