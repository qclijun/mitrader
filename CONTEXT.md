# mitrader Context

mitrader is a trading analysis tool for reviewing trade records, market price series, and strategy return series.

## Language

**Return Series**:
A named daily decimal return sequence used to evaluate one strategy or benchmark.
_Avoid_: PnL column, curve column

**Observed Date**:
A date row explicitly present in the input return data.
_Avoid_: Trading day, calendar day

**Daily Return Data**:
Return data where each Return Series has at most one observed return per date.
_Avoid_: Intraday returns, raw PnL events

**Business Date**:
The date label for a daily return observation, supplied as a date or timezone-free datetime.
_Avoid_: Instant timestamp, timezone datetime

**Benchmark**:
An optional Return Series used as the comparison baseline for benchmark-relative performance metrics.
_Avoid_: Index, baseline column

**Benchmark-Relative Metrics**:
Performance metrics calculated by comparing a Return Series with the Benchmark on the same Observed Dates.
_Avoid_: Excess stats, relative columns

**Excess Return Series**:
The daily active return sequence calculated as Return Series daily return minus Benchmark daily return on each Observed Date.
_Avoid_: Annualized return difference

**Undefined Metric**:
A metric value that is not meaningful for the current sample because of zero denominators, insufficient observations, or self-comparison to the Benchmark.
_Avoid_: Infinity, NaN

**Short Sample**:
An Analysis Range with too few observed returns to define sample statistics such as volatility or regression.
_Avoid_: Invalid range

**Annualized Volatility**:
Sample standard deviation of observed daily returns scaled by the square root of 252.
_Avoid_: Population volatility

**Metric Ranking**:
The comparison of visible metric table rows to identify the best defined value for a metric.
_Avoid_: Global ranking, hidden benchmark ranking

**Selected Return Series**:
The Return Series chosen by the user to display and compare in charts and tables.
_Avoid_: Active columns, checked strategies

**Loaded Return Data**:
Daily Return Data that has been explicitly loaded by the user from a local CSV path.
_Avoid_: Auto-loaded data

**Date Range Shortcut**:
A user-facing preset for choosing an Analysis Range, named in Chinese except the common investment abbreviation YTD.
_Avoid_: English range labels

**Decimal Return**:
A numeric return value where `0.0016` means `0.16%`.
_Avoid_: Percent return

**Valid Daily Return**:
A Decimal Return greater than or equal to `-1.0`, so a single day cannot lose more than 100% of starting value.
_Avoid_: Negative NAV return

**Finite Return**:
A Decimal Return that is not `NaN`, positive infinity, or negative infinity.
_Avoid_: Non-finite return

**Alpha**:
The annualized intercept from regressing a Return Series against the Benchmark, represented as a Decimal Return.
_Avoid_: Daily alpha

**Beta**:
The unitless slope from regressing a Return Series against the Benchmark.
_Avoid_: Beta return

**Regression Metrics**:
Alpha and Beta calculated from same-date daily returns of a Return Series and the Benchmark.
_Avoid_: Correlation metrics

**Analysis Range**:
The date window selected by the user for charting and risk/return metric calculation.
_Avoid_: Current range, filter range

**Recent Returns**:
Natural-calendar WTD, MTD, YTD, current-year max drawdown, and current-year current drawdown measured through the latest available data date, independent of the Analysis Range.
_Avoid_: Filtered WTD, window YTD

**Annualized Return**:
Geometric return scaled by the number of observed daily return rows using a 252-trading-day year.
_Avoid_: Calendar annualized return

**Net Value**:
The compounded value of a Return Series after applying each observed daily return to an initial value of 1.0.
_Avoid_: Equity curve

**Drawdown**:
The percentage decline of Net Value from the highest value reached since the start of the measurement window, with 1.0 as the initial high-water mark.
_Avoid_: Underwater curve

## Relationships

- A **Return Series** may be selected as the **Benchmark**
- A **Benchmark** may also be selected as a displayed **Return Series**, but its benchmark-relative metrics are not meaningful
- **Benchmark-Relative Metrics** align a **Return Series** and **Benchmark** by the same **Observed Dates** in the input data
- **Benchmark-Relative Metrics** that report excess return are calculated from the **Excess Return Series**, not by subtracting two annualized returns
- An **Undefined Metric** is displayed as blank or `-` and does not participate in ranking
- A **Short Sample** may still show Net Value and Drawdown, while sample-statistic metrics become **Undefined Metrics**
- **Annualized Volatility** requires at least two observed returns
- **Metric Ranking** only compares visible selected **Return Series** rows
- **Selected Return Series** has no hard count limit, but the page may default to a small readable selection
- **Loaded Return Data** is created only after the user explicitly requests loading from the CSV path
- **Date Range Shortcuts** are `全部`, `最近 5 年`, `最近 3 年`, `最近 1 年`, `YTD`, and `自定义`
- Calculations use **Decimal Returns**; presentation may format return-like values as percentages
- **Valid Daily Returns** may equal `-1.0`, but values below `-1.0` are invalid input
- **Finite Returns** are required after missing values are filled; `NaN` and infinities are invalid input
- **Alpha** is formatted like an annualized return; **Beta** is formatted as a unitless number
- **Regression Metrics** require at least two observed return pairs and non-zero Benchmark variance
- An **Analysis Range** limits net value charts, drawdown charts, and risk/return metric calculations
- **Recent Returns** use the latest available data date and do not follow the **Analysis Range**
- **Recent Returns** drawdown fields use the current natural year, not full-history drawdown
- **Annualized Return** uses the same daily observation basis as annualized volatility
- A **Net Value** point corresponds to one observed **Return Series** date; no synthetic 1.0 start point is inserted
- **Drawdown** for an **Analysis Range** starts with 1.0 as the initial high-water mark, so a loss on the first observed date is a negative drawdown
- Missing return values on an **Observed Date** are treated as zero, but missing date rows are not created
- Missing return values that become zero still participate in **Benchmark-Relative Metrics**
- **Daily Return Data** rejects duplicate **Observed Dates** instead of aggregating intraday rows
- **Business Dates** do not perform timezone conversion; timezone-aware timestamps are not valid first-version input
- A **Net Value** that reaches zero stays at zero under subsequent compounded returns because the model has no external capital flow

