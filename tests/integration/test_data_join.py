"""
Integration tests for data joining and filtering (7 tests).
"""
from datetime import date

import polars as pl
import pytest

from src.data_loader import (
    load_trade_data,
    load_price_data,
    get_asset_list,
    get_asset_trades,
    get_asset_prices,
    filter_assets,
)
from tests.fixtures.edge_cases import (
    create_prices_with_multiple_names,
    create_trade_with_no_matching_price,
    create_trade_with_single_asset,
)


@pytest.mark.integration
class TestGetAssetList:

    def test_get_asset_list_join_correct(self, sample_trade_path, sample_prices_path):
        """Trade stats join correctly with price asset names (bond_id ↔ asset)."""
        trade_df = load_trade_data(sample_trade_path)
        price_df = load_price_data(sample_prices_path)

        result = get_asset_list(trade_df, price_df)

        assert len(result) > 0
        assert 'asset_nm' in result.columns
        # At least some assets should have resolved names
        non_null = result.filter(pl.col('asset_nm').is_not_null())
        assert len(non_null) > 0

    def test_get_asset_list_unique_asset_id(self, sample_trade_path, sample_prices_path):
        """asset_id column has no duplicates in the returned list."""
        trade_df = load_trade_data(sample_trade_path)
        price_df = load_price_data(sample_prices_path)

        result = get_asset_list(trade_df, price_df)

        assert result['asset_id'].n_unique() == result.height

    def test_get_asset_list_multiple_names_concat(self):
        """Non-letter-prefixed bond_nm values are joined with ','."""
        trade_df = create_trade_with_single_asset('999001')
        price_df = create_prices_with_multiple_names('999001', ['债券甲', '债券乙'])

        result = get_asset_list(trade_df, price_df)

        row = result.filter(pl.col('asset_id') == '999001')
        assert row.height == 1
        nm = row['asset_nm'][0]
        assert '债券甲' in nm
        assert '债券乙' in nm
        assert ',' in nm

    def test_get_asset_list_strips_whitespace_from_names(self):
        """Whitespace inside bond_nm is removed before processing."""
        trade_df = create_trade_with_single_asset('777001')
        price_df = create_prices_with_multiple_names('777001', ['债 券 A', ' 债券B '])

        result = get_asset_list(trade_df, price_df)

        row = result.filter(pl.col('asset_id') == '777001')
        assert row.height == 1
        nm = row['asset_nm'][0]
        assert ' ' not in nm          # no spaces remain
        assert '债券A' in nm
        assert '债券B' in nm

    def test_get_asset_list_filters_letter_prefixed_names(self):
        """bond_nm values starting with an English letter (Z, XD, N…) are excluded."""
        trade_df = create_trade_with_single_asset('888001')
        # Mix: one Chinese name + two letter-prefixed names
        price_df = create_prices_with_multiple_names('888001', ['正常债券', 'Z888001', 'XD888001'])

        result = get_asset_list(trade_df, price_df)

        row = result.filter(pl.col('asset_id') == '888001')
        assert row.height == 1
        nm = row['asset_nm'][0]
        assert '正常债券' in nm
        assert 'Z888001' not in nm
        assert 'XD888001' not in nm

    def test_get_asset_list_no_matching_prices(self):
        """Asset in trades with no matching bond_id in prices has null asset_nm."""
        trade_df = create_trade_with_no_matching_price('NOMATCH001')
        price_df = pl.DataFrame({
            'trade_date': [date(2026, 4, 1)],
            'bond_id': ['OTHER999'],
            'bond_nm': ['其他债券'],
            'open': [100.0], 'high': [102.0], 'low': [99.0],
            'price': [101.0], 'volume': [1000.0],
        }).with_columns(
            pl.col('trade_date').cast(pl.Date),
            pl.col('bond_id').cast(pl.String),
        )

        result = get_asset_list(trade_df, price_df)

        row = result.filter(pl.col('asset_id') == 'NOMATCH001')
        assert row.height == 1
        assert row['asset_nm'][0] is None


@pytest.mark.integration
class TestGetAssetData:

    def test_get_asset_prices_by_id(self, sample_trade_path, sample_prices_path):
        """Filtering prices by bond_id returns only that asset's price series."""
        trade_df = load_trade_data(sample_trade_path)
        price_df = load_price_data(sample_prices_path)
        asset_id = trade_df['asset'][0]

        result = get_asset_prices(price_df, asset_id)

        assert len(result) > 0
        assert result['bond_id'].unique().to_list() == [asset_id]

    def test_get_asset_trades_by_id(self, sample_trade_path):
        """Filtering trades by asset returns only that asset's records."""
        trade_df = load_trade_data(sample_trade_path)
        asset_id = trade_df['asset'][0]

        result = get_asset_trades(trade_df, asset_id)

        assert len(result) > 0
        assert result['asset'].unique().to_list() == [asset_id]

    def test_filter_assets_fuzzy_search(self, sample_trade_path, sample_prices_path):
        """filter_assets matches on both asset_id and asset_nm (case-insensitive)."""
        trade_df = load_trade_data(sample_trade_path)
        price_df = load_price_data(sample_prices_path)
        asset_list = get_asset_list(trade_df, price_df)

        first_id = asset_list['asset_id'][0]
        partial_id = first_id[:3]  # partial match on ID

        result = filter_assets(asset_list, partial_id)

        assert len(result) > 0
        assert all(partial_id in row for row in result['asset_id'].to_list())
