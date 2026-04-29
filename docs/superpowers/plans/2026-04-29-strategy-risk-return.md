# Strategy Risk/Return Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate Streamlit page that loads `pnl.csv`, compares selected daily return series, and displays net value/drawdown charts plus risk/return tables.

**Architecture:** Keep the existing K-line page intact. Add one thin Streamlit page under `pages/` and three focused modules under `src/`: CSV loading/validation, pure performance calculations, and Plotly chart construction. Drive implementation with unit tests first, then add a focused E2E smoke test for the new page.

**Tech Stack:** Python 3.14, Streamlit, Polars, Plotly, pytest, Playwright E2E tests, graphify.

---

## File Structure

- Create: `src/pnl_loader.py`
  - Owns loading and validation for daily return CSV files.
  - Public API: `load_pnl_data(file_path: str) -> pl.DataFrame`, `get_return_columns(df: pl.DataFrame) -> list[str]`.

- Create: `src/performance.py`
  - Owns pure calculations for date ranges, net value, drawdown, risk metrics, and recent returns.
  - Public API: `resolve_date_range`, `filter_returns_by_date`, `calculate_nav_and_drawdown`, `calculate_metrics_table`, `calculate_recent_returns`.

- Create: `src/performance_charts.py`
  - Owns Plotly figure construction.
  - Public API: `build_nav_drawdown_chart(nav_drawdown_df: pl.DataFrame, series_names: list[str]) -> go.Figure`.

- Create: `pages/1_策略风险收益评估.py`
  - Owns Streamlit controls and presentation for the new feature.
  - Does not contain formula logic.

- Create: `tests/unit/test_pnl_loader.py`
  - Unit coverage for CSV loading and validation.

- Create: `tests/unit/test_performance.py`
  - Unit coverage for calculation logic.

- Create: `tests/unit/test_performance_charts.py`
  - Unit coverage for chart structure.

- Modify: `tests/e2e/test_app.py`
  - Add a new E2E test class for the risk/return page.
  - Keep existing K-line E2E tests unchanged except helper additions.

- Modify after code changes: generated files under `graphify-out/`
  - Run `graphify update .`.
  - Review and avoid committing unrelated `graphify-out/cache` churn unless graphify changes are intentionally included.

## Task 1: PnL CSV Loader

**Files:**
- Create: `tests/unit/test_pnl_loader.py`
- Create: `src/pnl_loader.py`

- [ ] **Step 1: Write loader tests**

Create `tests/unit/test_pnl_loader.py` with:

```python
"""
Unit tests for pnl_loader module.
"""
from pathlib import Path

import polars as pl
import pytest

from src.pnl_loader import get_return_columns, load_pnl_data


@pytest.mark.unit
class TestLoadPnlData:

    def test_load_pnl_data_basic(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0,jsl_index,kzz1\n'
            '2024-01-02T00:00:00.000000,0.0,0.0016,-0.0016\n'
            '2024-01-03T00:00:00.000000,0.01,-0.002,0.003\n'
        )

        df = load_pnl_data(str(p))

        assert df.height == 2
        assert df['datetime'].dtype == pl.Date
        assert df['kzz0'].dtype == pl.Float64
        assert df['jsl_index'].dtype == pl.Float64
        assert df['kzz1'].dtype == pl.Float64
        assert df['datetime'].to_list()[0].isoformat() == '2024-01-02'

    def test_load_pnl_data_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match='PnL file not found'):
            load_pnl_data(str(tmp_path / 'missing.csv'))

    def test_load_pnl_data_missing_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('kzz0,jsl_index\n0.01,0.02\n')

        with pytest.raises(ValueError, match='Missing required column'):
            load_pnl_data(str(p))

    def test_load_pnl_data_no_return_columns(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime\n2024-01-02\n')

        with pytest.raises(ValueError, match='No return series columns'):
            load_pnl_data(str(p))

    def test_load_pnl_data_invalid_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime,kzz0\nnot-a-date,0.01\n')

        with pytest.raises(ValueError, match='Unable to parse datetime'):
            load_pnl_data(str(p))

    def test_load_pnl_data_duplicate_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-02,0.01\n'
            '2024-01-02,0.02\n'
        )

        with pytest.raises(ValueError, match='Duplicate datetime'):
            load_pnl_data(str(p))

    def test_load_pnl_data_invalid_numeric_column(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-02,not-a-number\n'
        )

        with pytest.raises(ValueError, match='Unable to parse numeric return column: kzz0'):
            load_pnl_data(str(p))

    def test_load_pnl_data_fills_missing_returns_with_zero(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0,jsl_index\n'
            '2024-01-02,,0.01\n'
            '2024-01-03,0.02,\n'
        )

        df = load_pnl_data(str(p))

        assert df['kzz0'].to_list() == [0.0, 0.02]
        assert df['jsl_index'].to_list() == [0.01, 0.0]

    def test_load_pnl_data_sorts_by_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-03,0.02\n'
            '2024-01-02,0.01\n'
        )

        df = load_pnl_data(str(p))

        assert [d.isoformat() for d in df['datetime'].to_list()] == ['2024-01-02', '2024-01-03']


@pytest.mark.unit
class TestGetReturnColumns:

    def test_get_return_columns_excludes_datetime(self):
        df = pl.DataFrame({
            'datetime': [],
            'kzz0': [],
            'jsl_index': [],
        })

        assert get_return_columns(df) == ['kzz0', 'jsl_index']
```

