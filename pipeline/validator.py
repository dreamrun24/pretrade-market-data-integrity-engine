from __future__ import annotations

import pandas as pd

CHECKS = [
    "low_gt_open",
    "low_gt_close",
    "open_gt_high",
    "close_gt_high",
    "negative_volume",
    "null_close",
    "null_volume",
    "zero_close",
]


def validate_ohlcv(df: pd.DataFrame) -> dict:
    """Validate structural OHLCV constraints.

    Args:
        df: DataFrame containing Open, High, Low, Close, and Volume.

    Returns:
        Validation summary dictionary.

    Raises:
        TypeError: If df is not a DataFrame.
        ValueError: If required columns are missing.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    required_columns = {"Open", "High", "Low", "Close", "Volume"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing_columns)}")

    violations = {
        "low_gt_open": int((df["Low"] > df["Open"]).sum()),
        "low_gt_close": int((df["Low"] > df["Close"]).sum()),
        "open_gt_high": int((df["Open"] > df["High"]).sum()),
        "close_gt_high": int((df["Close"] > df["High"]).sum()),
        "negative_volume": int((df["Volume"] < 0).sum()),
        "null_close": int(df["Close"].isna().sum()),
        "null_volume": int(df["Volume"].isna().sum()),
        "zero_close": int((df["Close"] == 0).sum()),
    }
    n_rows = int(len(df))
    n_violations = int(sum(violations.values()))
    validity_rate = 1.0 if n_rows == 0 else max(0.0, (n_rows - n_violations) / n_rows)
    return {
        "valid": n_violations == 0,
        "n_violations": n_violations,
        "n_rows": n_rows,
        "violations": violations,
        "validity_rate": validity_rate,
    }
