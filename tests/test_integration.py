"""
Integration tests for data loading and filtering.
"""
import pytest
import polars as pl
from pathlib import Path

from src.data_loader import (
    load_trade_data,
    load_price_data,
    get_asset_list,
    get_asset_trades,
    get_asset_prices
)


@pytest.fixture
def sample_trade_csv(tmp_path: Path) -> str:
    """Create a sample trade.csv file for testing."""
    csv_path = tmp_path / "trade.csv"
    csv_content = """asset,date,price,size,curr_size,comm,order,pnl,pnlcomm,open_datetime
113027,2026-04-01,100.50,100,100,0.5,ORD001,0.0,0.0,2026-04-01
128082,2026-04-02,98.00,-100,0,0.5,ORD002,2.50,2.00,2026-04-01
"""
    csv_path.write_text(csv_content)
    return str(csv_path)


@pytest.fixture
def sample_price_parquet(tmp_path: Path) -> str:
    """Create a sample prices.parquet file for testing."""
    parquet_path = tmp_path / "prices.parquet"

    # Create price data with bond_id as string
    df = pl.DataFrame({
        'trade_date': ['2026-04-01', '2026-04-01', '2026-04-02', '2026-04-02'],
        'bond_id': ['113027', '128082', '113027', '128082'],
        'bond_nm': ['债券A', '债券B', '债券A', '债券B'],
        'open': [100.0, 98.0, 101.0, 97.0],
        'high': [102.0, 100.0, 103.0, 99.0],
        'low': [99.0, 96.0, 100.0, 95.0],
        'price': [101.0, 99.0, 102.0, 96.0],
        'volume': [1000.0, 2000.0, 1500.0, 2500.0]
    })

    df.write_parquet(str(parquet_path))
    return str(parquet_path)


@pytest.mark.integration
class TestAssetPriceJoin:
    """Tests for asset-price joining after type fix."""

    def test_get_asset_prices_returns_data(self, sample_trade_csv: str, sample_price_parquet: str):
        """Verify filtering by string asset_id returns non-empty DataFrame."""
        trade_df = load_trade_data(sample_trade_csv)
        price_df = load_price_data(sample_price_parquet)

        # Get first asset id (now string type)
        asset_id = trade_df['asset'][0]

        # Filter prices - should return data now that types match
        result = get_asset_prices(price_df, asset_id)

        assert len(result) > 0, f"Expected prices for asset {asset_id}, got empty DataFrame"

    def test_get_asset_trades_returns_data(self, sample_trade_csv: str):
        """Verify filtering trades by asset_id works."""
        trade_df = load_trade_data(sample_trade_csv)
        asset_id = '113027'

        result = get_asset_trades(trade_df, asset_id)

        assert len(result) > 0, f"Expected trades for asset {asset_id}"
        assert all(row['asset'] == '113027' for row in result.iter_rows(named=True))

    def test_get_asset_list_join_works(self, sample_trade_csv: str, sample_price_parquet: str):
        """Verify asset-bond_id join succeeds after type match."""
        trade_df = load_trade_data(sample_trade_csv)
        price_df = load_price_data(sample_price_parquet)

        result = get_asset_list(trade_df, price_df)

        # Should have joined successfully with asset names
        assert len(result) > 0
        assert 'asset_nm' in result.columns

        # No null asset names (join succeeded)
        null_count = result.filter(pl.col('asset_nm').is_null()).height
        assert null_count == 0, "Join failed - some asset_nm are null"