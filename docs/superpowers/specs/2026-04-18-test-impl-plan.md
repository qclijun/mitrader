# mitrader 测试实施计划

> 基于设计文档 `2026-04-18-test-design.md`，截至 2026-04-18

---

## 现状差距

| 层级 | 设计目标 | 现已存在 | 待实现 |
|------|----------|---------|--------|
| 单元测试 | 19 个（3 文件） | 3 个（`tests/test_data_loader.py`，扁平位置） | 16 个 + 迁移 3 个 |
| 集成测试 | 10 个（2 文件） | 3 个（`tests/test_integration.py`，扁平位置） | 7 个 + 迁移 3 个 |
| E2E 测试 | 6 个 | 3 个（全部 `pytest.skip`） | 6 个（重写） |
| 目录结构 | `tests/unit/`, `tests/integration/`, `tests/fixtures/` | 无 | 全部创建 |
| 共享 fixtures | `tests/conftest.py` | 无 | 创建 |

---

## 实施步骤

### 第一步：目录与基础设施（前置条件）

**1.1 创建目录结构**

```
tests/
├── unit/
│   └── __init__.py
├── integration/
│   └── __init__.py
├── fixtures/
│   ├── minimal_trade.csv
│   ├── empty_trade.csv
│   ├── missing_cols_trade.csv
│   └── edge_cases.py
└── conftest.py          ← 新建，迁移现有 fixture
```

**1.2 迁移现有扁平测试文件**

| 源文件 | 目标位置 | 处理方式 |
|--------|---------|---------|
| `tests/test_data_loader.py` | `tests/unit/test_data_loader.py` | 移动并扩展 |
| `tests/test_integration.py` | `tests/integration/test_data_join.py` | 移动并扩展 |

> 迁移后删除原扁平文件，避免重复执行。

**1.3 创建 `tests/conftest.py` 共享 fixtures**

从现有两个测试文件提取重复的 `sample_trade_csv`、`sample_price_parquet` fixture，
集中放入 `tests/conftest.py`，并新增以下 fixtures：

```python
# tests/conftest.py 需包含的 fixtures
sample_trade_path()        # sample_data/trade.csv 路径（主流程）
sample_prices_path()       # sample_data/prices.parquet 路径（主流程）
minimal_trade_df()         # 3-5 行 Polars DataFrame（边界）
minimal_price_df()         # 单资产 3-5 天数据（边界）
empty_trade_csv()          # 临时空 CSV 路径（tmpdir）
missing_cols_trade_csv()   # 缺列 CSV 路径（tmpdir）
multiple_names_price_df()  # 同 bond_id 多 bond_nm（名称拼接）
```

**1.4 创建 `tests/fixtures/edge_cases.py` 工厂函数**

```python
def create_trade_with_single_asset(asset_id: str) -> pl.DataFrame
def create_prices_with_multiple_names(bond_id: str, names: list[str]) -> pl.DataFrame
def create_trade_with_no_matching_price(asset_id: str) -> pl.DataFrame
```

---

### 第二步：单元测试（19 个）

#### `tests/unit/test_data_loader.py`（7 个）

迁移已有 3 个，**新增 4 个**：

| 测试 | 状态 | 说明 |
|------|------|------|
| `test_load_trade_data_asset_is_string` | ✅ 已有 | 迁移 |
| `test_load_trade_data_asset_values_preserved` | ✅ 已有 | 迁移 |
| `test_load_trade_data_dates_parsed` | ✅ 已有 | 迁移 |
| `test_load_trade_data_basic` | 🆕 新增 | 验证列名、行数 |
| `test_load_trade_data_empty_file` | 🆕 新增 | 空 CSV → 明确异常 |
| `test_load_trade_data_missing_columns` | 🆕 新增 | 缺列 → `ValueError` |
| `test_load_price_data_basic` | 🆕 新增 | Parquet schema 验证 |
| `test_load_price_data_date_conversion` | 🆕 新增（见下） | `trade_date` → `pl.Date` |

> 注：共 8 项（设计文档 7 个，含已有的 3 个合并后实为 8 个有意义用例，建议保留）。

#### `tests/unit/test_utils.py`（7 个，全部新增）

```python
test_get_trade_type_buy()                       # size > 0 → "买入"
test_get_trade_type_sell()                      # size < 0 → "卖出"
test_get_trade_type_zero()                      # size = 0 → 边界处理（当前实现返回"卖出"，需确认）
test_calculate_return_percentage_positive()     # 正值 → "+2.50"
test_calculate_return_percentage_negative()     # 负值 → "-1.50"
test_calculate_return_percentage_zero()         # 0 → "0.00%"
test_format_trade_row()                         # 完整格式化输出验证
```

> ⚠️ `get_trade_type(0)` 的行为：当前实现 `size > 0` 为买入，否则为卖出，即 0 返回"卖出"。
> 需在测试中明确记录此边界行为（而非视为 bug）。

#### `tests/unit/test_chart_builder.py`（5 个，全部新增）

