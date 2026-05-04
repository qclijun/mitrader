"""
Strategy risk/return evaluation Streamlit page.
"""
from datetime import date
from typing import Any, Optional

import pandas as pd
import polars as pl
import streamlit as st

from src.performance import (
    calculate_metrics_table,
    calculate_nav_and_drawdown,
    calculate_recent_returns,
    filter_returns_by_date,
    resolve_date_range,
)
from src.performance_charts import build_nav_drawdown_chart
from src.pnl_loader import get_return_columns, load_pnl_data


RANGE_OPTIONS = ['全部', '最近 5 年', '最近 3 年', '最近 1 年', 'YTD', '自定义']
SUMMARY_STYLE = """
<style>
.summary-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 0.5rem;
    margin: 0.25rem 0 0.75rem;
}
.summary-item {
    background: rgba(128, 128, 128, 0.08);
    border: 1px solid rgba(128, 128, 128, 0.28);
    border-radius: 0.375rem;
    padding: 0.45rem 0.55rem;
    min-width: 0;
}
.summary-label {
    color: var(--text-color);
    font-size: 0.72rem;
    line-height: 1.1;
    margin-bottom: 0.2rem;
    opacity: 0.7;
    white-space: nowrap;
}
.summary-value {
    color: var(--text-color);
    font-size: 0.88rem;
    font-weight: 600;
    line-height: 1.25;
    overflow-wrap: anywhere;
}
@media (max-width: 1100px) {
    .summary-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
</style>
"""


def main():
    st.set_page_config(
        page_title='策略风险收益评估',
        layout='wide',
        initial_sidebar_state='expanded',
    )
    st.title('策略风险收益')

    if 'pnl_df' not in st.session_state:
        st.session_state.pnl_df = None
    if 'pnl_columns' not in st.session_state:
        st.session_state.pnl_columns = []

    with st.sidebar:
        st.header('数据加载')
        pnl_path = st.text_input(
            'pnl.csv 路径',
            value='sample_data/pnl.csv',
            help='输入每日收益率 CSV 文件路径',
        )

        if st.button('加载收益数据', type='primary'):
            try:
                st.session_state.pnl_df = load_pnl_data(pnl_path)
                st.session_state.pnl_columns = get_return_columns(st.session_state.pnl_df)
                st.success(f'数据加载成功！共 {len(st.session_state.pnl_columns)} 个收益序列')
            except (FileNotFoundError, ValueError) as exc:
                st.session_state.pnl_df = None
                st.session_state.pnl_columns = []
                st.error(str(exc))

    if st.session_state.pnl_df is None:
        st.info('请在左侧加载 pnl.csv 数据')
        return

    pnl_df: pl.DataFrame = st.session_state.pnl_df
    return_columns: list[str] = st.session_state.pnl_columns

    control_cols = st.columns([2.2, 1.2, 2.1])
    with control_cols[0]:
        selected_series = st.multiselect(
            '收益序列',
            options=return_columns,
            default=return_columns[:1],
            help='可选择一个或多个策略或指数列进行分析',
        )
    with control_cols[1]:
        benchmark_options = ['不选择基准'] + return_columns
        benchmark_choice = st.selectbox(
            '基准',
            options=benchmark_options,
            index=0,
            help='基准用于计算超额收益、信息比例、Alpha 和 Beta',
        )
        benchmark = None if benchmark_choice == '不选择基准' else benchmark_choice
    with control_cols[2]:
        range_label = st.radio(
            '分析区间',
            options=RANGE_OPTIONS,
            horizontal=True,
            index=0,
        )

    custom_range: Optional[tuple[date, date]] = None
    min_date = pnl_df['datetime'].min()
    max_date = pnl_df['datetime'].max()
    if range_label == '自定义':
        cols = st.columns([1, 1, 3])
        with cols[0]:
            custom_start = st.date_input(
                '起始日期',
                value=min_date,
                min_value=min_date,
                max_value=max_date,
            )
        with cols[1]:
            custom_end = st.date_input(
                '结束日期',
                value=max_date,
                min_value=min_date,
                max_value=max_date,
            )
        custom_range = (custom_start, custom_end)

    if not selected_series:
        st.warning('请至少选择一个收益序列')
        return

    start_date, end_date = resolve_date_range(pnl_df, range_label, custom_range)
    if start_date > end_date:
        st.warning('起始日期不能晚于结束日期')
        return

    filtered_df = filter_returns_by_date(pnl_df, start_date, end_date)
    if filtered_df.is_empty():
        st.warning('当前时间范围内没有数据')
        return

    chart_series = _chart_series(selected_series, benchmark)
    recent_returns, metrics = prepare_strategy_tables(
        pnl_df,
        filtered_df,
        chart_series,
        benchmark=benchmark,
    )

    _render_summary(
        start_date=start_date,
        end_date=end_date,
        latest_date=max_date,
        selected_count=len(selected_series),
        benchmark=benchmark,
        metrics=metrics,
        selected_series=selected_series,
    )

    nav_drawdown_df = calculate_nav_and_drawdown(filtered_df, chart_series)
    fig = build_nav_drawdown_chart(nav_drawdown_df, chart_series, benchmark=benchmark)
    st.plotly_chart(fig, width='stretch')

    st.subheader('最近收益情况')
    st.dataframe(
        _format_recent_returns(recent_returns),
        width='stretch',
        hide_index=True,
        column_config=_recent_returns_column_config(),
    )

    st.subheader('风险收益评估')
    st.caption('核心指标')
    st.dataframe(
        _format_core_metrics(metrics),
        width='stretch',
        hide_index=True,
        column_config=_core_metrics_column_config(),
    )
    if benchmark:
        st.caption('基准指标')
        st.dataframe(
            _format_benchmark_metrics(metrics),
            width='stretch',
            hide_index=True,
            column_config=_benchmark_metrics_column_config(),
        )
    else:
        st.info('选择基准后显示超额收益、信息比例、Alpha 和 Beta')


