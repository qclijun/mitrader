# mitrader 测试设计文档

## 概述

为 mitrader 交易分析工具的「特性一：绘制买卖点」构建测试用例，覆盖用户流程：选择文件路径、加载数据、搜索资产、选择资产、查看图表和交易详情。

## 测试策略：金字塔模型

| 层级 | 占比 | 数量预估 | 目的 |
|------|------|----------|------|
| 单元测试 | ~70% | 19 个 | 函数级验证，快速执行，问题定位 |
| 集成测试 | ~20% | 10 个 | 模块间交互验证，数据流转正确性 |
| E2E 测试 | ~10% | 6 个 | 关键用户路径验证，UI 交互 |

**总计**：35 个测试

## 测试目录结构

```
tests/
├── fixtures/                  # 合成测试数据
│   ├── minimal_trade.csv      # 最小交易数据（边界测试）
│   ├── empty_trade.csv        # 空文件测试
│   ├── missing_cols_trade.csv # 缺少列的 CSV
│   └── minimal_prices.parquet # 最小价格数据
│   └── edge_cases.py          # fixtures factory 函数
├── unit/                      # 单元测试
│   ├── test_data_loader.py
│   ├── test_chart_builder.py
│   └── test_utils.py
├── integration/               # 集成测试
│   ├── test_data_join.py
│   └── test_asset_flow.py
├── e2e/                       # E2E 测试（Playwright）
│   ├── conftest.py            # 已存在
│   └── test_app.py            # 扩展现有 placeholder
└── conftest.py                # 共享 fixtures
```

## 测试数据策略

- **主流程测试**：直接使用 `sample_data/trade.csv` 和 `prices.parquet`
- **边界测试**：创建合成数据放在 `tests/fixtures/`
  - 空数据文件
  - 单条记录
  - 无匹配资产的交易
  - 同 bond_id 多 bond_nm（测试名称拼接）

---

## 单元测试设计（19 个）

### `test_data_loader.py` - 数据加载函数（7 个）

| 测试用例 | 描述 | 数据源 |
|----------|------|--------|
| `test_load_trade_data_basic` | 加载正常 CSV，验证列名、类型、行数 | sample_data |
| `test_load_trade_data_asset_string_cast` | 验证 asset 列被正确转换为 String | sample_data |
| `test_load_trade_data_date_parsing` | 验证 date 和 open_datetime 解析为日期类型 | sample_data |
| `test_load_trade_data_empty_file` | 加载空 CSV，应返回空 DataFrame 或抛出明确异常 | fixtures/empty_trade.csv |
| `test_load_trade_data_missing_columns` | 加载缺少必要列的 CSV，应抛出明确异常 | fixtures/missing_cols_trade.csv |
| `test_load_price_data_basic` | 加载正常 Parquet，验证 schema | sample_data |
| `test_load_price_data_date_conversion` | 验证 trade_date 转换为 Date 类型 | sample_data |

### `test_utils.py` - 工具函数（7 个）

| 测试用例 | 描述 |
|----------|------|
| `test_get_trade_type_buy` | size > 0 返回 "买入" |
| `test_get_trade_type_sell` | size < 0 返回 "卖出" |
| `test_get_trade_type_zero` | size = 0 的边界处理 |
| `test_calculate_return_percentage_positive` | 正收益率格式化 |
| `test_calculate_return_percentage_negative` | 负收益率格式化 |
| `test_calculate_return_percentage_zero` | 零收益率格式化 |
| `test_format_trade_row` | 单行格式化输出正确性 |

### `test_chart_builder.py` - 图表构建函数（5 个）

| 测试用例 | 描述 |
|----------|------|
| `test_build_candlestick_chart_empty_data` | 空数据输入，返回空图表或抛出明确异常 |
| `test_build_candlestick_chart_single_point` | 单条价格数据，图表仍能构建 |
| `test_build_candlestick_chart_traces_count` | 验证图表包含 candlestick + buy markers + sell markers 三个 trace |
| `test_get_trade_table_data_basic` | DataFrame 转 dict list，列名映射正确 |
| `test_get_trade_table_data_empty` | 空 DataFrame 返回空列表 |

---

## 集成测试设计（10 个）

### `test_data_join.py` - 数据关联测试（7 个）