```python
test_build_candlestick_chart_empty_data()       # 空 price_df → 返回 Figure 或 raise
test_build_candlestick_chart_single_point()     # 1 条价格数据 → 正常构建
test_build_candlestick_chart_traces_count()     # trace 数 = 3（K线 + 买入 + 卖出）
test_get_trade_table_data_basic()               # DataFrame → list[dict] 列名验证
test_get_trade_table_data_empty()              # 空 DataFrame → []
```

> ⚠️ `build_candlestick_chart` 对空数据行为：当前实现会构建空图而非 raise，
> 测试应验证"返回空 Figure"（有效行为），而非强制 raise。

---

### 第三步：集成测试（10 个）

#### `tests/integration/test_data_join.py`（7 个）

迁移已有 3 个（重命名对齐设计文档），**新增 4 个**：

| 测试 | 状态 | 说明 |
|------|------|------|
| `test_get_asset_list_join_works` | ✅ 已有 | 迁移 → `test_get_asset_list_join_correct` |
| `test_get_asset_prices_returns_data` | ✅ 已有 | 迁移 → `test_get_asset_prices_by_id` |
| `test_get_asset_trades_returns_data` | ✅ 已有 | 迁移 → `test_get_asset_trades_by_id` |
| `test_get_asset_list_unique_asset_id` | 🆕 新增 | `asset_id` 列无重复 |
| `test_get_asset_list_multiple_names_concat` | 🆕 新增 | 同 bond_id 多名称 → 逗号拼接 |
| `test_get_asset_list_no_matching_prices` | 🆕 新增 | 无匹配 bond_id → 结果有 null `asset_nm` 或过滤 |
| `test_filter_assets_fuzzy_search` | 🆕 新增 | 搜索 ID 和名称均可模糊匹配 |

> ⚠️ `test_get_asset_list_multiple_names_concat`：当前 `get_asset_list` 实现用
> `unique()` 获取名称，同 bond_id 多 bond_nm 时不会拼接，会随机取一个。
> 此测试会**揭示设计文档期望与实现的差异**，需决定是修改实现还是调整测试预期。

#### `tests/integration/test_asset_flow.py`（3 个，全部新增）

```python
test_full_asset_flow()         # 加载 → 获取列表 → 筛选 → 获取详情，全链路
test_chart_with_trades()       # 图表构建 + 交易标注日期对齐
test_chart_date_range_filter() # 日期范围过滤后图表只含范围内数据
```

---

### 第四步：E2E 测试（6 个）

**现有 3 个测试全部重写**（移除 `pytest.skip`，改为真实 Playwright 实现）。

| 测试 | 操作序列 | 验证点 |
|------|---------|--------|
| `test_e2e_load_data_success` | 导航 → 填路径 → 点加载 | 显示"数据加载成功"，资产数量 > 0 |
| `test_e2e_load_data_invalid_path` | 填无效路径 → 点加载 | 显示错误信息 |
| `test_e2e_search_and_select_asset` | 加载 → 搜索 → 选择资产 | 资产列表缩小，选中后图表显示 |
| `test_e2e_chart_render_with_markers` | 加载 → 选资产 → 查图表 | 图表含 K线 + 买入 + 卖出标记 |
| `test_e2e_trade_details_expander` | 加载 → 选资产 → 展开详情 | 表格有交易记录行 |
| `test_e2e_date_range_filter` | 加载 → 选资产 → 调日期范围 | 图表 x 轴范围改变 |

**实现方式**：使用 `playwright` Python 包（非 MCP 工具），在 pytest 内通过
`sync_playwright` 调用，依赖 `streamlit_server` fixture（已就绪）。

需在 `tests/e2e/conftest.py` 补充：
```python
@pytest.fixture
def browser_page(streamlit_server):
    """提供已导航到 app 的 Playwright page 对象。"""
```

---

## 优先实施顺序

```
第一步（基础设施）→ 第二步（单元）→ 第三步（集成）→ 第四步（E2E）
```

各步骤内可并行，但：
- 单元测试不依赖 fixtures 目录文件（用 `tmp_path` 或内联数据）
- 集成测试依赖 `tests/conftest.py` 中的 fixtures
- E2E 测试依赖 `streamlit_server` fixture（已有）和 `playwright` 安装

---

## 需提前确认的设计问题

| # | 问题 | 影响范围 |
|---|------|---------|
| 1 | `get_trade_type(0)` 应返回"卖出"还是"未知"？ | `test_get_trade_type_zero` |
| 2 | `get_asset_list` 同 bond_id 多 bond_nm 是拼接还是随机取一？ | `test_get_asset_list_multiple_names_concat` + 可能需改实现 |
| 3 | `load_trade_data` 加载空 CSV 应返回空 DataFrame 还是 raise？ | `test_load_trade_data_empty_file` |
| 4 | E2E 测试是否需要 `sample_data/` 中真实数据文件可访问？ | 所有 E2E 测试 |

---

## pytest.ini / pyproject.toml 配置检查

确认 `@pytest.mark.unit` / `integration` / `e2e` 标记已注册（避免警告），
以及 `testpaths` 覆盖新增的 `tests/unit/` 和 `tests/integration/`。
