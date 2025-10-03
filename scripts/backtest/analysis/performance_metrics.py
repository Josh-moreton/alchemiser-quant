"""Business Unit: shared | Status: current.

Performance metrics calculation for backtesting.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from scripts.backtest.models.backtest_result import PerformanceMetrics, TradeRecord
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def calculate_metrics(
    daily_values: list[tuple[datetime, Decimal]],
    trades: list[TradeRecord],
    initial_capital: Decimal,
) -> PerformanceMetrics:
    """Calculate performance metrics for a backtest.
    
    Args:
        daily_values: List of (date, portfolio_value) tuples
        trades: List of executed trades
        initial_capital: Starting portfolio value
        
    Returns:
        Performance metrics

    """
    if not daily_values:
        return _empty_metrics()

    final_value = daily_values[-1][1]

    # Total return
    total_return = ((final_value - initial_capital) / initial_capital) * Decimal("100")

    # Calculate daily returns
    daily_returns = _calculate_daily_returns(daily_values)

    # Sharpe ratio (annualized)
    sharpe_ratio = _calculate_sharpe_ratio(daily_returns)

    # Maximum drawdown
    max_drawdown = _calculate_max_drawdown(daily_values)

    # Trade statistics
    win_rate, avg_trade_return = _calculate_trade_stats(trades, daily_values)

    # Volatility (annualized)
    volatility = _calculate_volatility(daily_returns)

    return PerformanceMetrics(
        total_return=total_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        total_trades=len(trades),
        avg_trade_return=avg_trade_return,
        volatility=volatility,
    )


def _empty_metrics() -> PerformanceMetrics:
    """Return empty metrics when no data is available."""
    return PerformanceMetrics(
        total_return=Decimal("0"),
        sharpe_ratio=Decimal("0"),
        max_drawdown=Decimal("0"),
        win_rate=Decimal("0"),
        total_trades=0,
        avg_trade_return=Decimal("0"),
        volatility=Decimal("0"),
    )


def _calculate_daily_returns(
    daily_values: list[tuple[datetime, Decimal]]
) -> list[Decimal]:
    """Calculate daily returns from portfolio values.
    
    Args:
        daily_values: List of (date, value) tuples
        
    Returns:
        List of daily returns as decimals

    """
    if len(daily_values) < 2:
        return []

    returns: list[Decimal] = []

    for i in range(1, len(daily_values)):
        prev_value = daily_values[i - 1][1]
        curr_value = daily_values[i][1]

        if prev_value > 0:
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)

    return returns


def _calculate_sharpe_ratio(daily_returns: list[Decimal]) -> Decimal:
    """Calculate annualized Sharpe ratio.
    
    Assumes risk-free rate of 0 for simplicity.
    
    Args:
        daily_returns: List of daily returns
        
    Returns:
        Annualized Sharpe ratio

    """
    if not daily_returns:
        return Decimal("0")

    # Calculate mean and std dev
    mean_return = sum(daily_returns) / Decimal(str(len(daily_returns)))
    
    if len(daily_returns) < 2:
        return Decimal("0")

    variance = sum((r - mean_return) ** 2 for r in daily_returns) / Decimal(
        str(len(daily_returns) - 1)
    )
    std_dev = variance.sqrt() if variance > 0 else Decimal("0")

    if std_dev == 0:
        return Decimal("0")

    # Annualize (sqrt(252) for daily returns)
    return (mean_return / std_dev) * Decimal("252").sqrt()


def _calculate_max_drawdown(daily_values: list[tuple[datetime, Decimal]]) -> Decimal:
    """Calculate maximum drawdown as a percentage.
    
    Args:
        daily_values: List of (date, value) tuples
        
    Returns:
        Maximum drawdown percentage (positive number)

    """
    if not daily_values:
        return Decimal("0")

    max_value = daily_values[0][1]
    max_drawdown = Decimal("0")

    for _, value in daily_values:
        if value > max_value:
            max_value = value

        drawdown_value = (max_value - value) / max_value if max_value > 0 else Decimal("0")
        drawdown = drawdown_value * Decimal("100")

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def _calculate_trade_stats(
    trades: list[TradeRecord], daily_values: list[tuple[datetime, Decimal]]
) -> tuple[Decimal, Decimal]:
    """Calculate trade statistics.
    
    Args:
        trades: List of executed trades
        daily_values: List of portfolio values for context
        
    Returns:
        Tuple of (win_rate, avg_trade_return)

    """
    if not trades:
        return Decimal("0"), Decimal("0")

    # Simplified: Consider any BUY followed by SELL as a round trip
    # Track P&L per symbol
    symbol_pnl: dict[str, list[Decimal]] = {}

    for trade in trades:
        if trade.symbol not in symbol_pnl:
            symbol_pnl[trade.symbol] = []

        pnl = trade.value if trade.action == "SELL" else -trade.value
        symbol_pnl[trade.symbol].append(pnl)

    # Calculate wins
    total_pnl = sum(sum(pnls) for pnls in symbol_pnl.values())
    num_symbols = len(symbol_pnl)

    # Simplified win rate: symbols with positive P&L
    winning_symbols = sum(1 for pnls in symbol_pnl.values() if sum(pnls) > 0)
    win_rate = (
        (Decimal(str(winning_symbols)) / Decimal(str(num_symbols))) * Decimal("100")
        if num_symbols > 0
        else Decimal("0")
    )

    # Average trade return
    avg_trade_return = (
        total_pnl / Decimal(str(len(trades))) if trades else Decimal("0")
    )

    return win_rate, avg_trade_return


def _calculate_volatility(daily_returns: list[Decimal]) -> Decimal:
    """Calculate annualized volatility.
    
    Args:
        daily_returns: List of daily returns
        
    Returns:
        Annualized volatility percentage

    """
    if not daily_returns or len(daily_returns) < 2:
        return Decimal("0")

    mean_return = sum(daily_returns) / Decimal(str(len(daily_returns)))

    variance = sum((r - mean_return) ** 2 for r in daily_returns) / Decimal(
        str(len(daily_returns) - 1)
    )

    std_dev = variance.sqrt() if variance > 0 else Decimal("0")

    # Annualize (sqrt(252) for daily, then convert to percentage)
    return std_dev * Decimal("252").sqrt() * Decimal("100")
