"""Business Unit: backtest | Status: current.

Backtest result data transfer objects.

Defines immutable DTOs for backtest results including equity curves,
allocation history, trade log, and performance metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import pandas as pd

from the_alchemiser.backtest_v2.core.metrics import PerformanceMetrics


@dataclass(frozen=True)
class Trade:
    """Record of a single simulated trade.

    Attributes:
        date: Trade execution date
        symbol: Trading symbol
        action: 'BUY' or 'SELL'
        shares: Number of shares traded
        price: Execution price (after slippage)
        commission: Commission paid
        value: Total trade value (shares * price)

    """

    date: datetime
    symbol: str
    action: str  # 'BUY' or 'SELL'
    shares: Decimal
    price: Decimal
    commission: Decimal
    value: Decimal

    @property
    def net_value(self) -> Decimal:
        """Trade value after commission."""
        if self.action == "BUY":
            return self.value + self.commission
        return self.value - self.commission


@dataclass
class BacktestResult:
    """Complete results from a backtest run.

    Contains all data needed to analyze backtest performance including
    equity curves, allocations, trades, and computed metrics.

    Attributes:
        config_summary: Summary of backtest configuration
        equity_curve: DataFrame with daily portfolio values
        benchmark_curve: DataFrame with SPY benchmark values
        allocation_history: Dict of date -> target weights
        trades: List of executed trades
        metrics: Computed performance metrics
        strategy_metrics: Strategy-specific metrics
        benchmark_metrics: Benchmark (SPY) metrics for comparison

    """

    config_summary: dict[str, object]
    equity_curve: pd.DataFrame
    benchmark_curve: pd.DataFrame
    allocation_history: dict[datetime, dict[str, Decimal]]
    trades: list[Trade]
    metrics: PerformanceMetrics
    strategy_metrics: PerformanceMetrics
    benchmark_metrics: PerformanceMetrics
    errors: list[dict[str, object]] = field(default_factory=list)

    @property
    def total_return(self) -> Decimal:
        """Total strategy return."""
        return self.metrics.total_return

    @property
    def sharpe_ratio(self) -> float:
        """Strategy Sharpe ratio."""
        return self.metrics.sharpe_ratio

    @property
    def max_drawdown(self) -> Decimal:
        """Maximum drawdown."""
        return self.metrics.max_drawdown

    @property
    def alpha(self) -> float:
        """Alpha vs benchmark."""
        return float(self.total_return - self.benchmark_metrics.total_return)

    def to_dict(self) -> dict[str, object]:
        """Convert result to dictionary for serialization."""
        return {
            "config": self.config_summary,
            "metrics": {
                "total_return": str(self.metrics.total_return),
                "cagr": str(self.metrics.cagr),
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "sortino_ratio": self.metrics.sortino_ratio,
                "max_drawdown": str(self.metrics.max_drawdown),
                "max_drawdown_duration_days": self.metrics.max_drawdown_duration_days,
                "volatility": str(self.metrics.volatility),
                "win_rate": self.metrics.win_rate,
                "profit_factor": self.metrics.profit_factor,
                "total_trades": self.metrics.total_trades,
            },
            "benchmark_metrics": {
                "total_return": str(self.benchmark_metrics.total_return),
                "cagr": str(self.benchmark_metrics.cagr),
                "sharpe_ratio": self.benchmark_metrics.sharpe_ratio,
                "max_drawdown": str(self.benchmark_metrics.max_drawdown),
            },
            "alpha": self.alpha,
            "equity_curve": self.equity_curve.to_dict() if not self.equity_curve.empty else {},
            "trade_count": len(self.trades),
            "error_count": len(self.errors),
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 60,
            "BACKTEST RESULTS",
            "=" * 60,
            f"Strategy: {self.config_summary.get('strategy_path', 'N/A')}",
            f"Period: {self.config_summary.get('start_date', 'N/A')} to {self.config_summary.get('end_date', 'N/A')}",
            f"Initial Capital: ${self.config_summary.get('initial_capital', 'N/A'):,.2f}",
            "",
            "PERFORMANCE METRICS",
            "-" * 40,
            f"Total Return: {float(self.metrics.total_return) * 100:.2f}%",
            f"CAGR: {float(self.metrics.cagr) * 100:.2f}%",
            f"Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}",
            f"Sortino Ratio: {self.metrics.sortino_ratio:.2f}",
            f"Max Drawdown: {float(self.metrics.max_drawdown) * 100:.2f}%",
            f"Max DD Duration: {self.metrics.max_drawdown_duration_days} days",
            f"Volatility (Ann.): {float(self.metrics.volatility) * 100:.2f}%",
            "",
            "TRADING STATISTICS",
            "-" * 40,
            f"Total Trades: {self.metrics.total_trades}",
            f"Win Rate: {self.metrics.win_rate * 100:.1f}%",
            f"Profit Factor: {self.metrics.profit_factor:.2f}",
            "",
            "BENCHMARK COMPARISON (SPY)",
            "-" * 40,
            f"Benchmark Return: {float(self.benchmark_metrics.total_return) * 100:.2f}%",
            f"Alpha: {self.alpha * 100:.2f}%",
            f"Benchmark Sharpe: {self.benchmark_metrics.sharpe_ratio:.2f}",
            "",
            f"Errors: {len(self.errors)}",
            "=" * 60,
        ]
        return "\n".join(lines)