- [ ] **Step 2: Run loader tests and confirm they fail**

Run:

```bash
uv run pytest tests/unit/test_pnl_loader.py -v
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'src.pnl_loader'`.

- [ ] **Step 3: Implement `src/pnl_loader.py`**

Create `src/pnl_loader.py` with:

```python
"""
PnL CSV loading and validation module.
"""
from pathlib import Path

import polars as pl


DATE_COLUMN = 'datetime'


def get_return_columns(df: pl.DataFrame) -> list[str]:
    """Return the non-date columns that represent daily return series."""
    return [col for col in df.columns if col != DATE_COLUMN]


def load_pnl_data(file_path: str) -> pl.DataFrame:
    """Load daily return series from CSV.

    Args:
        file_path: Path to pnl.csv.

    Returns:
        DataFrame with datetime as pl.Date and return columns as Float64.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns or parseable values are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PnL file not found: {file_path}")

    try:
        df = pl.read_csv(file_path, infer_schema_length=0)
    except Exception as exc:
        raise ValueError(f"Unable to read PnL CSV: {exc}") from exc

    if DATE_COLUMN not in df.columns:
        raise ValueError(f"Missing required column: {DATE_COLUMN}")

    return_columns = get_return_columns(df)
    if not return_columns:
        raise ValueError("No return series columns found in pnl.csv")

    try:
        df = df.with_columns(
            pl.col(DATE_COLUMN).str.to_datetime(strict=True).dt.date().alias(DATE_COLUMN)
        )
    except Exception as exc:
        raise ValueError(f"Unable to parse datetime column: {exc}") from exc

    for col in return_columns:
        try:
            df = df.with_columns(
                pl.col(col).cast(pl.Float64, strict=True).fill_null(0.0).alias(col)
            )
        except Exception as exc:
            raise ValueError(f"Unable to parse numeric return column: {col}") from exc

    duplicate_count = df.group_by(DATE_COLUMN).len().filter(pl.col('len') > 1).height
    if duplicate_count > 0:
        raise ValueError("Duplicate datetime values found in pnl.csv")

    return df.sort(DATE_COLUMN)
```

- [ ] **Step 4: Run loader tests and confirm they pass**

Run:

```bash
uv run pytest tests/unit/test_pnl_loader.py -v
```

Expected: PASS for all tests in `tests/unit/test_pnl_loader.py`.

- [ ] **Step 5: Commit loader slice**

Run:

```bash
git add src/pnl_loader.py tests/unit/test_pnl_loader.py
git commit -m "feat: load pnl return data"
```

Expected: commit succeeds.

## Task 2: Core Performance Calculations

**Files:**
- Create: `tests/unit/test_performance.py`
- Create: `src/performance.py`

- [ ] **Step 1: Write performance tests**

Create `tests/unit/test_performance.py` with:

