"""
Unit tests for chart_builder module (5 tests).
"""
from datetime import date

import polars as pl
import pytest

from src.chart_builder import build_candlestick_chart, get_trade_table_data


def _make_price_df(n: int = 3) -> pl.DataFrame:
    return pl.DataFrame({
        'trade_date': [date(2026, 4, i + 1) for i in range(n)],
        'bond_id': ['111001'] * n,
        'bond_nm': ['债券A'] * n,
        'open': [100.0 + i for i in range(n)],
        'high': [102.0 + i for i in range(n)],
        'low': [99.0 + i for i in range(n)],
        'price': [101.0 + i for i in range(n)],
        'volume': [1000.0] * n,
    }).with_columns(pl.col('trade_date').cast(pl.Date))


def _make_trade_df(buys: int = 1, sells: int = 1, partial_sell: bool = False) -> pl.DataFrame:
    if buys == 0 and sells == 0:
        return pl.DataFrame({
            'date': pl.Series([], dtype=pl.Date),
            'size': pl.Series([], dtype=pl.Int64),
            'curr_size': pl.Series([], dtype=pl.Int64),
            'price': pl.Series([], dtype=pl.Float64),
            'comm': pl.Series([], dtype=pl.Float64),
            'pnl': pl.Series([], dtype=pl.Float64),
            'pnlcomm': pl.Series([], dtype=pl.Float64),
        })
    rows = []
    for i in range(buys):
        rows.append({
            'date': date(2026, 4, 1 + i),
            'size': 100,
            'curr_size': 100,
            'price': 100.0,
            'comm': 0.5,
            'pnl': 0.0,
            'pnlcomm': 0.0,
        })
    for i in range(sells):
        # partial_sell=True → curr_size stays > 0 (didn't fully close)
        rows.append({
            'date': date(2026, 4, 2 + buys + i),
            'size': -100,
            'curr_size': 50 if partial_sell else 0,
            'price': 102.0,
            'comm': 0.5,
            'pnl': 2.0,
            'pnlcomm': 1.5,
        })
    df = pl.DataFrame(rows)
    return df.with_columns(pl.col('date').cast(pl.Date))


@pytest.mark.unit
class TestBuildCandlestickChart:

    def test_build_candlestick_chart_empty_data(self):
        """Empty price DataFrame returns a Figure (no raise)."""
        import plotly.graph_objects as go

        empty_price = pl.DataFrame({
            'trade_date': pl.Series([], dtype=pl.Date),
            'open': pl.Series([], dtype=pl.Float64),
            'high': pl.Series([], dtype=pl.Float64),
            'low': pl.Series([], dtype=pl.Float64),
            'price': pl.Series([], dtype=pl.Float64),
        })
        empty_trade = _make_trade_df(0, 0)

        fig = build_candlestick_chart(empty_price, empty_trade, '空资产')

        assert isinstance(fig, go.Figure)

    def test_build_candlestick_chart_single_point(self):
        """Single price row still produces a valid Figure."""
        import plotly.graph_objects as go

        fig = build_candlestick_chart(_make_price_df(1), _make_trade_df(0, 0), '单点')

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_build_candlestick_chart_traces_count(self):
        """Chart with both buys and sells has 3 traces: K线 + 买入点 + 卖出点."""
        fig = build_candlestick_chart(_make_price_df(5), _make_trade_df(1, 1), '资产A')

        assert len(fig.data) == 3
        trace_names = [t.name for t in fig.data]
        assert 'K线' in trace_names
        assert '买入点' in trace_names
        assert '卖出点' in trace_names

    def test_buy_marker_text_includes_quantity(self):
        """Buy marker text includes the position quantity."""
        fig = build_candlestick_chart(_make_price_df(5), _make_trade_df(1, 0), '资产A')

        buy_trace = next(t for t in fig.data if t.name == '买入点')
        assert '100' in buy_trace.text[0]

    def test_full_close_sell_shows_return_percentage(self):
        """Full-close sell (curr_size==0) annotation includes return rate with '%'."""
        fig = build_candlestick_chart(_make_price_df(5), _make_trade_df(1, 1, partial_sell=False), '资产A')

        sell_trace = next(t for t in fig.data if t.name == '卖出点')
        text = sell_trace.text[0]
        assert '100' in text       # quantity
        assert '%' in text         # return rate

    def test_partial_sell_no_return_percentage(self):
        """Partial sell (curr_size>0) annotation has quantity but no return rate '%'."""
        fig = build_candlestick_chart(_make_price_df(5), _make_trade_df(1, 1, partial_sell=True), '资产A')

        sell_trace = next(t for t in fig.data if t.name == '卖出点')
        text = sell_trace.text[0]
        assert '100' in text       # quantity
        assert '%' not in text     # no return rate


@pytest.mark.unit
class TestGetTradeTableData:

    def test_get_trade_table_data_basic(self):
        """DataFrame converts to list of dicts with display column names."""
        trade_df = _make_trade_df(1, 1)
        result = get_trade_table_data(trade_df)

        assert isinstance(result, list)
        assert len(result) == 2
        assert '日期' in result[0]
        assert '类型' in result[0]
        assert '价格' in result[0]

    def test_get_trade_table_data_empty(self):
        """Empty DataFrame returns empty list."""
        empty = _make_trade_df(0, 0)
        result = get_trade_table_data(empty)

        assert result == []
