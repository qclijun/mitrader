## Problem Statement

mitrader currently helps users review trade records on K-line charts, but it does not provide a dedicated way to evaluate and compare strategy Return Series. Users who have Daily Return Data in a local CSV need to understand Net Value, Drawdown, Recent Returns, and risk/return metrics across different Analysis Ranges without changing the existing K-line workflow.

Without this feature, users must calculate Annualized Return, Annualized Volatility, Benchmark-Relative Metrics, Alpha, Beta, and Recent Returns outside the app, which makes strategy comparison slower and easier to calculate inconsistently.

## Solution

Add a separate Streamlit multipage view for strategy risk/return evaluation. The page will load local CSV Daily Return Data, let users choose Selected Return Series, optionally choose a Benchmark, select an Analysis Range, and display:

- A combined Plotly Net Value and Drawdown chart with shared x-axis subplots
- A risk/return metrics table with Metric Ranking highlights
- A Recent Returns table showing latest cumulative Net Value, WTD, MTD, YTD, current-year max Drawdown, and current-year current Drawdown

The feature will keep calculation logic in deep, testable modules separate from the Streamlit page. The first version is local-data only and will not fetch online index data or change the existing K-line page.

## User Stories

1. As a strategy analyst, I want to load Daily Return Data from a local CSV, so that I can evaluate strategies using my existing output files.
2. As a strategy analyst, I want the CSV to use a fixed Business Date column, so that the app can align Return Series consistently.
3. As a strategy analyst, I want each non-date numeric column to become a candidate Return Series, so that I can compare multiple strategies from one file.
4. As a strategy analyst, I want missing return values on an Observed Date to be treated as zero, so that sparse strategy output does not interrupt calculations.
5. As a strategy analyst, I want missing date rows to remain absent, so that the app does not invent market calendar assumptions.
6. As a strategy analyst, I want invalid Daily Return Data to produce clear loading errors, so that I can fix the source CSV quickly.
7. As a strategy analyst, I want duplicate Observed Dates to be rejected, so that intraday rows are not accidentally treated as daily strategy data.
8. As a strategy analyst, I want timezone-aware timestamps to be rejected, so that Business Dates are not shifted by implicit timezone conversion.
9. As a strategy analyst, I want non-finite returns to be rejected, so that NaN or infinity values do not pollute Net Value and metrics.
10. As a strategy analyst, I want returns below -100% to be rejected, so that Net Value calculations remain meaningful.
11. As a strategy analyst, I want the page to default to a local sample CSV path without auto-loading it, so that I stay in control of when local data is read.
12. As a strategy analyst, I want the app to show an empty or instructional state before loading data, so that the workflow is clear.
13. As a strategy analyst, I want to select one or more Return Series, so that I can compare strategies directly.
14. As a strategy analyst, I want the page to default to a small readable Selected Return Series set, so that the initial view is not cluttered.
15. As a strategy analyst, I want no hard maximum on Selected Return Series, so that I can perform broad comparisons when needed.
16. As a strategy analyst, I want an optional Benchmark, so that I can calculate Benchmark-Relative Metrics when appropriate.
17. As a strategy analyst, I want the Benchmark to be selectable even when it is not displayed as a Return Series, so that it can be used only as a comparison baseline.
18. As a strategy analyst, I want the Benchmark to also be displayable as a Return Series, so that I can see its Net Value and Drawdown on the chart.
19. As a strategy analyst, I want benchmark-relative values for the Benchmark row to show as undefined, so that self-comparison is not misleading.
20. As a strategy analyst, I want Date Range Shortcuts in Chinese, so that the page matches the existing product language.
21. As a strategy analyst, I want Analysis Range shortcuts to end at the latest available data date, so that analysis is based on the loaded data rather than the system date.
22. As a strategy analyst, I want recent-year shortcuts to use fixed day counts, so that the shortcut behavior is predictable.
23. As a strategy analyst, I want YTD Analysis Range to start at January 1 of the latest data year, so that selected-window analysis follows natural-year expectations.
24. As a strategy analyst, I want custom date inputs constrained to loaded data bounds, so that I cannot accidentally select impossible dates.
25. As a strategy analyst, I want a clear empty-range message, so that I understand why charts and tables are skipped.
26. As a strategy analyst, I want Net Value to compound from an internal initial value of 1.0, so that strategy growth is comparable.
27. As a strategy analyst, I want the first displayed Net Value point to correspond to the first Observed Date, so that charts do not show synthetic dates.
28. As a strategy analyst, I want Drawdown to include 1.0 as the initial high-water mark, so that a first-day loss is shown as a Drawdown.
29. As a strategy analyst, I want Net Value that reaches zero to stay at zero, so that the app does not imply external capital flows.
30. As a strategy analyst, I want Net Value and Drawdown in one shared-x chart, so that I can compare growth and risk over the same dates.
31. As a strategy analyst, I want the same series color in both chart subplots, so that the visual comparison is easy to follow.
32. As a strategy analyst, I want duplicate chart legends avoided, so that the chart remains readable.
33. As a strategy analyst, I want risk/return metrics to follow the Analysis Range, so that changing the range changes the analytical output.
34. As a strategy analyst, I want Annualized Return to use observed daily rows and a 252-day year, so that it aligns with daily return observations.
35. As a strategy analyst, I want Annualized Volatility to use sample standard deviation, so that volatility estimates use the agreed statistical basis.
36. As a strategy analyst, I want Short Sample outputs to keep defined values visible, so that a short range still provides useful information.
37. As a strategy analyst, I want Undefined Metrics to display as a blank or hyphen, so that divide-by-zero and insufficient samples are not shown as errors or infinity.
38. As a strategy analyst, I want Sharpe ratio, Sortino ratio, Calmar ratio, Information Ratio, Alpha, and Beta, so that I can evaluate risk-adjusted performance.
39. As a strategy analyst, I want Excess Return Series metrics to be calculated from daily active returns, so that excess return and Information Ratio use a consistent basis.
40. As a strategy analyst, I want Alpha to be annualized and displayed like a return, so that it is comparable to other annualized return metrics.
41. As a strategy analyst, I want Beta to remain unitless, so that exposure is not confused with return.
42. As a strategy analyst, I want Regression Metrics to require at least two observed pairs and non-zero Benchmark variance, so that Alpha and Beta are not calculated from invalid samples.
43. As a strategy analyst, I want Metric Ranking to compare only visible table rows, so that hidden Benchmark data does not affect visible highlights.
44. As a strategy analyst, I want higher-is-better and lower-is-better metrics highlighted appropriately, so that I can quickly identify the strongest strategy per metric.
45. As a strategy analyst, I want Maximum Drawdown ranking to treat values closest to zero as best, so that less severe Drawdown is highlighted correctly.
46. As a strategy analyst, I want Recent Returns to ignore the Analysis Range, so that WTD, MTD, and YTD remain natural-calendar results.
47. As a strategy analyst, I want Recent Returns to use the latest available data date, so that reporting is based on the loaded CSV rather than today.
48. As a strategy analyst, I want current-year max Drawdown and current-year current Drawdown in Recent Returns, so that recent risk is shown on the same natural-year basis as YTD.
49. As a strategy analyst, I want latest cumulative Net Value in Recent Returns, so that I can see each selected strategy's total compounded state.
50. As a strategy analyst, I want calculation outputs to remain Decimal Returns, so that tests and downstream formatting can use numeric values.
51. As a strategy analyst, I want the Streamlit presentation to format return-like values as percentages, so that tables are easy to read.
52. As a maintainer, I want loading logic separated from performance calculations, so that data validation can be tested independently.
53. As a maintainer, I want chart construction separated from calculation logic, so that Plotly structure can be tested without recalculating metrics.
54. As a maintainer, I want the new page to be a thin orchestration layer, so that formulas are not hidden in UI code.
55. As a maintainer, I want the existing K-line page untouched, so that the current trade visualization workflow does not regress.
56. As a maintainer, I want explicit Pandas dependency when using Pandas Styler, so that table highlighting does not rely on transitive dependencies.
57. As a maintainer, I want the page file name to be English, so that project file names stay consistent.
58. As a maintainer, I want E2E navigation through the Streamlit multipage sidebar, so that tests follow user behavior rather than hard-coding brittle routes.

