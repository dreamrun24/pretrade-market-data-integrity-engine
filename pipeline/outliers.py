from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_WINDOW = 63
DEFAULT_THRESHOLD = 3.5
MAD_SCALE_FACTOR = 1.4826


def compute_mad(series: pd.Series) -> float:
    """Compute median absolute deviation.

    Args:
        series: Numeric series.

    Returns:
        Median absolute deviation.

    Raises:
        TypeError: If series is not a Series.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")
    clean_series = series.dropna()
    if clean_series.empty:
        return 0.0
    median_value = clean_series.median()
    return float((clean_series - median_value).abs().median())


def modified_z_scores(series: pd.Series) -> pd.Series:
    """Compute MAD-based modified z-scores.

    Args:
        series: Numeric series.

    Returns:
        Series of modified z-scores.

    Raises:
        TypeError: If series is not a Series.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")
    median_value = series.median()
    mad_value = compute_mad(series)
    if mad_value == 0 or np.isnan(mad_value):
        return pd.Series(0.0, index=series.index)
    return (series - median_value) / (MAD_SCALE_FACTOR * mad_value)


def detect_outliers_mad(
    returns: pd.Series,
    window: int = DEFAULT_WINDOW,
    threshold: float = DEFAULT_THRESHOLD,
    min_periods: int = 20,
) -> dict:
    """Detect rolling MAD-based outliers.

    Args:
        returns: Return series.
        window: Rolling window length.
        threshold: Absolute modified z-score threshold.
        min_periods: Minimum observations per rolling window.

    Returns:
        Detection dictionary with scores and flags.

    Raises:
        TypeError: If returns is not a Series.
        ValueError: If parameters are invalid.
    """
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series")
    if window <= 0 or min_periods <= 0 or threshold <= 0:
        raise ValueError("window, threshold, and min_periods must be positive")

    modified_z = pd.Series(0.0, index=returns.index, dtype=float)
    for end_position in range(len(returns)):
        start_position = max(0, end_position - window + 1)
        rolling_values = returns.iloc[start_position : end_position + 1].dropna()
        if len(rolling_values) >= min_periods:
            current_window_scores = modified_z_scores(rolling_values)
            modified_z.iloc[end_position] = float(current_window_scores.iloc[-1])
    is_outlier = modified_z.abs() > threshold
    outlier_dates = pd.DatetimeIndex(returns.index[is_outlier])
    return {
        "modified_z": modified_z,
        "is_outlier": is_outlier,
        "n_outliers": int(is_outlier.sum()),
        "outlier_dates": outlier_dates,
    }