```python
"""
Unit tests for performance calculations.
"""
from datetime import date

import pytest
import polars as pl

from src.performance import (
    ANNUALIZATION_DAYS,
    calculate_metrics_table,
    calculate_nav_and_drawdown,
    calculate_recent_returns,
    filter_returns_by_date,
    resolve_date_range,
)


def _returns_df() -> pl.DataFrame:
    return pl.DataFrame({
        'datetime': [
            date(2024, 1, 2),
            date(2024, 1, 3),
            date(2024, 1, 4),
            date(2024, 1, 5),
        ],
        'strategy': [0.10, -0.05, 0.0, 0.05],
        'benchmark': [0.02, 0.01, -0.01, 0.00],
        'flat': [0.0, 0.0, 0.0, 0.0],
    }).with_columns(pl.col('datetime').cast(pl.Date))


def _full_year_df() -> pl.DataFrame:
    dates = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 4, 29)]
    return pl.DataFrame({
        'datetime': dates,
        'strategy': [0.01, -0.02, 0.03],
        'benchmark': [0.0, 0.0, 0.0],
    }).with_columns(pl.col('datetime').cast(pl.Date))


@pytest.mark.unit
class TestDateRanges:

    def test_resolve_date_range_all(self):
        df = _returns_df()

        start, end = resolve_date_range(df, '全部')

        assert start == date(2024, 1, 2)
        assert end == date(2024, 1, 5)

    def test_resolve_date_range_ytd_uses_last_data_year(self):
        df = _full_year_df()

        start, end = resolve_date_range(df, 'YTD')

        assert start == date(2024, 1, 1)
        assert end == date(2024, 4, 29)

    def test_filter_returns_by_date(self):
        df = _returns_df()

        filtered = filter_returns_by_date(df, date(2024, 1, 3), date(2024, 1, 4))

        assert [d.isoformat() for d in filtered['datetime'].to_list()] == ['2024-01-03', '2024-01-04']


@pytest.mark.unit
class TestNavAndDrawdown:

    def test_calculate_nav_and_drawdown(self):
        df = _returns_df()

        result = calculate_nav_and_drawdown(df, ['strategy'])

        assert result.select('strategy_nav').to_series().to_list() == pytest.approx([
            1.10,
            1.045,
            1.045,
            1.09725,
        ])
        assert result.select('strategy_drawdown').to_series().to_list() == pytest.approx([
            0.0,
            -0.05,
            -0.05,
            -0.0025,
        ])


@pytest.mark.unit
class TestRecentReturns:

    def test_calculate_recent_returns(self):
        df = pl.DataFrame({
            'datetime': [
                date(2024, 1, 1),
                date(2024, 1, 2),
                date(2024, 1, 31),
                date(2024, 4, 29),
            ],
            'strategy': [0.01, -0.02, 0.03, 0.04],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        result = calculate_recent_returns(df, ['strategy'])
        row = result.row(0, named=True)

        assert row['series'] == 'strategy'
        assert row['latest_nav'] == pytest.approx((1.01 * 0.98 * 1.03 * 1.04))
        assert row['wtd_return'] == pytest.approx(0.04)
        assert row['mtd_return'] == pytest.approx(0.04)
        assert row['ytd_return'] == pytest.approx((1.01 * 0.98 * 1.03 * 1.04) - 1)
        assert row['current_drawdown'] <= 0.0
        assert row['year_max_drawdown'] <= 0.0


@pytest.mark.unit
class TestMetricsTable:

    def test_calculate_metrics_without_benchmark(self):
        df = _returns_df()

        result = calculate_metrics_table(df, ['strategy'], benchmark=None)
        row = result.row(0, named=True)

        assert row['series'] == 'strategy'
        assert row['annualized_return'] is not None
        assert row['annualized_volatility'] is not None
        assert row['sharpe_ratio'] is not None
        assert row['max_drawdown'] == pytest.approx(-0.05)
        assert row['excess_annualized_return'] is None
        assert row['information_ratio'] is None
        assert row['alpha'] is None
        assert row['beta'] is None

    def test_calculate_metrics_with_benchmark(self):
        df = _returns_df()

        result = calculate_metrics_table(df, ['strategy'], benchmark='benchmark')
        row = result.row(0, named=True)

        assert row['series'] == 'strategy'
        assert row['excess_annualized_return'] is not None
        assert row['excess_annualized_volatility'] is not None
        assert row['information_ratio'] is not None
        assert row['alpha'] is not None
        assert row['beta'] is not None

    def test_benchmark_row_has_blank_relative_metrics(self):
        df = _returns_df()

        result = calculate_metrics_table(df, ['benchmark'], benchmark='benchmark')
        row = result.row(0, named=True)

        assert row['series'] == 'benchmark'
        assert row['excess_annualized_return'] is None
        assert row['excess_annualized_volatility'] is None
        assert row['information_ratio'] is None
        assert row['alpha'] is None
        assert row['beta'] is None

    def test_zero_volatility_metrics_are_blank(self):
        df = _returns_df()

        result = calculate_metrics_table(df, ['flat'], benchmark=None)
        row = result.row(0, named=True)

        assert row['annualized_volatility'] == 0.0
        assert row['sharpe_ratio'] is None
        assert row['sortino_ratio'] is None
        assert row['calmar_ratio'] is None


def test_annualization_days_is_252():
    assert ANNUALIZATION_DAYS == 252
```

- [ ] **Step 2: Run performance tests and confirm they fail**

Run:

```bash
uv run pytest tests/unit/test_performance.py -v
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'src.performance'`.

- [ ] **Step 3: Implement `src/performance.py`**

Create `src/performance.py` with:

