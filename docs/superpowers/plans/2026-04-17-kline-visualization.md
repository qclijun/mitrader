# K 线图可视化工具实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Streamlit Web 应用，读取交易记录和价格数据，生成带有买卖点标注的交互式 K 线图。

**Architecture:** 侧边栏包含数据加载、资产选择、日期控制；主区域显示 K 线图（占页面 70%+）和可折叠的交易详情表格。数据用 Polars 处理，图表用 Plotly 生成。

**Tech Stack:** Streamlit, Plotly, Polars

---

## 文件结构

```
mitrader/
├── app.py                    # Streamlit 主应用入口（侧边栏 + 主内容区）
├── src/
│   ├── __init__.py           # 空文件，标记为 Python 包
│   ├── data_loader.py        # 加载 CSV/Parquet，验证数据，获取资产列表
│   ├── chart_builder.py      # 构建 Plotly K 线图，添加买卖点标注
│   └── utils.py              # 计算收益率百分比等辅助函数
├── requirements.txt          # 依赖列表
├── sample_data/              # 示例数据（已存在）
└── docs/
    └── superpowers/
        └── specs/            # 设计文档（已存在）
        └── plans/            # 实现计划
```

---

### Task 1: 项目初始化与依赖管理

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
streamlit>=1.28.0
plotly>=5.18.0
polars>=0.20.0
```

- [ ] **Step 2: 创建 src 目录和 __init__.py**

```bash
mkdir -p src
touch src/__init__.py
```

- [ ] **Step 3: 验证环境**

运行命令验证依赖可安装（如果已安装则跳过）：
```bash
pip install -r requirements.txt
```

- [ ] **Step 4: 提交**

```bash
git add requirements.txt src/__init__.py
git commit -m "chore: init project structure and dependencies"
```

---

### Task 2: 数据加载模块

**Files:**
- Create: `src/data_loader.py`

- [ ] **Step 1: 编写数据加载函数**

```python
"""
Data loading and validation module.
"""
import polars as pl
from pathlib import Path
from typing import Optional


def load_trade_data(file_path: str) -> pl.DataFrame:
    """Load trade records from CSV file.
    
    Args:
        file_path: Path to trade.csv file
        
    Returns:
        Polars DataFrame with trade records
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If required columns are missing
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Trade file not found: {file_path}")
    
    df = pl.read_csv(file_path)
    
    # Validate required columns
    required_cols = ['asset', 'date', 'price', 'size', 'pnl', 'pnlcomm', 'open_datetime']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in trade.csv: {missing}")
    
    # Parse date column
    df = df.with_columns(
        pl.col('date').str.to_date('%Y-%m-%d').alias('date'),
        pl.col('open_datetime').str.to_date('%Y-%m-%d').alias('open_datetime')
    )
    
    return df


def load_price_data(file_path: str) -> pl.DataFrame:
    """Load price data from Parquet file.
    
    Args:
        file_path: Path to prices.parquet file
        
    Returns:
        Polars DataFrame with price data
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Price file not found: {file_path}")
    
    df = pl.read_parquet(file_path)
    
    # Convert trade_date to date type for matching
    df = df.with_columns(
        pl.col('trade_date').cast(pl.Date).alias('trade_date')
    )
    
    return df


def get_asset_list(trade_df: pl.DataFrame, price_df: pl.DataFrame) -> pl.DataFrame:
    """Get unique assets from trade records with their stats.
    
    Args:
        trade_df: Trade records DataFrame
        price_df: Price data DataFrame
        
    Returns:
        DataFrame with columns: asset_id, asset_nm, trade_count, total_pnlcomm
    """
    # Get bond_nm from price data
    asset_names = price_df.select(['bond_id', 'bond_nm']).unique()
    
    # Aggregate trade stats per asset
    trade_stats = trade_df.group_by('asset').agg([
        pl.len().alias('trade_count'),
        pl.col('pnlcomm').sum().alias('total_pnlcomm')
    ])
    
    # Join to get asset names
    result = trade_stats.join(
        asset_names,
        left_on='asset',
        right_on='bond_id',
        how='left'
    ).select([
        pl.col('asset').alias('asset_id'),
        pl.col('bond_nm').alias('asset_nm'),
        'trade_count',
        'total_pnlcomm'
    ]).sort('total_pnlcomm', descending=True)
    
    return result


