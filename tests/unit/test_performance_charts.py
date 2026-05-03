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
            'strategy_nav': [1.01, 0.9999],
            'strategy_drawdown': [0.0, -0.01],
            'benchmark_nav': [0.99, 0.9801],
            'benchmark_drawdown': [-0.01, -0.0199],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        fig = build_nav_drawdown_chart(df, ['strategy', 'benchmark'], benchmark='benchmark')

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 4
        assert len(fig.layout.shapes) == 1
        assert fig.layout.xaxis.matches == 'x2'
        assert fig.layout.xaxis2.title.text == '日期'
        assert fig.layout.yaxis.title.text == '净值'
        assert fig.layout.yaxis2.title.text == '回撤'
        assert fig.layout.annotations[0].text == '累计净值'
        assert fig.layout.annotations[1].text == '回撤'
        assert fig.layout.hovermode == 'x unified'
        assert fig.layout.legend.orientation == 'h'
        assert fig.layout.legend.font.color == '#111827'

    def test_build_nav_drawdown_chart_uses_consistent_colors(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2), date(2024, 1, 3)],
            'strategy_nav': [1.01, 0.9999],
            'strategy_drawdown': [0.0, -0.01],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        fig = build_nav_drawdown_chart(df, ['strategy'])

        assert fig.data[0].line.color == fig.data[1].line.color
        assert fig.data[0].name == 'strategy'
        assert fig.data[0].showlegend is True
        assert fig.data[1].showlegend is False
        assert fig.data[0].hovertemplate == '%{y:.4f}<extra></extra>'
        assert fig.data[1].hovertemplate == '%{y:.2%}<extra></extra>'
        assert fig.data[1].fill == 'tozeroy'

    def test_build_nav_drawdown_chart_renders_benchmark_distinctly(self):
        df = pl.DataFrame({
            'datetime': [date(2024, 1, 2), date(2024, 1, 3)],
            'strategy_nav': [1.01, 0.9999],
            'strategy_drawdown': [0.0, -0.01],
            'benchmark_nav': [0.99, 0.9801],
            'benchmark_drawdown': [-0.01, -0.0199],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        fig = build_nav_drawdown_chart(df, ['strategy', 'benchmark'], benchmark='benchmark')

        strategy_nav = fig.data[0]
        strategy_drawdown = fig.data[1]
        benchmark_nav = fig.data[2]
        benchmark_drawdown = fig.data[3]

        assert strategy_nav.line.dash == 'solid'
        assert benchmark_nav.line.color == '#6b7280'
        assert benchmark_nav.line.dash == 'dash'
        assert benchmark_nav.line.width < strategy_nav.line.width
        assert benchmark_drawdown.line.color == benchmark_nav.line.color
        assert benchmark_drawdown.line.dash == 'dash'
        assert strategy_drawdown.fill == benchmark_drawdown.fill == 'tozeroy'
