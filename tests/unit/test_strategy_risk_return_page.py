"""
Unit tests for strategy risk/return page table formatting.
"""
from importlib import util
from datetime import date
from pathlib import Path

import pandas as pd
import polars as pl
import pytest


PAGE_PATH = Path(__file__).resolve().parents[2] / 'pages' / '1_strategy_risk_return.py'


def _load_strategy_page_module():
    spec = util.spec_from_file_location('strategy_risk_return_page', PAGE_PATH)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
class TestStrategyTablePreparation:

    def test_recent_returns_use_full_loaded_data_while_metrics_use_analysis_range(self):
        page = _load_strategy_page_module()
        full_df = pl.DataFrame({
            'datetime': [
                date(2024, 1, 2),
                date(2024, 12, 30),
                date(2024, 12, 31),
            ],
            'strategy': [0.10, 0.20, -0.10],
        }).with_columns(pl.col('datetime').cast(pl.Date))
        analysis_df = full_df.filter(pl.col('datetime') == date(2024, 1, 2))

        recent_returns, metrics = page.prepare_strategy_tables(
            full_df,
            analysis_df,
            ['strategy'],
            benchmark=None,
        )

        recent_row = recent_returns.row(0, named=True)
        metrics_row = metrics.row(0, named=True)
        assert recent_row['latest_nav'] == pytest.approx(1.10 * 1.20 * 0.90)
        assert recent_row['wtd_return'] == pytest.approx((1.20 * 0.90) - 1)
        assert metrics_row['annualized_return'] == pytest.approx((1.10 ** 252) - 1)


@pytest.mark.unit
class TestMetricsHighlighting:

    def test_recent_returns_formatting_uses_percentages_and_dash_for_undefined_values(self):
        page = _load_strategy_page_module()
        recent_returns = pl.DataFrame({
            'series': ['strategy'],
            'latest_nav': [1.23456],
            'wtd_return': [0.01234],
            'mtd_return': [None],
            'ytd_return': [-0.05678],
            'year_max_drawdown': [-0.12346],
            'current_drawdown': [None],
        })

        formatted = page._format_recent_returns(recent_returns)
        row = formatted.iloc[0]

        assert row['收益序列'] == 'strategy'
        assert row['最新累计净值'] == pytest.approx(1.2346)
        assert row['WTD(%)'] == pytest.approx(1.23)
        assert row['MTD(%)'] == '-'
        assert row['YTD(%)'] == pytest.approx(-5.68)
        assert row['本年最大回撤(%)'] == pytest.approx(-12.35)
        assert row['本年当前回撤(%)'] == '-'

    def test_metric_formatting_uses_percentages_and_dash_for_undefined_values(self):
        page = _load_strategy_page_module()
        metrics = pl.DataFrame({
            'series': ['strategy'],
            'annualized_return': [0.12346],
            'annualized_volatility': [None],
            'excess_annualized_return': [0.02346],
            'excess_annualized_volatility': [None],
            'sharpe_ratio': [1.23456],
            'max_drawdown': [-0.05678],
            'sortino_ratio': [None],
            'calmar_ratio': [None],
            'information_ratio': [None],
            'alpha': [0.03457],
            'beta': [0.98765],
        })

        formatted = page._format_metrics(metrics)
        row = formatted.iloc[0]

        assert row['收益序列'] == 'strategy'
        assert row['年化收益率(%)'] == pytest.approx(12.35)
        assert row['年化波动率(%)'] == '-'
        assert row['超额年化收益率(%)'] == pytest.approx(2.35)
        assert row['夏普率'] == pytest.approx(1.2346)
        assert row['最大回撤(%)'] == pytest.approx(-5.68)
        assert row['索提诺比率'] == '-'
        assert row['Alpha(%)'] == pytest.approx(3.46)
        assert row['Beta'] == pytest.approx(0.9876)

    def test_undefined_metrics_do_not_participate_in_ranking(self):
        page = _load_strategy_page_module()
        data = pd.DataFrame({
            '收益序列': ['benchmark', 'strategy'],
            '超额年化收益率(%)': ['-', 2.5],
            '最大回撤(%)': ['-', -4.0],
        })

        styles = page._highlight_best_metrics(data)

        assert styles.loc[0, '超额年化收益率(%)'] == ''
        assert styles.loc[0, '最大回撤(%)'] == ''
        assert styles.loc[1, '超额年化收益率(%)'] == 'background-color: #d4edda'
        assert styles.loc[1, '最大回撤(%)'] == 'background-color: #d4edda'
