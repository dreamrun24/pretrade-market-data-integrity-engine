from __future__ import annotations

import pytest
import pandas as pd

from pipeline.loader import OHLCV_COLUMNS, build_price_dataframe


def test_build_price_dataframe_correct_columns_index_and_sorting() -> None:
    dates = ["2024-01-03", "2024-01-02"]
    frame = build_price_dataframe(dates, [11, 10], [12, 11], [10, 9], [11, 10], [100, 90])
    assert list(frame.columns) == OHLCV_COLUMNS
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert frame.index.is_monotonic_increasing


def test_build_price_dataframe_lengths_match() -> None:
    with pytest.raises(ValueError):
        build_price_dataframe(["2024-01-02"], [10, 11], [11], [9], [10], [100])
