from __future__ import annotations

import pandas as pd

PRICE_COLUMNS = ["Open", "High", "Low", "Close"]
VOLUME_COLUMN = "Volume"


def detect_gaps(dates: pd.DatetimeIndex, threshold: int = 5) -> list[dict]:
    """Detect calendar gaps between adjacent observations.

    Args:
        dates: DatetimeIndex to inspect.
        threshold: Minimum calendar-day gap to report.

    Returns:
        List of gap dictionaries.

    Raises:
        TypeError: If dates is not a DatetimeIndex.
        ValueError: If threshold is below one.
    """
    if not isinstance(dates, pd.DatetimeIndex):
        raise TypeError("dates must be a pandas DatetimeIndex")
    if threshold < 1:
        raise ValueError("threshold must be positive")
    sorted_dates = pd.DatetimeIndex(dates).sort_values()
    gaps: list[dict] = []
    for previous_date, current_date in zip(sorted_dates[:-1], sorted_dates[1:]):
        calendar_days = int((current_date - previous_date).days)
        if calendar_days >= threshold:
            business_days = len(pd.bdate_range(previous_date, current_date)) - 2
            gaps.append(
                {
                    "start": previous_date,
                    "end": current_date,
                    "calendar_days": calendar_days,
                    "business_days": max(0, int(business_days)),
                }
            )
    return gaps


def forward_fill_prices(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Forward-fill missing prices and zero-fill missing volume.

    Args:
        df: OHLCV DataFrame.

    Returns:
        Filled DataFrame and fill report dictionary.

    Raises:
        TypeError: If df is not a DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    filled = df.copy()
    missing_before = filled[PRICE_COLUMNS + [VOLUME_COLUMN]].isna()
    filled[PRICE_COLUMNS] = filled[PRICE_COLUMNS].ffill()
    filled[VOLUME_COLUMN] = filled[VOLUME_COLUMN].fillna(0)
    audit = build_fill_report(df, filled)
    return filled, {
        "n_values_filled": int(len(audit)),
        "n_rows_with_fills": int(missing_before.any(axis=1).sum()),
        "audit": audit,
    }


def build_fill_report(original: pd.DataFrame, filled: pd.DataFrame) -> pd.DataFrame:
    """Build an audit table of changed values.

    Args:
        original: DataFrame before filling.
        filled: DataFrame after filling.

    Returns:
        Audit DataFrame with date, column, original_value, and new_value.

    Raises:
        ValueError: If shapes or indexes differ.
    """
    if not original.index.equals(filled.index) or list(original.columns) != list(filled.columns):
        raise ValueError("original and filled must have matching index and columns")
    records: list[dict] = []
    for column in original.columns:
        changed = original[column].ne(filled[column]) | (original[column].isna() & filled[column].notna())
        for date in original.index[changed]:
            records.append(
                {
                    "date": date,
                    "column": column,
                    "original_value": original.at[date, column],
                    "new_value": filled.at[date, column],
                }
            )
    return pd.DataFrame.from_records(records, columns=["date", "column", "original_value", "new_value"])
