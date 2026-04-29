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
            'strategy_nav': [1.01, 0.9999],
            'strategy_drawdown': [0.0, -0.01],
        }).with_columns(pl.col('datetime').cast(pl.Date))

        fig = build_nav_drawdown_chart(df, ['strategy'])

        assert fig.data[0].line.color == fig.data[1].line.color
        assert fig.data[0].showlegend is True
        assert fig.data[1].showlegend is False
