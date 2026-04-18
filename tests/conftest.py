"""
Shared pytest fixtures for all test layers.
"""
from datetime import date
from pathlib import Path

import polars as pl
import pytest


# ── Paths ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def sample_trade_path() -> str:
    """Path to real sample_data/trade.csv (main-flow tests)."""
    p = Path(__file__).parent.parent / 'sample_data' / 'trade.csv'
    assert p.exists(), f"sample_data/trade.csv not found at {p}"
    return str(p)


@pytest.fixture(scope='session')
def sample_prices_path() -> str:
    """Path to real sample_data/prices.parquet (main-flow tests)."""
    p = Path(__file__).parent.parent / 'sample_data' / 'prices.parquet'
    assert p.exists(), f"sample_data/prices.parquet not found at {p}"
    return str(p)


# ── In-memory minimal DataFrames ───────────────────────────────────────────────

@pytest.fixture
def minimal_trade_df() -> pl.DataFrame:
    """3-row trade DataFrame with both buy and sell records."""
    return pl.DataFrame({
        'asset': ['111001', '111001', '222002'],
        'date': [date(2026, 4, 1), date(2026, 4, 5), date(2026, 4, 2)],
        'price': [100.0, 102.0, 98.0],
        'size': [100, -100, 200],
        'curr_size': [100, 0, 200],
        'comm': [0.5, 0.5, 1.0],
        'order': ['ORD001', 'ORD002', 'ORD003'],
        'pnl': [0.0, 2.0, 0.0],
        'pnlcomm': [0.0, 1.5, 0.0],
        'open_datetime': [date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 2)],
    }).with_columns(
        pl.col('asset').cast(pl.String),
        pl.col('date').cast(pl.Date),
        pl.col('open_datetime').cast(pl.Date),
    )


@pytest.fixture
def minimal_price_df() -> pl.DataFrame:
    """5-day price DataFrame for a single asset."""
    return pl.DataFrame({
        'trade_date': [
            date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3),
            date(2026, 4, 4), date(2026, 4, 5),
        ],
        'bond_id': ['111001'] * 5,
        'bond_nm': ['测试债券A'] * 5,
        'open': [100.0, 101.0, 101.5, 102.0, 101.0],
        'high': [102.0, 103.0, 103.0, 104.0, 103.0],
        'low': [99.0, 100.0, 100.5, 101.0, 100.0],
        'price': [101.0, 102.0, 102.5, 103.0, 102.0],
        'volume': [1000.0] * 5,
    }).with_columns(
        pl.col('trade_date').cast(pl.Date),
        pl.col('bond_id').cast(pl.String),
    )


# ── Temporary file fixtures ───────────────────────────────────────────────────

@pytest.fixture
def empty_trade_csv(tmp_path: Path) -> str:
    """CSV with headers only, no data rows."""
    p = tmp_path / 'empty_trade.csv'
    p.write_text(
        'asset,date,price,size,curr_size,comm,order,pnl,pnlcomm,open_datetime\n'
    )
    return str(p)


@pytest.fixture
def missing_cols_trade_csv(tmp_path: Path) -> str:
    """CSV missing required columns (no pnl/pnlcomm)."""
    p = tmp_path / 'missing_cols_trade.csv'
    p.write_text(
        'asset,date,price,size\n'
        '111001,2026-04-01,100.0,100\n'
    )
    return str(p)


@pytest.fixture
def multiple_names_price_df() -> pl.DataFrame:
    """Price DataFrame where one bond_id maps to two different bond_nm values."""
    return pl.DataFrame({
        'trade_date': [date(2026, 4, 1), date(2026, 4, 2)],
        'bond_id': ['999001', '999001'],
        'bond_nm': ['债券甲', '债券乙'],
        'open': [100.0, 101.0],
        'high': [102.0, 103.0],
        'low': [99.0, 100.0],
        'price': [101.0, 102.0],
        'volume': [1000.0, 1000.0],
    }).with_columns(
        pl.col('trade_date').cast(pl.Date),
        pl.col('bond_id').cast(pl.String),
    )
