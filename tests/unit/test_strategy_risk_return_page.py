"""
Unit tests for strategy risk/return page table formatting.
"""
from importlib import util
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
class TestMetricsHighlighting:

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
