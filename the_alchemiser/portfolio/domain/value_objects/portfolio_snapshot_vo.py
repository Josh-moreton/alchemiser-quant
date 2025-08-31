"""Business Unit: portfolio assessment & management | Status: current

Portfolio snapshot value object for capturing portfolio state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from the_alchemiser.shared_kernel.value_objects.money import Money
from the_alchemiser.shared_kernel.value_objects.percentage import Percentage


@dataclass(frozen=True)
class PortfolioSnapshotVO:
    """Immutable portfolio state snapshot."""

    portfolio_id: UUID
    total_value: Money
    cash_balance: Money
    invested_value: Money
    unrealized_pnl: Money
    realized_pnl: Money
    day_change: Money
    day_change_percent: Percentage
    total_return: Money
    total_return_percent: Percentage
    position_count: int
    largest_position_weight: Percentage
    diversification_score: Decimal
    risk_score: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate portfolio snapshot data.

        TODO: Add validation for derived fields (e.g., total_value = cash + invested)
        FIXME: Consider adding range validation for percentages and scores
        """
        if self.total_value.amount < Decimal("0"):
            raise ValueError("Total value cannot be negative")
        if self.cash_balance.amount < Decimal("0"):
            raise ValueError("Cash balance cannot be negative")
        if self.position_count < 0:
            raise ValueError("Position count cannot be negative")
