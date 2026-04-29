"""
Unit tests for performance calculations.
"""
from datetime import date

import polars as pl
import pytest

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

    def test_resolve_date_range_custom_requires_custom_range(self):
        df = _returns_df()

        with pytest.raises(ValueError, match='Custom date range is required'):
            resolve_date_range(df, '自定义')

    def test_resolve_date_range_rejects_unknown_label(self):
        df = _returns_df()

        with pytest.raises(ValueError, match='Unknown date range'):
            resolve_date_range(df, '最近 2 年')

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

    def test_nav_stays_at_zero_after_total_loss(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2), date(2024, 1, 3)],
            'strategy': [-1.0, 0.50],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        result = calculate_nav_and_drawdown(df, ['strategy'])

        assert result['strategy_nav'].to_list() == [0.0, 0.0]
        assert result['strategy_drawdown'].to_list() == [-1.0, -1.0]


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

    def test_recent_returns_current_drawdown_uses_current_year(self):
        df = pl.DataFrame({
            'datetime': [
                date(2023, 12, 29),
                date(2024, 1, 2),
                date(2024, 1, 3),
            ],
            'strategy': [2.0, -1 / 3, -0.10],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        result = calculate_recent_returns(df, ['strategy'])
        row = result.row(0, named=True)

        assert row['latest_nav'] == pytest.approx(1.8)
        assert row['current_drawdown'] == pytest.approx(-0.10)
        assert row['year_max_drawdown'] == pytest.approx(-0.10)


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

    def test_single_observation_keeps_annualized_return_but_blanks_sample_stats(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2)],
            'strategy': [0.01],
            'benchmark': [0.0],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        result = calculate_metrics_table(df, ['strategy'], benchmark='benchmark')
        row = result.row(0, named=True)

        assert row['annualized_return'] is not None
        assert row['annualized_volatility'] is None
        assert row['sharpe_ratio'] is None
        assert row['alpha'] is None
        assert row['beta'] is None

    def test_minus_one_return_annualizes_to_minus_one(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2)],
            'strategy': [-1.0],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        result = calculate_metrics_table(df, ['strategy'], benchmark=None)
        row = result.row(0, named=True)

        assert row['annualized_return'] == pytest.approx(-1.0)
        assert row['max_drawdown'] == pytest.approx(-1.0)

    def test_constant_benchmark_blanks_regression_metrics(self):
        df = _full_year_df()

        result = calculate_metrics_table(df, ['strategy'], benchmark='benchmark')
        row = result.row(0, named=True)

        assert row['alpha'] is None
        assert row['beta'] is None


def test_annualization_days_is_252():
    assert ANNUALIZATION_DAYS == 252