def get_asset_trades(trade_df: pl.DataFrame, asset_id: str) -> pl.DataFrame:
    """Get all trades for a specific asset.
    
    Args:
        trade_df: Trade records DataFrame
        asset_id: Asset ID to filter
        
    Returns:
        DataFrame with trades for the asset, sorted by date
    """
    return trade_df.filter(pl.col('asset') == asset_id).sort('date')


def get_asset_prices(price_df: pl.DataFrame, asset_id: str) -> pl.DataFrame:
    """Get all price data for a specific asset.
    
    Args:
        price_df: Price data DataFrame  
        asset_id: Asset ID to filter
        
    Returns:
        DataFrame with price data for the asset, sorted by date
    """
    return price_df.filter(pl.col('bond_id') == asset_id).sort('trade_date')


def filter_assets(asset_list: pl.DataFrame, search_term: str) -> pl.DataFrame:
    """Filter asset list by search term (ID or name).
    
    Args:
        asset_list: Full asset list DataFrame
        search_term: Search string to filter by
        
    Returns:
        Filtered DataFrame
    """
    if not search_term:
        return asset_list
    
    search_lower = search_term.lower()
    return asset_list.filter(
        pl.col('asset_id').str.contains(search_lower) |
        pl.col('asset_nm').str.contains(search_lower.casefold())
    )
```

- [ ] **Step 2: 提交**

```bash
git add src/data_loader.py
git commit -m "feat: add data loader module for CSV and Parquet"
```

---

### Task 3: 辅助函数模块

**Files:**
- Create: `src/utils.py`

- [ ] **Step 1: 编写辅助函数**

```python
"""
Utility functions for calculations and formatting.
"""


def calculate_return_percentage(pnl: float, pnlcomm: float) -> str:
    """Calculate and format return percentage.
    
    Args:
        pnl: Gross profit/loss
        pnlcomm: Net profit/loss after commission
        
    Returns:
        Formatted string showing percentage
    """
    if pnlcomm == 0:
        return "0.00%"
    
    percentage = pnlcomm
    sign = "+" if percentage > 0 else ""
    return f"{sign}{percentage:.2f}"


def get_trade_type(size: int) -> str:
    """Determine trade type from position size.
    
    Args:
        size: Position size (positive = buy, negative = sell)
        
    Returns:
        '买入' or '卖出'
    """
    return "买入" if size > 0 else "卖出"


def format_trade_row(row: dict) -> dict:
    """Format a trade row for display.
    
    Args:
        row: Raw trade record dict
        
    Returns:
        Formatted dict with display-friendly values
    """
    return {
        '日期': row['date'],
        '类型': get_trade_type(row['size']),
        '价格': f"{row['price']:.2f}",
        '仓位': abs(row['size']),
        '手续费': f"{row['comm']:.2f}",
        'pnl': f"{row['pnl']:.2f}",
        'pnlcomm': f"{row['pnlcomm']:.2f}"
    }
```

- [ ] **Step 2: 提交**

```bash
git add src/utils.py
git commit -m "feat: add utility functions for formatting"
```

---

### Task 4: 图表构建模块

**Files:**
- Create: `src/chart_builder.py`

- [ ] **Step 1: 编写图表构建函数**

```python
"""
Plotly chart building module for K-line visualization.
"""
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
```

- [ ] **Step 2: 提交**

```bash
git add src/chart_builder.py
git commit -m "feat: add chart builder for candlestick with buy/sell markers"
```

---

### Task 5: Streamlit 主应用

**Files:**
- Create: `app.py`

- [ ] **Step 1: 编写 Streamlit 主应用**

```python
"""
mitrader - Trading Analysis Visualization Tool

Streamlit application for visualizing trade records on K-line charts.
"""
import streamlit as st
import polars as pl
from datetime import date

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
    get_trade_table_data
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
            
            # Display asset list as clickable dataframe
            if len(filtered_list) > 0:
                st.dataframe(
                    filtered_list,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'asset_id': st.column_config.TextColumn('资产ID'),
                        'asset_nm': st.column_config.TextColumn('资产名称'),
                        'trade_count': st.column_config.NumberColumn('交易次数'),
                        'total_pnlcomm': st.column_config.NumberColumn('总收益', format='%.2f')
                    }
                )
                
                # Asset selection
                asset_ids = filtered_list['asset_id'].to_list()
                selected_asset = st.selectbox(
                    '选择资产',
                    options=asset_ids,
                    help='选择要查看的资产'
                )
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
            
            min_date = asset_trades['date'].min()
            max_date = asset_trades['date'].max()
            
            start_date = st.date_input(
                '起始日期',
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )
            
            end_date = st.date_input(
                '结束日期',
                value=max_date,
                min_value=min_date,
                max_value=max_date
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
            
            # Highlight buy/sell rows
            def highlight_row(row):
                if row['类型'] == '买入':
                    return ['background-color: #e6ffe6'] * len(row)
                else:
                    return ['background-color: #ffe6e6'] * len(row)
            
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )
    
    else:
        st.info('请在左侧加载数据并选择资产')


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 提交**

