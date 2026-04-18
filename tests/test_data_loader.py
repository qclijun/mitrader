"""
Unit tests for data_loader module.
"""
import pytest
import polars as pl
from pathlib import Path

from src.data_loader import load_trade_data


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


class TestLoadTradeDataTypes:
    """Tests for data type handling in load_trade_data."""

    @pytest.mark.unit
    def test_load_trade_data_asset_is_string(self, sample_trade_csv: str):
        """Verify asset column is cast to String type."""
        df = load_trade_data(sample_trade_csv)

        # Check dtype is String
        assert df['asset'].dtype == pl.String

    @pytest.mark.unit
    def test_load_trade_data_asset_values_preserved(self, sample_trade_csv: str):
        """Verify asset values are converted correctly (113027 -> '113027')."""
        df = load_trade_data(sample_trade_csv)

        # Values should be strings but preserve the numeric content
        asset_values = df['asset'].to_list()
        assert asset_values == ['113027', '128082']

    @pytest.mark.unit
    def test_load_trade_data_dates_parsed(self, sample_trade_csv: str):
        """Verify date columns are parsed correctly."""
        df = load_trade_data(sample_trade_csv)

        assert df['date'].dtype == pl.Date
        assert df['open_datetime'].dtype == pl.Date