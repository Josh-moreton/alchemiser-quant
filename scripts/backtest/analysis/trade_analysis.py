"""Business Unit: shared | Status: current.

Trade analysis for backtesting results.
"""

from __future__ import annotations

from decimal import Decimal

from scripts.backtest.models.backtest_result import TradeRecord


def analyze_trades(trades: list[TradeRecord]) -> dict[str, str | int | Decimal]:
    """Analyze trade history and return summary statistics.
    
    Args:
        trades: List of trade records
        
    Returns:
        Dictionary with trade analysis metrics

    """
    if not trades:
        return {
            "total_trades": 0,
            "buy_count": 0,
            "sell_count": 0,
            "total_volume": Decimal("0"),
            "total_commissions": Decimal("0"),
            "symbols_traded": 0,
        }

    buy_trades = [t for t in trades if t.action == "BUY"]
    sell_trades = [t for t in trades if t.action == "SELL"]

    total_volume = sum(t.value for t in trades)
    total_commissions = sum(t.commission for t in trades)

    symbols = {t.symbol for t in trades}

    return {
        "total_trades": len(trades),
        "buy_count": len(buy_trades),
        "sell_count": len(sell_trades),
        "total_volume": total_volume,
        "total_commissions": total_commissions,
        "symbols_traded": len(symbols),
        "unique_symbols": sorted(symbols),
    }