## Implementation Decisions

- Build a deep Daily Return Data loader module with a small public interface for loading data and listing Return Series.
- The loader requires a fixed Business Date column named `datetime`.
- The loader treats all non-date numeric columns as Return Series.
- The loader parses dates or timezone-free datetimes to dates.
- The loader rejects missing date columns, empty date values, timezone-aware timestamps, duplicate Observed Dates, non-numeric return columns, non-finite returns, and returns below -100%.
- The loader fills missing return values with zero and sorts rows by date.
- Build a deep performance calculation module with pure functions for date range resolution, filtering, Net Value, Drawdown, risk/return metrics, and Recent Returns.
- Risk/return metrics use the selected Analysis Range.
- Recent Returns use full Loaded Return Data through the latest available data date and do not follow the Analysis Range.
- Recent Returns current Drawdown is current-year current Drawdown, not full-history current Drawdown.
- Annualized Return uses geometric compounding over observed return rows with a 252-day annualization basis.
- Annualized Volatility uses sample standard deviation with a 252-day annualization basis.
- Alpha and Beta use same-date daily returns against the Benchmark, require at least two observed pairs, and require non-zero Benchmark variance.
- Excess return metrics use the Excess Return Series rather than subtracting annualized strategy and Benchmark returns.
- Undefined Metrics are represented as null values in calculation outputs and displayed as hyphens in the UI.
- Build a chart module that accepts prepared Net Value and Drawdown data and returns one Plotly figure with two shared-x subplots.
- Build a new Streamlit multipage view with an English file name and Chinese user-facing content.
- The page defaults the CSV path to the sample local file but only loads after the user explicitly clicks the load action.
- The page defaults Selected Return Series to the first available Return Series and allows users to choose any number of series.
- The Benchmark is optional and may be either hidden as a comparison baseline or also included in Selected Return Series.
- Date Range Shortcuts are `全部`, `最近 5 年`, `最近 3 年`, `最近 1 年`, `YTD`, and `自定义`.
- Recent-year shortcuts use fixed day counts of 365, 1095, and 1825 days.
- The page uses Pandas Styler for metrics-table highlighting, so Pandas is a direct dependency.
- Metric Ranking highlights only visible selected rows and excludes Undefined Metrics.
- Commit steps in the implementation plan are optional; agents should not create commits unless explicitly asked.

