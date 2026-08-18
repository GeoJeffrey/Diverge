"""
periodicity_analysis.py

Phase 2 Timing Track: Periodicity Analysis
Reads ticker_time_bins and post_timing (populated by timing_features.py).
For each ticker, in rolling 2-hour windows, computes:
  1. KS Test — inter-arrival times vs exponential distribution fit
  2. Autocorrelation (ACF) — peak lag and strength
  3. FFT — dominant frequency in minutes (null if no significant peak)
  4. Onset Dispersion Index — variance-to-mean ratio of first-mentions per sub-bucket

Minimum sample guard: windows with < MIN_POSTS_PER_WINDOW posts are skipped with a warning.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from . import config, storage, utils

logger = utils.setup_logger("periodicity_analysis")

# Configuration
WINDOW_HOURS = 2            # Rolling window size in hours
BIN_MINUTES = 5             # Bin size in minutes (must match ticker_time_bins)
MIN_POSTS_PER_WINDOW = 20   # Minimum posts needed to compute reliable statistics
FFT_NOISE_THRESHOLD = 3.0   # FFT peak must exceed (N * median power) to count as dominant


def _parse_dt(s: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _load_ticker_time_bins(db_path: Path) -> Dict[str, List[Tuple[datetime, int]]]:
    """
    Load all ticker_time_bins rows, grouped by ticker.
    Returns dict: ticker -> sorted list of (bin_start_dt, post_count)
    """
    conn = storage.get_connection(db_path)
    rows = conn.execute(
        "SELECT ticker, bin_start_utc, post_count FROM ticker_time_bins ORDER BY ticker, bin_start_utc"
    ).fetchall()
    conn.close()

    ticker_bins: Dict[str, List[Tuple[datetime, int]]] = {}
    for ticker, bin_start, count in rows:
        dt = _parse_dt(bin_start)
        if dt is None:
            continue
        ticker_bins.setdefault(ticker, []).append((dt, count))
    return ticker_bins


def _load_post_timing_for_ticker(ticker: str, db_path: Path) -> List[Dict[str, Any]]:
    """Load post_timing rows for a given ticker."""
    conn = storage.get_connection(db_path)
    rows = conn.execute(
        """
        SELECT post_id, timestamp_utc, delta_seconds, is_first_mention
        FROM post_timing
        WHERE ticker = ?
        ORDER BY timestamp_utc ASC
        """,
        (ticker,),
    ).fetchall()
    conn.close()
    return [
        {
            "post_id": r[0],
            "timestamp_utc": r[1],
            "delta_seconds": r[2],
            "is_first_mention": r[3],
        }
        for r in rows
    ]


def _compute_ks_statistic(delta_seconds: List[float]) -> Optional[float]:
    """
    Fit exponential distribution to inter-arrival deltas and run KS test.
    Returns KS statistic (0-1), or None on failure.
    Higher value means the arrivals deviate more from a Poisson process (more structured).
    """
    from scipy import stats

    deltas = [d for d in delta_seconds if d is not None and d > 0]
    if len(deltas) < 10:
        return None
    arr = np.array(deltas, dtype=float)
    try:
        loc, scale = stats.expon.fit(arr, floc=0)
        ks_stat, _ = stats.kstest(arr, "expon", args=(loc, scale))
        return round(float(ks_stat), 6)
    except Exception:
        return None


def _compute_acf_peak(series: List[int]) -> Tuple[Optional[float], Optional[float]]:
    """
    Compute autocorrelation (ACF) of binned post-count series.
    Returns (peak_lag_minutes, peak_strength) excluding lag=0.
    """
    from statsmodels.tsa.stattools import acf

    arr = np.array(series, dtype=float)
    if len(arr) < 10 or arr.std() == 0:
        return None, None
    try:
        n_lags = min(len(arr) - 1, 50)
        acf_values = acf(arr, nlags=n_lags, fft=True)
        # Exclude lag 0 (always 1.0)
        acf_abs = np.abs(acf_values[1:])
        peak_lag_idx = int(np.argmax(acf_abs)) + 1  # +1 to map back to real lag
        peak_strength = float(acf_abs[peak_lag_idx - 1])
        peak_lag_minutes = float(peak_lag_idx * BIN_MINUTES)
        return round(peak_lag_minutes, 2), round(peak_strength, 6)
    except Exception:
        return None, None


def _compute_fft_dominant_period(series: List[int]) -> Optional[float]:
    """
    Run FFT on binned post-count series.
    Returns dominant period in minutes if any peak exceeds FFT_NOISE_THRESHOLD * median power.
    Returns None if no clear dominant frequency exists.
    """
    arr = np.array(series, dtype=float)
    if len(arr) < 10 or arr.std() == 0:
        return None
    try:
        # Zero-mean the series
        arr = arr - arr.mean()
        fft_vals = np.fft.rfft(arr)
        power = np.abs(fft_vals) ** 2
        # Exclude DC component (index 0)
        power = power[1:]
        if len(power) == 0:
            return None
        noise_floor = np.median(power)
        if noise_floor == 0:
            return None
        peak_idx = int(np.argmax(power))
        if power[peak_idx] < FFT_NOISE_THRESHOLD * noise_floor:
            return None  # No dominant frequency
        # Convert to period: period = N / (peak_idx+1) bins * BIN_MINUTES
        n = len(arr)
        period_bins = n / (peak_idx + 1)
        period_minutes = period_bins * BIN_MINUTES
        return round(period_minutes, 2)
    except Exception:
        return None


def _compute_onset_dispersion(timing_rows: List[Dict], window_start: datetime, window_end: datetime) -> Optional[float]:
    """
    Compute variance-to-mean ratio (index of dispersion) of first-mention counts
    across BIN_MINUTES sub-buckets within the window.
    Returns None if no first-mentions exist in this window.
    Values well above 1 indicate clustering.
    """
    first_mention_times = []
    for row in timing_rows:
        if row.get("is_first_mention") != 1:
            continue
        dt = _parse_dt(row["timestamp_utc"])
        if dt and window_start <= dt < window_end:
            first_mention_times.append(dt)

    if not first_mention_times:
        return None

    # Build sub-bucket counts
    n_buckets = int((window_end - window_start).total_seconds() / (BIN_MINUTES * 60))
    if n_buckets == 0:
        return None
    counts = np.zeros(n_buckets, dtype=float)
    for dt in first_mention_times:
        bucket_idx = int((dt - window_start).total_seconds() / (BIN_MINUTES * 60))
        bucket_idx = min(bucket_idx, n_buckets - 1)
        counts[bucket_idx] += 1

    mean_count = counts.mean()
    if mean_count == 0:
        return None
    dispersion = float(counts.var() / mean_count)
    return round(dispersion, 6)


def analyse_ticker(ticker: str, bins: List[Tuple[datetime, int]], timing_rows: List[Dict]) -> List[Dict[str, Any]]:
    """
    For a single ticker, compute periodicity statistics in rolling WINDOW_HOURS windows.
    Returns list of dicts for insert_periodicity_stats.
    """
    if not bins:
        return []

    results = []
    all_bin_times = [b[0] for b in bins]
    window_td = timedelta(hours=WINDOW_HOURS)
    bin_td = timedelta(minutes=BIN_MINUTES)

    # Build set of distinct window starts (every BIN_MINUTES across the full range)
    min_time = all_bin_times[0]
    max_time = all_bin_times[-1]

    current_start = min_time
    while current_start + window_td <= max_time + window_td:
        window_end = current_start + window_td

        # Get bins in this window
        window_bins = [(dt, cnt) for dt, cnt in bins if current_start <= dt < window_end]
        total_posts = sum(cnt for _, cnt in window_bins)

        if total_posts < MIN_POSTS_PER_WINDOW:
            logger.debug(
                f"Skipping window {current_start.isoformat()} for {ticker}: "
                f"only {total_posts} posts (need {MIN_POSTS_PER_WINDOW})"
            )
            current_start += bin_td
            continue

        # Build dense count series for this window
        n_slots = int(window_td.total_seconds() / (BIN_MINUTES * 60))
        series = [0] * n_slots
        for bin_dt, cnt in window_bins:
            slot = int((bin_dt - current_start).total_seconds() / (BIN_MINUTES * 60))
            if 0 <= slot < n_slots:
                series[slot] = cnt

        # Get delta_seconds for timing rows in this window
        deltas = []
        for row in timing_rows:
            dt = _parse_dt(row["timestamp_utc"])
            if dt and current_start <= dt < window_end:
                if row["delta_seconds"] is not None:
                    deltas.append(row["delta_seconds"])

        ks_stat = _compute_ks_statistic(deltas) if deltas else None
        acf_lag, acf_strength = _compute_acf_peak(series)
        dominant_freq = _compute_fft_dominant_period(series)
        dispersion = _compute_onset_dispersion(timing_rows, current_start, window_end)

        results.append({
            "ticker": ticker,
            "window_start_utc": current_start.isoformat(),
            "window_end_utc": window_end.isoformat(),
            "ks_statistic": ks_stat,
            "acf_peak_lag_minutes": acf_lag,
            "acf_peak_strength": acf_strength,
            "dominant_frequency_minutes": dominant_freq,
            "onset_dispersion_index": dispersion,
        })

        current_start += bin_td  # slide by one bin

    return results


def run(db_path: Path = config.DB_PATH) -> int:
    """
    Execute periodicity analysis for all tickers.
    Returns count of periodicity_stats rows written.
    """
    logger.info("Starting periodicity analysis...")

    ticker_bins = _load_ticker_time_bins(db_path)
    if not ticker_bins:
        logger.warning("No ticker_time_bins data found. Run timing_features.run() first.")
        return 0

    all_results = []
    for ticker, bins in ticker_bins.items():
        logger.info(f"Analysing periodicity for {ticker} ({len(bins)} bins)...")
        timing_rows = _load_post_timing_for_ticker(ticker, db_path)
        rows = analyse_ticker(ticker, bins, timing_rows)
        logger.info(f"  -> {len(rows)} windows computed for {ticker}.")
        all_results.extend(rows)

    if not all_results:
        logger.warning("No periodicity results computed (insufficient data in all windows).")
        return 0

    new_rows = storage.insert_periodicity_stats(all_results, db_path=db_path)
    logger.info(f"Periodicity analysis complete. {new_rows} rows written to periodicity_stats.")
    return new_rows


if __name__ == "__main__":
    run()
