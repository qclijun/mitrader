"""
Plotly chart builders for strategy performance views.
"""
import plotly.graph_objects as go
import polars as pl
from plotly.subplots import make_subplots


COLORWAY = [
    '#1f77b4',
    '#d62728',
    '#2ca02c',
    '#9467bd',
    '#ff7f0e',
    '#17becf',
    '#8c564b',
    '#e377c2',
]


def build_nav_drawdown_chart(nav_drawdown_df: pl.DataFrame, series_names: list[str]) -> go.Figure:
    """Build one figure with net value and drawdown subplots sharing x-axis."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.65, 0.35],
        subplot_titles=('收益/净值曲线', '回撤曲线'),
    )

    dates = nav_drawdown_df['datetime'].to_list()
    for index, name in enumerate(series_names):
        color = COLORWAY[index % len(COLORWAY)]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=nav_drawdown_df[f'{name}_nav'].to_list(),
                mode='lines',
                name=name,
                line=dict(color=color),
                showlegend=True,
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=nav_drawdown_df[f'{name}_drawdown'].to_list(),
                mode='lines',
                name=f'{name} 回撤',
                line=dict(color=color),
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=720,
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
    )
    fig.update_yaxes(title_text='净值', row=1, col=1)
    fig.update_yaxes(title_text='回撤', tickformat='.1%', row=2, col=1)
    fig.update_xaxes(title_text='日期', row=2, col=1)

    return fig
