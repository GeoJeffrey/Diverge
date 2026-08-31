"""
sentiment_variance.py

Phase 4: Sentiment variance calculator and baseline normalizer.
Computes sample variance of sentiment_score in a window.
Normalizes variance against that ticker's own historical variance baseline so "low"
is relative to what's normal for that specific ticker.

Note: LOW variance indicates suspicious sentiment clustering / coordination.
"""

from typing import List, Optional, Tuple

import numpy as np

from .. import utils

logger = utils.setup_logger("sentiment_variance")


def compute_window_sentiment_variance(scores: List[float]) -> float:
    """
    Compute population/sample variance of sentiment scores in a window.
    Returns float variance >= 0.0.
    """
    if not scores or len(scores) <= 1:
        return 0.0
    arr = np.array(scores, dtype=float)
    return float(np.var(arr))


def normalize_sentiment_variance(
    variance: float, historical_baseline: Optional[Tuple[float, float]] = None
) -> float:
    """
    Normalize raw variance to 0-1 scale relative to ticker's baseline mean and std.
    Returns float in [0.0, 1.0]. Lower values indicate abnormally low variance (suspicious).
    """
    if historical_baseline is None or historical_baseline[1] <= 1e-6:
        # Default scaling assuming standard variance range [0.0, 0.25]
        norm = min(1.0, variance / 0.25)
        return round(float(norm), 4)

    b_mean, b_std = historical_baseline
    z = (variance - b_mean) / b_std
    # Map Z-score to [0, 1] range using sigmoid / min-max
    norm = 1.0 / (1.0 + np.exp(-z))
    return round(float(norm), 4)