```python
"""
Performance and risk metric calculations for daily return series.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

import polars as pl


ANNUALIZATION_DAYS = 252
DATE_COLUMN = 'datetime'


def resolve_date_range(
    df: pl.DataFrame,
    range_label: str,
    custom_range: Optional[tuple[date, date]] = None,
) -> tuple[date, date]:
    """Resolve a UI range label to concrete start/end dates."""
    min_date = df[DATE_COLUMN].min()
    max_date = df[DATE_COLUMN].max()

    if custom_range is not None:
        start, end = custom_range
        return max(start, min_date), min(end, max_date)

    if range_label == '全部':
        return min_date, max_date
    if range_label == 'YTD':
        return max(date(max_date.year, 1, 1), min_date), max_date

    days_by_label = {
        '最近 5 年': 365 * 5,
        '最近 3 年': 365 * 3,
        '最近 1 年': 365,
    }
    if range_label in days_by_label:
        return max(max_date - timedelta(days=days_by_label[range_label]), min_date), max_date

    return min_date, max_date


def filter_returns_by_date(df: pl.DataFrame, start_date: date, end_date: date) -> pl.DataFrame:
    """Filter returns to the inclusive date range."""
    return df.filter(
        (pl.col(DATE_COLUMN) >= start_date) &
        (pl.col(DATE_COLUMN) <= end_date)
    )


def calculate_nav_and_drawdown(df: pl.DataFrame, series_names: list[str]) -> pl.DataFrame:
    """Calculate compounded net value and drawdown for selected series."""
    result = df.select(DATE_COLUMN)
    for name in series_names:
        values = df[name].to_list()
        nav_values = []
        nav = 1.0
        running_max = 1.0
        drawdown_values = []
        for daily_return in values:
            nav *= 1.0 + float(daily_return)
            running_max = max(running_max, nav)
            nav_values.append(nav)
            drawdown_values.append((nav / running_max) - 1.0)
        result = result.with_columns(
            pl.Series(f'{name}_nav', nav_values),
            pl.Series(f'{name}_drawdown', drawdown_values),
        )
    return result


def calculate_recent_returns(df: pl.DataFrame, series_names: list[str]) -> pl.DataFrame:
    """Calculate latest NAV plus WTD, MTD, YTD, and drawdown values."""
    if df.is_empty():
        return pl.DataFrame()

    last_date = df[DATE_COLUMN].max()
    week_start = last_date - timedelta(days=last_date.weekday())
    month_start = date(last_date.year, last_date.month, 1)
    year_start = date(last_date.year, 1, 1)
    rows = []

    for name in series_names:
        nav_dd = calculate_nav_and_drawdown(df, [name])
        latest_nav = nav_dd[f'{name}_nav'][-1]
        current_drawdown = nav_dd[f'{name}_drawdown'][-1]

        year_df = filter_returns_by_date(df, year_start, last_date)
        year_dd = calculate_nav_and_drawdown(year_df, [name])
        year_max_drawdown = year_dd[f'{name}_drawdown'].min()

        rows.append({
            'series': name,
            'latest_nav': latest_nav,
            'wtd_return': _compound_range_return(df, name, week_start, last_date),
            'mtd_return': _compound_range_return(df, name, month_start, last_date),
            'ytd_return': _compound_range_return(df, name, year_start, last_date),
            'year_max_drawdown': year_max_drawdown,
            'current_drawdown': current_drawdown,
        })

    return pl.DataFrame(rows)


def calculate_metrics_table(
    df: pl.DataFrame,
    series_names: list[str],
    benchmark: Optional[str] = None,
) -> pl.DataFrame:
    """Calculate risk/return metrics for selected return series."""
    rows = []
    benchmark_returns = df[benchmark].to_list() if benchmark else None

    for name in series_names:
        returns = [float(v) for v in df[name].to_list()]
        nav_dd = calculate_nav_and_drawdown(df, [name])
        max_drawdown = nav_dd[f'{name}_drawdown'].min()

        row = {
            'series': name,
            'annualized_return': _annualized_return(returns),
            'annualized_volatility': _annualized_volatility(returns),
            'excess_annualized_return': None,
            'excess_annualized_volatility': None,
            'sharpe_ratio': None,
            'max_drawdown': max_drawdown,
            'sortino_ratio': None,
            'calmar_ratio': None,
            'information_ratio': None,
            'alpha': None,
            'beta': None,
        }

        row['sharpe_ratio'] = _safe_div(row['annualized_return'], row['annualized_volatility'])
        row['sortino_ratio'] = _safe_div(row['annualized_return'], _downside_deviation(returns))
        row['calmar_ratio'] = _safe_div(row['annualized_return'], abs(max_drawdown))

        if benchmark and benchmark_returns is not None and name != benchmark:
            excess_returns = [r - float(b) for r, b in zip(returns, benchmark_returns)]
            row['excess_annualized_return'] = _annualized_return(excess_returns)
            row['excess_annualized_volatility'] = _annualized_volatility(excess_returns)
            row['information_ratio'] = _safe_div(
                row['excess_annualized_return'],
                row['excess_annualized_volatility'],
            )
            alpha, beta = _alpha_beta(returns, [float(v) for v in benchmark_returns])
            row['alpha'] = alpha
            row['beta'] = beta

        rows.append(row)

    return pl.DataFrame(rows)


def _compound_range_return(df: pl.DataFrame, series_name: str, start_date: date, end_date: date) -> float:
    range_df = filter_returns_by_date(df, start_date, end_date)
    if range_df.is_empty():
        range_df = df
    nav = 1.0
    for daily_return in range_df[series_name].to_list():
        nav *= 1.0 + float(daily_return)
    return nav - 1.0


def _annualized_return(returns: list[float]) -> Optional[float]:
    if not returns:
        return None
    nav = 1.0
    for daily_return in returns:
        nav *= 1.0 + daily_return
    if nav <= 0:
        return None
    years = len(returns) / ANNUALIZATION_DAYS
    if years <= 0:
        return None
    return (nav ** (1.0 / years)) - 1.0


def _annualized_volatility(returns: list[float]) -> Optional[float]:
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(ANNUALIZATION_DAYS)


def _downside_deviation(returns: list[float]) -> Optional[float]:
    downside_returns = [r for r in returns if r < 0]
    if len(downside_returns) < 2:
        return None
    mean_square = sum(r ** 2 for r in downside_returns) / len(downside_returns)
    return math.sqrt(mean_square) * math.sqrt(ANNUALIZATION_DAYS)


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _alpha_beta(returns: list[float], benchmark_returns: list[float]) -> tuple[Optional[float], Optional[float]]:
    if len(returns) != len(benchmark_returns) or len(returns) < 2:
        return None, None
    benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)
    return_mean = sum(returns) / len(returns)
    variance = sum((b - benchmark_mean) ** 2 for b in benchmark_returns)
    if variance == 0:
        return None, None
    covariance = sum(
        (r - return_mean) * (b - benchmark_mean)
        for r, b in zip(returns, benchmark_returns)
    )
    beta = covariance / variance
    daily_alpha = return_mean - beta * benchmark_mean
    return daily_alpha * ANNUALIZATION_DAYS, beta
```

