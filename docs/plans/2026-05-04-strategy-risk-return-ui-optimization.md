# Strategy Risk/Return UI Optimization Plan

## Background

The strategy risk/return page currently loads Daily Return Data, lets users select Return Series, optionally choose a Benchmark, choose an Analysis Range, and inspect Net Value, Drawdown, Recent Returns, and risk/return metrics.

The current implementation is functional, but the default view does not make the analytical answer obvious enough. The page should help a strategy analyst quickly answer:

- Which Return Series performs best in the selected Analysis Range?
- Where did the main drawdown risk occur?
- Which metrics are worth comparing, and which metrics are unavailable because no Benchmark was selected?

## Design Direction

Use a restrained professional research-workbench style:

- Dense but readable information layout
- Minimal decoration
- Clear hierarchy between controls, chart, summary, and tables
- Strong visual distinction between selected strategies and Benchmark
- Tables optimized for scanning and comparison rather than presentation polish

The goal is not to make the page visually louder. The goal is to make the chart and tables simpler, clearer, and friendlier for repeated analytical use.

## Current Issues

1. The first viewport spends too much space on title, controls, and blank vertical rhythm. The chart is pushed down, so users cannot immediately inspect the main output.
2. The chart labels are understandable but not sharp enough. `收益/净值曲线` can be simplified to `累计净值`, and the drawdown chart should visually emphasize downside risk.
3. Multi-series comparison lacks visual rules. Strategy lines, Benchmark lines, and highlighted focus series should not look equivalent.
4. The risk/return metrics table has too many columns in one row. Column headers wrap heavily and reduce readability.
5. Missing metric values are shown poorly in the rendered table, especially when Benchmark-relative metrics are unavailable.
6. Green best-value highlighting is too broad. When many cells are highlighted, the user has to think harder instead of less.
7. The page does not show a compact summary of the selected range, latest data date, selected series count, Benchmark, and headline metrics.
8. Streamlit warns that `use_container_width=True` should be replaced with `width='stretch'`.

## Scope

### In Scope

- Improve the Streamlit page layout in `pages/1_strategy_risk_return.py`.
- Improve Plotly chart readability in `src/performance_charts.py`.
- Improve Recent Returns and risk/return table formatting.
- Add focused unit tests for formatting helpers and chart structure where practical.
- Update E2E expectations only if visible text or layout changes affect existing tests.

### Out of Scope

- Changing performance metric formulas.
- Changing Daily Return Data CSV format.
- Adding automatic market index detection.
- Replacing Streamlit with another frontend framework.
- Adding persisted user preferences.

## Proposed Changes

### Phase 1: Layout And Summary

Move the page toward a compact analysis workspace.

- Reduce title dominance by using a shorter title or smaller introductory rhythm.
- Keep data loading in the sidebar.
- Put analysis controls in a compact top control area:
  - Selected Return Series
  - Benchmark
  - Analysis Range
  - Custom date inputs only when `自定义` is selected
- Add a compact summary row above the chart:
  - Analysis Range
  - Latest data date
  - Selected Return Series count
  - Benchmark status
  - Best annualized return in the current selection
  - Lowest max drawdown in the current selection
- Keep the first useful chart visible as early as possible in the first viewport.

Acceptance criteria:

- After loading `sample_data/pnl.csv`, the user can see the selected range summary and the top of the Net Value chart without scrolling.
- The summary values update when selected series, Benchmark, or Analysis Range changes.
- Empty and invalid states remain clear.

### Phase 2: Chart Simplification

Improve `build_nav_drawdown_chart` so the chart communicates quickly.

- Rename subplot titles:
  - `累计净值`
  - `回撤`
- Add a horizontal `y=1.0` reference line to the Net Value subplot.
- Format Net Value hover values to 4 decimals.
- Format Drawdown hover values as percentages.
- Use `hovermode='x unified'` and a concise hover template.
- Use a restrained color palette with enough contrast for 3-8 series.
- Render Benchmark differently:
  - Neutral gray
  - Dashed line
  - Slightly thinner than selected strategy lines
- Render selected strategies as solid lines.
- Consider direct line-end labels for selected series when the number of visible lines is small.
- Convert the Drawdown subplot from plain lines to lightly filled negative area traces, using each series color at low opacity.
- Reduce unnecessary chart chrome:
  - Lighter grid lines
  - No heavy background
  - Horizontal legend above the chart

Acceptance criteria:

- Strategy and Benchmark lines are visually distinguishable.
- Drawdown is easier to read as downside risk, not just another line.
- The chart remains clear with all three sample series selected.
- Plotly modebar does not dominate the visual area.

### Phase 3: Table Readability

Replace static table rendering with scan-friendly dataframes.