## Example Dialogue

> **Dev:** "If the user selects the last 1 year as the Analysis Range, should YTD start from that range's first date?"
> **Domain expert:** "No. Recent Returns stay on natural-calendar periods through the latest data date; the Analysis Range only changes charts and risk/return metrics."

> **Dev:** "Can the Benchmark also appear on the chart as a selected Return Series?"
> **Domain expert:** "Yes. Show its own absolute metrics, but leave benchmark-relative metrics blank for that row."

## Flagged Ambiguities

- "YTD" can mean a natural-calendar recent return or a selected-window shortcut. Resolved: **Recent Returns** YTD is natural-calendar; **Analysis Range** YTD is a range shortcut ending at the latest data date.
- "Current drawdown" in **Recent Returns** can mean full-history current drawdown or current-year current drawdown. Resolved: **Recent Returns** current drawdown uses the current natural year.
- "Metrics" can mean either the risk/return metrics table or Recent Returns. Resolved: risk/return metrics follow the **Analysis Range**; **Recent Returns** do not.
- "Insufficient samples" can imply hiding the whole analysis. Resolved: a **Short Sample** keeps defined outputs visible and blanks only undefined metrics.
- "Annualized" can mean calendar-day scaling or observed-trading-day scaling. Resolved: **Annualized Return** uses observed daily return rows with a 252-trading-day year.
- "Standard deviation" can mean population or sample standard deviation. Resolved: **Annualized Volatility** uses sample standard deviation.
- "Initial net value is 1.0" can imply inserting a synthetic chart point. Resolved: **Net Value** starts from 1.0 internally, then the first displayed point applies the first observed daily return.
- "Return series" can imply contributions or resets after total loss. Resolved: **Net Value** has no external capital flow and does not recover from zero by compounding later returns.
- "Drawdown" can either ignore or include the measurement window's starting capital as a high-water mark. Resolved: **Drawdown** includes the initial 1.0 high-water mark.
- "Missing data" can mean an empty return value or an absent date row. Resolved: empty return values become zero; absent date rows remain absent.
- "Datetime" can imply intraday observations. Resolved: return input is **Daily Return Data**; multiple rows on the same date are invalid.
- "Datetime" can imply an instant in a timezone. Resolved: return input uses **Business Dates**, not timezone-aware timestamps.
- "Benchmark" can mean either a hidden comparison baseline or a visible plotted series. Resolved: a **Benchmark** may also be a displayed **Return Series**.
- "Align with benchmark" can imply dropping missing strategy or benchmark values. Resolved: **Benchmark-Relative Metrics** use the same Observed Dates after missing values have been converted to zero.
- "Excess annualized return" can mean annualizing daily active returns or subtracting annualized returns. Resolved: it annualizes the **Excess Return Series**.
- "Undefined ratio" can imply infinity when a denominator is zero. Resolved: such values are **Undefined Metrics**, not infinite values.
- "Return percentage" can mean either a decimal calculation value or a formatted UI value. Resolved: calculations use **Decimal Returns**; UI formatting adds percent display where appropriate.
- "Daily return" can mathematically be less than `-100%`, but not for this Net Value model. Resolved: **Valid Daily Return** rejects values below `-1.0`.
- "Numeric return" can include `NaN` or infinity in floating-point data. Resolved: return inputs must be **Finite Returns**.
- "Alpha" can mean daily regression intercept or annualized active return. Resolved: **Alpha** means annualized regression intercept.
- "Regression" can imply accepting one point or a constant Benchmark. Resolved: **Regression Metrics** require at least two observed pairs and non-zero Benchmark variance.
- "Best metric" can imply comparison against hidden Benchmark data. Resolved: **Metric Ranking** only uses visible table rows.
- "Select one or more" can imply selecting every series by default. Resolved: the page defaults to a small readable **Selected Return Series** set without enforcing a hard maximum.
- "Default path" can imply automatic data loading. Resolved: a default local CSV path may be shown, but **Loaded Return Data** requires an explicit load action.
- Date range labels appeared in both English and Chinese. Resolved: **Date Range Shortcuts** use Chinese UI labels except `YTD`.
