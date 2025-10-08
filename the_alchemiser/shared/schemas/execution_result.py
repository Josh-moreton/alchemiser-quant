"""Business Unit: shared | Status: current.

Execution-related data transfer objects for order placement and tracking.

Note: This is a lightweight DTO for simple single-order execution results.
For multi-order execution with complete traceability, use
execution_v2.models.execution_result.ExecutionResult instead.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExecutionResult(BaseModel):
    """Result of an order execution attempt.

    Contains all information about a single order placement,
    whether successful or failed.

    This is a lightweight DTO for simple execution tracking. For multi-order
    execution with complete traceability and metrics, use
    execution_v2.models.execution_result.ExecutionResult instead.

    Example:
        >>> from datetime import datetime, UTC
        >>> from decimal import Decimal
        >>> result = ExecutionResult(
        ...     schema_version="1.0",
        ...     symbol="AAPL",
        ...     side="buy",
        ...     quantity=Decimal("10"),
        ...     status="filled",
        ...     success=True,
        ...     execution_strategy="market",
        ...     price=Decimal("150.50"),
        ...     timestamp=datetime.now(UTC)
        ... )
        >>> assert result.success
        >>> assert result.quantity == Decimal("10")

    Migrated from dataclass to Pydantic v2 for architecture compliance.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(
        default="1.0", description="Schema version for evolution tracking"
    )
    symbol: str = Field(min_length=1, description="Trading symbol")
    side: Literal["buy", "sell"] = Field(description="Order side (buy/sell)")
    quantity: Decimal = Field(gt=0, description="Order quantity (must be positive)")
    status: Literal["pending", "filled", "cancelled", "rejected", "failed"] = Field(
        description="Execution status"
    )
    success: bool = Field(description="Whether execution was successful")
    execution_strategy: Literal["market", "limit", "adaptive"] = Field(
        description="Execution strategy used"
    )
    order_id: str | None = Field(default=None, description="Order ID if available")
    price: Decimal | None = Field(
        default=None, gt=0, description="Execution price (must be positive if provided)"
    )
    error_code: str | None = Field(
        default=None, description="Machine-readable error code if failed"
    )
    error_message: str | None = Field(
        default=None, description="Human-readable error message if failed"
    )
    timestamp: datetime = Field(
        ..., description="Execution timestamp (UTC timezone-aware, must be explicit)"
    )
    correlation_id: str | None = Field(
        default=None, description="Correlation ID for distributed tracing"
    )
    causation_id: str | None = Field(
        default=None, description="Causation ID for event sourcing"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata only"
    )  # Arbitrary JSON-serializable metadata for extensibility; type safety not required, so Any is justified.
