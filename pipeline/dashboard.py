from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from pipeline.report import COLORS

ALERT_THRESHOLD = 0.90
WARNING_THRESHOLD = 0.95
GRADE_COLORS = {
    'A': '#26804a',
    'B': '#339b5e',
    'C': '#f0883e',
    'F': '#f85149',
}


def _status_badge(overall: float) -> tuple[str, str]:
    """Classify score status.

    Args:
        overall: Overall quality score.

    Returns:
        Label and CSS class.
    """
    if overall >= WARNING_THRESHOLD:
        return "HEALTHY", "healthy"
    if overall >= ALERT_THRESHOLD:
        return "WARNING", "warning"
    return "ALERT - DO NOT USE", "alert"


def generate_dashboard(all_results: dict, output_path: str) -> None:
    """Generate a self-contained multi-ticker quality dashboard.

    Args:
        all_results: Mapping of ticker to result dict from run_full_pipeline().
        output_path: Destination HTML path.

    Returns:
        None.

    Raises:
        ValueError: If all_results is empty.
    """
    if not all_results:
        raise ValueError("all_results must not be empty")
    timestamp = next(iter(all_results.values()))["pipeline_run_timestamp"]
    grade_counts = {grade: sum(1 for result in all_results.values() if result["quality_score"]["grade"] == grade) for grade in ["A", "B", "C", "F"]}
    alert_count = sum(1 for result in all_results.values() if result["quality_score"]["overall"] < ALERT_THRESHOLD)
    rows_html = "\n".join(_quality_row(ticker, result) for ticker, result in all_results.items())
    chart_base64 = _build_component_chart(all_results)
    comparison_base64 = _build_multi_ticker_comparison_chart(all_results)
    visualizations_html = _build_pipeline_visualizations(all_results)
    alerts_html = _build_alerts(all_results)
    outlier_html = _build_outlier_events(all_results)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Pre-Trade Market Data Integrity Engine - Quality Dashboard</title><style>
