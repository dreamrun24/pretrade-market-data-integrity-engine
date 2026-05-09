# Pre-Trade Market Data Integrity Engine

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Before any strategy runs, before any backtest starts, before
any risk model fires - someone has to make sure the data is
actually trustworthy. This is that system.

---

## Why This Exists

Bad data doesn't give you wrong answers. It gives you
confidently wrong answers - which is far more dangerous.

A portfolio optimizer fed unadjusted prices will see a 4:1
stock split as a 75% crash and rebalance wildly. A risk model
trained on data with gaps will underestimate volatility during
holidays. An outlier detector using standard z-scores will miss
genuine anomalies in fat-tailed return distributions because one
extreme value inflates the standard deviation and hides itself.

This engine catches all of that automatically, every time,
before anything downstream ever sees the data.

---

## What It Does

Fetches real daily OHLCV data for any stock, runs it through
six validation and cleaning layers, scores the output from A
to F, and generates a monitoring dashboard showing the health
of every ticker at a glance.

```text
Fetch -> Validate -> Adjust Corporate Actions -> Fill Gaps
     -> Compute Returns -> Detect Outliers -> Score + Report
```

The order is not arbitrary. Corporate actions are adjusted
before outlier detection because an unadjusted stock split
looks like a 75% crash - it would be flagged and removed as
an error. Gaps are filled before returns are computed because
NaN prices cascade silently into every downstream calculation.
Get the order wrong and every model inherits the mistake
without knowing it.

---

## Get Started

```bash
git clone https://github.com/YOUR_USERNAME/pretrade-data-integrity-engine.git
cd pretrade-data-integrity-engine
pip install -r requirements.txt
python run_pipeline.py --ticker AAPL
```

---

## Usage

```bash
# Single ticker
python run_pipeline.py --ticker AAPL

# Multiple tickers - runs all and generates dashboard
python run_pipeline.py --ticker AAPL MSFT TSLA GOOG

# Custom period and output location
python run_pipeline.py --ticker AAPL --period 5y --output-dir ./my_outputs
```

---

## What Gets Built

| Component | What it does |
|---|---|
| DataFrame Builder | Structures raw OHLCV arrays into proper pandas DataFrames |
| Simple Return Calculator | Percentage price changes for PnL and attribution |
| Log Return Calculator | Continuously compounded returns for statistical modelling |
| Rolling Volatility Estimator | Annualised realised volatility over configurable windows |
| OHLCV Validator | Catches impossible price relationships before anything else runs |
| Gap Detector | Finds missing trading days and distinguishes holidays from feed failures |
| Forward-Fill Engine | Propagates last valid prices across gaps without look-ahead bias |
| Volume Zero-Filler | Handles missing volume separately - no trades means zero, not carried forward |
| MAD Calculator | Robust spread measure that one extreme value cannot distort |
| Modified Z-Score Engine | Outlier scores that work correctly on fat-tailed financial data |
| Rolling Outlier Detector | Adapts the outlier threshold to the current volatility regime |
| Split Adjustment Engine | Removes phantom crashes caused by unadjusted stock splits |
| Dividend Adjustment Engine | Removes artificial price drops on ex-dividend dates |
| Full Quality Pipeline | Runs all six layers in the correct order automatically |
| Quality Report Generator | Letter grades and per-component breakdowns per ticker |
| Monitoring Dashboard | One HTML page showing every ticker's health with colour-coded alerts |

---

## The Modules

| Module | What it handles |
|---|---|
| `loader.py` | Fetches real OHLCV data from Yahoo Finance |
| `validator.py` | Checks structural constraints - catches impossible prices |
| `gaps.py` | Detects missing days, fills prices forward, zeros volume |
| `returns.py` | Simple returns, log returns, rolling volatility |
| `outliers.py` | MAD-based outlier detection for fat-tailed distributions |
| `corporate_actions.py` | Adjusts historical prices for splits and dividends |
| `quality.py` | Orchestrates all six layers, computes quality grade |
| `report.py` | Per-ticker HTML report and fat-tails comparison chart |
| `dashboard.py` | Monitoring dashboard with grade badges, alerts, outlier table |

---

## What You Get

For each ticker:
- `AAPL_clean_data.csv` - cleaned OHLCV with returns,
  volatility, and outlier flags
- `AAPL_fill_report.csv` - audit trail of every value changed
- `AAPL_quality_report.json` - grade, score, per-component
  breakdown
- `AAPL_report.html` - self-contained visual report with
  four embedded charts

Shared across all tickers:
- `multi_ticker_comparison.png` - return distributions vs
  normal curve, one panel per ticker, fat tails visible
- `quality_dashboard.html` - health check across every ticker
- `pipeline_summary.txt` - one line per ticker

---

## Running the Tests

```bash
pytest tests/ -v
```

All tests use small handcrafted DataFrames. No network calls.
No live data required to run the test suite.

---

## Where This Goes Next

The foundation - validate, adjust, fill, detect, score -
applies to any asset class, any frequency, any data source.
The implementations change. The architecture doesn't.

- Add a second data source and reconcile between vendors -
  disagreements are the earliest signal of a data error
- Implement a proper trading calendar to distinguish every
  exchange holiday from a genuine feed failure
- Extend to minute-bar intraday data with market hours
  and pre/post-market session handling
- Add fundamental data - earnings dates, dividend
  announcements, index reconstitution events
- Automate with cron or Airflow to run daily before
  market open without human intervention
- Store clean data and quality reports in PostgreSQL
  or TimescaleDB for historical trend analysis
- Extend the dashboard with persistent score history
  across runs so degradation trends become visible

---

## The Research Behind It

Every algorithmic choice has a published justification.
Full citations and code annotations are in `REFERENCES.md`.

- **Leys et al. (2013)** - why MAD beats standard deviation
  for non-normal data, the direct basis for `outliers.py`
- **Hampel (1974)** - origin of the 1.4826 scaling constant
  used in every modified z-score calculation
- **Cont (2001)** - canonical proof that equity returns have
  fat tails, justification for the fat-tails comparison chart
- **Elton, Gruber & Blake (1996)** - survivorship bias
  quantified at ~0.9% per year in equity portfolios
- **Lo & MacKinlay (1990)** - look-ahead bias in financial
  model testing, why forward-fill not interpolation
- **CRSP Data Description Guide** - institutional standard
  for split and dividend adjustment conventions
- **Lopez de Prado (2018)** - financial ML data structures,
  Chapters 2-3 on bar types and data quality

---

## License

MIT

---

## Push to GitHub

```bash
git init
git add .
git commit -m "feat: pre-trade market data integrity engine"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pretrade-data-integrity-engine.git
git push -u origin main
```

Suggested description:
`Automated pre-trade data validation engine - validates,
adjusts, and scores market data before any strategy or
risk model sees it.`

Suggested topics:
`python` `quantitative-finance` `data-pipeline` `pandas`
`numpy` `market-data` `algorithmic-trading` `data-engineering`
`prop-trading` `pre-trade`
