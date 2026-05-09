from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

COLORS = {
    'primary':   '#26804a',
    'secondary': '#339b5e',
    'accent':    '#56b67d',
    'light':     '#8dd1a8',
    'red':       '#f85149',
    'orange':    '#f0883e',
    'blue':      '#58a6ff',
    'purple':    '#bc8cff',
    'gray':      '#8b949e',
    'white':     '#e6edf3',
}

plt.style.use('dark_background')
plt.rcParams.update({
    'figure.figsize': (14, 6),
    'figure.dpi': 150,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'font.size': 11,
})


def _figure_to_base64(builder: Callable[[plt.Axes], None]) -> str:
    """Render a matplotlib figure as base64 PNG.

    Args:
        builder: Function that draws onto the axes.

    Returns:
        Base64-encoded PNG string.

    Raises:
        RuntimeError: If rendering fails.
    """
    figure, axes = plt.subplots()
    builder(axes)
    buffer = BytesIO()
    figure.tight_layout()
    figure.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _normal_overlay(axis: plt.Axes, values: pd.Series) -> None:
    """Draw a normal density overlay when data has variance.

    Args:
        axis: Matplotlib axis.
        values: Return values.

    Returns:
        None.
    """
    clean_values = values.dropna()
    if len(clean_values) > 1 and clean_values.std() > 0:
        x_values = np.linspace(clean_values.min(), clean_values.max(), 200)
        axis.plot(x_values, stats.norm.pdf(x_values, clean_values.mean(), clean_values.std()), color=COLORS['red'], linewidth=2, linestyle='--')


def generate_html_report(result: dict, output_path: str) -> None:
    """Generate a self-contained per-ticker HTML quality report.

    Args:
        result: Result dictionary from run_full_pipeline.
        output_path: Destination HTML path.

    Returns:
        None.

    Raises:
        ValueError: If result lacks clean_data.
    """
    if "clean_data" not in result:
        raise ValueError("result must contain clean_data")
    ticker = result["ticker"]
    data = result["clean_data"]
    outliers = result.get("outliers", {})

    close_chart = _figure_to_base64(lambda ax: (ax.plot(data.index, data["Close"], color=COLORS['primary'], linewidth=1.5), ax.set_title(f"{ticker} Adjusted Close"), ax.set_ylabel("Price")))
    returns_chart = _build_returns_chart(data, outliers, ticker)
    vol_chart = _figure_to_base64(lambda ax: (ax.plot(data.index, data["realized_vol_20d"], color=COLORS['blue'], label="20d"), ax.plot(data.index, data["realized_vol_60d"], color=COLORS['purple'], label="60d"), ax.legend(), ax.set_title(f"{ticker} Realized Volatility")))
    distribution_chart = _build_distribution_chart(data, ticker)
    quality = result["quality_score"]
    fill_audit = result["fill_report"]["audit"].head(50).to_html(index=False)
    outlier_rows = _outlier_table(data, outliers)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{ticker} Quality Report</title><style>