- Use `st.dataframe` instead of `st.table` for metric tables.
- Use `column_config` for stable formatting:
  - Percent metrics: 2 decimals with `%`
  - Net Value: 4 decimals
  - Ratios: 2 or 4 decimals depending on existing precision needs
- Display unavailable metrics as `-`, not list markers or blank artifacts.
- Split the risk/return table into two groups:
  - Core metrics: Annualized Return, Annualized Volatility, Sharpe, Max Drawdown, Sortino, Calmar
  - Benchmark metrics: Excess Annualized Return, Excess Annualized Volatility, Information Ratio, Alpha, Beta
- If no Benchmark is selected, hide the Benchmark metrics table or show a compact neutral note: `选择基准后显示超额收益、信息比例、Alpha 和 Beta`.
- Keep Recent Returns as a compact dataframe above the detailed metrics.

Acceptance criteria:

- Risk/return table headers no longer wrap into hard-to-read vertical fragments on a 1280px-wide viewport.
- Missing Benchmark-relative metrics are intentionally represented.
- Recent Returns and Core Metrics are readable without horizontal scrolling for the sample data.

### Phase 4: Better Highlighting

Make highlighting support decisions instead of coloring too many cells.

- Highlight only the best value per metric among visible selected rows.
- Use subtle color treatment:
  - Positive/best: pale green
  - Risk/best lower volatility or lower drawdown: pale blue or muted green
  - Avoid saturated blocks
- Do not highlight unavailable metrics.
- Add optional rank indicators only if they remain visually quiet.
- Consider making the selected Benchmark row visually neutral when it is also included as a Return Series.

Acceptance criteria:

- With multiple selected series, the user can quickly identify which strategy is best for each key metric.
- Single-row tables do not over-highlight every available metric; either skip best-value highlighting for one row or keep it extremely subtle.

### Phase 5: Interaction Details

Improve controls for repeated analytical use.

- Add a `全选` / `清空` behavior if Streamlit's native multiselect remains awkward.
- Keep default selection small and readable.
- Show a warning when many Return Series are selected, e.g. more than 8:
  - Chart may become crowded.
  - Tables remain useful for broad comparison.
- Make Benchmark explanation clearer:
  - Benchmark can be selected only for relative metrics.
  - Benchmark may also be selected as a visible Return Series.
- Keep the current custom range behavior but place start/end date inputs close to the range selector.

Acceptance criteria:

- Users can quickly compare one strategy against a Benchmark.
- Users can intentionally broaden the comparison without the chart becoming confusing by accident.

## Implementation Notes

Expected files:

- `pages/1_strategy_risk_return.py`
- `src/performance_charts.py`
- `tests/unit/test_strategy_risk_return_page.py`
- Add or update chart tests if existing coverage allows stable Plotly structure assertions.
- Update `tests/e2e/test_app.py` only if visible labels change.

Before modifying any function or method, run GitNexus impact analysis for the target symbol, following the repository instructions.

Likely symbols requiring impact checks:

- `main`
- `prepare_strategy_tables`
- `_format_recent_returns`
- `_format_metrics`
- `_highlight_best_metrics`
- `build_nav_drawdown_chart`

## Testing Plan

Run focused checks first:

```bash
uv run pytest tests/unit/test_strategy_risk_return_page.py
```

Run chart-related unit tests if added or existing:

```bash
uv run pytest tests/unit
```

Run E2E after visible UI changes:

```bash
uv run pytest -m e2e
```

Manual verification:

1. Start the app:

```bash
uv run streamlit run app.py
```

2. Open `/strategy_risk_return`.
3. Load `sample_data/pnl.csv`.
4. Verify the default single-series state.
5. Select all sample series and verify chart readability.
6. Select `jsl_index` as Benchmark and verify Benchmark-relative metrics.
7. Switch between `全部`, `最近 1 年`, `YTD`, and `自定义`.

## Risks And Tradeoffs

- Splitting the metrics table improves readability but adds another section. Keep section titles short and avoid explanatory clutter.
- Direct line-end labels help small comparisons but may overlap with many series. Enable them only under a small-series threshold.
- Streamlit styling control is limited. Prefer robust Plotly and dataframe improvements over fragile CSS overrides.
- Hiding Benchmark metrics when no Benchmark is selected is cleaner, but tests expecting those columns may need updating.

## Definition Of Done

- The loaded page presents a compact summary and readable chart without unnecessary scrolling.
- Net Value and Drawdown charts are visually distinct and easy to scan.
- Benchmark is visually distinct from strategies.
- Recent Returns and risk/return metrics display with intentional numeric formatting.
- Missing Benchmark-relative metrics are shown cleanly.
- Existing tests pass or are updated to match the improved UI contract.
