# Strategy Risk/Return Evaluation Design

## Context

`mitrader` currently provides a Streamlit page for visualizing trade records on K-line charts. The new feature adds a separate Streamlit page for evaluating and comparing the risk and return of daily return series from `pnl.csv`.

The first version is intentionally local-data only. It does not fetch online index data and does not change the existing K-line page layout or workflow.

## Goals

- Load daily return series from a local CSV file.
- Let users select one or more return series to analyze.
- Let users optionally select one CSV column as the benchmark.
- Show net value and drawdown curves in one Plotly figure with two shared-x subplots.
- Show a risk/return metrics table with best-value highlighting.
- Show a recent returns table for WTD, MTD, YTD, year max drawdown, and current drawdown.
- Keep calculation logic separate from Streamlit UI so it can be unit tested.

## Non-Goals

- No online benchmark or index data source.
- No support for file formats other than CSV.
- No automatic detection of built-in common indexes such as CSI 300 unless they already exist as columns in `pnl.csv`.
- No redesign of the existing trade/K-line page.

## Page And Module Boundaries

Add a new Streamlit multipage file:

- `pages/1_策略风险收益评估.py`

Keep the existing `app.py` as the K-line trade visualization page. The new page owns its own CSV path input, loading state, return-series selection, benchmark selection, date-range controls, charts, and tables.

Add focused modules under `src/`:

- `src/pnl_loader.py`
  - Reads and validates `pnl.csv`.
  - Requires a `datetime` column.
  - Treats all non-date numeric columns as return series.
  - Parses `datetime` to `pl.Date`.
  - Casts return series to float.
  - Fills missing return values with `0`.
  - Sorts by date.
  - Rejects duplicate dates.

- `src/performance.py`
  - Contains pure calculation functions.
  - Computes net value, drawdown, risk/return metrics, and recent returns.
  - Uses selected series, optional benchmark, and selected date range as inputs.

- `src/performance_charts.py`
  - Builds Plotly figures from prepared net value and drawdown data.
  - Does not calculate metrics.

The Streamlit page remains a thin orchestration layer around these modules.

## Input Data Contract

The first version supports a local CSV shaped like:

```csv
datetime,kzz0,jsl_index,kzz1
2024-01-02T00:00:00.000000,0.0,0.0016,-0.0016
```

Rules:

- `datetime` is the fixed date column name.
- Every other column is a candidate return series.
- Daily returns are decimal returns, so `0.0016` means `0.16%`.
- Missing values are treated as `0` for all calculations and charts.
- Duplicate `datetime` values are invalid and produce a loading error.
- Non-date `datetime` values are invalid.
- Non-numeric return columns are invalid and the error identifies the column.

## User Selection Rules

- Users can select one or more return series for analysis.
- The benchmark is optional.
- If selected, the benchmark must be one of the return series columns in the current CSV.
- The benchmark does not need to be included in the selected analysis series. If it is not selected, it is still used for benchmark-relative calculations.
- If the selected benchmark is also included as an analyzed series, benchmark-relative columns for that row display `-` and do not participate in ranking.

## Date Range Rules

The page provides these date-range options:

- All
- Last 5 years
- Last 3 years
- Last 1 year
- YTD
- Custom

Shortcut ranges use the last date in the loaded data as the end date, not the current system date. YTD starts on January 1 of the last data date's year. If a shortcut start date is earlier than the first data date, the first data date is used.

Custom ranges use date inputs constrained to the data's minimum and maximum dates.

If the selected date range contains no rows, the page shows a clear message and skips charts and tables.

## Net Value And Drawdown

For each selected series:

- Initial net value is `1.0`.
- Net value is calculated by compounding daily returns: `nav = product(1 + daily_return)`.
- Drawdown is `nav / rolling_max(nav) - 1`.

The page displays one Plotly figure with two vertically stacked subplots:

- Top subplot: net value curves.
- Bottom subplot: drawdown curves.
- Both subplots share the x-axis.
- The same series uses the same color in both subplots.
- Legends should avoid duplicate entries where possible.

## Recent Returns Table

For each selected series, show:

