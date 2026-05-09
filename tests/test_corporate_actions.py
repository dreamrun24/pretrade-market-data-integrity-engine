from __future__ import annotations

import pytest

from pipeline.corporate_actions import adjust_for_dividends, adjust_for_splits
from pipeline.loader import build_price_dataframe


def test_two_for_one_split_halves_prices_and_doubles_volume_before_date() -> None:
    frame = build_price_dataframe(["2024-01-02", "2024-01-03"], [100, 50], [110, 55], [90, 45], [100, 50], [1000, 2000])
    adjusted = adjust_for_splits(frame, [{"date": "2024-01-03", "ratio": 2.0}])
    assert adjusted.iloc[0]["Close"] == pytest.approx(50.0)
    assert adjusted.iloc[0]["Volume"] == pytest.approx(2000.0)
    assert adjusted.iloc[1]["Close"] == pytest.approx(50.0)


def test_dividend_factor_formula() -> None:
    frame = build_price_dataframe(["2024-01-02", "2024-01-03"], [100, 99], [101, 100], [99, 98], [100, 99], [1000, 1000])
    adjusted = adjust_for_dividends(frame, [{"ex_date": "2024-01-03", "amount": 1.0}])
    assert adjusted.iloc[0]["Close"] == pytest.approx(99.0)
    assert adjusted.iloc[1]["Close"] == pytest.approx(99.0)
