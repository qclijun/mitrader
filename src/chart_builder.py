"""
Plotly chart building module for K-line visualization.
"""
import polars as pl
import plotly.graph_objects as go
from typing import Optional


def build_candlestick_chart(
    price_df: pl.DataFrame,
    trade_df: pl.DataFrame,
    asset_nm: str,
    date_range: Optional[tuple] = None
) -> go.Figure:
    """Build interactive candlestick chart with buy/sell markers.

    Args:
        price_df: Price data for the asset
        trade_df: Trade records for the asset
        asset_nm: Asset name for chart title
        date_range: Optional (start_date, end_date) tuple to filter

    Returns:
        Plotly Figure object
    """
    # Filter by date range if provided
    if date_range:
        start_date, end_date = date_range
        price_df = price_df.filter(
            (pl.col('trade_date') >= start_date) &
            (pl.col('trade_date') <= end_date)
        )

    # Build candlestick
    fig = go.Figure()

    candlestick = go.Candlestick(
        x=price_df['trade_date'].to_list(),
        open=price_df['open'].to_list(),
        high=price_df['high'].to_list(),
        low=price_df['low'].to_list(),
        close=price_df['price'].to_list(),
        name='K线',
        increasing_line_color='red',  # 中国股市惯例：涨红跌绿
        decreasing_line_color='green'
    )
    fig.add_trace(candlestick)

    # Separate buy and sell trades
    buy_trades = trade_df.filter(pl.col('size') > 0)
    sell_trades = trade_df.filter(pl.col('size') < 0)

    # Add buy markers (green up arrow)
    if len(buy_trades) > 0:
        fig.add_trace(go.Scatter(
            x=buy_trades['date'].to_list(),
            y=buy_trades['price'].to_list(),
            mode='markers+text',
            marker=dict(
                symbol='triangle-up',
                size=15,
                color='green',
                line=dict(color='darkgreen', width=1)
            ),
            text=['买入'] * len(buy_trades),
            textposition='top center',
            name='买入点'
        ))

    # Add sell markers (red down arrow) with return rate annotation
    if len(sell_trades) > 0:
        sell_dates = sell_trades['date'].to_list()
        sell_prices = sell_trades['price'].to_list()
        pnlcomm_values = sell_trades['pnlcomm'].to_list()

        # Format return rate text
        return_texts = [
            f"卖出\n{p:+.2f}" if p != 0 else "卖出"
            for p in pnlcomm_values
        ]

        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers+text',
            marker=dict(
                symbol='triangle-down',
                size=15,
                color='red',
                line=dict(color='darkred', width=1)
            ),
            text=return_texts,
            textposition='bottom center',
            name='卖出点'
        ))

    # Update layout
    fig.update_layout(
        title=f'{asset_nm} K线图',
        xaxis_title='日期',
        yaxis_title='价格',
        xaxis_rangeslider_visible=False,
        height=700,
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

    # Remove weekend gaps (common for stock data)
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=['sat', 'mon'])  # Hide weekends
        ]
    )

    return fig


def get_trade_table_data(trade_df: pl.DataFrame) -> list:
    """Convert trade DataFrame to list of dicts for table display.

    Args:
        trade_df: Trade records for an asset

    Returns:
        List of row dicts with formatted values
    """
    rows = []
    for row in trade_df.iter_rows(named=True):
        row_data = {
            '日期': str(row['date']),
            '类型': '买入' if row['size'] > 0 else '卖出',
            '价格': f"{row['price']:.2f}",
            '仓位': abs(row['size']),
            '手续费': f"{row['comm']:.2f}",
            'pnl': f"{row['pnl']:.2f}",
            'pnlcomm': f"{row['pnlcomm']:.2f}"
        }
        rows.append(row_data)
    return rows