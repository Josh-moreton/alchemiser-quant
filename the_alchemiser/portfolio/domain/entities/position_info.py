"""Business Unit: portfolio assessment & management; Status: current.

Position value objects for portfolio domain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionInfo:
    """Detailed position information with analysis."""

    symbol: str
    quantity: float
    market_value: float | None
    unrealized_pnl: float | None
    unrealized_pnl_percent: float | None
    cost_basis: float | None
    current_price: float | None
    weight_percent: float | None  # Position weight in portfolio


@dataclass(frozen=True)
class PortfolioSummary:
    """Portfolio-level position summary."""

    total_market_value: float
    total_positions: int
    largest_position_value: float
    largest_position_percent: float
    cash_balance: float | None
    total_equity: float | None


class PositionValidationError(Exception):
    """Exception raised when position validation fails."""