- [ ] **Step 4: Run performance tests and confirm they pass**

Run:

```bash
uv run pytest tests/unit/test_performance.py -v
```

Expected: PASS for all tests in `tests/unit/test_performance.py`.

- [ ] **Step 5: Commit performance slice**

Run:

```bash
git add src/performance.py tests/unit/test_performance.py
git commit -m "feat: calculate strategy performance metrics"
```

Expected: commit succeeds.

## Task 3: Combined Net Value And Drawdown Chart

**Files:**
- Create: `tests/unit/test_performance_charts.py`
- Create: `src/performance_charts.py`

- [ ] **Step 1: Write chart tests**

Create `tests/unit/test_performance_charts.py` with:

```python
"""
Unit tests for performance chart construction.
"""
from datetime import date

import plotly.graph_objects as go
import polars as pl
import pytest

from src.performance_charts import build_nav_drawdown_chart


@pytest.mark.unit
class TestBuildNavDrawdownChart:

    def test_build_nav_drawdown_chart_structure(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2), date(2024, 1, 3)],
            'strategy_nav': [1.0, 1.01],
            'strategy_drawdown': [0.0, -0.01],
            'benchmark_nav': [1.0, 0.99],
            'benchmark_drawdown': [0.0, -0.01],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        fig = build_nav_drawdown_chart(df, ['strategy', 'benchmark'])

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 4
        assert fig.layout.xaxis.matches == 'x2'
        assert fig.layout.xaxis2.title.text == '日期'
        assert fig.layout.yaxis.title.text == '净值'
        assert fig.layout.yaxis2.title.text == '回撤'

    def test_build_nav_drawdown_chart_uses_consistent_colors(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2), date(2024, 1, 3)],
            'strategy_nav': [1.0, 1.01],
            'strategy_drawdown': [0.0, -0.01],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        fig = build_nav_drawdown_chart(df, ['strategy'])

        assert fig.data[0].line.color == fig.data[1].line.color
        assert fig.data[0].showlegend is True
        assert fig.data[1].showlegend is False
```

- [ ] **Step 2: Run chart tests and confirm they fail**

Run:

```bash
uv run pytest tests/unit/test_performance_charts.py -v
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'src.performance_charts'`.

- [ ] **Step 3: Implement `src/performance_charts.py`**

Create `src/performance_charts.py` with:

```python
"""
Plotly chart builders for strategy performance views.
"""
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORWAY = [
    '#1f77b4',
    '#d62728',
    '#2ca02c',
    '#9467bd',
    '#ff7f0e',
    '#17becf',
    '#8c564b',
    '#e377c2',
]


def build_nav_drawdown_chart(nav_drawdown_df: pl.DataFrame, series_names: list[str]) -> go.Figure:
    """Build one figure with net value and drawdown subplots sharing x-axis."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.65, 0.35],
        subplot_titles=('收益/净值曲线', '回撤曲线'),
    )

    dates = nav_drawdown_df['datetime'].to_list()
    for index, name in enumerate(series_names):
        color = COLORWAY[index % len(COLORWAY)]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=nav_drawdown_df[f'{name}_nav'].to_list(),
                mode='lines',
                name=name,
                line=dict(color=color),
                showlegend=True,
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=nav_drawdown_df[f'{name}_drawdown'].to_list(),
                mode='lines',
                name=f'{name} 回撤',
                line=dict(color=color),
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=720,
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
    )
    fig.update_yaxes(title_text='净值', row=1, col=1)
    fig.update_yaxes(title_text='回撤', tickformat='.1%', row=2, col=1)
    fig.update_xaxes(title_text='日期', row=2, col=1)

    return fig
```

