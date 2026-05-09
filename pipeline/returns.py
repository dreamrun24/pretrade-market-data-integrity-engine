from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def add_simple_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add simple returns from close prices.

    Args:
        df: DataFrame with Close column.

    Returns:
        Copy of df with simple_return column.

    Raises:
        ValueError: If Close column is missing.
    """
    if "Close" not in df.columns:
        raise ValueError("df must contain Close column")
    result = df.copy()
    result["simple_return"] = (result["Close"] / result["Close"].shift(1)) - 1
    return result


def add_log_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add log returns from close prices.

    Args:
        df: DataFrame with Close column.

    Returns:
        Copy of df with log_return column.

    Raises:
        ValueError: If Close column is missing.
    """
    if "Close" not in df.columns:
        raise ValueError("df must contain Close column")
    result = df.copy()
    result["log_return"] = np.log(result["Close"] / result["Close"].shift(1))
    return result


def add_realized_vol(df: pd.DataFrame, windows: list[int] | None = None) -> pd.DataFrame:
    """Add annualised rolling realized volatility columns.

    Args:
        df: DataFrame with log_return column.
        windows: Rolling windows in trading days.

    Returns:
        Copy of df with realized volatility columns.

    Raises:
        ValueError: If log_return is missing or windows are invalid.
    """
    if "log_return" not in df.columns:
        raise ValueError("df must contain log_return column")
    windows = [20, 60] if windows is None else windows
    if any(window <= 0 for window in windows):
        raise ValueError("windows must be positive")
    result = df.copy()
    for window in windows:
        result[f"realized_vol_{window}d"] = (
            result["log_return"].rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        )
    return result
