"""
coordination_score.py

Phase 4 Combiner: Integrity / Coordination Score Calculator.

Combines 5 normalized integrity components into a 0-100 coordination score:
  1. ks_component (from periodicity_stats.ks_statistic, normalized 0-1)
  2. acf_component (from periodicity_stats.acf_peak_strength, normalized 0-1)
  3. onset_component (from periodicity_stats.onset_dispersion_index, normalized 0-1)
  4. duplicate_ratio (from duplicate_detection.py, 0-1)
  5. inverted_sentiment_variance (1.0 - normalized_sentiment_variance, 0-1)

CRITICAL CROSS-CHECK:
If a legitimate news event (RSS news / Google Trends) is present in the same window,
dampens onset_component weight from 0.20 to 0.05 to prevent false-positive coordination flags
on real news reactions. Logs this adjustment explicitly for auditability.

GUARD:
If < 20 posts in window -> confidence_flag = 'insufficient_data' and score = 0.0.

CLASSIFICATION:
  - coordination_score >= 70 -> 'low_trust'
  - coordination_score 40-69 -> 'moderate'
  - coordination_score < 40  -> 'high_trust'
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config, storage, utils
from . import duplicate_detection, sentiment_variance

logger = utils.setup_logger("coordination_score")

MIN_POSTS_FOR_TRUST = 20


def normalize_01(val: Optional[float], default_max: float = 1.0) -> float:
    """Normalize a raw float metric to [0.0, 1.0]."""
    if val is None:
        return 0.0
    return max(0.0, min(1.0, float(val) / default_max))


def calculate_coordination_score(
    ks_stat: Optional[float],
    acf_strength: Optional[float],
    onset_dispersion: Optional[float],
    duplicate_ratio: float,
    sentiment_var: float,
    total_posts: int,
    news_event_present: bool = False,
    ticker: str = "",
    window_start: str = "",
) -> Dict[str, Any]:
    """
    Calculate 0-100 coordination score and assign confidence_flag.
    """
    # Guard check for insufficient data
    if total_posts < MIN_POSTS_FOR_TRUST:
        logger.info(f"Trust Guard: < {MIN_POSTS_FOR_TRUST} posts ({total_posts}) in window for {ticker} -> insufficient_data.")
        return {
            "ks_component": normalize_01(ks_stat),
            "acf_component": normalize_01(acf_strength),
            "onset_component": normalize_01(onset_dispersion),
            "duplicate_ratio": round(duplicate_ratio, 4),
            "sentiment_variance": round(sentiment_var, 4),
            "coordination_score": 0.0,
            "confidence_flag": "insufficient_data",
        }

    ks_comp = normalize_01(ks_stat)
    acf_comp = normalize_01(acf_strength)
    onset_comp = normalize_01(onset_dispersion)
    dup_comp = min(1.0, max(0.0, duplicate_ratio))

    norm_var = sentiment_variance.normalize_sentiment_variance(sentiment_var)
    inv_var_comp = max(0.0, min(1.0, 1.0 - norm_var))

    # Weighting logic with news dampening
    if news_event_present:
        logger.info(
            f"[AUDIT] News event present for ticker {ticker} in window {window_start}: "
            "dampening onset_component weight from 0.20 to 0.05."
        )
        w_ks, w_acf, w_onset, w_dup, w_var = 0.2375, 0.2375, 0.05, 0.2375, 0.2375
    else:
        w_ks, w_acf, w_onset, w_dup, w_var = 0.20, 0.20, 0.20, 0.20, 0.20

    combined = (
        w_ks * ks_comp
        + w_acf * acf_comp
        + w_onset * onset_comp
        + w_dup * dup_comp
        + w_var * inv_var_comp
    )
    score_100 = round(float(combined * 100.0), 2)

    # Classification
    if score_100 >= 70.0:
        flag = "low_trust"
    elif score_100 >= 40.0:
        flag = "moderate"
    else:
        flag = "high_trust"

    return {
        "ks_component": round(ks_comp, 4),
        "acf_component": round(acf_comp, 4),
        "onset_component": round(onset_comp, 4),
        "duplicate_ratio": round(dup_comp, 4),
        "sentiment_variance": round(sentiment_var, 4),
        "coordination_score": score_100,
        "confidence_flag": flag,
    }


def compute_coordination_for_window(
    ticker: str,
    window_start_utc: str,
    window_end_utc: str,
    pstat: Optional[Dict[str, Any]] = None,
    db_path: Path = config.DB_PATH,
) -> Dict[str, Any]:
    """
    Fetch posts, duplicate ratio, sentiment variance, periodicity stats, and compute coordination score.
    """
    posts = storage.get_text_and_posts_for_window(ticker, window_start_utc, window_end_utc, db_path=db_path)
    total_posts = len(posts)

    dup_ratio = duplicate_detection.compute_duplicate_ratio(posts)
    scores = [p["sentiment_score"] for p in posts if p.get("sentiment_score") is not None]
    sent_var = sentiment_variance.compute_window_sentiment_variance(scores)

    ks_stat = pstat.get("ks_statistic") if pstat else None
    acf_str = pstat.get("acf_peak_strength") if pstat else None
    onset_disp = pstat.get("onset_dispersion_index") if pstat else None

    has_news = storage.check_news_event_in_window(ticker, window_start_utc, window_end_utc, db_path=db_path)

    res = calculate_coordination_score(
        ks_stat=ks_stat,
        acf_strength=acf_str,
        onset_dispersion=onset_disp,
        duplicate_ratio=dup_ratio,
        sentiment_var=sent_var,
        total_posts=total_posts,
        news_event_present=has_news,
        ticker=ticker,
        window_start=window_start_utc,
    )
    res["ticker"] = ticker
    res["window_start_utc"] = window_start_utc
    res["window_end_utc"] = window_end_utc
    return res

