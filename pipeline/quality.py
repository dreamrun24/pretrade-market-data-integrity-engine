from __future__ import annotations

from datetime import datetime, timezone
import logging

import pandas as pd

from pipeline.corporate_actions import adjust_for_dividends, adjust_for_splits
from pipeline.gaps import detect_gaps, forward_fill_prices
from pipeline.loader import fetch_ohlcv
from pipeline.outliers import detect_outliers_mad
from pipeline.returns import add_log_returns, add_realized_vol, add_simple_returns
from pipeline.validator import validate_ohlcv

LOGGER = logging.getLogger(__name__)
MIN_SCORE = 0.0
MAX_SCORE = 1.0
GRADE_A_THRESHOLD = 0.99
GRADE_B_THRESHOLD = 0.95
GRADE_C_THRESHOLD = 0.90


def _clamp_score(score: float) -> float:
    """Clamp a score into the quality-score interval.

    Args:
        score: Raw score.

    Returns:
        Score in [0, 1].

    Raises:
        TypeError: If score is not numeric.
    """
    if not isinstance(score, (int, float)):
        raise TypeError("score must be numeric")
    return min(MAX_SCORE, max(MIN_SCORE, float(score)))


def compute_quality_score(validity_score: float, completeness_score: float, outlier_score: float) -> dict:
    """Compute multiplicative quality score and letter grade.

    Args:
        validity_score: Structural validity score.
        completeness_score: Completeness after filling.
        outlier_score: Outlier cleanliness score.

    Returns:
        Quality score dictionary.

    Raises:
        TypeError: If any score is not numeric.
    """
    validity = _clamp_score(validity_score)
    completeness = _clamp_score(completeness_score)
    outlier_component = _clamp_score(outlier_score)
    overall = validity * completeness * outlier_component
    if overall >= GRADE_A_THRESHOLD:
        grade = "A"
    elif overall >= GRADE_B_THRESHOLD:
        grade = "B"
    elif overall >= GRADE_C_THRESHOLD:
        grade = "C"
    else:
        grade = "F"
    return {
        "validity": validity,
        "completeness": completeness,
        "outlier_score": outlier_component,
        "overall": overall,
        "grade": grade,
    }


def run_full_pipeline(
    ticker: str,
    period: str = "2y",
    splits: list | None = None,
    dividends: list | None = None,
) -> dict:
    """Run the full market data integrity pipeline.

    Args:
        ticker: Ticker symbol.
        period: yfinance period.
        splits: Optional split events.
        dividends: Optional dividend events.

    Returns:
        Pipeline result dictionary.

    Raises:
        ValueError: If no data can be fetched.
    """
    splits = [] if splits is None else splits
    dividends = [] if dividends is None else dividends
    raw_df = fetch_ohlcv(ticker=ticker, period=period)
    validation = validate_ohlcv(raw_df)
    adjusted_df = adjust_for_splits(raw_df, splits) if splits else raw_df.copy()
    adjusted_df = adjust_for_dividends(adjusted_df, dividends) if dividends else adjusted_df
    gaps = detect_gaps(adjusted_df.index)
    business_calendar = pd.bdate_range(adjusted_df.index.min(), adjusted_df.index.max())
    reindexed_df = adjusted_df.reindex(business_calendar)
    filled_df, fill_report = forward_fill_prices(reindexed_df)
    completeness_score = 1.0 - (fill_report["n_rows_with_fills"] / max(1, len(filled_df)))
    enriched_df = add_simple_returns(filled_df)
    enriched_df = add_log_returns(enriched_df)
    enriched_df = add_realized_vol(enriched_df, windows=[20, 60])
    outliers = detect_outliers_mad(enriched_df["log_return"])
    outlier_score = 1.0 - (outliers["n_outliers"] / max(1, enriched_df["log_return"].notna().sum()))
    quality_score = compute_quality_score(validation["validity_rate"], completeness_score, outlier_score)
    timestamp = datetime.now(timezone.utc).isoformat()
    enriched_df["pipeline_run_timestamp"] = timestamp
    LOGGER.info("Completed pipeline for %s with grade %s", ticker, quality_score["grade"])
    return {
        "ticker": ticker.upper(),
        "raw_df": raw_df,
        "clean_data": enriched_df,
        "validation": validation,
        "gaps": gaps,
        "fill_report": fill_report,
        "outliers": outliers,
        "quality_score": quality_score,
        "pipeline_run_timestamp": timestamp,
    }
