"""
mitrader - Trading Analysis Visualization Tool

Streamlit application for visualizing trade records on K-line charts.
"""
import streamlit as st
import polars as pl
from datetime import date, timedelta

from src.data_loader import (
    load_trade_data,
    load_price_data,
    get_asset_list,
    get_asset_trades,
    get_asset_prices,
    filter_assets
)
from src.chart_builder import (
    build_candlestick_chart,
    get_trade_table_data,
    style_trade_table
)


def main():
    st.set_page_config(
        page_title='mitrader - 交易分析工具',
        layout='wide',
        initial_sidebar_state='expanded'
    )

    st.title('mitrader - 交易记录 K 线图可视化')

    # Initialize session state
    if 'trade_df' not in st.session_state:
        st.session_state.trade_df = None
    if 'price_df' not in st.session_state:
        st.session_state.price_df = None
    if 'asset_list' not in st.session_state:
        st.session_state.asset_list = None
    if 'selected_asset_id' not in st.session_state:
        st.session_state.selected_asset_id = None

    # Sidebar: Data loading
    with st.sidebar:
        st.header('数据加载')

        trade_path = st.text_input(
            'trade.csv 路径',
            value='sample_data/trade.csv',
            help='输入交易记录 CSV 文件的路径'
        )

        price_path = st.text_input(
            'prices.parquet 路径',
            value='sample_data/prices.parquet',
            help='输入价格数据 Parquet 文件的路径'
        )

        if st.button('加载数据', type='primary'):
            try:
                st.session_state.trade_df = load_trade_data(trade_path)
                st.session_state.price_df = load_price_data(price_path)
                st.session_state.asset_list = get_asset_list(
                    st.session_state.trade_df,
                    st.session_state.price_df
                )
                st.success(f'数据加载成功！共 {len(st.session_state.asset_list)} 个资产')
            except FileNotFoundError as e:
                st.error(str(e))
            except ValueError as e:
                st.error(str(e))

        st.divider()

        # Asset selection
        st.header('资产选择')

        if st.session_state.asset_list is not None:
            search_term = st.text_input(
                '搜索过滤',
                placeholder='输入资产ID或名称',
                help='支持模糊搜索'
            )

            filtered_list = filter_assets(st.session_state.asset_list, search_term)

            # Display asset list as dataframe (single-row click selects asset)
            if len(filtered_list) > 0:
                event = st.dataframe(
                    filtered_list,
                    use_container_width=True,
                    hide_index=True,
                    on_select='rerun',
                    selection_mode='single-row',
                    column_config={
                        'asset_id': st.column_config.TextColumn('资产ID'),
                        'asset_nm': st.column_config.TextColumn('资产名称'),
                        'trade_count': st.column_config.NumberColumn('交易次数'),
                        'total_pnlcomm': st.column_config.NumberColumn('总收益', format='%.2f')
                    }
                )

                # Row click → update session state
                if event.selection.rows:
                    st.session_state.selected_asset_id = filtered_list['asset_id'][event.selection.rows[0]]

                # Default to first row if nothing selected yet (or selection no longer in list)
                asset_ids = filtered_list['asset_id'].to_list()
                if st.session_state.selected_asset_id not in asset_ids:
                    st.session_state.selected_asset_id = asset_ids[0]

                selected_asset = st.session_state.selected_asset_id
                st.caption(f'当前选中：{selected_asset}')
            else:
                st.warning('没有匹配的资产')
                selected_asset = None
        else:
            st.info('请先加载数据')
            selected_asset = None

        st.divider()

        # Date range control
        st.header('日期范围')

        if selected_asset and st.session_state.trade_df is not None:
            asset_trades = get_asset_trades(st.session_state.trade_df, selected_asset)
            asset_prices = get_asset_prices(st.session_state.price_df, selected_asset)

            first_trade = asset_trades['date'].min()
            last_trade = asset_trades['date'].max()
            price_min = asset_prices['trade_date'].min()
            price_max = asset_prices['trade_date'].max()

            default_start = max(first_trade - timedelta(days=30), price_min)
            default_end = min(last_trade + timedelta(days=30), price_max)

            start_date = st.date_input(
                '起始日期',
                value=default_start,
                min_value=price_min,
                max_value=price_max
            )

            end_date = st.date_input(
                '结束日期',
                value=default_end,
                min_value=price_min,
                max_value=price_max
            )

            date_range = (start_date, end_date)
        else:
            date_range = None

    # Main content area
    if selected_asset and st.session_state.trade_df is not None:
        # Get data for selected asset
        asset_trades = get_asset_trades(st.session_state.trade_df, selected_asset)
        asset_prices = get_asset_prices(st.session_state.price_df, selected_asset)

        # Get asset name
        asset_nm = st.session_state.asset_list.filter(
            pl.col('asset_id') == selected_asset
        ).select('asset_nm').item()

        # Build and display chart
        fig = build_candlestick_chart(
            asset_prices,
            asset_trades,
            asset_nm,
            date_range
        )

        st.plotly_chart(fig, use_container_width=True, height=700)

        # Trade details table (collapsible)
        with st.expander('交易详情', expanded=False):
            table_data = get_trade_table_data(asset_trades)
            styled_table = style_trade_table(table_data)

            st.dataframe(
                styled_table,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.info('请在左侧加载数据并选择资产')


if __name__ == '__main__':
    main()