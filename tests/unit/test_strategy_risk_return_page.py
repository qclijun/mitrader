"""
Unit tests for strategy risk/return page table formatting.
"""
import py_compile
import tomllib
from datetime import date
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
class TestStrategyPageCompatibility:

    def test_strategy_page_compiles(self):
        py_compile.compile(PAGE_PATH, doraise=True)

    def test_pandas_is_direct_project_dependency(self):
        pyproject_path = PAGE_PATH.parents[1] / 'pyproject.toml'
        pyproject = tomllib.loads(pyproject_path.read_text())

        dependencies = pyproject['project']['dependencies']
        assert any(dependency.startswith('pandas') for dependency in dependencies)


@pytest.mark.unit
class TestStrategyTablePreparation:

    def test_chart_series_includes_hidden_benchmark_after_selected_series(self):
        page = _load_strategy_page_module()

        chart_series = page._chart_series(['strategy'], benchmark='jsl_index')

        assert chart_series == ['strategy', 'jsl_index']

    def test_chart_series_does_not_duplicate_visible_benchmark(self):
        page = _load_strategy_page_module()

        chart_series = page._chart_series(['strategy', 'jsl_index'], benchmark='jsl_index')

        assert chart_series == ['strategy', 'jsl_index']

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

    def test_tables_include_hidden_benchmark_series(self):
        page = _load_strategy_page_module()
        full_df = pl.DataFrame({
            'datetime': [
                date(2024, 1, 2),
                date(2024, 1, 3),
            ],
            'strategy': [0.10, -0.05],
            'jsl_index': [0.01, 0.02],
        }).with_columns(pl.col('datetime').cast(pl.Date))
        visible_series = page._chart_series(['strategy'], benchmark='jsl_index')

        recent_returns, metrics = page.prepare_strategy_tables(
            full_df,
            full_df,
            visible_series,
            benchmark='jsl_index',
        )

        assert recent_returns['series'].to_list() == ['strategy', 'jsl_index']
        assert metrics['series'].to_list() == ['strategy', 'jsl_index']
        benchmark_row = metrics.filter(pl.col('series') == 'jsl_index').row(0, named=True)
        assert benchmark_row['annualized_return'] is not None
        assert benchmark_row['excess_annualized_return'] is None
        assert benchmark_row['alpha'] is None
        assert benchmark_row['beta'] is None


@pytest.mark.unit
class TestStrategySummary:

    def test_summary_values_use_selected_series_for_headline_metrics(self):
        page = _load_strategy_page_module()
        metrics = pl.DataFrame({
            'series': ['strategy_a', 'strategy_b', 'jsl_index'],
            'annualized_return': [0.10, 0.18, 0.30],
            'max_drawdown': [-0.05, -0.12, -0.01],
        })

        summary = dict(page._summary_values(
            start_date=date(2024, 1, 2),
            end_date=date(2024, 12, 31),
            latest_date=date(2025, 1, 3),
            selected_count=2,
            benchmark='jsl_index',
            metrics=metrics,
            selected_series=['strategy_a', 'strategy_b'],
        ))

        assert summary['分析区间'] == '2024-01-02 至 2024-12-31'
        assert summary['最新数据'] == '2025-01-03'
        assert summary['收益序列'] == '2 个'
        assert summary['基准'] == 'jsl_index'
        assert summary['最佳年化收益'] == 'strategy_b 18.00%'
        assert summary['最低最大回撤'] == 'strategy_a -5.00%'

    def test_summary_values_show_dash_when_metrics_are_unavailable(self):
        page = _load_strategy_page_module()
        metrics = pl.DataFrame({
            'series': ['strategy'],
            'annualized_return': [None],
            'max_drawdown': [None],
        })

        summary = dict(page._summary_values(
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 3),
            latest_date=date(2024, 1, 3),
            selected_count=1,
            benchmark=None,
            metrics=metrics,
            selected_series=['strategy'],
        ))

        assert summary['基准'] == '未选择'
        assert summary['最佳年化收益'] == '-'
        assert summary['最低最大回撤'] == '-'

    def test_summary_html_escapes_labels_and_values(self):
        page = _load_strategy_page_module()

        html = page._summary_html([('基准', 'a<b&c')])

        assert 'summary-grid' in html
        assert 'summary-item' in html
        assert 'a&lt;b&amp;c' in html
        assert 'a<b&c' not in html


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
        assert row['最新累计净值'] == '1.2346'
        assert row['WTD'] == '1.23%'
        assert row['MTD'] == '-'
        assert row['YTD'] == '-5.68%'
        assert row['本年最大回撤'] == '-12.35%'
        assert row['本年当前回撤'] == '-'

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
        assert row['年化收益率'] == '12.35%'
        assert row['年化波动率'] == '-'
        assert row['超额年化收益率'] == '2.35%'
        assert row['超额年化波动率'] == '-'
        assert row['夏普率'] == '1.23'
        assert row['最大回撤'] == '-5.68%'
        assert row['索提诺比率'] == '-'
        assert row['卡玛比率'] == '-'
        assert row['信息比例'] == '-'
        assert row['Alpha'] == '3.46%'
        assert row['Beta'] == '0.9877'

    def test_metrics_are_split_into_core_and_benchmark_groups(self):
        page = _load_strategy_page_module()
        metrics = pl.DataFrame({
            'series': ['strategy'],
            'annualized_return': [0.12346],
            'annualized_volatility': [0.22346],
            'excess_annualized_return': [0.02346],
            'excess_annualized_volatility': [0.12346],
            'sharpe_ratio': [1.23456],
            'max_drawdown': [-0.05678],
            'sortino_ratio': [1.34567],
            'calmar_ratio': [2.34567],
            'information_ratio': [0.45678],
            'alpha': [0.03457],
            'beta': [0.98765],
        })

        core = page._format_core_metrics(metrics)
        benchmark = page._format_benchmark_metrics(metrics)

        assert core.columns.to_list() == [
            '收益序列',
            '年化收益率',
            '年化波动率',
            '夏普率',
            '最大回撤',
            '索提诺比率',
            '卡玛比率',
        ]
        assert benchmark.columns.to_list() == [
            '收益序列',
            '超额年化收益率',
            '超额年化波动率',
            '信息比例',
            'Alpha',
            'Beta',
        ]

    def test_dataframe_column_configs_cover_display_columns(self):
        page = _load_strategy_page_module()

        assert set(page._recent_returns_column_config()) == {
            '收益序列',
            '最新累计净值',
            'WTD',
            'MTD',
            'YTD',
            '本年最大回撤',
            '本年当前回撤',
        }
        assert set(page._core_metrics_column_config()) == {
            '收益序列',
            '年化收益率',
            '年化波动率',
            '夏普率',
            '最大回撤',
            '索提诺比率',
            '卡玛比率',
        }
        assert set(page._benchmark_metrics_column_config()) == {
            '收益序列',
            '超额年化收益率',
            '超额年化波动率',
            '信息比例',
            'Alpha',
            'Beta',
        }

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
