"""Business Unit: shared | Status: current.

Execution-related data transfer objects for order placement and tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


@dataclass
class ExecutionResult:
    """Result of an order execution attempt.

    Contains all information about the order placement,
    whether successful or failed.
    """

    symbol: str
    side: str
    quantity: Decimal
    status: str
    success: bool
    execution_strategy: str
    order_id: str | None = None
    price: Decimal | None = None
    error: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