body{{margin:0;background:#0d1117;color:#e6edf3;font-family:Arial,sans-serif}}main{{max-width:1180px;margin:auto;padding:28px}}.badge{{display:inline-block;padding:8px 14px;border-radius:6px;background:{_grade_color(quality['grade'])};font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}}section{{border:1px solid #30363d;padding:16px;border-radius:8px;margin:18px 0}}img{{width:100%}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #30363d;padding:8px;text-align:left}}th{{color:#8dd1a8}}</style></head><body><main>
<h1>{ticker} Market Data Quality Report <span class="badge">Grade {quality['grade']} | {quality['overall']:.3f}</span></h1>
<section><h2>Summary Stats</h2>{data[['Close','simple_return','log_return','realized_vol_20d','realized_vol_60d']].describe().to_html()}</section>
<div class="grid"><section><img src="data:image/png;base64,{close_chart}"></section><section><img src="data:image/png;base64,{returns_chart}"></section><section><img src="data:image/png;base64,{vol_chart}"></section><section><img src="data:image/png;base64,{distribution_chart}"></section></div>
<section><h2>Fill Report</h2>{fill_audit}</section><section><h2>Outlier Dates</h2>{outlier_rows}</section>
<footer>Pipeline run timestamp: {result['pipeline_run_timestamp']}</footer></main></body></html>"""
    Path(output_path).write_text(html, encoding="utf-8")


def _build_returns_chart(data: pd.DataFrame, outliers: dict, ticker: str) -> str:
    """Build return series chart with outlier markers.

    Args:
        data: Clean data.
        outliers: Outlier detection dictionary.
        ticker: Ticker symbol.

    Returns:
        Base64 PNG string.
    """
    def builder(axis: plt.Axes) -> None:
        axis.plot(data.index, data["log_return"], color=COLORS['accent'], linewidth=1)
        flags = outliers.get("is_outlier", pd.Series(False, index=data.index))
        axis.scatter(data.index[flags], data.loc[flags, "log_return"], color=COLORS['red'], s=18)
        axis.set_title(f"{ticker} Log Returns with Outliers")
    return _figure_to_base64(builder)


def _build_distribution_chart(data: pd.DataFrame, ticker: str) -> str:
    """Build return distribution histogram.

    Args:
        data: Clean data.
        ticker: Ticker symbol.

    Returns:
        Base64 PNG string.
    """
    def builder(axis: plt.Axes) -> None:
        values = data["log_return"].dropna()
        axis.hist(values, bins=40, density=True, alpha=0.7, color=COLORS['secondary'], edgecolor='none')
        _normal_overlay(axis, values)
        axis.set_title(f"{ticker} Return Distribution")
        axis.set_xlabel("Log Return")
        axis.set_ylabel("Density")
    return _figure_to_base64(builder)


def _outlier_table(data: pd.DataFrame, outliers: dict) -> str:
    """Build an HTML outlier table.

    Args:
        data: Clean data.
        outliers: Outlier detection dictionary.

    Returns:
        HTML table.
    """
    flags = outliers.get("is_outlier", pd.Series(False, index=data.index))
    modified_z = outliers.get("modified_z", pd.Series(0.0, index=data.index))
    table = pd.DataFrame({"date": data.index[flags], "log_return": data.loc[flags, "log_return"].values, "modified_z": modified_z.loc[flags].values})
    return table.to_html(index=False)


def _grade_color(grade: str) -> str:
    """Return a report badge color.

    Args:
        grade: Letter grade.

    Returns:
        Hex color string.
    """
    return {"A": COLORS['primary'], "B": COLORS['secondary'], "C": COLORS['orange'], "F": COLORS['red']}.get(grade, COLORS['gray'])


def generate_multi_ticker_chart(results: dict, output_path: str) -> None:
    """Generate a 2x2 fat-tails comparison chart.

    Args:
        results: Mapping of ticker to pipeline result.
        output_path: Destination PNG path.

    Returns:
        None.

    Raises:
        ValueError: If results is empty.
    """
    if not results:
        raise ValueError("results must not be empty")
    figure, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=150)
    for axis, (ticker, result) in zip(axes.ravel(), list(results.items())[:4]):
        values = result["clean_data"]["log_return"].dropna()
        kurtosis_value = stats.kurtosis(values, fisher=True, bias=False) if len(values) > 3 else np.nan
        axis.hist(values, bins=40, density=True, alpha=0.7, color=COLORS['secondary'], edgecolor='none')
        _normal_overlay(axis, values)
        axis.set_title(f"{ticker} (excess kurtosis = {kurtosis_value:.1f})")
        axis.set_xlabel("Log Return")
        axis.set_ylabel("Density")
    for axis in axes.ravel()[len(results):]:
        axis.set_visible(False)
    figure.suptitle("Return Distributions vs Normal - Fat Tails Evidence", color=COLORS['white'])
    figure.tight_layout()
    figure.savefig(output_path, format="png", bbox_inches="tight")
    plt.close(figure)


def generate_pipeline_output_chart(result: dict, output_path: str) -> None:
    """Generate a compact three-panel pipeline output chart.

    Args:
        result: Result dictionary from run_full_pipeline.
        output_path: Destination PNG path.

    Returns:
        None.

    Raises:
        ValueError: If result lacks clean_data.
    """
    if "clean_data" not in result:
        raise ValueError("result must contain clean_data")
    ticker = result["ticker"]
    data = result["clean_data"]
    quality = result["quality_score"]
    flags = result["outliers"].get("is_outlier", pd.Series(False, index=data.index))
    figure, axes = plt.subplots(3, 1, figsize=(14, 9), dpi=150, sharex=True)
    axes[0].plot(data.index, data["Close"], color=COLORS["primary"], linewidth=1.3)
    axes[0].scatter(data.index[flags], data.loc[flags, "Close"], color=COLORS["red"], s=18, label=f"{int(flags.sum())} outliers")
    axes[0].legend(loc="upper left")
    axes[0].set_title(f"{ticker} - Clean Pipeline Output (Grade: {quality['grade']})")
    axes[0].set_ylabel("Close Price")
    axes[1].bar(data.index, data["log_return"], color=COLORS["light"], width=1.0, alpha=0.75)
    axes[1].set_ylabel("Log Return")
    axes[2].plot(data.index, data["realized_vol_20d"], color=COLORS["accent"], linewidth=1.3)
    axes[2].set_ylabel("20d Ann. Vol")
    axes[2].set_xlabel("Date")
    figure.tight_layout()
    figure.savefig(output_path, format="png", bbox_inches="tight")
    plt.close(figure)