| 测试用例 | 描述 | 数据源 |
|----------|------|--------|
| `test_get_asset_list_join_correct` | 交易统计与资产名称正确关联，验证 bond_id ↔ asset 匹配 | sample_data |
| `test_get_asset_list_unique_asset_id` | 资产列表中 asset_id 列唯一，无重复 | sample_data |
| `test_get_asset_list_multiple_names_concat` | 同一 asset_id 有多个 bond_nm 时，名称用逗号连接 | fixtures 合成 |
| `test_get_asset_list_no_matching_prices` | 交易中有 asset 但 prices 中无匹配 bond_id，结果应正确处理 | fixtures 合成 |
| `test_get_asset_prices_by_id` | 按 bond_id 筛选价格数据，返回正确资产的价格序列 | sample_data |
| `test_get_asset_trades_by_id` | 按 asset 筛选交易记录，返回正确资产的交易 | sample_data |
| `test_filter_assets_fuzzy_search` | 搜索功能在 ID 和名称上都能模糊匹配 | sample_data |

### `test_asset_flow.py` - 资产选择流程测试（3 个）

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| `test_full_asset_flow` | 从加载 → 获取资产列表 → 筛选 → 获取详情，全链路验证 | 数据一致性 |
| `test_chart_with_trades` | 图表构建时交易记录正确标注到对应日期 | chart_builder + data_loader 协作 |
| `test_chart_date_range_filter` | 日期范围筛选后，图表仅显示范围内数据 | 时间过滤正确性 |

---

## E2E 测试设计（6 个）

使用 Playwright MCP 工具测试关键用户路径。

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| `test_e2e_load_data_success` | 输入文件路径 → 点击加载 → 显示成功消息和资产数量 | 数据加载成功，UI 反馈正确 |
| `test_e2e_load_data_invalid_path` | 输入无效路径 → 点击加载 → 显示错误消息 | 错误处理正确 |
| `test_e2e_search_and_select_asset` | 加载后 → 在资产列表搜索 → 选择资产 → 图表显示 | 搜索筛选、资产选择、图表渲染 |
| `test_e2e_chart_render_with_markers` | 选择资产后 → 图表显示 K 线 + 买入/卖出标记 | 图表包含正确的买卖点标注 |
| `test_e2e_trade_details_expander` | 展开「交易详情」→ 显示交易记录表格 | 表格数据正确显示 |
| `test_e2e_date_range_filter` | 调整日期范围 → 图表仅显示范围内数据 | 日期筛选生效 |

**启动方式**：利用现有 `tests/e2e/conftest.py` 的 `streamlit_server` fixture 启动服务。

---

## 测试 Fixtures

### `tests/conftest.py` - 共享 fixtures

| Fixture | 描述 | 用途 |
|---------|------|------|
| `sample_trade_path` | sample_data/trade.csv 路径 | 主流程测试 |
| `sample_prices_path` | sample_data/prices.parquet 路径 | 主流程测试 |
| `minimal_trade_df` | 最小交易 DataFrame（Polars，含 3-5 条记录） | 边界测试 |
| `minimal_price_df` | 最小价格 DataFrame（Polars，含单资产 3-5 天数据） | 边界测试 |
| `empty_trade_csv` | 临时空 CSV 文件路径 | 异常测试 |
| `missing_cols_trade_csv` | 临时缺少必要列的 CSV | 异常测试 |
| `multiple_names_prices_df` | 同 bond_id 多 bond_nm 的价格 DataFrame | 名称拼接测试 |

### `tests/fixtures/edge_cases.py` - 边界数据工厂

```python
def create_trade_with_single_asset(asset_id: str) -> pl.DataFrame
def create_prices_with_multiple_names(bond_id: str, names: list[str]) -> pl.DataFrame
def create_trade_with_no_matching_price(asset_id: str) -> pl.DataFrame
```

---

## 测试执行命令

```bash
# 运行全部测试
pytest

# 仅运行单元测试
pytest -m unit

# 仅运行集成测试
pytest -m integration

# 仅运行 E2E 测试
pytest -m e2e

# 按目录运行
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### 执行顺序建议

| 阶段 | 命令 | 适用场景 |
|------|------|----------|
| 快速验证 | `pytest -m unit` | 开发时频繁运行 |
| 本地完整验证 | `pytest -m "unit or integration"` | 提交前检查 |
| CI/CD | `pytest`（含 E2E） | PR 合入前 |

---

## 设计日期

2026-04-18