- [ ] **Step 4: Run chart tests and confirm they pass**

Run:

```bash
uv run pytest tests/unit/test_performance_charts.py -v
```

Expected: PASS for all tests in `tests/unit/test_performance_charts.py`.

- [ ] **Step 5: Commit chart slice**

Run:

```bash
git add src/performance_charts.py tests/unit/test_performance_charts.py
git commit -m "feat: build performance comparison chart"
```

Expected: commit succeeds.

## Task 4: New Streamlit Risk/Return Page

**Files:**
- Create: `pages/1_策略风险收益评估.py`

- [ ] **Step 1: Create the Streamlit page**

Create `pages/1_策略风险收益评估.py` with:

```python
"""
Strategy risk/return evaluation Streamlit page.
"""
from datetime import date
from typing import Optional

import polars as pl
import streamlit as st

from src.performance import (
    calculate_metrics_table,
    calculate_nav_and_drawdown,
    calculate_recent_returns,
    filter_returns_by_date,
    resolve_date_range,
)
from src.performance_charts import build_nav_drawdown_chart
from src.pnl_loader import get_return_columns, load_pnl_data


RANGE_OPTIONS = ['全部', '最近 5 年', '最近 3 年', '最近 1 年', 'YTD', '自定义']


def main():
    st.set_page_config(
        page_title='策略风险收益评估',
        layout='wide',
        initial_sidebar_state='expanded',
    )
    st.title('策略风险收益评估及对比')

    if 'pnl_df' not in st.session_state:
        st.session_state.pnl_df = None
    if 'pnl_columns' not in st.session_state:
        st.session_state.pnl_columns = []

    with st.sidebar:
        st.header('数据加载')
        pnl_path = st.text_input(
            'pnl.csv 路径',
            value='sample_data/pnl.csv',
            help='输入每日收益率 CSV 文件路径',
        )

        if st.button('加载收益数据', type='primary'):
            try:
                st.session_state.pnl_df = load_pnl_data(pnl_path)
                st.session_state.pnl_columns = get_return_columns(st.session_state.pnl_df)
                st.success(f'数据加载成功！共 {len(st.session_state.pnl_columns)} 个收益序列')
            except (FileNotFoundError, ValueError) as exc:
                st.session_state.pnl_df = None
                st.session_state.pnl_columns = []
                st.error(str(exc))

    if st.session_state.pnl_df is None:
        st.info('请在左侧加载 pnl.csv 数据')
        return

    pnl_df: pl.DataFrame = st.session_state.pnl_df
    return_columns: list[str] = st.session_state.pnl_columns

    selected_series = st.multiselect(
        '选择收益序列',
        options=return_columns,
        default=return_columns[: min(2, len(return_columns))],
        help='可选择一个或多个策略或指数列进行分析',
    )

    benchmark_options = ['不选择基准'] + return_columns
    benchmark_choice = st.selectbox(
        '选择基准',
        options=benchmark_options,
        index=0,
        help='第一版只支持选择当前 CSV 中的一列作为基准',
    )
    benchmark = None if benchmark_choice == '不选择基准' else benchmark_choice

    if not selected_series:
        st.warning('请至少选择一个收益序列')
        return

    range_label = st.radio(
        '时间范围',
        options=RANGE_OPTIONS,
        horizontal=True,
        index=0,
    )

    custom_range: Optional[tuple[date, date]] = None
    min_date = pnl_df['datetime'].min()
    max_date = pnl_df['datetime'].max()
    if range_label == '自定义':
        cols = st.columns(2)
        with cols[0]:
            custom_start = st.date_input(
                '起始日期',
                value=min_date,
                min_value=min_date,
                max_value=max_date,
            )
        with cols[1]:
            custom_end = st.date_input(
                '结束日期',
                value=max_date,
                min_value=min_date,
                max_value=max_date,
            )
        custom_range = (custom_start, custom_end)

    start_date, end_date = resolve_date_range(pnl_df, range_label, custom_range)
    if start_date > end_date:
        st.warning('起始日期不能晚于结束日期')
        return

    filtered_df = filter_returns_by_date(pnl_df, start_date, end_date)
    if filtered_df.is_empty():
        st.warning('当前时间范围内没有数据')
        return

    st.caption(f'分析区间：{start_date} 至 {end_date}')

    nav_drawdown_df = calculate_nav_and_drawdown(filtered_df, selected_series)
    fig = build_nav_drawdown_chart(nav_drawdown_df, selected_series)
    st.plotly_chart(fig, use_container_width=True)

    recent_returns = calculate_recent_returns(filtered_df, selected_series)
    metrics = calculate_metrics_table(filtered_df, selected_series, benchmark=benchmark)

    st.subheader('最近收益情况')
    st.dataframe(
        _format_recent_returns(recent_returns),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader('风险收益评估')
    st.dataframe(
        _format_metrics(metrics).style.apply(_highlight_best_metrics, axis=None),
        use_container_width=True,
        hide_index=True,
    )


def _format_recent_returns(df: pl.DataFrame) -> pl.DataFrame:
    return df.select([
        pl.col('series').alias('收益序列'),
        pl.col('latest_nav').round(4).alias('最新净值'),
        (pl.col('wtd_return') * 100).round(2).alias('WTD(%)'),
        (pl.col('mtd_return') * 100).round(2).alias('MTD(%)'),
        (pl.col('ytd_return') * 100).round(2).alias('YTD(%)'),
        (pl.col('year_max_drawdown') * 100).round(2).alias('本年最大回撤(%)'),
        (pl.col('current_drawdown') * 100).round(2).alias('当前回撤(%)'),
    ])


def _format_metrics(df: pl.DataFrame) -> pl.DataFrame:
    return df.select([
        pl.col('series').alias('收益序列'),
        _percent_col('annualized_return', '年化收益率(%)'),
        _percent_col('annualized_volatility', '年化波动率(%)'),
        _percent_col('excess_annualized_return', '超额年化收益率(%)'),
        _percent_col('excess_annualized_volatility', '超额年化波动率(%)'),
        pl.col('sharpe_ratio').round(4).alias('夏普率'),
        _percent_col('max_drawdown', '最大回撤(%)'),
        pl.col('sortino_ratio').round(4).alias('索提诺比率'),
        pl.col('calmar_ratio').round(4).alias('卡玛比率'),
        pl.col('information_ratio').round(4).alias('信息比例'),
        _percent_col('alpha', 'Alpha(%)'),
        pl.col('beta').round(4).alias('Beta'),
    ]).to_pandas().fillna('-')


def _percent_col(source: str, alias: str) -> pl.Expr:
    return (pl.col(source) * 100).round(2).alias(alias)


def _highlight_best_metrics(data):
    styles = data.copy()
    styles.loc[:, :] = ''
    higher_better = [
        '年化收益率(%)',
        '超额年化收益率(%)',
        '夏普率',
        '索提诺比率',
        '卡玛比率',
        '信息比例',
        'Alpha(%)',
    ]
    lower_better = [
        '年化波动率(%)',
        '超额年化波动率(%)',
    ]
    closest_to_zero = ['最大回撤(%)']

    for col in higher_better:
        numeric = _numeric_column(data[col])
        if not numeric.empty:
            styles.loc[numeric.idxmax(), col] = 'background-color: #d4edda'

    for col in lower_better:
        numeric = _numeric_column(data[col])
        if not numeric.empty:
            styles.loc[numeric.idxmin(), col] = 'background-color: #d4edda'

    for col in closest_to_zero:
        numeric = _numeric_column(data[col])
        if not numeric.empty:
            styles.loc[numeric.abs().idxmin(), col] = 'background-color: #d4edda'

    return styles


def _numeric_column(series):
    return series.replace('-', None).dropna().astype(float)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run new page import smoke check**

Run:

```bash
uv run python -m py_compile pages/1_策略风险收益评估.py
```

Expected: command exits with status 0.

- [ ] **Step 3: Run all unit tests**

Run:

```bash
uv run pytest tests/unit -v
```

Expected: PASS for all unit tests.

- [ ] **Step 4: Commit page slice**

Run:

```bash
git add pages/1_策略风险收益评估.py
git commit -m "feat: add strategy risk return page"
```

Expected: commit succeeds.

## Task 5: Page Compatibility Fixes

**Files:**
- Modify if tests reveal issues: `src/performance.py`
- Modify if tests reveal issues: `src/performance_charts.py`
- Modify if tests reveal issues: `pages/1_策略风险收益评估.py`

- [ ] **Step 1: Run a focused integration smoke from real sample data**

Run:

```bash
uv run python -c "from src.pnl_loader import load_pnl_data, get_return_columns; from src.performance import calculate_nav_and_drawdown, calculate_metrics_table, calculate_recent_returns; df=load_pnl_data('sample_data/pnl.csv'); cols=get_return_columns(df); selected=cols[:2]; print(cols); print(calculate_nav_and_drawdown(df, selected).height); print(calculate_metrics_table(df, selected, benchmark=cols[0]).height); print(calculate_recent_returns(df, selected).height)"
```

Expected: prints the available return columns and three positive row counts without exceptions.

- [ ] **Step 2: Fix any pandas dependency issue from Streamlit styling**

If Step 1 passes but page validation fails because `pandas` is unavailable, inspect whether Streamlit installed pandas transitively:

```bash
uv run python -c "import pandas; print(pandas.__version__)"
```

Expected: prints a pandas version. If it fails, modify `pyproject.toml` to add:

```toml
dependencies = [
    "pandas>=2.3.0",
    "plotly>=6.7.0",
    "polars>=1.39.3",
    "streamlit>=1.56.0",
]
```

Then run:

```bash
uv sync
uv run pytest tests/unit -v
```

Expected: dependency sync succeeds and unit tests pass.

- [ ] **Step 3: Commit compatibility fixes if any were needed**

If Step 2 changed `pyproject.toml` or `uv.lock`, run:

```bash
git add pyproject.toml uv.lock
git commit -m "fix: include dataframe styling dependency"
```

Expected: commit succeeds. If no files changed, skip this step.

## Task 6: E2E Coverage For The New Page

**Files:**
- Modify: `tests/e2e/test_app.py`

- [ ] **Step 1: Add E2E helper constants and test class**

Modify `tests/e2e/test_app.py` by adding these constants near existing path constants:

```python
PNL_PATH = str(Path(__file__).parent.parent.parent / 'sample_data' / 'pnl.csv')
STRATEGY_PAGE_URL = 'http://localhost:8501/策略风险收益评估'
```

Append this test class after `TestMitraderUI`:

```python
@pytest.mark.e2e
class TestStrategyRiskReturnUI:

    def test_e2e_strategy_page_loads_pnl_and_renders_outputs(self, browser_page):
        """New multipage page loads pnl.csv and renders chart plus tables."""
        browser_page.goto(STRATEGY_PAGE_URL, wait_until='networkidle')

        inputs = browser_page.locator('[data-testid="stTextInput"] input').all()
        inputs[0].fill(PNL_PATH)
        browser_page.get_by_role('button', name='加载收益数据').click()

        browser_page.wait_for_selector('[data-testid="stAlertContentSuccess"]', timeout=20_000)
        assert '数据加载成功' in browser_page.locator('[data-testid="stAlertContentSuccess"]').inner_text()

        browser_page.wait_for_selector('[data-testid="stPlotlyChart"]', timeout=20_000)
        assert browser_page.locator('[data-testid="stPlotlyChart"]').is_visible()

        page_text = browser_page.inner_text('body')
        assert '最近收益情况' in page_text
        assert '风险收益评估' in page_text
        assert '最新净值' in page_text
        assert '年化收益率' in page_text
