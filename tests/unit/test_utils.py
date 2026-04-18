"""
Unit tests for utils module (7 tests).
"""
import pytest

from src.utils import get_trade_type, calculate_return_percentage, format_trade_row
from datetime import date


@pytest.mark.unit
class TestGetTradeType:

    def test_get_trade_type_buy(self):
        """Positive size returns '买入'."""
        assert get_trade_type(100) == '买入'
        assert get_trade_type(1) == '买入'

    def test_get_trade_type_sell(self):
        """Negative size returns '卖出'."""
        assert get_trade_type(-100) == '卖出'
        assert get_trade_type(-1) == '卖出'

    def test_get_trade_type_zero(self):
        """Zero size returns '未知' (boundary: no trade direction)."""
        assert get_trade_type(0) == '未知'


@pytest.mark.unit
class TestCalculateReturnPercentage:

    def test_calculate_return_percentage_positive(self):
        """Positive return: pnlcomm / (price×|size| - pnl) × 100 with '+' prefix."""
        # cost_basis = 110.0 × 100 - (-5.0) = 11005.0, pct = 550.0 / 11005.0 * 100 ≈ +4.998%
        result = calculate_return_percentage(-5.0, 550.0, 110.0, -100)
        assert result.startswith('+')
        assert result.endswith('%')
        assert '+4.99' in result or '+5.00' in result

    def test_calculate_return_percentage_negative(self):
        """Negative return: result starts with '-' and ends with '%'."""
        # cost_basis = 137.99 × 120 - (-693.60) = 17252.4, pct = -700.36 / 17252.4 * 100 ≈ -4.06%
        result = calculate_return_percentage(-693.60, -700.36, 137.99, -120)
        assert result.startswith('-')
        assert result.endswith('%')
        assert '-4.0' in result

    def test_calculate_return_percentage_zero(self):
        """Zero pnlcomm returns '0.00%'."""
        result = calculate_return_percentage(0.0, 0.0, 100.0, -100)
        assert result == '0.00%'


@pytest.mark.unit
class TestFormatTradeRow:

    def test_format_trade_row(self):
        """Row dict is formatted with correct keys and display values."""
        row = {
            'date': date(2026, 4, 1),
            'size': 100,
            'price': 100.5,
            'comm': 0.5,
            'pnl': 0.0,
            'pnlcomm': 0.0,
        }
        result = format_trade_row(row)

        assert result['日期'] == '2026-04-01'
        assert result['类型'] == '买入'
        assert result['价格'] == '100.50'
        assert result['仓位'] == 100
        assert result['手续费'] == '0.50'
