"""Business Unit: shared | Status: current.

Reporting for backtesting results.
"""

from __future__ import annotations

from scripts.backtest.analysis.trade_analysis import analyze_trades
from scripts.backtest.models.backtest_result import BacktestResult


def generate_report(result: BacktestResult) -> str:
    """Generate a text report of backtest results.
    
    Args:
        result: Backtest result object
        
    Returns:
        Formatted text report

    """
    trade_stats = analyze_trades(result.trades)

    report_lines = [
        "=" * 60,
        "BACKTEST RESULTS",
        "=" * 60,
        "",
        f"Strategy: {result.strategy_name}",
        f"Period: {result.start_date.date()} to {result.end_date.date()}",
        "",
        "PERFORMANCE METRICS",
        "-" * 60,
        f"Initial Capital: ${result.initial_capital:,.2f}",
        f"Final Capital: ${result.final_capital:,.2f}",
        f"Total Return: {result.metrics.total_return:.2f}%",
        f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}",
        f"Max Drawdown: {result.metrics.max_drawdown:.2f}%",
        f"Volatility: {result.metrics.volatility:.2f}%",
        "",
        "TRADE STATISTICS",
        "-" * 60,
        f"Total Trades: {result.metrics.total_trades}",
        f"Win Rate: {result.metrics.win_rate:.2f}%",
        f"Avg Trade Return: ${result.metrics.avg_trade_return:.2f}",
        f"Total Volume: ${trade_stats['total_volume']:,.2f}",
        f"Total Commissions: ${trade_stats['total_commissions']:,.2f}",
        f"Symbols Traded: {trade_stats['symbols_traded']}",
        "",
        "=" * 60,
    ]

    return "\n".join(report_lines)


def print_report(result: BacktestResult) -> None:
    """Print backtest report to console.
    
    Args:
        result: Backtest result object

    """
    report = generate_report(result)
    print(report)