body{{margin:0;background:#0d1117;color:#e6edf3;font-family:Arial,sans-serif}}main{{max-width:1220px;margin:auto;padding:28px}}.panel{{border:1px solid #30363d;border-radius:8px;padding:18px;margin:18px 0;background:#161b22}}.cards{{display:flex;flex-wrap:wrap;gap:12px}}.card{{border:1px solid #30363d;border-radius:8px;padding:12px 16px;min-width:145px}}.viz-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:18px}}.viz-card{{border:1px solid #30363d;border-radius:8px;padding:12px;background:#0d1117}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #30363d;text-align:left}}th{{color:#8dd1a8}}.healthy{{background:#26804a}}.warning{{background:#f0883e;color:#111}}.alert{{background:#f85149}}.badge{{padding:5px 8px;border-radius:5px;font-weight:700}}tr.alert-row{{background:rgba(248,81,73,.18)}}tr.warning-row{{background:rgba(240,136,62,.16)}}.box{{border-radius:8px;padding:12px;margin:8px 0}}.red{{border:1px solid #f85149}}.amber{{border:1px solid #f0883e}}.green{{border:1px solid #26804a}}img{{width:100%;max-height:620px;object-fit:contain}}@media(max-width:700px){{main{{padding:14px}}table{{font-size:13px}}.viz-grid{{grid-template-columns:1fr}}}}</style></head><body><main>
<h1>Pre-Trade Market Data Integrity Engine - Quality Dashboard</h1>
<section class="panel"><h2>Pipeline Run Summary</h2><div class="cards"><div class="card">Run timestamp<br><strong>{timestamp}</strong></div><div class="card">Tickers<br><strong>{len(all_results)}</strong></div><div class="card">A / B / C / F<br><strong>{grade_counts['A']} / {grade_counts['B']} / {grade_counts['C']} / {grade_counts['F']}</strong></div><div class="card">Alerts<br><strong>{alert_count}</strong></div></div></section>
<section class="panel"><h2>Overall Quality Score Table</h2><table><thead><tr><th>Ticker</th><th>Grade</th><th>Overall Score</th><th>Validity</th><th>Completeness</th><th>Outlier Score</th><th>Gaps Filled</th><th>Outliers Detected</th><th>Status Badge</th></tr></thead><tbody>{rows_html}</tbody></table></section>
<section class="panel"><h2>Quality Score Components by Ticker</h2><img src="data:image/png;base64,{chart_base64}"></section>
<section class="panel"><h2>Multi-Ticker Fat-Tails Comparison</h2><img src="data:image/png;base64,{comparison_base64}"></section>
<section class="panel"><h2>Pipeline Visualizations</h2><div class="viz-grid">{visualizations_html}</div></section>
<section class="panel"><h2>Alerts</h2>{alerts_html}</section>
<section class="panel"><h2>Outlier Events</h2>{outlier_html}<p>These are flagged for investigation - not automatically removed.</p></section>
<footer>Pipeline run timestamp: {timestamp}</footer></main></body></html>"""
    Path(output_path).write_text(html, encoding="utf-8")


def _quality_row(ticker: str, result: dict) -> str:
    """Build one quality table row.

    Args:
        ticker: Ticker symbol.
        result: Pipeline result.

    Returns:
        HTML row string.
    """
    quality = result["quality_score"]
    status, css_class = _status_badge(quality["overall"])
    row_class = "alert-row" if quality["overall"] < ALERT_THRESHOLD else "warning-row" if quality["overall"] < WARNING_THRESHOLD else ""
    return f"""<tr class="{row_class}"><td>{ticker}</td><td><span class="badge" style="background:{GRADE_COLORS[quality['grade']]}">{quality['grade']}</span></td><td>{quality['overall']:.3f}</td><td>{quality['validity']:.3f}</td><td>{quality['completeness']:.3f}</td><td>{quality['outlier_score']:.3f}</td><td>{result['fill_report']['n_rows_with_fills']}</td><td>{result['outliers']['n_outliers']}</td><td><span class="badge {css_class}">{status}</span></td></tr>"""


def _build_component_chart(all_results: dict) -> str:
    """Build grouped horizontal component bar chart.

    Args:
        all_results: Mapping of ticker to result dictionaries.

    Returns:
        Base64-encoded PNG string.
    """
    tickers = list(all_results.keys())
    y_positions = range(len(tickers))
    figure, axis = plt.subplots(figsize=(12, max(4, len(tickers) * 1.1)), dpi=150)
    offsets = [-0.25, 0.0, 0.25]
    components = [("validity", COLORS['primary']), ("completeness", COLORS['blue']), ("outlier_score", COLORS['purple'])]
    for offset, (component, color) in zip(offsets, components):
        values = [all_results[ticker]["quality_score"][component] for ticker in tickers]
        axis.barh([position + offset for position in y_positions], values, height=0.22, label=component.replace("_", " ").title(), color=color)
    axis.axvline(ALERT_THRESHOLD, color=COLORS['red'], linestyle="--", linewidth=2)
    axis.set_xlim(0.0, 1.0)
    axis.set_yticks(list(y_positions))
    axis.set_yticklabels(tickers)
    axis.set_title("Quality Score Components by Ticker")
    axis.legend()
    buffer = BytesIO()
    figure.tight_layout()
    figure.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _build_multi_ticker_comparison_chart(all_results: dict) -> str:
    """Build embedded multi-ticker return distribution chart.

    Args:
        all_results: Mapping of ticker to result dictionaries.

    Returns:
        Base64-encoded PNG string.
    """
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), dpi=150)
    for axis, (ticker, result) in zip(axes.ravel(), list(all_results.items())[:4]):
        values = result["clean_data"]["log_return"].dropna()
        kurtosis_value = stats.kurtosis(values, fisher=True, bias=False) if len(values) > 3 else 0.0
        axis.hist(values, bins=40, density=True, alpha=0.7, color=COLORS["secondary"], edgecolor="none")
        if len(values) > 1 and values.std() > 0:
            x_values = pd.Series(pd.interval_range(values.min(), values.max(), periods=200).mid)
            normal_values = stats.norm.pdf(x_values, values.mean(), values.std())
            axis.plot(x_values, normal_values, color=COLORS["red"], linewidth=2, linestyle="--")
        axis.set_title(f"{ticker} (excess kurtosis = {kurtosis_value:.1f})")
        axis.set_xlabel("Log Return")
        axis.set_ylabel("Density")
    for axis in axes.ravel()[len(all_results):]:
        axis.set_visible(False)
    figure.suptitle("Return Distributions vs Normal - Fat Tails Evidence", color=COLORS["white"])
    buffer = BytesIO()
    figure.tight_layout()
    figure.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _build_pipeline_visualizations(all_results: dict) -> str:
    """Build embedded per-ticker pipeline visualization cards.

    Args:
        all_results: Mapping of ticker to result dictionaries.

    Returns:
        HTML containing base64-embedded PNG charts.
    """
    cards = []
    for ticker, result in all_results.items():
        chart_base64 = _build_pipeline_visualization_chart(result)
        cards.append(f"<div class='viz-card'><h3>{ticker}</h3><img src='data:image/png;base64,{chart_base64}'></div>")
    return "".join(cards)


def _build_pipeline_visualization_chart(result: dict) -> str:
    """Build one compact pipeline output chart.

    Args:
        result: Pipeline result dictionary.

    Returns:
        Base64-encoded PNG string.
    """
    ticker = result["ticker"]
    data = result["clean_data"]
    quality = result["quality_score"]
    flags = result["outliers"]["is_outlier"]
    figure, axes = plt.subplots(3, 1, figsize=(9, 6), dpi=150, sharex=True)
    axes[0].plot(data.index, data["Close"], color=COLORS["primary"], linewidth=1.1)
    axes[0].scatter(data.index[flags], data.loc[flags, "Close"], color=COLORS["red"], s=12, label=f"{int(flags.sum())} outliers")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[0].set_title(f"{ticker} - Clean Pipeline Output (Grade: {quality['grade']})")
    axes[0].set_ylabel("Close")
    axes[1].bar(data.index, data["log_return"], color=COLORS["light"], width=1.0, alpha=0.75)
    axes[1].set_ylabel("Log Ret")
    axes[2].plot(data.index, data["realized_vol_20d"], color=COLORS["accent"], linewidth=1.1)
    axes[2].set_ylabel("20d Vol")
    axes[2].set_xlabel("Date")
    buffer = BytesIO()
    figure.tight_layout()
    figure.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _build_alerts(all_results: dict) -> str:
    """Build alerts section HTML.

    Args:
        all_results: Mapping of ticker to result dictionaries.

    Returns:
        HTML string.
    """
    alert_items = []
    warning_items = []
    for ticker, result in all_results.items():
        quality = result["quality_score"]
        lowest_component = min(["validity", "completeness", "outlier_score"], key=lambda key: quality[key])
        text = f"{ticker}: {quality['overall']:.3f}, weakest component: {lowest_component}"
        if quality["overall"] < ALERT_THRESHOLD:
            alert_items.append(text)
        elif quality["overall"] < WARNING_THRESHOLD:
            warning_items.append(text)
    sections = []
    if alert_items:
        sections.append(f"<div class='box red'><strong>Alerts</strong><ul>{''.join(f'<li>{item}</li>' for item in alert_items)}</ul></div>")
    if warning_items:
        sections.append(f"<div class='box amber'><strong>Warnings</strong><ul>{''.join(f'<li>{item}</li>' for item in warning_items)}</ul></div>")
    return "".join(sections) if sections else "<div class='box green'>All tickers healthy - no action required.</div>"


def _build_outlier_events(all_results: dict) -> str:
    """Build outlier events HTML table.

    Args:
        all_results: Mapping of ticker to result dictionaries.

    Returns:
        HTML table.
    """
    records: list[dict] = []
    for ticker, result in all_results.items():
        data = result["clean_data"]
        flags = result["outliers"]["is_outlier"]
        scores = result["outliers"]["modified_z"]
        for date in data.index[flags]:
            records.append({"Ticker": ticker, "Date": date.date().isoformat(), "Log Return": data.at[date, "log_return"], "Modified Z-Score": scores.at[date]})
    table = pd.DataFrame.from_records(records, columns=["Ticker", "Date", "Log Return", "Modified Z-Score"])
    if table.empty:
        return "<p>No outliers detected.</p>"
    table = table.reindex(table["Modified Z-Score"].abs().sort_values(ascending=False).index)
    rows = []
    for _, row in table.iterrows():
        css_class = " class='alert-row'" if abs(row["Modified Z-Score"]) > 5.0 else ""
        rows.append(f"<tr{css_class}><td>{row['Ticker']}</td><td>{row['Date']}</td><td>{row['Log Return']:.6f}</td><td>{row['Modified Z-Score']:.2f}</td></tr>")
    return "<table><caption>These are flagged for investigation - not automatically removed.</caption><thead><tr><th>Ticker</th><th>Date</th><th>Log Return</th><th>Modified Z-Score</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
