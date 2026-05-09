from __future__ import annotations

from pipeline.loader import build_price_dataframe
from pipeline.validator import validate_ohlcv


def test_valid_data_passes() -> None:
    frame = build_price_dataframe(["2024-01-02"], [10], [12], [9], [11], [100])
    result = validate_ohlcv(frame)
    assert result["valid"] is True
    assert result["validity_rate"] == 1.0


def test_low_greater_than_open_caught() -> None:
    frame = build_price_dataframe(["2024-01-02"], [10], [12], [11], [11], [100])
    assert validate_ohlcv(frame)["violations"]["low_gt_open"] == 1


def test_negative_volume_caught() -> None:
    frame = build_price_dataframe(["2024-01-02"], [10], [12], [9], [11], [-1])
    assert validate_ohlcv(frame)["violations"]["negative_volume"] == 1


def test_zero_close_caught() -> None:
    frame = build_price_dataframe(["2024-01-02"], [10], [12], [0], [0], [100])
    assert validate_ohlcv(frame)["violations"]["zero_close"] == 1
