"""Business Unit: shared | Status: current.

QuantStats-based performance reporting.

Generates professional tearsheet reports using QuantStats library.
Supports both equity curve inputs (backtest) and trade reconstruction (production).

USAGE:
======
# From backtest results (equity curve available)
from the_alchemiser.shared.reporting import generate_tearsheet
generate_tearsheet(equity_series, output_path="report.html")

# From production trade data (reconstruct equity)
from the_alchemiser.shared.reporting import generate_tearsheet_from_trades
generate_tearsheet_from_trades(trades, initial_capital, output_path="report.html")

# Get extended metrics only
from the_alchemiser.shared.reporting import calculate_extended_metrics
metrics = calculate_extended_metrics(returns_series)
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

# QuantStats imports
import quantstats as qs

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.strategy_lot import StrategyLot

logger = get_logger(__name__)

__all__ = [
    "ExtendedMetrics",
    "calculate_extended_metrics",
    "generate_tearsheet",
    "generate_tearsheet_from_trades",
]


# Risk-free rate and annualization constants
RISK_FREE_RATE = 0.05  # 5% annual
TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class ExtendedMetrics:
    """Extended performance metrics calculated via QuantStats.

    Provides additional risk metrics beyond the core PerformanceMetrics.
    All values are calculated using QuantStats library functions.

    Attributes:
        var_95: Value at Risk at 95% confidence (daily)
        cvar_95: Conditional VaR (Expected Shortfall) at 95%
        omega_ratio: Omega ratio (probability-weighted gains/losses)
        kelly_criterion: Kelly bet size for optimal growth
        ulcer_index: Ulcer Index (measure of drawdown pain)
        payoff_ratio: Average win / average loss
        tail_ratio: Right tail / left tail (95th percentile)
        common_sense_ratio: Tail ratio * payoff ratio
        outlier_win_ratio: Profit from outliers vs total profit
        outlier_loss_ratio: Loss from outliers vs total loss

    """

    var_95: float
    cvar_95: float
    omega_ratio: float
    kelly_criterion: float
    ulcer_index: float
    payoff_ratio: float
    tail_ratio: float
    common_sense_ratio: float
    outlier_win_ratio: float
    outlier_loss_ratio: float


def _equity_to_returns(equity: pd.Series) -> pd.Series:
    """Convert equity curve to daily returns series.

    Args:
        equity: Series of portfolio values indexed by date

    Returns:
        Series of daily percentage returns (decimals, not percent)

    """
    returns = equity.pct_change().dropna()
    # QuantStats expects timezone-naive index
    if returns.index.tz is not None:
        returns.index = returns.index.tz_localize(None)
    return returns


def calculate_extended_metrics(
    returns: pd.Series,
    rf: float = RISK_FREE_RATE,
) -> ExtendedMetrics:
    """Calculate extended performance metrics using QuantStats.

    Args:
        returns: Daily returns series (decimals, e.g., 0.01 = 1%)
        rf: Annual risk-free rate (default 5%)

    Returns:
        ExtendedMetrics dataclass with all calculated values

    """
    # Ensure timezone-naive
    if returns.index.tz is not None:
        returns = returns.copy()
        returns.index = returns.index.tz_localize(None)

    # Calculate metrics using QuantStats
    return ExtendedMetrics(
        var_95=float(qs.stats.var(returns)),
        cvar_95=float(qs.stats.cvar(returns)),
        omega_ratio=float(qs.stats.omega(returns, rf=rf)),
        kelly_criterion=float(qs.stats.kelly_criterion(returns)),
        ulcer_index=float(qs.stats.ulcer_index(returns)),
        payoff_ratio=float(qs.stats.payoff_ratio(returns)),
        tail_ratio=float(qs.stats.tail_ratio(returns)),
        common_sense_ratio=float(qs.stats.common_sense_ratio(returns)),
        outlier_win_ratio=float(qs.stats.outlier_win_ratio(returns)),
        outlier_loss_ratio=float(qs.stats.outlier_loss_ratio(returns)),
    )


def generate_tearsheet(
    equity: pd.Series,
    output_path: Path | str | None = None,
    title: str = "Portfolio Performance",
    benchmark: str = "SPY",
    rf: float = RISK_FREE_RATE,
) -> str:
    """Generate QuantStats HTML tearsheet from equity curve.

    Creates a professional-grade performance report with:
    - 50+ performance metrics
    - Equity curve vs benchmark
    - Drawdown analysis
    - Monthly/yearly returns heatmaps
    - Rolling statistics

    Args:
        equity: Series of portfolio values indexed by datetime
        output_path: Path to save HTML file (optional)
        title: Report title
        benchmark: Benchmark ticker for comparison (default SPY)
        rf: Annual risk-free rate (default 5%)

    Returns:
        HTML report as string

    Raises:
        ValueError: If equity series is empty or too short

    """
    if equity.empty:
        raise ValueError("Cannot generate tearsheet from empty equity series")

    if len(equity) < 5:
        raise ValueError("Equity series too short for meaningful analysis (need >= 5 days)")

    # Convert to returns
    returns = _equity_to_returns(equity)

    logger.info(
        "Generating QuantStats tearsheet",
        extra={
            "title": title,
            "benchmark": benchmark,
            "data_points": len(returns),
            "start_date": str(returns.index.min()),
            "end_date": str(returns.index.max()),
        },
    )

    # Generate HTML to string buffer if no path provided
    if output_path is None:
        # Generate to string buffer
        output = io.StringIO()
        qs.reports.html(
            returns,
            benchmark=benchmark,
            output=output,
            title=title,
            rf=rf,
            periods_per_year=TRADING_DAYS_PER_YEAR,
        )
        html = output.getvalue()
        output.close()
        return html

    # Generate to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    qs.reports.html(
        returns,
        benchmark=benchmark,
        output=str(output_path),
        title=title,
        rf=rf,
        periods_per_year=TRADING_DAYS_PER_YEAR,
    )

    logger.info(
        "Tearsheet saved",
        extra={"output_path": str(output_path)},
    )

    return output_path.read_text(encoding="utf-8")


def generate_tearsheet_from_trades(
    trades: list[StrategyLot],
    initial_capital: Decimal,
    output_path: Path | str | None = None,
    title: str = "Portfolio Performance",
    benchmark: str = "SPY",
    rf: float = RISK_FREE_RATE,
) -> str:
    """Generate tearsheet by reconstructing equity curve from trade data.

    Useful for production reporting where we have trade records but not
    a pre-computed equity curve.

    Args:
        trades: List of StrategyLot objects representing closed trades
        initial_capital: Starting portfolio value
        output_path: Path to save HTML file (optional)
        title: Report title
        benchmark: Benchmark ticker for comparison
        rf: Annual risk-free rate

    Returns:
        HTML report as string

    Raises:
        ValueError: If no valid trades provided

    """
    if not trades:
        raise ValueError("Cannot generate tearsheet with no trades")

    # Reconstruct equity curve from trades
    equity = _reconstruct_equity_from_trades(trades, initial_capital)

    if equity.empty:
        raise ValueError("Could not reconstruct equity curve from trades")

    return generate_tearsheet(
        equity=equity,
        output_path=output_path,
        title=title,
        benchmark=benchmark,
        rf=rf,
    )


def _reconstruct_equity_from_trades(
    trades: list[StrategyLot],
    initial_capital: Decimal,
) -> pd.Series:
    """Reconstruct daily equity curve from trade records.

    Uses closed trade P&L to build a cumulative equity series.
    Assumes trades are sorted by exit timestamp.

    Args:
        trades: List of closed StrategyLot objects
        initial_capital: Starting portfolio value

    Returns:
        Series of daily portfolio values indexed by date

    """
    if not trades:
        return pd.Series(dtype=float)

    # Filter to closed trades only and sort by exit date
    closed_trades = [t for t in trades if not t.is_open and t.fully_closed_at is not None]

    if not closed_trades:
        return pd.Series(dtype=float)

    # Sort by exit timestamp
    closed_trades.sort(key=lambda t: t.fully_closed_at)  # type: ignore[arg-type, return-value]

    # Build daily P&L
    daily_pnl: dict[datetime, Decimal] = {}

    for trade in closed_trades:
        # Use exit date (date only, not datetime)
        exit_date = trade.fully_closed_at.replace(  # type: ignore[union-attr]
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        )

        # Calculate realized P&L for this trade
        pnl = trade.realized_pnl

        if exit_date in daily_pnl:
            daily_pnl[exit_date] += pnl
        else:
            daily_pnl[exit_date] = pnl

    # Convert to series and build cumulative equity
    pnl_series = pd.Series(daily_pnl).sort_index()
    cumulative_pnl = pnl_series.cumsum()
    equity = float(initial_capital) + cumulative_pnl.astype(float)

    # Ensure we have a complete date range (fill gaps with previous value)
    if len(equity) > 1:
        date_range = pd.date_range(start=equity.index.min(), end=equity.index.max(), freq="D")
        equity = equity.reindex(date_range, method="ffill")

    equity.name = "portfolio_value"
    return equity


def generate_metrics_snapshot(
    equity: pd.Series,
    benchmark: str = "SPY",
    rf: float = RISK_FREE_RATE,
) -> dict[str, float]:
    """Generate a quick metrics snapshot without full HTML report.

    Useful for logging, monitoring, or quick performance checks.

    Args:
        equity: Series of portfolio values indexed by datetime
        benchmark: Benchmark ticker for comparison
        rf: Annual risk-free rate

    Returns:
        Dictionary of key performance metrics

    """
    if equity.empty or len(equity) < 2:
        return {}

    returns = _equity_to_returns(equity)

    # Get basic QuantStats metrics (moved to reports module in v0.0.78+)
    metrics = qs.reports.metrics(returns, benchmark=benchmark, rf=rf, display=False)

    # Convert to dict with float values
    result: dict[str, float] = {}
    if isinstance(metrics, pd.DataFrame):
        for idx in metrics.index:
            val = metrics.loc[idx, "Strategy"]
            if pd.notna(val):
                with contextlib.suppress(ValueError, TypeError):
                    result[str(idx)] = float(val)

    return result
