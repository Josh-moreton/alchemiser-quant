"""Business Unit: dashboard | Status: current.

Risk metrics calculations for strategy performance analytics.

Computes annualised P&L Sharpe, max drawdown, volatility, and profit
factor from daily realised-P&L time series snapshots.
"""

from __future__ import annotations

import math
from typing import Any


def calculate_risk_metrics(
    time_series: list[dict[str, Any]],
) -> dict[str, float | None]:
    """Calculate risk metrics from strategy performance time series.

    Computes annualised Sharpe from daily realised-P&L changes (dollar terms).
    This is a P&L Sharpe -- appropriate for per-strategy analysis where each
    strategy operates within a consistent capital allocation.  The portfolio-
    level Sharpe in portfolio_overview uses percentage returns instead.

    Args:
        time_series: List of snapshot dicts, each with ``realized_pnl`` key.

    Returns:
        Dict with pnl_sharpe, max_drawdown, max_drawdown_pct, volatility,
        profit_factor (``None`` when there are no losses).
    """
    if len(time_series) < 3:
        return {
            "pnl_sharpe": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "volatility": 0.0,
            "profit_factor": None,
        }

    pnl_values = [s["realized_pnl"] for s in time_series]

    # Daily changes in realized P&L (returns proxy)
    daily_changes = [pnl_values[i] - pnl_values[i - 1] for i in range(1, len(pnl_values))]

    if not daily_changes:
        return {
            "pnl_sharpe": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "volatility": 0.0,
            "profit_factor": None,
        }

    # -- P&L Sharpe (annualized, risk-free = 0, dollar-term daily P&L changes)
    avg_change = sum(daily_changes) / len(daily_changes)
    variance = sum((c - avg_change) ** 2 for c in daily_changes) / max(len(daily_changes) - 1, 1)
    std_change = math.sqrt(variance)
    pnl_sharpe = (avg_change / std_change) * math.sqrt(252) if std_change > 0 else 0.0

    # -- Max drawdown (peak-to-trough in cumulative P&L)
    running_max = pnl_values[0]
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    for pnl in pnl_values:
        if pnl > running_max:
            running_max = pnl
        drawdown = running_max - pnl
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            if not math.isclose(running_max, 0.0, abs_tol=1e-9):
                max_drawdown_pct = (drawdown / abs(running_max)) * 100

    # -- Volatility (annualized std of daily P&L changes)
    volatility = std_change * math.sqrt(252)

    # -- Profit factor (sum of gains / sum of losses)
    gross_wins = sum(c for c in daily_changes if c > 0)
    gross_losses = abs(sum(c for c in daily_changes if c < 0))
    profit_factor: float | None = (
        gross_wins / gross_losses
        if not math.isclose(gross_losses, 0.0, abs_tol=1e-9)
        else None
    )

    return {
        "pnl_sharpe": pnl_sharpe,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown_pct,
        "volatility": volatility,
        "profit_factor": profit_factor,
    }