def prepare_strategy_tables(
    loaded_df: pl.DataFrame,
    analysis_df: pl.DataFrame,
    selected_series: list[str],
    benchmark: Optional[str] = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Calculate page tables from their intended date scopes."""
    recent_returns = calculate_recent_returns(loaded_df, selected_series)
    metrics = calculate_metrics_table(analysis_df, selected_series, benchmark=benchmark)
    return recent_returns, metrics


def _chart_series(selected_series: list[str], benchmark: Optional[str] = None) -> list[str]:
    chart_series = list(selected_series)
    if benchmark and benchmark not in chart_series:
        chart_series.append(benchmark)
    return chart_series


def _render_summary(
    start_date: date,
    end_date: date,
    latest_date: date,
    selected_count: int,
    benchmark: Optional[str],
    metrics: pl.DataFrame,
    selected_series: list[str],
) -> None:
    summary = _summary_values(
        start_date=start_date,
        end_date=end_date,
        latest_date=latest_date,
        selected_count=selected_count,
        benchmark=benchmark,
        metrics=metrics,
        selected_series=selected_series,
    )
    st.markdown(SUMMARY_STYLE + _summary_html(summary), unsafe_allow_html=True)


def _summary_html(summary: list[tuple[str, str]]) -> str:
    items = ''.join(
        '<div class="summary-item">'
        f'<div class="summary-label">{_escape_html(label)}</div>'
        f'<div class="summary-value">{_escape_html(value)}</div>'
        '</div>'
        for label, value in summary
    )
    return f'<div class="summary-grid">{items}</div>'


def _escape_html(value: str) -> str:
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;')
    )


def _summary_values(
    start_date: date,
    end_date: date,
    latest_date: date,
    selected_count: int,
    benchmark: Optional[str],
    metrics: pl.DataFrame,
    selected_series: list[str],
) -> list[tuple[str, str]]:
    selected_metrics = metrics.filter(pl.col('series').is_in(selected_series))
    best_return = _best_metric_text(
        selected_metrics,
        metric='annualized_return',
        higher_is_better=True,
    )
    lowest_drawdown = _best_metric_text(
        selected_metrics,
        metric='max_drawdown',
        higher_is_better=True,
    )
    return [
        ('分析区间', f'{_format_date(start_date)} 至 {_format_date(end_date)}'),
        ('最新数据', _format_date(latest_date)),
        ('收益序列', f'{selected_count} 个'),
        ('基准', benchmark or '未选择'),
        ('最佳年化收益', best_return),
        ('最低最大回撤', lowest_drawdown),
    ]


def _best_metric_text(
    metrics: pl.DataFrame,
    metric: str,
    higher_is_better: bool,
) -> str:
    if metrics.is_empty() or metric not in metrics.columns:
        return '-'

    values = metrics.select([
        pl.col('series'),
        pl.col(metric).cast(pl.Float64, strict=False),
    ]).drop_nulls(metric)
    if values.is_empty():
        return '-'

    sorted_values = values.sort(metric, descending=higher_is_better)
    row = sorted_values.row(0, named=True)
    return f"{row['series']} {_format_percent(row[metric])}"


def _format_date(value: Any) -> str:
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def _format_percent(value: float) -> str:
    return f'{value * 100:.2f}%'


def _format_recent_returns(df: pl.DataFrame) -> pd.DataFrame:
    formatted = df.select([
        pl.col('series').alias('收益序列'),
        pl.col('latest_nav').cast(pl.Float64, strict=False).alias('最新累计净值'),
        pl.col('wtd_return').cast(pl.Float64, strict=False).alias('WTD'),
        pl.col('mtd_return').cast(pl.Float64, strict=False).alias('MTD'),
        pl.col('ytd_return').cast(pl.Float64, strict=False).alias('YTD'),
        pl.col('year_max_drawdown').cast(pl.Float64, strict=False).alias('本年最大回撤'),
        pl.col('current_drawdown').cast(pl.Float64, strict=False).alias('本年当前回撤'),
    ]).to_pandas()
    return _format_display_dataframe(
        formatted,
        percent_columns=['WTD', 'MTD', 'YTD', '本年最大回撤', '本年当前回撤'],
        number_columns={'最新累计净值': 4},
    )


def _format_metrics(df: pl.DataFrame) -> pd.DataFrame:
    return pd.concat([
        _format_core_metrics(df),
        _format_benchmark_metrics(df).drop(columns=['收益序列']),
    ], axis=1)


def _format_core_metrics(df: pl.DataFrame) -> pd.DataFrame:
    formatted = df.select([
        pl.col('series').alias('收益序列'),
        pl.col('annualized_return').cast(pl.Float64, strict=False).alias('年化收益率'),
        pl.col('annualized_volatility').cast(pl.Float64, strict=False).alias('年化波动率'),
        pl.col('sharpe_ratio').cast(pl.Float64, strict=False).alias('夏普率'),
        pl.col('max_drawdown').cast(pl.Float64, strict=False).alias('最大回撤'),
        pl.col('sortino_ratio').cast(pl.Float64, strict=False).alias('索提诺比率'),
        pl.col('calmar_ratio').cast(pl.Float64, strict=False).alias('卡玛比率'),
    ]).to_pandas()
    return _format_display_dataframe(
        formatted,
        percent_columns=['年化收益率', '年化波动率', '最大回撤'],
        number_columns={'夏普率': 2, '索提诺比率': 2, '卡玛比率': 2},
    )


def _format_benchmark_metrics(df: pl.DataFrame) -> pd.DataFrame:
    formatted = df.select([
        pl.col('series').alias('收益序列'),
        pl.col('excess_annualized_return').cast(pl.Float64, strict=False).alias('超额年化收益率'),
        pl.col('excess_annualized_volatility').cast(pl.Float64, strict=False).alias('超额年化波动率'),
        pl.col('information_ratio').cast(pl.Float64, strict=False).alias('信息比例'),
        pl.col('alpha').cast(pl.Float64, strict=False).alias('Alpha'),
        pl.col('beta').cast(pl.Float64, strict=False).alias('Beta'),
    ]).to_pandas()
    return _format_display_dataframe(
        formatted,
        percent_columns=['超额年化收益率', '超额年化波动率', 'Alpha'],
        number_columns={'信息比例': 2, 'Beta': 4},
    )


def _format_display_dataframe(
    data: pd.DataFrame,
    percent_columns: list[str],
    number_columns: dict[str, int],
) -> pd.DataFrame:
    formatted = data.copy()
    for column in percent_columns:
        formatted[column] = formatted[column].map(_format_percentage_cell)
    for column, decimals in number_columns.items():
        formatted[column] = formatted[column].map(lambda value, d=decimals: _format_number_cell(value, d))
    return formatted


def _format_percentage_cell(value: Any) -> str:
    if pd.isna(value):
        return '-'
    return f'{float(value) * 100:.2f}%'


def _format_number_cell(value: Any, decimals: int) -> str:
    if pd.isna(value):
        return '-'
    return f'{float(value):.{decimals}f}'


def _recent_returns_column_config() -> dict[str, Any]:
    return {
        '收益序列': st.column_config.TextColumn('收益序列', width='medium', pinned=True),
        '最新累计净值': st.column_config.TextColumn('最新累计净值', width='small'),
        'WTD': st.column_config.TextColumn('WTD', width='small'),
        'MTD': st.column_config.TextColumn('MTD', width='small'),
        'YTD': st.column_config.TextColumn('YTD', width='small'),
        '本年最大回撤': st.column_config.TextColumn('本年最大回撤', width='small'),
        '本年当前回撤': st.column_config.TextColumn('本年当前回撤', width='small'),
    }


def _core_metrics_column_config() -> dict[str, Any]:
    return {
        '收益序列': st.column_config.TextColumn('收益序列', width='medium', pinned=True),
        '年化收益率': st.column_config.TextColumn('年化收益率', width='small'),
        '年化波动率': st.column_config.TextColumn('年化波动率', width='small'),
        '夏普率': st.column_config.TextColumn('夏普率', width='small'),
        '最大回撤': st.column_config.TextColumn('最大回撤', width='small'),
        '索提诺比率': st.column_config.TextColumn('索提诺比率', width='small'),
        '卡玛比率': st.column_config.TextColumn('卡玛比率', width='small'),
    }


def _benchmark_metrics_column_config() -> dict[str, Any]:
    return {
        '收益序列': st.column_config.TextColumn('收益序列', width='medium', pinned=True),
        '超额年化收益率': st.column_config.TextColumn('超额年化收益率', width='small'),
        '超额年化波动率': st.column_config.TextColumn('超额年化波动率', width='small'),
        '信息比例': st.column_config.TextColumn('信息比例', width='small'),
        'Alpha': st.column_config.TextColumn('Alpha', width='small'),
        'Beta': st.column_config.TextColumn('Beta', width='small'),
    }


def _highlight_best_metrics(data: pd.DataFrame) -> pd.DataFrame:
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    higher_better = [
        '年化收益率(%)',
        '超额年化收益率(%)',
        '夏普率',
        '索提诺比率',
        '卡玛比率',
        '信息比例',
        'Alpha(%)',
    ]
    lower_better = [
        '年化波动率(%)',
        '超额年化波动率(%)',
    ]
    closest_to_zero = ['最大回撤(%)']

    for col in higher_better:
        if col not in data.columns:
            continue
        numeric = _numeric_column(data[col])
        if not numeric.empty:
            styles.loc[numeric.idxmax(), col] = 'background-color: #d4edda'

    for col in lower_better:
        if col not in data.columns:
            continue
        numeric = _numeric_column(data[col])
        if not numeric.empty:
            styles.loc[numeric.idxmin(), col] = 'background-color: #d4edda'

    for col in closest_to_zero:
        if col not in data.columns:
            continue
        numeric = _numeric_column(data[col])
        if not numeric.empty:
            styles.loc[numeric.abs().idxmin(), col] = 'background-color: #d4edda'

    return styles


def _numeric_column(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.rstrip('%').replace('-', None)
    return pd.to_numeric(cleaned, errors='coerce').dropna()


if __name__ == '__main__':
    main()
