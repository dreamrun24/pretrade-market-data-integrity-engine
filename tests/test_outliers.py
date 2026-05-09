from __future__ import annotations

import pandas as pd
import pytest

from pipeline.outliers import MAD_SCALE_FACTOR, compute_mad, detect_outliers_mad, modified_z_scores


def test_mad_zero_for_constant_series() -> None:
    assert compute_mad(pd.Series([1.0, 1.0, 1.0])) == pytest.approx(0.0)


def test_modified_z_score_formula() -> None:
    series = pd.Series([1.0, 2.0, 3.0])
    scores = modified_z_scores(series)
    assert scores.iloc[2] == pytest.approx((3.0 - 2.0) / (MAD_SCALE_FACTOR * 1.0))


def test_outlier_correctly_flagged() -> None:
    dates = pd.date_range("2024-01-01", periods=25, freq="B")
    baseline = [0.005, 0.007, 0.009, 0.011, 0.013] * 4
    series = pd.Series(baseline + [0.0, 0.01, 0.02, 0.01, 0.30], index=dates)
    result = detect_outliers_mad(series, window=25, threshold=3.5, min_periods=20)
    assert bool(result["is_outlier"].iloc[-1]) is True
    assert result["n_outliers"] >= 1
