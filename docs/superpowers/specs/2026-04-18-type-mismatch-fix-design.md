# Type Mismatch Fix + TDD Test Cases Design

**Date:** 2026-04-18

## Problem Summary

The mitrader application shows JavaScript error "Cannot read properties of undefined (reading 'trade_date')" after loading data. Root cause: type mismatch between `asset` (i64) in trade.csv and `bond_id` (str) in prices.parquet causes `get_asset_prices()` to return empty DataFrame, leading to undefined data in frontend rendering.

## Fix Implementation

**Location:** `src/data_loader.py` - `load_trade_data()` function

Cast the `asset` column to string during data loading:

```python
df = df.with_columns(
    pl.col('date').str.to_date('%Y-%m-%d').alias('date'),
    pl.col('open_datetime').str.to_date('%Y-%m-%d').alias('open_datetime'),
    pl.col('asset').cast(pl.String).alias('asset')
)
```

This ensures `asset` matches `bond_id` type (both string), so filtering works correctly in `get_asset_prices()` and `get_asset_trades()`.

## Test Cases (TDD Approach)

### Test Pyramid

1. **Unit Tests** (`tests/test_data_loader.py`) - Verify type conversion at boundary
2. **Integration Tests** (`tests/test_integration.py`) - Verify filtering returns data  
3. **Playwright E2E Tests** (`tests/e2e/test_app.py`) - Verify UI renders correctly

### Unit Tests

| Test | Purpose |
|------|---------|
| `test_load_trade_data_asset_is_string` | Verify `asset` column dtype is String after loading |
| `test_load_trade_data_asset_values_preserved` | Verify values converted correctly (113027 → "113027") |

### Integration Tests

| Test | Purpose |
|------|---------|
| `test_get_asset_prices_returns_data` | Verify filtering by string asset_id returns non-empty DataFrame |
| `test_get_asset_list_join_works` | Verify asset-bond_id join succeeds after type match |

### Playwright E2E Tests

| Test | Purpose |
|------|---------|
| `test_load_data_no_error` | Load data → verify no JavaScript error in console |
| `test_select_asset_shows_chart` | Select asset → verify K-line chart renders |
| `test_chart_has_candlestick_trace` | Verify chart contains candlestick data |

## Test Execution Order (TDD)

1. Write unit tests → run (expect fail before fix)
2. Implement fix → run tests (expect pass)
3. Write integration tests → run (expect pass)
4. Write E2E tests → run (expect pass)

## Playwright Implementation Details

### Test Setup

- Start Streamlit app on localhost before tests
- Use Playwright MCP tools for browser automation
- Capture console errors using `browser_console_messages()` tool

### Key Test Flow Example

```python
def test_load_data_no_error(browser):
    browser_navigate("http://localhost:8501")
    browser_snapshot()
    browser_click("加载按钮")
    console = browser_console_messages(level="error")
    assert len(console) == 0, f"Console errors: {console}"
```

### Test Infrastructure

- pytest as test runner
- Playwright MCP tools for browser automation
- Test fixtures for sample data paths
- Streamlit subprocess management for E2E tests