"""
Data loading and validation module.
"""
import polars as pl
from pathlib import Path
from typing import Optional


def load_trade_data(file_path: str) -> pl.DataFrame:
    """Load trade records from CSV file.

    Args:
        file_path: Path to trade.csv file

    Returns:
        Polars DataFrame with trade records

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If required columns are missing
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Trade file not found: {file_path}")

    df = pl.read_csv(file_path)

    # Validate required columns
    required_cols = ['asset', 'date', 'price', 'size', 'pnl', 'pnlcomm', 'open_datetime']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in trade.csv: {missing}")

    # Parse date columns and cast asset to string for bond_id matching
    df = df.with_columns(
        pl.col('date').str.to_date('%Y-%m-%d').alias('date'),
        pl.col('open_datetime').str.to_date('%Y-%m-%d').alias('open_datetime'),
        pl.col('asset').cast(pl.String).alias('asset')
    )

    return df


def load_price_data(file_path: str) -> pl.DataFrame:
    """Load price data from Parquet file.

    Args:
        file_path: Path to prices.parquet file

    Returns:
        Polars DataFrame with price data

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Price file not found: {file_path}")

    df = pl.read_parquet(file_path)

    # Convert trade_date to date type for matching
    df = df.with_columns(
        pl.col('trade_date').cast(pl.Date).alias('trade_date')
    )

    return df


def get_asset_list(trade_df: pl.DataFrame, price_df: pl.DataFrame) -> pl.DataFrame:
    """Get unique assets from trade records with their stats.

    Args:
        trade_df: Trade records DataFrame
        price_df: Price data DataFrame

    Returns:
        DataFrame with columns: asset_id, asset_nm, trade_count, total_pnlcomm
    """
    # Get bond_nm from price data — concatenate multiple names for same bond_id
    asset_names = (
        price_df.select(['bond_id', 'bond_nm'])
        .unique()
        .group_by('bond_id')
        .agg(pl.col('bond_nm').sort().str.join(','))
    )

    # Aggregate trade stats per asset
    trade_stats = trade_df.group_by('asset').agg([
        pl.len().alias('trade_count'),
        pl.col('pnlcomm').sum().alias('total_pnlcomm')
    ])

    # Join to get asset names
    result = trade_stats.join(
        asset_names,
        left_on='asset',
        right_on='bond_id',
        how='left'
    ).select([
        pl.col('asset').alias('asset_id'),
        pl.col('bond_nm').alias('asset_nm'),
        'trade_count',
        'total_pnlcomm'
    ]).sort('total_pnlcomm', descending=True)

    return result


def get_asset_trades(trade_df: pl.DataFrame, asset_id: str) -> pl.DataFrame:
    """Get all trades for a specific asset.

    Args:
        trade_df: Trade records DataFrame
        asset_id: Asset ID to filter

    Returns:
        DataFrame with trades for the asset, sorted by date
    """
    return trade_df.filter(pl.col('asset') == asset_id).sort('date')


def get_asset_prices(price_df: pl.DataFrame, asset_id: str) -> pl.DataFrame:
    """Get all price data for a specific asset.

    Args:
        price_df: Price data DataFrame
        asset_id: Asset ID to filter

    Returns:
        DataFrame with price data for the asset, sorted by date
    """
    return price_df.filter(pl.col('bond_id') == asset_id).sort('trade_date')


def filter_assets(asset_list: pl.DataFrame, search_term: str) -> pl.DataFrame:
    """Filter asset list by search term (ID or name).

    Args:
        asset_list: Full asset list DataFrame
        search_term: Search string to filter by

    Returns:
        Filtered DataFrame
    """
    if not search_term:
        return asset_list

    search_lower = search_term.lower()
    return asset_list.filter(
        pl.col('asset_id').str.contains(search_lower) |
        pl.col('asset_nm').str.contains(search_lower.casefold())
    )