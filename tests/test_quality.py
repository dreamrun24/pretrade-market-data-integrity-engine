from __future__ import annotations

import pytest

from pipeline.quality import compute_quality_score


def test_grade_boundaries() -> None:
    assert compute_quality_score(1.0, 1.0, 0.99)["grade"] == "A"
    assert compute_quality_score(1.0, 1.0, 0.95)["grade"] == "B"
    assert compute_quality_score(1.0, 1.0, 0.90)["grade"] == "C"
    assert compute_quality_score(1.0, 1.0, 0.89)["grade"] == "F"


def test_overall_is_product_not_average() -> None:
    result = compute_quality_score(0.9, 0.9, 0.9)
    assert result["overall"] == pytest.approx(0.729)


def test_scores_clamped_to_interval() -> None:
    result = compute_quality_score(1.2, -0.2, 0.5)
    assert result["validity"] == pytest.approx(1.0)
    assert result["completeness"] == pytest.approx(0.0)
    assert 0.0 <= result["overall"] <= 1.0
