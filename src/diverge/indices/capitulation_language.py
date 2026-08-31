"""
cli_index.py

Capitulation Leak Index (CLI) calculation.
CLI = (posts where capitulation_flag = 1) / (total posts mentioning ticker in window).

Returns None (null) on empty window / zero post volume, logged gracefully.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config, storage, utils

logger = utils.setup_logger("cli_index")


def compute_cli_for_posts(posts: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calculate CLI ratio from a list of post feature dictionaries.
    Each dict should contain at least: 'capitulation_flag' (0 or 1).
    Returns float ratio in [0.0, 1.0], or None if list is empty.
    """
    if not posts:
        logger.info("CLI calculation window has 0 posts -> returning None (null).")
        return None

    cap_count = sum(1 for p in posts if p.get("capitulation_flag") == 1)
    total_count = len(posts)

    if total_count == 0:
        return None

    cli_value = round(cap_count / total_count, 4)
    return cli_value


def compute_cli(
    ticker: str,
    window_start_utc: Optional[str] = None,
    window_end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Optional[float]:
    """
    Fetch text features from DB for (ticker, window) and return computed CLI value.
    """
    posts = storage.get_text_features_for_window(
        ticker=ticker,
        start_utc=window_start_utc,
        end_utc=window_end_utc,
        db_path=db_path,
    )
    if not posts:
        logger.info(f"No posts found for ticker {ticker} in window -> CLI is None.")
        return None

    return compute_cli_for_posts(posts)