## Testing Decisions

- Tests should assert external behavior and stable contracts rather than implementation details.
- Loader unit tests should cover successful CSV loading, date parsing, sorting, missing values, missing date column, no return columns, empty date values, timezone-aware datetime rejection, duplicate dates, non-numeric returns, non-finite returns, and returns below -100%.
- Performance unit tests should cover date range resolution, strict unknown label behavior, Net Value compounding, Drawdown with 1.0 initial high-water mark, Recent Returns natural-calendar behavior, current-year Drawdown behavior, Annualized Return, Annualized Volatility, Sharpe, Sortino, Calmar, Excess Return Series metrics, Information Ratio, Alpha, Beta, no-Benchmark behavior, self-Benchmark behavior, Short Sample behavior, and Undefined Metrics.
- Chart unit tests should cover figure construction, two vertically stacked subplots, shared x-axis behavior, matching trace counts, and consistent colors between Net Value and Drawdown traces.
- Page smoke checks should compile the new page and verify Pandas is available as a direct dependency.
- E2E tests should navigate through Streamlit multipage navigation, load the sample Daily Return Data, and confirm the chart plus Recent Returns and risk/return tables render.
- Existing K-line unit, integration, and E2E tests should continue to pass.
- Prior art exists in the repository's current unit tests for loader/chart helpers and Playwright-backed E2E tests for Streamlit behavior.
- Graph artifacts should be refreshed after code changes with graphify, while avoiding unrelated cache churn unless explicitly desired.

## Out of Scope

- Online Benchmark or index data fetching.
- Automatic detection of built-in common indexes unless they already exist as Return Series columns in the loaded CSV.
- File formats other than CSV.
- Redesigning the existing K-line trade visualization page.
- Adding market calendars or generating missing date rows.
- Supporting intraday return observations or aggregating multiple rows per date.
- Supporting timezone conversion for datetime values.
- Modeling cash flows, external capital additions, or strategy resets after Net Value reaches zero.
- Persisting uploaded data or storing analysis results.
- Adding a custom Streamlit navigation framework solely to localize the sidebar page label.

## Further Notes

- The PRD is based on the current project glossary and the strategy risk/return design and implementation plan.
- The first implementation should keep the Streamlit page thin and place formulas in testable calculation modules.
- Calculation modules should return numeric Decimal Returns; formatting belongs in the presentation layer.
- The new feature should not change the existing K-line page layout or workflow.
