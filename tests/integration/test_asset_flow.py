"""
Integration tests for end-to-end asset selection flow (3 tests).
"""
from datetime import date

import polars as pl
import pytest

from src.data_loader import (
    load_trade_data,
    load_price_data,
    get_asset_list,
    get_asset_trades,
    get_asset_prices,
    filter_assets,
)
from src.chart_builder import build_candlestick_chart


@pytest.mark.integration
class TestFullAssetFlow:

    def test_full_asset_flow(self, sample_trade_path, sample_prices_path):
        """Load → get asset list → filter → get detail: data stays consistent."""
        trade_df = load_trade_data(sample_trade_path)
        price_df = load_price_data(sample_prices_path)

        asset_list = get_asset_list(trade_df, price_df)
        assert len(asset_list) > 0

        # Pick first asset from list
        asset_id = asset_list['asset_id'][0]

        # Filter list by that id
        filtered = filter_assets(asset_list, asset_id)
        assert len(filtered) > 0
        assert filtered['asset_id'][0] == asset_id

        # Fetch detail data
        asset_trades = get_asset_trades(trade_df, asset_id)
        asset_prices = get_asset_prices(price_df, asset_id)

        assert len(asset_trades) > 0
        assert len(asset_prices) > 0

        # All trade records belong to the selected asset
        assert all(r == asset_id for r in asset_trades['asset'].to_list())

    def test_chart_with_trades(self, minimal_trade_df, minimal_price_df):
        """Trade markers are plotted on the correct dates in the chart."""
        import plotly.graph_objects as go

        asset_trades = minimal_trade_df.filter(pl.col('asset') == '111001')
        asset_prices = minimal_price_df  # bond_id='111001'

        fig = build_candlestick_chart(asset_prices, asset_trades, '测试债券A')

        assert isinstance(fig, go.Figure)
        # At least candlestick + buy marker
        assert len(fig.data) >= 2

        # Buy marker x-dates must be a subset of trade dates
        trade_dates = set(asset_trades['date'].to_list())
        buy_trace = next((t for t in fig.data if t.name == '买入点'), None)
        if buy_trace is not None:
            for d in buy_trace.x:
                assert d in trade_dates

    def test_chart_date_range_filter(self, minimal_trade_df, minimal_price_df):
        """Date range filter restricts price data shown in the chart."""
        asset_trades = minimal_trade_df.filter(pl.col('asset') == '111001')

        start = date(2026, 4, 2)
        end = date(2026, 4, 4)
        fig = build_candlestick_chart(
            minimal_price_df, asset_trades, '测试债券A',
            date_range=(start, end)
        )

        # Candlestick x-axis should only contain dates within [start, end]
        candlestick = fig.data[0]
        for d in candlestick.x:
            assert start <= d <= end
