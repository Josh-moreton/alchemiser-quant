"""Business Unit: order execution/placement; Status: current.

Execution Report Contract V1 for cross-context communication.

This module provides the versioned application contract for execution reports,
enabling clean communication from Execution back to Portfolio context without
domain leakage.

Example Usage:
    # Creating an execution report contract
    report = ExecutionReportContractV1(
        correlation_id=uuid4(),
        report_id=uuid4(),
        fills=[
            FillV1(
                fill_id=uuid4(),
                order_id=uuid4(),
                symbol=Symbol("AAPL"),
                side=ActionType.BUY,
                quantity=Decimal("10"),
                price=Decimal("150.25"),
                filled_at=datetime.now(UTC)
            )
        ],
        summary="Successfully executed 1 order",
        account_delta=Decimal("1502.50")
    )

    # Accessing contract data
    print(f"Report {report.report_id}: {len(report.fills)} fills")
    print(f"Account delta: ${report.account_delta}")
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.domain.shared_kernel import ActionType
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol

from ._envelope import EnvelopeV1


class FillV1(BaseModel):
    """Fill information within an execution report contract.

    Represents a single order fill that occurred during execution.
    Contains all information needed by Portfolio context for position updates.

    Attributes:
        fill_id: Unique identifier for this fill
        order_id: ID of the order that was filled
        symbol: Stock/ETF symbol from shared kernel
        side: Fill side (BUY/SELL)
        quantity: Number of shares filled (always positive)
        price: Price per share for this fill
        filled_at: UTC timestamp when the fill occurred

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    fill_id: UUID = Field(default_factory=uuid4, description="Unique fill identifier")
    order_id: UUID = Field(..., description="Order ID that was filled")
    symbol: Symbol = Field(..., description="Stock/ETF symbol")
    side: ActionType = Field(..., description="Fill side: BUY or SELL")
    quantity: Decimal = Field(..., gt=0, description="Quantity filled (positive)")
    price: Decimal = Field(..., gt=0, description="Price per share")
    filled_at: datetime = Field(..., description="UTC timestamp when fill occurred")

    @field_validator("side")
    @classmethod
    def validate_side_not_hold(cls, v: ActionType) -> ActionType:
        """Validate that fill side is not HOLD (fills must be actionable)."""
        if v == ActionType.HOLD:
            raise ValueError("Fill side cannot be HOLD - fills must be BUY or SELL")
        return v


class ExecutionReportContractV1(EnvelopeV1):
    """Version 1 contract for execution reports crossing context boundaries.

    This contract enables Execution -> Portfolio communication without exposing
    internal domain objects. Contains fill information and execution summary.

    Attributes:
        report_id: Unique identifier for this execution report
        generated_at: When the execution report was generated
        fills: List of fills that occurred during execution
        summary: Optional human-readable summary of execution
        account_delta: Optional net value change to account from execution

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    report_id: UUID = Field(default_factory=uuid4, description="Unique report identifier")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When the report was generated"
    )
    fills: list[FillV1] = Field(
        default_factory=list, description="Fills that occurred during execution"
    )
    summary: str | None = Field(None, description="Optional execution summary")
    account_delta: Decimal | None = Field(None, description="Net value change to account")


def execution_report_from_domain(
    fills_data: list[dict[str, Any]],  # Fill data from domain - using dict to avoid domain import
    correlation_id: UUID,
    causation_id: UUID | None = None,
    summary: str | None = None,
    account_delta: Decimal | None = None,
) -> ExecutionReportContractV1:
    """Map domain fill data to an ExecutionReportContractV1.

    Args:
        fills_data: List of fill dictionaries with keys: fill_id, order_id, symbol,
                   side, quantity, price, filled_at
        correlation_id: Root correlation ID for message tracing
        causation_id: Optional ID of the message that caused this report
        summary: Optional execution summary
        account_delta: Optional net account value change

    Returns:
        ExecutionReportContractV1 ready for cross-context communication

    Note:
        This function uses dict for fill data to avoid importing domain
        objects into the application layer.

    """
    fills = []

    for fill_data in fills_data:
        # Map side string to ActionType
        side_str = str(fill_data["side"])
        side = ActionType.BUY if side_str == "BUY" else ActionType.SELL

        # Create Symbol from string
        symbol = Symbol(str(fill_data["symbol"]))

        fill = FillV1(
            fill_id=UUID(str(fill_data["fill_id"])),
            order_id=UUID(str(fill_data["order_id"])),
            symbol=symbol,
            side=side,
            quantity=Decimal(str(fill_data["quantity"])),
            price=Decimal(str(fill_data["price"])),
            filled_at=cast(datetime, fill_data["filled_at"]),
        )
        fills.append(fill)

    return ExecutionReportContractV1(
        correlation_id=correlation_id,
        causation_id=causation_id,
        fills=fills,
        summary=summary,
        account_delta=account_delta,
    )


# Note: to_domain() method intentionally omitted to avoid cross-context domain coupling.
# Portfolio context should translate contract data to its own domain representations
# rather than reconstructing Execution domain objects.
