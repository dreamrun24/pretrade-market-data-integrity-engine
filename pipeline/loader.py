from __future__ import annotations

from typing import Sequence

import pandas as pd
import yfinance as yf

OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def fetch_ohlcv(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Fetch OHLCV bars from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol.
        period: Yahoo Finance period string.

    Returns:
        DataFrame with timezone-naive DatetimeIndex and OHLCV columns.

    Raises:
        TypeError: If inputs are not strings.
        ValueError: If ticker is empty or no data is returned.
    """
    if not isinstance(ticker, str) or not isinstance(period, str):
        raise TypeError("ticker and period must be strings")
    if not ticker.strip():
        raise ValueError("ticker must be non-empty")

    raw_data = yf.download(ticker.strip().upper(), period=period, progress=False, auto_adjust=False)
    if raw_data.empty:
        raise ValueError(f"No OHLCV data returned for ticker {ticker!r}")
    if isinstance(raw_data.columns, pd.MultiIndex):
        raw_data.columns = raw_data.columns.get_level_values(0)

    missing_columns = [column for column in OHLCV_COLUMNS if column not in raw_data.columns]
    if missing_columns:
        raise ValueError(f"Downloaded data missing columns: {missing_columns}")

    result = raw_data.loc[:, OHLCV_COLUMNS].copy()
    result.index = pd.to_datetime(result.index).tz_localize(None)
    return result.sort_index()


def build_price_dataframe(
    dates: Sequence[object],
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    volumes: Sequence[float],
) -> pd.DataFrame:
    """Build a clean OHLCV DataFrame from arrays.

    Args:
        dates: Date-like values.
        opens: Open prices.
        highs: High prices.
        lows: Low prices.
        closes: Close prices.
        volumes: Volumes.

    Returns:
        Sorted OHLCV DataFrame.

    Raises:
        ValueError: If input lengths differ.
    """
    lengths = {len(dates), len(opens), len(highs), len(lows), len(closes), len(volumes)}
    if len(lengths) != 1:
        raise ValueError("dates, opens, highs, lows, closes, and volumes must have equal lengths")
    frame = pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=pd.to_datetime(dates),
    )
    frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
    return frame.loc[:, OHLCV_COLUMNS].sort_index()