```

- [ ] **Step 2: Run E2E test for the new page**

Run:

```bash
uv run pytest tests/e2e/test_app.py::TestStrategyRiskReturnUI::test_e2e_strategy_page_loads_pnl_and_renders_outputs -v
```

Expected: PASS, or SKIP if Playwright is unavailable in the environment.

- [ ] **Step 3: Run the full E2E file**

Run:

```bash
uv run pytest tests/e2e/test_app.py -v
```

Expected: existing K-line tests still pass, and the new page test passes or skips only for missing Playwright.

- [ ] **Step 4: Commit E2E slice**

Run:

```bash
git add tests/e2e/test_app.py
git commit -m "test: cover strategy risk return page"
```

Expected: commit succeeds.

## Task 7: Full Verification And Graph Update

**Files:**
- Modify generated graph artifacts as produced by `graphify update .`

- [ ] **Step 1: Run full pytest suite**

Run:

```bash
uv run pytest
```

Expected: PASS for unit and integration tests. E2E tests pass or skip only when Playwright/browser dependencies are unavailable.

- [ ] **Step 2: Run graphify update**

Run:

```bash
graphify update .
```

Expected: graphify completes and updates generated graph artifacts.

- [ ] **Step 3: Inspect graphify changes**

Run:

```bash
git status --short
```

Expected: code/test changes are already committed by earlier tasks. Graph changes may appear under `graphify-out/`. Do not stage unrelated `graphify-out/cache` churn unless graph maintenance is explicitly desired.

- [ ] **Step 4: Commit intended graph artifacts**

If `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json`, `graphify-out/graph.html`, `graphify-out/manifest.json`, or `graphify-out/cost.json` changed and should be recorded, run:

```bash
git add graphify-out/GRAPH_REPORT.md graphify-out/graph.json graphify-out/graph.html graphify-out/manifest.json graphify-out/cost.json
git commit -m "docs: update codebase graph"
```

Expected: commit succeeds. If only `graphify-out/cache` changed, skip this commit unless explicitly instructed.

- [ ] **Step 5: Final status check**

Run:

```bash
git status --short
```

Expected: either clean, or only intentionally untracked user files remain such as `docs/features.md`.

## Self-Review

- Spec coverage:
  - Local CSV loading: Task 1.
  - Multi-select analysis series and optional benchmark: Task 4.
  - Date ranges including YTD/custom: Task 2 and Task 4.
  - Shared-x net value/drawdown subplots: Task 3 and Task 4.
  - Risk/return metrics: Task 2 and Task 4.
  - Recent returns: Task 2 and Task 4.
  - Error handling: Task 1, Task 2, Task 4.
  - Unit and E2E tests: Tasks 1, 2, 3, 6.
  - Graphify update: Task 7.

- Placeholder scan:
  - No unresolved marker words are intentionally left.
  - The only conditional steps are explicit compatibility and graph-artifact decisions based on actual command output.

- Type consistency:
  - Date column is consistently `datetime`.
  - Return series arguments are consistently `list[str]`.
  - Missing metric values are consistently represented as `None` in calculation outputs and displayed as `-` in the page.
