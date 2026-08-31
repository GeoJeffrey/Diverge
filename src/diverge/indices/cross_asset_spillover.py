"""
cassi_index.py

Cross-Asset Sentiment Spillover Index (CASSI) calculation.
Pulls daily average sentiment per ticker via storage.get_multi_ticker_sentiment_series().
Fits statsmodels.tsa.api.VAR across all tracked tickers.
Uses forecast-error variance decomposition (.fevd()) to measure the fraction of ticker i's
sentiment variance attributable to shocks from other tickers j != i.

GUARD: Requires >= 30 daily points across >= 2 tickers, else returns None.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

from .. import config, storage, utils

logger = utils.setup_logger("cassi_index")

MIN_DAILY_POINTS = 30
MIN_TICKERS = 2


def compute_cassi_from_dataframe(df_sentiment: pd.DataFrame, max_lags: int = 2) -> Dict[str, Optional[float]]:
    """
    Compute CASSI for each column (ticker) in a daily sentiment DataFrame.
    df_sentiment: DataFrame indexed by date, columns = tickers, values = float daily avg sentiment.

    Returns dict mapping ticker -> CASSI score (float between 0.0 and 1.0), or None if guard fails.
    """
    results: Dict[str, Optional[float]] = {}
    tickers = list(df_sentiment.columns)

    if len(tickers) < MIN_TICKERS:
        logger.info(f"CASSI GUARD TRIGGERED: Only {len(tickers)} tickers available (< {MIN_TICKERS}). Returning None.")
        for t in tickers:
            results[t] = None
        return results

    # Drop missing rows or fill with forward/backward fill
    clean_df = df_sentiment.ffill().bfill().dropna()

    if len(clean_df) < MIN_DAILY_POINTS:
        logger.info(
            f"CASSI GUARD TRIGGERED: Only {len(clean_df)} daily points (< {MIN_DAILY_POINTS}). Returning None for all."
        )
        for t in tickers:
            results[t] = None
        return results

    try:
        # Check variance of columns
        variances = clean_df.var()
        non_zero_cols = list(variances[variances > 1e-8].index)
        if len(non_zero_cols) < MIN_TICKERS:
            logger.info("CASSI GUARD TRIGGERED: Insufficient variance in sentiment series. Returning None.")
            for t in tickers:
                results[t] = None
            return results

        var_df = clean_df[non_zero_cols]
        # Determine appropriate lag order
        model = VAR(var_df)
        fitted_model = model.fit(maxlags=min(max_lags, len(var_df) // 5 or 1))

        fevd = fitted_model.fevd(periods=5)
        # fevd.decomp is shape (steps, n_eq, n_eq)
        step_idx = min(4, fevd.decomp.shape[0] - 1)
        last_decomp = fevd.decomp[step_idx]

        for idx, col in enumerate(non_zero_cols):
            own_var = last_decomp[idx, idx]
            total_var = np.sum(last_decomp[idx, :])
            other_var = total_var - own_var
            cassi_val = float(other_var / total_var) if total_var > 0 else 0.0
            results[col] = round(max(0.0, min(1.0, cassi_val)), 4)

        for t in tickers:
            if t not in results:
                results[t] = None

    except Exception as e:
        logger.warning(f"VAR model fitting failed for CASSI: {e}. Returning None.")
        for t in tickers:
            results[t] = None

    return results


def compute_cassi(
    tickers: Optional[List[str]] = None,
    window_start_utc: Optional[str] = None,
    window_end_utc: Optional[str] = None,
    db_path: Path = config.DB_PATH,
) -> Dict[str, Optional[float]]:
    """
    Fetch sentiment series for tickers from DB, construct daily matrix, and compute CASSI.
    """
    if tickers is None:
        tickers = list(config.TICKERS.keys())

    raw_series = storage.get_multi_ticker_sentiment_series(
        tickers=tickers,
        start_utc=window_start_utc,
        end_utc=window_end_utc,
        db_path=db_path,
    )

    if not raw_series:
        logger.info("No sentiment data returned from DB for CASSI calculation.")
        return {t: None for t in tickers}

    # Reconstruct combined DataFrame
    all_dates = sorted(list(set(d for series in raw_series.values() for d, _ in series)))
    if len(all_dates) < MIN_DAILY_POINTS:
        logger.info(f"Insufficient total dates ({len(all_dates)} < {MIN_DAILY_POINTS}). CASSI returning None.")
        return {t: None for t in tickers}

    df = pd.DataFrame(index=all_dates)
    for t in tickers:
        series_dict = dict(raw_series.get(t, []))
        df[t] = [series_dict.get(d, np.nan) for d in all_dates]

    return compute_cassi_from_dataframe(df)

