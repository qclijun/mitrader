"""
Factory functions for edge-case test data.
"""
from datetime import date
import polars as pl


def create_trade_with_single_asset(asset_id: str) -> pl.DataFrame:
    """Single trade record for one asset (boundary test)."""
    return pl.DataFrame({
        'asset': [asset_id],
        'date': [date(2026, 4, 1)],
        'price': [100.0],
        'size': [100],
        'curr_size': [100],
        'comm': [0.5],
        'order': ['ORD001'],
        'pnl': [0.0],
        'pnlcomm': [0.0],
        'open_datetime': [date(2026, 4, 1)],
    }).with_columns(
        pl.col('asset').cast(pl.String),
        pl.col('date').cast(pl.Date),
        pl.col('open_datetime').cast(pl.Date),
    )


def create_prices_with_multiple_names(bond_id: str, names: list[str]) -> pl.DataFrame:
    """Price records where one bond_id maps to multiple bond_nm values."""
    rows = []
    for i, nm in enumerate(names):
        rows.append({
            'trade_date': date(2026, 4, 1 + i),
            'bond_id': bond_id,
            'bond_nm': nm,
            'open': 100.0 + i,
            'high': 102.0 + i,
            'low': 99.0 + i,
            'price': 101.0 + i,
            'volume': 1000.0,
        })
    return pl.DataFrame(rows).with_columns(
        pl.col('trade_date').cast(pl.Date),
        pl.col('bond_id').cast(pl.String),
    )


def create_trade_with_no_matching_price(asset_id: str) -> pl.DataFrame:
    """Trade record for an asset that has no entry in prices data."""
    return pl.DataFrame({
        'asset': [asset_id],
        'date': [date(2026, 4, 1)],
        'price': [100.0],
        'size': [100],
        'curr_size': [100],
        'comm': [0.5],
        'order': ['ORD001'],
        'pnl': [0.0],
        'pnlcomm': [0.0],
        'open_datetime': [date(2026, 4, 1)],
    }).with_columns(
        pl.col('asset').cast(pl.String),
        pl.col('date').cast(pl.Date),
        pl.col('open_datetime').cast(pl.Date),
    )
