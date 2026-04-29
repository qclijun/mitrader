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
    """Resolve a UI range label to concrete inclusive start/end dates."""
    min_date = df[DATE_COLUMN].min()
    max_date = df[DATE_COLUMN].max()

    if range_label == '自定义':
        if custom_range is None:
            raise ValueError("Custom date range is required")
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
        return max(max_date - timedelta(days=days_by_label[range_label] - 1), min_date), max_date

    raise ValueError(f"Unknown date range: {range_label}")


def filter_returns_by_date(df: pl.DataFrame, start_date: date, end_date: date) -> pl.DataFrame:
    """Filter returns to the inclusive Analysis Range."""
    return df.filter(
        (pl.col(DATE_COLUMN) >= start_date)
        & (pl.col(DATE_COLUMN) <= end_date)
    )


def calculate_nav_and_drawdown(df: pl.DataFrame, series_names: list[str]) -> pl.DataFrame:
    """Calculate compounded net value and drawdown for selected series."""
    result = df.select(DATE_COLUMN)
    for name in series_names:
        nav_values = []
        drawdown_values = []
        nav = 1.0
        running_max = 1.0
        for daily_return in df[name].to_list():
            nav *= 1.0 + float(daily_return)
            running_max = max(running_max, nav)
            nav_values.append(nav)
            drawdown_values.append((nav / running_max) - 1.0 if running_max else 0.0)

        result = result.with_columns(
            pl.Series(f'{name}_nav', nav_values),
            pl.Series(f'{name}_drawdown', drawdown_values),
        )
    return result


def calculate_recent_returns(df: pl.DataFrame, series_names: list[str]) -> pl.DataFrame:
    """Calculate latest NAV plus WTD, MTD, YTD, and current-year drawdowns."""
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

        year_df = filter_returns_by_date(df, year_start, last_date)
        year_drawdowns = _period_drawdowns(year_df[name].to_list())
        year_max_drawdown = min(year_drawdowns)
        current_drawdown = year_drawdowns[-1]

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
    benchmark_returns = [float(v) for v in df[benchmark].to_list()] if benchmark else None

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

        if benchmark_returns is not None and name != benchmark:
            excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]
            row['excess_annualized_return'] = _annualized_return(excess_returns)
            row['excess_annualized_volatility'] = _annualized_volatility(excess_returns)
            row['information_ratio'] = _safe_div(
                row['excess_annualized_return'],
                row['excess_annualized_volatility'],
            )
            alpha, beta = _alpha_beta(returns, benchmark_returns)
            row['alpha'] = alpha
            row['beta'] = beta

        rows.append(row)

    return pl.DataFrame(rows)


def _compound_range_return(
    df: pl.DataFrame,
    series_name: str,
    start_date: date,
    end_date: date,
) -> Optional[float]:
    range_df = filter_returns_by_date(df, start_date, end_date)
    if range_df.is_empty():
        return None
    nav = 1.0
    for daily_return in range_df[series_name].to_list():
        nav *= 1.0 + float(daily_return)
    return nav - 1.0


def _period_drawdowns(returns: list[float]) -> list[float]:
    if not returns:
        return []
    nav = 1.0
    drawdowns = []
    running_max = 1.0
    for daily_return in returns:
        nav *= 1.0 + float(daily_return)
        running_max = max(running_max, nav)
        drawdowns.append((nav / running_max) - 1.0 if running_max else 0.0)
    return drawdowns


def _annualized_return(returns: list[float]) -> Optional[float]:
    if not returns:
        return None
    nav = 1.0
    for daily_return in returns:
        nav *= 1.0 + daily_return
    if nav < 0:
        return None
    if nav == 0:
        return -1.0
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


def _alpha_beta(
    returns: list[float],
    benchmark_returns: list[float],
) -> tuple[Optional[float], Optional[float]]:
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
