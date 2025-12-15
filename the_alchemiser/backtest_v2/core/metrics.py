"""Business Unit: backtest | Status: current.

Performance metrics calculation for backtesting.

Computes standard risk/return metrics from equity curves using vectorized
pandas operations for performance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

import pandas as pd

from the_alchemiser.backtest_v2.core.result import Trade
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Module constant
MODULE_NAME = "backtest_v2.core.metrics"

# Constants
TRADING_DAYS_PER_YEAR: Final[int] = 252
RISK_FREE_RATE: Final[float] = 0.05  # 5% annual risk-free rate


@dataclass(frozen=True)
class PerformanceMetrics:
    """Immutable container for backtest performance metrics.

    All percentages are expressed as decimals (e.g., 0.10 = 10%).

    Attributes:
        total_return: Total return over period (e.g., 0.25 = 25%)
        cagr: Compound annual growth rate
        sharpe_ratio: Risk-adjusted return (annualized)
        sortino_ratio: Downside risk-adjusted return
        max_drawdown: Maximum peak-to-trough decline
        max_drawdown_duration_days: Longest drawdown period
        volatility: Annualized volatility (std dev of returns)
        win_rate: Percentage of winning trades
        profit_factor: Gross profits / gross losses
        total_trades: Total number of trades executed
        calmar_ratio: CAGR / max drawdown

    """

    total_return: Decimal
    cagr: Decimal
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: Decimal
    max_drawdown_duration_days: int
    volatility: Decimal
    win_rate: float
    profit_factor: float
    total_trades: int
    calmar_ratio: float

    @classmethod
    def empty(cls) -> PerformanceMetrics:
        """Create empty metrics for failed backtests."""
        return cls(
            total_return=Decimal("0"),
            cagr=Decimal("0"),
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=Decimal("0"),
            max_drawdown_duration_days=0,
            volatility=Decimal("0"),
            win_rate=0.0,
            profit_factor=0.0,
            total_trades=0,
            calmar_ratio=0.0,
        )


def calculate_metrics(
    equity_curve: pd.DataFrame,
    trades: list[Trade] | None = None,
    risk_free_rate: float = RISK_FREE_RATE,
) -> PerformanceMetrics:
    """Calculate performance metrics from equity curve.

    Uses vectorized pandas operations for efficiency.

    Args:
        equity_curve: DataFrame with 'portfolio_value' column indexed by date
        trades: Optional list of Trade objects for win rate calculation
        risk_free_rate: Annual risk-free rate for Sharpe calculation

    Returns:
        PerformanceMetrics with all computed values

    """
    if equity_curve.empty or len(equity_curve) < 2:
        logger.warning("Empty or insufficient equity curve data", module=MODULE_NAME)
        return PerformanceMetrics.empty()

    try:
        values = equity_curve["portfolio_value"].astype(float)

        # Total return
        start_value = values.iloc[0]
        end_value = values.iloc[-1]
        total_return = Decimal(str((end_value - start_value) / start_value))

        # Calculate daily returns
        daily_returns = values.pct_change().dropna()

        if len(daily_returns) == 0:
            return PerformanceMetrics.empty()

        # CAGR
        num_days = len(values)
        years = num_days / TRADING_DAYS_PER_YEAR
        if years > 0 and end_value > 0 and start_value > 0:
            cagr_float = (end_value / start_value) ** (1 / years) - 1
            cagr = Decimal(str(cagr_float))
        else:
            cagr = Decimal("0")

        # Volatility (annualized)
        daily_vol = daily_returns.std()
        ann_vol = daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)
        volatility = Decimal(str(ann_vol))

        # Sharpe ratio
        daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
        excess_returns = daily_returns - daily_rf
        if daily_vol > 0:
            sharpe = (excess_returns.mean() / daily_vol) * math.sqrt(TRADING_DAYS_PER_YEAR)
        else:
            sharpe = 0.0

        # Sortino ratio (downside deviation)
        negative_returns = daily_returns[daily_returns < 0]
        if len(negative_returns) > 0:
            downside_dev = negative_returns.std() * math.sqrt(TRADING_DAYS_PER_YEAR)
            sortino = (float(cagr) - risk_free_rate) / downside_dev if downside_dev > 0 else 0.0
        else:
            sortino = float("inf") if float(cagr) > risk_free_rate else 0.0

        # Max drawdown
        cumulative_max = values.cummax()
        drawdown = (values - cumulative_max) / cumulative_max
        max_dd = Decimal(str(abs(drawdown.min())))

        # Max drawdown duration
        is_in_drawdown = drawdown < 0
        dd_groups = (~is_in_drawdown).cumsum()
        dd_durations = is_in_drawdown.groupby(dd_groups).sum()
        max_dd_duration = int(dd_durations.max()) if len(dd_durations) > 0 else 0

        # Calmar ratio
        if max_dd > 0:
            calmar = float(cagr) / float(max_dd)
        else:
            calmar = float("inf") if float(cagr) > 0 else 0.0

        # Trade statistics
        total_trades = len(trades) if trades else 0
        win_rate = 0.0
        profit_factor = 0.0

        if trades and len(trades) > 0:
            # Group trades by symbol to calculate P&L
            # For now, use simple heuristic based on equity curve
            positive_days = (daily_returns > 0).sum()
            total_days = len(daily_returns)
            win_rate = positive_days / total_days if total_days > 0 else 0.0

            # Profit factor from returns
            gross_profit = daily_returns[daily_returns > 0].sum()
            gross_loss = abs(daily_returns[daily_returns < 0].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        return PerformanceMetrics(
            total_return=total_return,
            cagr=cagr,
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4) if not math.isinf(sortino) else 999.0,
            max_drawdown=max_dd,
            max_drawdown_duration_days=max_dd_duration,
            volatility=volatility,
            win_rate=round(win_rate, 4),
            profit_factor=round(profit_factor, 4) if not math.isinf(profit_factor) else 999.0,
            total_trades=total_trades,
            calmar_ratio=round(calmar, 4) if not math.isinf(calmar) else 999.0,
        )

    except Exception as e:
        logger.error(
            "Failed to calculate metrics",
            module=MODULE_NAME,
            error=str(e),
            error_type=type(e).__name__,
        )
        return PerformanceMetrics.empty()


def calculate_benchmark_metrics(
    benchmark_curve: pd.DataFrame,
    risk_free_rate: float = RISK_FREE_RATE,
) -> PerformanceMetrics:
    """Calculate performance metrics for benchmark (SPY).

    Args:
        benchmark_curve: DataFrame with 'close' column indexed by date
        risk_free_rate: Annual risk-free rate

    Returns:
        PerformanceMetrics for benchmark

    """
    if benchmark_curve.empty:
        return PerformanceMetrics.empty()

    # Convert benchmark to portfolio_value format
    equity_format = pd.DataFrame(
        {"portfolio_value": benchmark_curve["close"]},
        index=benchmark_curve.index,
    )

    return calculate_metrics(equity_format, trades=None, risk_free_rate=risk_free_rate)
