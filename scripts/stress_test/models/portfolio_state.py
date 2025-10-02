"""Business Unit: utilities | Status: current.

Portfolio state tracking models for stateful stress testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class PortfolioState:
    """Tracks portfolio composition at a point in time."""

    scenario_id: str
    timestamp: datetime
    positions: dict[str, Decimal]  # symbol -> quantity
    market_values: dict[str, Decimal]  # symbol -> market_value
    cash_balance: Decimal
    total_value: Decimal
    allocation_percentages: dict[str, float]  # symbol -> percentage

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scenario_id": self.scenario_id,
            "timestamp": self.timestamp.isoformat(),
            "positions": {k: str(v) for k, v in self.positions.items()},
            "market_values": {k: str(v) for k, v in self.market_values.items()},
            "cash_balance": str(self.cash_balance),
            "total_value": str(self.total_value),
            "allocation_percentages": self.allocation_percentages,
        }


@dataclass
class PortfolioTransition:
    """Tracks changes between portfolio states."""

    from_scenario: str
    to_scenario: str
    trades_executed: int
    symbols_added: list[str] = field(default_factory=list)
    symbols_removed: list[str] = field(default_factory=list)
    symbols_adjusted: list[str] = field(default_factory=list)
    rebalance_percentage: float = 0.0  # % of portfolio rebalanced
    turnover_cost: Decimal = Decimal("0")
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_scenario": self.from_scenario,
            "to_scenario": self.to_scenario,
            "trades_executed": self.trades_executed,
            "symbols_added": self.symbols_added,
            "symbols_removed": self.symbols_removed,
            "symbols_adjusted": self.symbols_adjusted,
            "rebalance_percentage": self.rebalance_percentage,
            "turnover_cost": str(self.turnover_cost),
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }
