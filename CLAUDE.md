# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mitrader is a trading analysis tool (交易分析工具) for analyzing user trading records. The primary feature is plotting buy/sell points on K-line (candlestick) charts with return rates displayed.

## Data Formats

### Trade Records (`trade.csv`)
- `asset`: Asset identifier (bond_id)
- `date`: Transaction date
- `price`: Transaction price
- `size`: Position size (positive for buy, negative for sell)
- `curr_size`: Current position
- `comm`: Commission fee
- `order`: Order ID
- `pnl`: Gross return rate
- `pnlcomm`: Net return rate (after commission)
- `open_datetime`: Position opening date

### Price Data (`prices.parquet`)
Polars DataFrame with schema:
```
trade_date: Datetime(μs)
bond_id: String
bond_nm: String
open: Float64
high: Float64
low: Float64
price: Float64  # close price
volume: Float64
```

The `bond_id` in prices.parquet corresponds to `asset` in trade.csv.

## Python Project

This is a Python project. Use Polars for DataFrame operations (evident from the parquet schema in README.md). Sample data files are located in `sample_data/`.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
