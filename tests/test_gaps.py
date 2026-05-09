from __future__ import annotations

import pandas as pd

from pipeline.gaps import build_fill_report, detect_gaps, forward_fill_prices


def test_seven_day_gap_flagged() -> None:
    gaps = detect_gaps(pd.DatetimeIndex(["2024-01-02", "2024-01-09"]), threshold=5)
    assert len(gaps) == 1
    assert gaps[0]["calendar_days"] == 7


def test_three_day_weekend_not_flagged() -> None:
    gaps = detect_gaps(pd.DatetimeIndex(["2024-01-05", "2024-01-08"]), threshold=5)
    assert gaps == []


def test_fill_report_accuracy_and_volume_zeroed() -> None:
    frame = pd.DataFrame(
        {"Open": [10.0, None], "High": [11.0, None], "Low": [9.0, None], "Close": [10.5, None], "Volume": [100.0, None]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    filled, report = forward_fill_prices(frame)
    audit = build_fill_report(frame, filled)
    assert filled.iloc[1]["Volume"] == 0
    assert report["n_values_filled"] == len(audit)
    assert set(audit["column"]) == {"Open", "High", "Low", "Close", "Volume"}
