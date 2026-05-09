from __future__ import annotations

import numpy as np
import pytest

from pipeline.loader import build_price_dataframe
from pipeline.returns import TRADING_DAYS_PER_YEAR, add_log_returns, add_realized_vol, add_simple_returns


def test_simple_and_log_returns_formulas_and_first_nan() -> None:
    frame = build_price_dataframe(["2024-01-02", "2024-01-03"], [10, 12], [11, 13], [9, 11], [10, 12], [100, 110])
    frame = add_simple_returns(frame)
    frame = add_log_returns(frame)
    assert np.isnan(frame["simple_return"].iloc[0])
    assert frame["simple_return"].iloc[1] == pytest.approx(0.2)
    assert frame["log_return"].iloc[1] == pytest.approx(np.log(1.2))


def test_realized_vol_std_times_sqrt_252() -> None:
    frame = build_price_dataframe(range(1, 5), [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 2, 4, 8], [1, 1, 1, 1])
    frame = add_log_returns(frame)
    frame = add_realized_vol(frame, windows=[2])
    expected = frame["log_return"].iloc[2:4].std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert frame["realized_vol_2d"].iloc[3] == pytest.approx(expected)
