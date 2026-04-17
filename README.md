## 项目概览
mitrader是一个交易分析工具，用于分析用户的交易记录

## 特性

### 特性一：绘制买卖点
根据用户的交易记录文件(格式参考 @sample_data/trade.csv), 绘制股票/债券的K线图（价格信息来自 @sample_data/prices.parquet），并在K线图上标注买卖点及这笔交易的收益率。

## 使用方法

### 安装依赖

```bash
uv sync
```

### 启动应用

```bash
uv run streamlit run app.py
```

浏览器将自动打开 http://localhost:8501

### 操作步骤

1. 在侧边栏输入数据文件路径（默认已填写示例数据路径）
2. 点击「加载数据」按钮
3. 在资产列表中搜索或选择要查看的资产
4. K 线图将显示该资产的买卖点和收益率
5. 可调整日期范围查看特定时间段
6. 点击「交易详情」查看完整交易记录表格


## 数据格式说明

### 交易记录文件 trade.csv
- asset: 资产代号
- date: 交易日期
- price: 交易价格
- size: 交易仓位
- curr_size: 持仓仓位
- comm: 手续费
- order: order id
- pnl: 毛收益率
- pnlcomm: 去掉手续费后的收益
- open_datetime: 开仓时间

### 资产价格数据 prices.parquet
- trade_date: 交易日期
- bond_id: 债券id (跟trade.csv中的asset对应)
- bond_nm: 债券名称
- open: 开盘价
- high: 最高价
- low: 最低价
- price: 收盘价
- volume: 成交量

它的schema为
```
Schema([('trade_date', Datetime(time_unit='us', time_zone=None)),
        ('bond_id', String),
        ('bond_nm', String),
        ('open', Float64),
        ('high', Float64),
        ('low', Float64),
        ('price', Float64),
        ('volume', Float64)])
```
