from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.dashboard import generate_dashboard
from pipeline.gaps import detect_gaps, forward_fill_prices
from pipeline.loader import build_price_dataframe
from pipeline.outliers import detect_outliers_mad
from pipeline.quality import run_full_pipeline
from pipeline.report import generate_html_report, generate_multi_ticker_chart, generate_pipeline_output_chart
from pipeline.returns import add_log_returns, add_realized_vol, add_simple_returns
from pipeline.validator import validate_ohlcv

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
DEFAULT_TICKERS = ["AAPL", "MSFT", "TSLA", "GOOG"]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        None.

    Returns:
        Parsed argparse namespace.
    """
    parser = argparse.ArgumentParser(description="Run the pre-trade market data integrity pipeline.")
    parser.add_argument("--ticker", nargs="+", default=DEFAULT_TICKERS, help="One or more ticker symbols.")
    parser.add_argument("--period", default="2y", choices=sorted(VALID_PERIODS), help="Historical period.")
    parser.add_argument("--output-dir", default="./outputs", help="Directory for outputs.")
    parser.add_argument("--demo-data", action="store_true", help="Use deterministic offline demo data instead of Yahoo Finance.")
    return parser.parse_args()


def _serializable_quality_report(result: dict) -> dict:
    """Build JSON-safe quality report.

    Args:
        result: Pipeline result dictionary.

    Returns:
        JSON-safe summary dictionary.
    """
    return {
        "ticker": result["ticker"],
        "validation": result["validation"],
        "gaps": [
            {**gap, "start": gap["start"].isoformat(), "end": gap["end"].isoformat()}
            for gap in result["gaps"]
        ],
        "fill_report": {
            "n_values_filled": result["fill_report"]["n_values_filled"],
            "n_rows_with_fills": result["fill_report"]["n_rows_with_fills"],
        },
        "outliers": {
            "n_outliers": result["outliers"]["n_outliers"],
            "outlier_dates": [date.isoformat() for date in result["outliers"]["outlier_dates"]],
        },
        "quality_score": result["quality_score"],
        "pipeline_run_timestamp": result["pipeline_run_timestamp"],
    }


def _run_demo_pipeline(ticker: str) -> dict:
    """Run the pipeline on deterministic synthetic OHLCV data.

    Args:
        ticker: Ticker symbol used to seed the demo series.

    Returns:
        Pipeline result dictionary compatible with report generators.
    """
    seed = sum(ord(character) for character in ticker.upper())
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-02", periods=180)
    log_returns = rng.normal(loc=0.0005, scale=0.015, size=len(dates))
    log_returns[70] = 0.11
    close = 100 * np.exp(np.cumsum(log_returns))
    open_prices = close * (1 + rng.normal(0.0, 0.003, len(dates)))
    high = np.maximum(open_prices, close) * (1 + rng.uniform(0.001, 0.01, len(dates)))
    low = np.minimum(open_prices, close) * (1 - rng.uniform(0.001, 0.01, len(dates)))
    volume = rng.integers(900_000, 4_000_000, len(dates))
    raw_df = build_price_dataframe(dates, open_prices, high, low, close, volume)
    validation = validate_ohlcv(raw_df)
    gaps = detect_gaps(raw_df.index)
    filled_df, fill_report = forward_fill_prices(raw_df)
    enriched_df = add_simple_returns(filled_df)
    enriched_df = add_log_returns(enriched_df)
    enriched_df = add_realized_vol(enriched_df, windows=[20, 60])
    outliers = detect_outliers_mad(enriched_df["log_return"])
    outlier_score = 1.0 - (outliers["n_outliers"] / max(1, enriched_df["log_return"].notna().sum()))
    timestamp = pd.Timestamp.utcnow().isoformat()
    enriched_df["pipeline_run_timestamp"] = timestamp
    quality_score = {
        "validity": validation["validity_rate"],
        "completeness": 1.0,
        "outlier_score": outlier_score,
        "overall": validation["validity_rate"] * outlier_score,
        "grade": "A" if validation["validity_rate"] * outlier_score >= 0.99 else "B",
    }
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


def _format_detailed_summary(result: dict) -> str:
    """Format a platform-style pipeline summary block.

    Args:
        result: Pipeline result dictionary.

    Returns:
        Multi-line summary string.
    """
    quality = result["quality_score"]
    return f"""=== Data Quality Pipeline: {result['ticker']} ===
Raw data: {len(result['raw_df'])} trading days

Structural violations: {result['validation']['n_violations']}
Missing business days: {result['fill_report']['n_rows_with_fills']}
Outliers flagged: {result['outliers']['n_outliers']}

========================================
QUALITY GRADE: {quality['grade']} ({quality['overall']:.3f})
  Validity:     {quality['validity']:.4f}
  Completeness: {quality['completeness']:.4f}
  Outlier:      {quality['outlier_score']:.4f}
========================================"""


def main() -> None:
    """Run the CLI pipeline.

    Args:
        None.

    Returns:
        None.
    """
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_results = {}
    summary_lines = []
    for ticker in args.ticker:
        result = _run_demo_pipeline(ticker) if args.demo_data else run_full_pipeline(ticker=ticker, period=args.period)
        all_results[result["ticker"]] = result
        result["clean_data"].to_csv(output_dir / f"{result['ticker']}_clean_data.csv")
        result["fill_report"]["audit"].to_csv(output_dir / f"{result['ticker']}_fill_report.csv", index=False)
        (output_dir / f"{result['ticker']}_quality_report.json").write_text(json.dumps(_serializable_quality_report(result), indent=2), encoding="utf-8")
        generate_html_report(result, str(output_dir / f"{result['ticker']}_report.html"))
        generate_pipeline_output_chart(result, str(output_dir / f"{result['ticker']}_pipeline_output.png"))
        summary_block = _format_detailed_summary(result)
        line = f"{result['ticker']}: grade {result['quality_score']['grade']}, overall {result['quality_score']['overall']:.3f}, outliers {result['outliers']['n_outliers']}"
        summary_lines.append(summary_block)
        print(summary_block)
        print()
    generate_multi_ticker_chart(all_results, str(output_dir / "multi_ticker_comparison.png"))
    dashboard_path = output_dir / "quality_dashboard.html"
    generate_dashboard(all_results, str(dashboard_path))
    (output_dir / "pipeline_summary.txt").write_text("\n\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Dashboard: {dashboard_path}")


if __name__ == "__main__":
    main()
