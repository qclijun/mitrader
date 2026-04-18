# Graph Report - .  (2026-04-18)

## Corpus Check
- Corpus is ~13,543 words - fits in a single context window. You may not need a graph.

## Summary
- 78 nodes · 83 edges · 12 communities detected
- Extraction: 67% EXTRACTED · 33% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Data Loading & App Entry|Data Loading & App Entry]]
- [[_COMMUNITY_Chart Building & Utilities|Chart Building & Utilities]]
- [[_COMMUNITY_Data Loader Design & Testing|Data Loader Design & Testing]]
- [[_COMMUNITY_UI & Visualization Design|UI & Visualization Design]]
- [[_COMMUNITY_Test Execution Screenshot|Test Execution Screenshot]]
- [[_COMMUNITY_Type Mismatch Bug & Fix|Type Mismatch Bug & Fix]]
- [[_COMMUNITY_Project Core Concepts|Project Core Concepts]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Data Column Mapping|Data Column Mapping]]
- [[_COMMUNITY_Test Init|Test Init]]
- [[_COMMUNITY_E2E Test Init|E2E Test Init]]
- [[_COMMUNITY_Utils Module|Utils Module]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `Data Loader Module` - 9 edges
3. `Streamlit Application` - 5 edges
4. `pytest Test Execution Output` - 5 edges
5. `get_trade_type()` - 4 edges
6. `format_trade_row()` - 4 edges
7. `build_candlestick_chart()` - 4 edges
8. `get_trade_table_data()` - 4 edges
9. `Chart Builder Module` - 4 edges
10. `Type Mismatch Bug (asset i64 vs bond_id str)` - 4 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `build_candlestick_chart()`  [INFERRED]
  app.py → src/chart_builder.py
- `main()` --calls--> `get_trade_table_data()`  [INFERRED]
  app.py → src/chart_builder.py
- `main()` --calls--> `load_trade_data()`  [INFERRED]
  app.py → src/data_loader.py
- `main()` --calls--> `load_price_data()`  [INFERRED]
  app.py → src/data_loader.py
- `main()` --calls--> `get_asset_list()`  [INFERRED]
  app.py → src/data_loader.py

## Hyperedges (group relationships)
- **K-line Visualization Implementation Components** — data_loader_module, chart_builder_module, utils_module, streamlit_app [EXTRACTED 1.00]
- **Test Pyramid for Type Mismatch Fix** — unit_tests, integration_tests, playwright_e2e_tests [EXTRACTED 1.00]
- **Bug Cascade: Type Mismatch to UI Error** — type_mismatch_bug, empty_dataframe_result, javascript_console_error [EXTRACTED 1.00]
- **Test Modules in pytest Suite** — screenshot_20260418075613152_test_chart_plotter, screenshot_20260418075613152_test_data_loader, screenshot_20260418075613152_test_integration [EXTRACTED 1.00]

## Communities

### Community 0 - "Data Loading & App Entry"
Cohesion: 0.15
Nodes (15): main(), mitrader - Trading Analysis Visualization Tool  Streamlit application for visual, filter_assets(), get_asset_list(), get_asset_prices(), get_asset_trades(), load_price_data(), load_trade_data() (+7 more)

### Community 1 - "Chart Building & Utilities"
Cohesion: 0.16
Nodes (12): build_candlestick_chart(), get_trade_table_data(), Plotly chart building module for K-line visualization., Convert trade DataFrame to list of dicts for table display.      Args:         t, Build interactive candlestick chart with buy/sell markers.      Args:         pr, calculate_return_percentage(), format_trade_row(), get_trade_type() (+4 more)

### Community 2 - "Data Loader Design & Testing"
Cohesion: 0.19
Nodes (14): Asset-Bond ID Join Relationship, Data Loader Module, filter_assets Function, get_asset_list Function, get_asset_prices Function, get_asset_trades Function, Integration Tests (Filtering/Joins), load_price_data Function (+6 more)

### Community 3 - "UI & Visualization Design"
Cohesion: 0.2
Nodes (10): build_candlestick_chart Function, Buy/Sell Point Markers, Chart Builder Module, get_trade_table_data Function, Playwright E2E Tests, Plotly Library, Return Rate Annotation on Sell Points, Sidebar Layout UI Pattern (+2 more)

### Community 4 - "Test Execution Screenshot"
Cohesion: 0.29
Nodes (8): Deprecation Warning, pytest Test Execution Output, pytest Testing Framework, test_chart_plotter.py Test Module, test_data_loader.py Test Module, Test FAILED Status, test_integration.py Test Module, Test PASSED Status

### Community 5 - "Type Mismatch Bug & Fix"
Cohesion: 0.5
Nodes (5): Asset Type Conversion Fix (cast to String), Empty DataFrame Result from Filtering, JavaScript Console Error (undefined trade_date), Test-Driven Development Approach, Type Mismatch Bug (asset i64 vs bond_id str)

### Community 6 - "Project Core Concepts"
Cohesion: 0.67
Nodes (3): Candlestick Chart Visualization Type, K-line Visualization Feature, mitrader Project

### Community 7 - "Package Init"
Cohesion: 1.0
Nodes (1): mitrader source modules.

### Community 8 - "Data Column Mapping"
Cohesion: 1.0
Nodes (2): Asset Column (trade.csv), Bond ID Column (prices.parquet)

### Community 9 - "Test Init"
Cohesion: 1.0
Nodes (0): 

### Community 10 - "E2E Test Init"
Cohesion: 1.0
Nodes (0): 

### Community 11 - "Utils Module"
Cohesion: 1.0
Nodes (1): Utils Module

## Knowledge Gaps
- **36 isolated node(s):** `mitrader - Trading Analysis Visualization Tool  Streamlit application for visual`, `Utility functions for calculations and formatting.`, `Calculate and format return percentage.      Args:         pnl: Gross profit/los`, `Determine trade type from position size.      Args:         size: Position size`, `Format a trade row for display.      Args:         row: Raw trade record dict` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Package Init`** (2 nodes): `mitrader source modules.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Data Column Mapping`** (2 nodes): `Asset Column (trade.csv)`, `Bond ID Column (prices.parquet)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `E2E Test Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Utils Module`** (1 nodes): `Utils Module`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Data Loading & App Entry` to `Chart Building & Utilities`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `Data Loader Module` connect `Data Loader Design & Testing` to `UI & Visualization Design`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `Streamlit Application` connect `UI & Visualization Design` to `Data Loader Design & Testing`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `main()` (e.g. with `load_trade_data()` and `load_price_data()`) actually correct?**
  _`main()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Data Loader Module` (e.g. with `Polars Library` and `pytest Test Runner`) actually correct?**
  _`Data Loader Module` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Streamlit Application` (e.g. with `Streamlit Framework` and `Sidebar Layout UI Pattern`) actually correct?**
  _`Streamlit Application` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mitrader - Trading Analysis Visualization Tool  Streamlit application for visual`, `Utility functions for calculations and formatting.`, `Calculate and format return percentage.      Args:         pnl: Gross profit/los` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._