- Latest net value.
- WTD return, using Monday as the week start.
- MTD return, using the first day of the natural month.
- YTD return, using the first day of the natural year.
- Current-year max drawdown.
- Current drawdown.

If a WTD, MTD, or YTD start date is earlier than the available data, calculation starts from the first available row in the relevant data. Missing returns have already been filled with `0`, so they do not interrupt compounding.

## Risk/Return Metrics

For each selected series, show:

- Annualized return.
- Annualized volatility.
- Excess annualized return.
- Excess annualized volatility.
- Sharpe ratio.
- Maximum drawdown.
- Sortino ratio.
- Calmar ratio.
- Information ratio.
- Alpha.
- Beta.

Calculation rules:

- Annualization factor is fixed at `252`.
- Risk-free rate is fixed at `0`.
- Annualized return uses a geometric approach: period cumulative return converted to annualized return.
- Annualized volatility is daily return standard deviation times `sqrt(252)`.
- Sharpe ratio is annualized return divided by annualized volatility.
- Downside deviation for Sortino uses daily returns below `0`; Sortino uses annualized downside deviation.
- Calmar ratio is annualized return divided by the absolute value of maximum drawdown.
- Excess daily return is strategy daily return minus benchmark daily return.
- Excess annualized return and volatility are calculated from the excess daily return series.
- Information ratio is excess annualized return divided by excess annualized volatility.
- Alpha and Beta use linear regression of strategy daily returns against benchmark daily returns. Alpha is annualized by multiplying daily alpha by `252`.
- If no benchmark is selected, excess metrics, information ratio, Alpha, and Beta display `-`.
- If the analyzed row is the selected benchmark, benchmark-relative metrics display `-`.
- Division by zero or insufficient samples produce `-` instead of an exception.

## Highlighting Rules

The metrics table highlights the best valid value for each ranked metric:

- Higher is better:
  - Annualized return.
  - Excess annualized return.
  - Sharpe ratio.
  - Sortino ratio.
  - Calmar ratio.
  - Information ratio.
  - Alpha.

- Lower is better:
  - Annualized volatility.
  - Excess annualized volatility.

- Maximum drawdown:
  - Values are negative.
  - The best value is closest to `0`.

Beta is displayed but not highlighted. `-` values do not participate in ranking.

## Error Handling

The page handles expected user and data problems without crashing:

- Missing CSV path: show an error.
- Missing `datetime` column: show an error.
- No return series columns: show an error.
- Unparseable date values: show an error.
- Unparseable numeric return columns: show an error with the column name.
- Duplicate dates: show an error.
- No selected return series: show an instruction to select at least one series.
- Empty selected date range: show an empty-range message.
- Metric division by zero or insufficient samples: show `-`.

## Testing Plan

Unit tests for `src/pnl_loader.py`:

- Loads normal CSV and returns expected columns and types.
- Parses `datetime` to `pl.Date`.
- Rejects missing `datetime`.
- Rejects duplicate dates.
- Rejects non-numeric return columns.
- Fills missing return values with `0`.

Unit tests for `src/performance.py`:

- Net value compounding.
- Drawdown calculation.
- WTD, MTD, and YTD returns.
- Current-year max drawdown.
- Current drawdown.
- Annualized return.
- Annualized volatility.
- Sharpe ratio.
- Sortino ratio.
- Calmar ratio.
- Excess annualized return and volatility.
- Information ratio.
- Alpha and Beta.
- No-benchmark behavior.
- Division-by-zero and insufficient-sample behavior.

Unit tests for `src/performance_charts.py`:

- Builds one Plotly figure.
- Figure contains two vertically stacked subplots.
- Subplots share the x-axis.
- Net value and drawdown trace counts match selected series.
- Series colors are consistent between net value and drawdown traces.

E2E tests:

- Navigate to the new page.
- Load `sample_data/pnl.csv`.
- Select multiple series.
- Select an optional benchmark.
- Change the date range.
- Confirm the combined chart, metrics table, and recent returns table render.

## Repository Maintenance

After code changes, run:

```bash
graphify update .
```

Do not commit unrelated `graphify-out/cache` churn unless graph maintenance is explicitly part of the task.
