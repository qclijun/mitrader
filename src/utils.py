"""
Utility functions for calculations and formatting.
"""


def calculate_return_percentage(pnl: float, pnlcomm: float, price: float, size: int) -> str:
    """Calculate and format return rate percentage for a sell trade.

    Uses the formula: cost_basis = price × |size| - pnl
    return_pct = pnlcomm / cost_basis × 100

    Args:
        pnl: Gross profit/loss (yuan)
        pnlcomm: Net profit/loss after commission (yuan)
        price: Sell price
        size: Position size (negative for sell)

    Returns:
        Formatted string like '+1.23%' or '-4.06%'
    """
    if pnlcomm == 0:
        return "0.00%"

    cost_basis = price * abs(size) - pnl
    if cost_basis == 0:
        return "0.00%"

    pct = pnlcomm / cost_basis * 100
    return f"{pct:+.2f}%"


def get_trade_type(size: int) -> str:
    """Determine trade type from position size.

    Args:
        size: Position size (positive = buy, negative = sell)

    Returns:
        '买入' or '卖出'
    """
    if size > 0:
        return "买入"
    elif size < 0:
        return "卖出"
    else:
        return "未知"


def format_trade_row(row: dict) -> dict:
    """Format a trade row for display.

    Args:
        row: Raw trade record dict

    Returns:
        Formatted dict with display-friendly values
    """
    # Calculate return percentage only for complete close sells (curr_size == 0)
    if row['size'] < 0 and row['curr_size'] == 0:
        return_pct = calculate_return_percentage(
            row['pnl'], row['pnlcomm'], row['price'], row['size']
        )
    else:
        return_pct = "-"

    return {
        '日期': str(row['date']),
        '类型': get_trade_type(row['size']),
        '价格': f"{row['price']:.2f}",
        '仓位': abs(row['size']),
        '手续费': f"{row['comm']:.2f}",
        'pnl': f"{row['pnl']:.2f}",
        'pnlcomm': f"{row['pnlcomm']:.2f}",
        '收益率': return_pct
    }