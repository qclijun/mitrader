"""
Unit tests for data_loader module (7 tests).
"""
import pytest
import polars as pl
from pathlib import Path

from src.data_loader import load_trade_data, load_price_data


@pytest.mark.unit
class TestLoadTradeData:

    def test_load_trade_data_basic(self, tmp_path: Path):
        """Normal CSV loads with correct columns and row count."""
        p = tmp_path / 'trade.csv'
        p.write_text(
            'asset,date,price,size,curr_size,comm,order,pnl,pnlcomm,open_datetime\n'
            '113027,2026-04-01,100.50,100,100,0.5,ORD001,0.0,0.0,2026-04-01\n'
            '128082,2026-04-02,98.00,-100,0,0.5,ORD002,2.50,2.00,2026-04-01\n'
        )
        df = load_trade_data(str(p))

        assert df.height == 2
        for col in ['asset', 'date', 'price', 'size', 'pnl', 'pnlcomm', 'open_datetime']:
            assert col in df.columns

    def test_load_trade_data_asset_string_cast(self, tmp_path: Path):
        """asset column is cast to String type."""
        p = tmp_path / 'trade.csv'
        p.write_text(
            'asset,date,price,size,curr_size,comm,order,pnl,pnlcomm,open_datetime\n'
            '113027,2026-04-01,100.50,100,100,0.5,ORD001,0.0,0.0,2026-04-01\n'
        )
        df = load_trade_data(str(p))

        assert df['asset'].dtype == pl.String
        assert df['asset'][0] == '113027'

    def test_load_trade_data_date_parsing(self, tmp_path: Path):
        """date and open_datetime are parsed to pl.Date."""
        p = tmp_path / 'trade.csv'
        p.write_text(
            'asset,date,price,size,curr_size,comm,order,pnl,pnlcomm,open_datetime\n'
            '113027,2026-04-01,100.50,100,100,0.5,ORD001,0.0,0.0,2026-03-15\n'
        )
        df = load_trade_data(str(p))

        assert df['date'].dtype == pl.Date
        assert df['open_datetime'].dtype == pl.Date

    def test_load_trade_data_empty_file(self, empty_trade_csv: str):
        """Headers-only CSV returns empty DataFrame (does not raise)."""
        df = load_trade_data(empty_trade_csv)

        assert isinstance(df, pl.DataFrame)
        assert df.height == 0

    def test_load_trade_data_missing_columns(self, missing_cols_trade_csv: str):
        """CSV missing required columns raises ValueError."""
        with pytest.raises(ValueError, match='Missing required columns'):
            load_trade_data(missing_cols_trade_csv)

    def test_load_price_data_basic(self, tmp_path: Path):
        """Normal Parquet loads with expected schema columns."""
        price_df = pl.DataFrame({
            'trade_date': ['2026-04-01', '2026-04-02'],
            'bond_id': ['111001', '111001'],
            'bond_nm': ['债券A', '债券A'],
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [99.0, 100.0],
            'price': [101.0, 102.0],
            'volume': [1000.0, 1500.0],
        })
        p = tmp_path / 'prices.parquet'
        price_df.write_parquet(str(p))

        df = load_price_data(str(p))

        for col in ['trade_date', 'bond_id', 'bond_nm', 'open', 'high', 'low', 'price', 'volume']:
            assert col in df.columns

    def test_load_price_data_date_conversion(self, tmp_path: Path):
        """trade_date is converted to pl.Date."""
        price_df = pl.DataFrame({
            'trade_date': ['2026-04-01'],
            'bond_id': ['111001'],
            'bond_nm': ['债券A'],
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'price': [101.0],
            'volume': [1000.0],
        })
        p = tmp_path / 'prices.parquet'
        price_df.write_parquet(str(p))

        df = load_price_data(str(p))

        assert df['trade_date'].dtype == pl.Date
