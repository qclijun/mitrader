"""
Unit tests for pnl_loader module.
"""
from pathlib import Path

import polars as pl
import pytest

from src.pnl_loader import get_return_columns, load_pnl_data


@pytest.mark.unit
class TestLoadPnlData:

    def test_load_pnl_data_basic(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0,jsl_index,kzz1\n'
            '2024-01-02T00:00:00.000000,0.0,0.0016,-0.0016\n'
            '2024-01-03T00:00:00.000000,0.01,-0.002,0.003\n'
        )

        df = load_pnl_data(str(p))

        assert df.height == 2
        assert df['datetime'].dtype == pl.Date
        assert df['kzz0'].dtype == pl.Float64
        assert df['jsl_index'].dtype == pl.Float64
        assert df['kzz1'].dtype == pl.Float64
        assert df['datetime'].to_list()[0].isoformat() == '2024-01-02'

    def test_load_pnl_data_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match='PnL file not found'):
            load_pnl_data(str(tmp_path / 'missing.csv'))

    def test_load_pnl_data_missing_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('kzz0,jsl_index\n0.01,0.02\n')

        with pytest.raises(ValueError, match='Missing required column'):
            load_pnl_data(str(p))

    def test_load_pnl_data_no_return_columns(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime\n2024-01-02\n')

        with pytest.raises(ValueError, match='No return series columns'):
            load_pnl_data(str(p))

    def test_load_pnl_data_invalid_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime,kzz0\nnot-a-date,0.01\n')

        with pytest.raises(ValueError, match='Unable to parse datetime'):
            load_pnl_data(str(p))

    def test_load_pnl_data_rejects_empty_datetime_value(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime,kzz0\n,0.01\n')

        with pytest.raises(ValueError, match='Unable to parse datetime'):
            load_pnl_data(str(p))

    def test_load_pnl_data_rejects_timezone_aware_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime,kzz0\n2024-01-02T00:00:00+08:00,0.01\n')

        with pytest.raises(ValueError, match='Timezone-aware datetime values are not supported'):
            load_pnl_data(str(p))

    def test_load_pnl_data_rejects_timezone_aware_datetime_without_colon(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text('datetime,kzz0\n2024-01-02T00:00:00+0800,0.01\n')

        with pytest.raises(ValueError, match='Timezone-aware datetime values are not supported'):
            load_pnl_data(str(p))

    def test_load_pnl_data_duplicate_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-02,0.01\n'
            '2024-01-02,0.02\n'
        )

        with pytest.raises(ValueError, match='Duplicate datetime'):
            load_pnl_data(str(p))

    def test_load_pnl_data_invalid_numeric_column(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-02,not-a-number\n'
        )

        with pytest.raises(ValueError, match='Unable to parse numeric return column: kzz0'):
            load_pnl_data(str(p))

    def test_load_pnl_data_rejects_return_below_minus_one(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-02,-1.01\n'
        )

        with pytest.raises(ValueError, match='Return values below -1.0 in column: kzz0'):
            load_pnl_data(str(p))

    @pytest.mark.parametrize('bad_value', ['NaN', 'inf', '-inf'])
    def test_load_pnl_data_rejects_non_finite_returns(self, tmp_path: Path, bad_value: str):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            f'2024-01-02,{bad_value}\n'
        )

        with pytest.raises(ValueError, match='Non-finite return values in column: kzz0'):
            load_pnl_data(str(p))

    def test_load_pnl_data_fills_missing_returns_with_zero(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0,jsl_index\n'
            '2024-01-02,,0.01\n'
            '2024-01-03,0.02,\n'
        )

        df = load_pnl_data(str(p))

        assert df['kzz0'].to_list() == [0.0, 0.02]
        assert df['jsl_index'].to_list() == [0.01, 0.0]

    def test_load_pnl_data_sorts_by_datetime(self, tmp_path: Path):
        p = tmp_path / 'pnl.csv'
        p.write_text(
            'datetime,kzz0\n'
            '2024-01-03,0.02\n'
            '2024-01-02,0.01\n'
        )

        df = load_pnl_data(str(p))

        assert [d.isoformat() for d in df['datetime'].to_list()] == ['2024-01-02', '2024-01-03']


@pytest.mark.unit
class TestGetReturnColumns:

    def test_get_return_columns_excludes_datetime(self):
        df = pl.DataFrame({
            'datetime': [],
            'kzz0': [],
            'jsl_index': [],
        })

        assert get_return_columns(df) == ['kzz0', 'jsl_index']