```bash
git add app.py
git commit -m "feat: add Streamlit main application with sidebar layout"
```

---

### Task 6: 验证运行

**Files:**
- None (验证步骤)

- [ ] **Step 1: 启动应用**

```bash
streamlit run app.py
```

预期结果：浏览器自动打开 http://localhost:8501，显示侧边栏和主内容区布局。

- [ ] **Step 2: 手动验证功能**

检查以下功能是否正常：
1. 数据加载 - 输入路径后点击加载，显示成功信息
2. 资产列表 - 显示所有资产，支持搜索过滤
3. 资产选择 - 选择资产后显示 K 线图
4. 买卖点标注 - 买入点绿色向上箭头，卖出点红色向下箭头
5. 收益率标注 - 卖出点旁显示收益数值
6. 日期范围 - 可调整日期范围
7. 交易详情表格 - 可折叠展开，显示交易记录

---

### Task 7: 更新 README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 添加运行说明**

在 README.md 的特性一部分添加使用说明：

```markdown
## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
streamlit run app.py
```

浏览器将自动打开 http://localhost:8501

### 操作步骤

1. 在侧边栏输入数据文件路径（默认已填写示例数据路径）
2. 点击「加载数据」按钮
3. 在资产列表中搜索或选择要查看的资产
4. K 线图将显示该资产的买卖点和收益率
5. 可调整日期范围查看特定时间段
6. 点击「交易详情」查看完整交易记录表格
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add usage instructions to README"
```

---

## Self-Review 检查清单

**1. Spec 覆盖检查:**
- ✅ 数据文件加载 → Task 2 (data_loader.py), Task 5 (sidebar)
- ✅ 资产选择列表 → Task 2 (get_asset_list), Task 5 (sidebar)
- ✅ 搜索过滤 → Task 2 (filter_assets), Task 5 (sidebar search input)
- ✅ K 线图展示 → Task 4 (build_candlestick_chart)
- ✅ 买卖点箭头标注 → Task 4 (buy/sell markers)
- ✅ 收益率标注 → Task 4 (return_texts on sell markers)
- ✅ 日期范围控制 → Task 5 (sidebar date inputs)
- ✅ 交易详情表格 → Task 4 (get_trade_table_data), Task 5 (expander)
- ✅ 错误处理 → Task 2 (FileNotFoundError, ValueError), Task 5 (try/except)
- ✅ 侧边栏布局 → Task 5 (st.sidebar)
- ✅ K 线图占页面大部分 → Task 5 (height=700, use_container_width=True)

**2. Placeholder 检查:**
- 无 TBD/TODO
- 无 "add validation" 等模糊指令
- 所有代码步骤包含完整代码

**3. 类型一致性检查:**
- `load_trade_data` 返回 `pl.DataFrame` → `get_asset_list` 接收 `pl.DataFrame` ✓
- `get_asset_trades` 返回 `pl.DataFrame` → `build_candlestick_chart` 接收 `pl.DataFrame` ✓
- `get_trade_table_data` 返回 `list` → Streamlit `st.dataframe` 接收 `list` ✓

---

Plan complete and saved to `docs/superpowers/plans/2026-04-17-kline-visualization.md`. Two execution options:

**1. Subagent-Driven (推荐)** - 我为每个任务派遣独立的子代理，任务间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用 executing-plans 执行，批量执行并在检查点暂停审查

选择哪种方式？