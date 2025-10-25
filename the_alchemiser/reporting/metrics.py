"""Business Unit: reporting | Status: current.

Performance metrics calculator for account reports.

Computes key trading metrics from account snapshot data:
- Sharpe Ratio
- Calmar Ratio
- Maximum Drawdown
- CAGR (Compound Annual Growth Rate)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import numpy as np

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

__all__ = ["compute_metrics_from_snapshot"]


def compute_sharpe_ratio(
    returns: list[Decimal], risk_free_rate: Decimal = Decimal("0.02")
) -> Decimal:
    """Calculate Sharpe Ratio from returns.

    Args:
        returns: List of period returns
        risk_free_rate: Annual risk-free rate (default 2%)

    Returns:
        Sharpe Ratio as Decimal

    """
    if not returns or len(returns) < 2:
        return Decimal("0.0")

    # Convert to numpy for calculations
    returns_arr = np.array([float(r) for r in returns])

    # Annualize the Sharpe ratio (assuming daily returns)
    mean_return = np.mean(returns_arr)
    std_return = np.std(returns_arr, ddof=1)

    if std_return == 0:
        return Decimal("0.0")

    # Sharpe = (mean_return - risk_free_daily) / std * sqrt(252)
    risk_free_daily = float(risk_free_rate) / 252
    sharpe = (mean_return - risk_free_daily) / std_return * np.sqrt(252)

    return Decimal(str(round(sharpe, 2)))


def compute_max_drawdown(equity_curve: list[Decimal]) -> Decimal:
    """Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of portfolio equity values over time

    Returns:
        Maximum drawdown as percentage (negative value)

    """
    if not equity_curve or len(equity_curve) < 2:
        return Decimal("0.0")

    equity_arr = np.array([float(e) for e in equity_curve])

    # Calculate running maximum
    running_max = np.maximum.accumulate(equity_arr)

    # Calculate drawdown at each point
    drawdowns = (equity_arr - running_max) / running_max

    max_dd = np.min(drawdowns)

    return Decimal(str(round(max_dd * 100, 2)))  # Return as percentage


def compute_cagr(start_equity: Decimal, end_equity: Decimal, days: int) -> Decimal:
    """Calculate Compound Annual Growth Rate.

    Args:
        start_equity: Starting equity value
        end_equity: Ending equity value
        days: Number of days in the period

    Returns:
        CAGR as percentage

    """
    if days <= 0 or start_equity <= 0:
        return Decimal("0.0")

    years = days / 365.25
    cagr = (float(end_equity) / float(start_equity)) ** (1 / years) - 1

    return Decimal(str(round(cagr * 100, 2)))


def compute_calmar_ratio(cagr: Decimal, max_drawdown: Decimal) -> Decimal:
    """Calculate Calmar Ratio (CAGR / Max Drawdown).

    Args:
        cagr: CAGR as percentage
        max_drawdown: Maximum drawdown as percentage (negative)

    Returns:
        Calmar Ratio

    """
    if max_drawdown >= 0:
        return Decimal("0.0")

    # Calmar = CAGR / abs(MaxDrawdown)
    calmar = float(cagr) / abs(float(max_drawdown))

    return Decimal(str(round(calmar, 2)))


def compute_metrics_from_snapshot(snapshot_data: dict[str, Any]) -> dict[str, Decimal]:
    """Compute all performance metrics from snapshot data.

    Args:
        snapshot_data: Account snapshot containing equity history

    Returns:
        Dictionary of computed metrics

    """
    logger.info("Computing performance metrics from snapshot")

    # Extract equity curve from snapshot
    # This assumes the snapshot contains historical equity data
    # For now, we'll use placeholder logic since snapshot structure needs to be defined
    alpaca_account = snapshot_data.get("alpaca_account", {})

    # Get current equity
    current_equity = Decimal(str(alpaca_account.get("equity", "0")))
    portfolio_value = Decimal(str(alpaca_account.get("portfolio_value", "0")))

    # For MVP, compute simple metrics
    # In production, this would pull from a historical equity curve
    equity_curve = [current_equity]  # Placeholder
    returns: list[Decimal] = []  # Placeholder

    # Compute metrics
    sharpe = compute_sharpe_ratio(returns) if returns else Decimal("0.0")
    max_dd = compute_max_drawdown(equity_curve) if len(equity_curve) > 1 else Decimal("0.0")

    # For CAGR, we need period information
    # Placeholder: assume 30 days for MVP
    cagr = Decimal("0.0")  # Would need historical data

    calmar = compute_calmar_ratio(cagr, max_dd)

    metrics = {
        "sharpe_ratio": sharpe,
        "calmar_ratio": calmar,
        "max_drawdown": max_dd,
        "cagr": cagr,
        "current_equity": current_equity,
        "portfolio_value": portfolio_value,
    }

    logger.info("Metrics computed", metrics=metrics)

    return metrics
