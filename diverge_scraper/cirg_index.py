"""
cirg_index.py

Consumer-Investor Rating Gap (CIRG) index calculation.
CIRG = Z(investor sentiment) - Z(consumer review sentiment score).

GUARD: No review data for a ticker -> returns None (null),
logs as "no CIRG coverage for this ticker" (expected for non-consumer-facing names like IT services — not an error).
"""

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from . import config, storage, utils
from .vdi_index import calculate_z_score

logger = utils.setup_logger("cirg_index")


def compute_cirg_from_scores(
    investor_scores: List[float],
    review_scores: List[float],
    investor_baseline: Optional[Tuple[float, float]] = None,
    review_baseline: Optional[Tuple[float, float]] = None,
) -> Optional[float]:
    """
    Calculate CIRG given lists of investor sentiment scores and consumer review sentiment scores.
    Returns None if review_scores is empty.
    """
    if not review_scores:
        logger.info("no CIRG coverage for this ticker (no consumer review data available). Returning None.")
        return None

    if not investor_scores:
        logger.info("No investor sentiment data for this ticker in window. Returning None.")
        return None

    inv_b_mean, inv_b_std = investor_baseline if investor_baseline else (None, None)
    rev_b_mean, rev_b_std = review_baseline if review_baseline else (None, None)

    z_investor = calculate_z_score(investor_scores, inv_b_mean, inv_b_std)
    z_review = calculate_z_score(review_scores, rev_b_mean, rev_b_std)

    cirg_value = round(float(z_investor - z_review), 4)
    return cirg_value


def compute_cirg(
    ticker: str,
    window_start_utc: Optional[str] = None,
    window_end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Optional[float]:
    """
    Fetch investor sentiment from text_features and consumer reviews from consumer_sentiment,
    compute Z-scores, and return CIRG.
    """
    # 1. Fetch consumer review sentiment records
    review_rows = storage.get_consumer_sentiment_for_ticker(
        ticker=ticker,
        start_utc=window_start_utc,
        end_utc=window_end_utc,
        db_path=db_path,
    )
    if not review_rows:
        logger.info(f"no CIRG coverage for this ticker ({ticker}) (no consumer review data available).")
        return None

    review_scores = [float(r["review_sentiment_score"]) for r in review_rows if r.get("review_sentiment_score") is not None]

    # 2. Fetch investor sentiment records
    text_rows = storage.get_text_features_for_window(
        ticker=ticker,
        start_utc=window_start_utc,
        end_utc=window_end_utc,
        db_path=db_path,
    )
    investor_scores = []
    for p in text_rows:
        score = p.get("irony_adjusted_sentiment")
        if score is None:
            score = p.get("sentiment_score")
        if score is not None:
            investor_scores.append(float(score))

    return compute_cirg_from_scores(investor_scores, review_scores)
