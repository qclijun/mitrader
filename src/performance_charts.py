"""
Plotly chart builders for strategy performance views.
"""
import plotly.graph_objects as go
import polars as pl
from plotly.subplots import make_subplots


COLORWAY = [
    '#2563eb',
    '#dc2626',
    '#16a34a',
    '#9333ea',
    '#ea580c',
    '#0891b2',
    '#be123c',
    '#4d7c0f',
]
BENCHMARK_COLOR = '#6b7280'


def build_nav_drawdown_chart(
    nav_drawdown_df: pl.DataFrame,
    series_names: list[str],
    benchmark: str | None = None,
) -> go.Figure:
    """Build one figure with net value and drawdown subplots sharing x-axis."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.65, 0.35],
        subplot_titles=('累计净值', '回撤'),
    )

    dates = nav_drawdown_df['datetime'].to_list()
    for index, name in enumerate(series_names):
        is_benchmark = benchmark == name
        color = BENCHMARK_COLOR if is_benchmark else COLORWAY[index % len(COLORWAY)]
        line_width = 1.6 if is_benchmark else 2.2
        line_dash = 'dash' if is_benchmark else 'solid'
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=nav_drawdown_df[f'{name}_nav'].to_list(),
                mode='lines',
                name=name,
                line=dict(color=color, width=line_width, dash=line_dash),
                showlegend=True,
                hovertemplate='%{y:.4f}<extra></extra>',
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
                line=dict(color=color, width=1.2, dash=line_dash),
                fill='tozeroy',
                fillcolor=_hex_to_rgba(color, 0.14 if is_benchmark else 0.18),
                showlegend=False,
                hovertemplate='%{y:.2%}<extra></extra>',
            ),
            row=2,
            col=1,
        )

    fig.add_hline(
        y=1.0,
        line_width=1,
        line_dash='dot',
        line_color='rgba(107, 114, 128, 0.7)',
        row=1,
        col=1,
    )
    fig.update_layout(
        height=720,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#111827'),
        margin=dict(l=48, r=24, t=72, b=44),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.04,
            xanchor='left',
            x=0,
            title_text='',
            font=dict(color='#111827'),
        ),
    )
    fig.update_yaxes(
        title_text='净值',
        title_font=dict(color='#111827', size=13),
        tickfont=dict(color='#374151', size=12),
        gridcolor='rgba(17, 24, 39, 0.08)',
        zeroline=False,
        automargin=True,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text='回撤',
        title_font=dict(color='#111827', size=13),
        tickfont=dict(color='#374151', size=12),
        tickformat='.1%',
        gridcolor='rgba(17, 24, 39, 0.08)',
        zeroline=False,
        automargin=True,
        row=2,
        col=1,
    )
    fig.update_xaxes(
        title_text='日期',
        title_font=dict(color='#111827', size=13),
        tickfont=dict(color='#374151', size=12),
        gridcolor='rgba(17, 24, 39, 0.06)',
        automargin=True,
        row=2,
        col=1,
    )
    fig.update_xaxes(
        tickfont=dict(color='#374151', size=12),
        gridcolor='rgba(17, 24, 39, 0.06)',
        automargin=True,
        row=1,
        col=1,
    )

    return fig


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    color = hex_color.lstrip('#')
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f'rgba({red}, {green}, {blue}, {alpha})'
