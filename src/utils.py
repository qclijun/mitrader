"""
Utility functions for calculations and formatting.
"""


def calculate_return_percentage(pnl: float, pnlcomm: float) -> str:
    """Calculate and format return percentage.

    Args:
        pnl: Gross profit/loss
        pnlcomm: Net profit/loss after commission

    Returns:
        Formatted string showing percentage
    """
    if pnlcomm == 0:
        return "0.00%"

    percentage = pnlcomm
    sign = "+" if percentage > 0 else ""
    return f"{sign}{percentage:.2f}"


def get_trade_type(size: int) -> str:
    """Determine trade type from position size.

    Args:
        size: Position size (positive = buy, negative = sell)

    Returns:
        '买入' or '卖出'
    """
    return "买入" if size > 0 else "卖出"


def format_trade_row(row: dict) -> dict:
    """Format a trade row for display.

    Args:
        row: Raw trade record dict

    Returns:
        Formatted dict with display-friendly values
    """
    return {
        '日期': row['date'],
        '类型': get_trade_type(row['size']),
        '价格': f"{row['price']:.2f}",
        '仓位': abs(row['size']),
        '手续费': f"{row['comm']:.2f}",
        'pnl': f"{row['pnl']:.2f}",
        'pnlcomm': f"{row['pnlcomm']:.2f}"
    }