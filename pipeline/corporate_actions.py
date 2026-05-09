from __future__ import annotations

import pandas as pd

PRICE_COLUMNS = ["Open", "High", "Low", "Close"]
VOLUME_COLUMN = "Volume"


def adjust_for_splits(df: pd.DataFrame, splits: list[dict]) -> pd.DataFrame:
    """Adjust historical prices and volume for stock splits.

    Args:
        df: OHLCV DataFrame.
        splits: List of split events with date and ratio.

    Returns:
        Adjusted DataFrame.

    Raises:
        TypeError: If inputs have invalid types.
        ValueError: If a split ratio is not positive.
    """
    if not isinstance(df, pd.DataFrame) or not isinstance(splits, list):
        raise TypeError("df must be a DataFrame and splits must be a list")
    adjusted = df.copy()
    adjusted[PRICE_COLUMNS + [VOLUME_COLUMN]] = adjusted[PRICE_COLUMNS + [VOLUME_COLUMN]].astype(float)
    for split in sorted(splits, key=lambda item: pd.Timestamp(item["date"])):
        split_date = pd.Timestamp(split["date"])
        ratio = float(split["ratio"])
        if ratio <= 0:
            raise ValueError("split ratio must be positive")
        historical_mask = adjusted.index < split_date
        adjusted.loc[historical_mask, PRICE_COLUMNS] = adjusted.loc[historical_mask, PRICE_COLUMNS] / ratio
        adjusted.loc[historical_mask, VOLUME_COLUMN] = adjusted.loc[historical_mask, VOLUME_COLUMN] * ratio
    return adjusted


def adjust_for_dividends(df: pd.DataFrame, dividends: list[dict]) -> pd.DataFrame:
    """Apply multiplicative dividend adjustments to historical prices.

    Args:
        df: OHLCV DataFrame.
        dividends: List of dividend events with ex_date and amount.

    Returns:
        Adjusted DataFrame.

    Raises:
        TypeError: If inputs have invalid types.
        ValueError: If dividend amount cannot be applied.
    """
    if not isinstance(df, pd.DataFrame) or not isinstance(dividends, list):
        raise TypeError("df must be a DataFrame and dividends must be a list")
    adjusted = df.copy()
    adjusted[PRICE_COLUMNS] = adjusted[PRICE_COLUMNS].astype(float)
    for dividend in sorted(dividends, key=lambda item: pd.Timestamp(item["ex_date"])):
        ex_date = pd.Timestamp(dividend["ex_date"])
        amount = float(dividend["amount"])
        prior_closes = adjusted.loc[adjusted.index < ex_date, "Close"]
        if prior_closes.empty:
            raise ValueError(f"No prior close available before dividend ex-date {ex_date.date()}")
        prior_close = float(prior_closes.iloc[-1])
        if prior_close <= 0 or amount >= prior_close:
            raise ValueError("dividend amount must be less than the prior positive close")
        factor = 1 - (amount / prior_close)
        adjusted.loc[adjusted.index < ex_date, PRICE_COLUMNS] = adjusted.loc[adjusted.index < ex_date, PRICE_COLUMNS] * factor
    return adjusted
