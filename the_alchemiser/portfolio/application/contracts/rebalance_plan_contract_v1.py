"""Business Unit: portfolio assessment & management; Status: current.

Portfolio Rebalance Plan Contract V1 for cross-context communication.

This module provides the versioned application contract for portfolio rebalance
plans, enabling clean communication between Portfolio and Execution contexts
without domain leakage.

Example Usage:
    # Creating a rebalance plan contract
    plan = RebalancePlanContractV1(
        correlation_id=uuid4(),
        plan_id=uuid4(),
        planned_orders=[
            PlannedOrderV1(
                order_id=uuid4(),
                symbol=Symbol("AAPL"),
                side=ActionType.BUY,
                quantity=Decimal("10"),
                limit_price=Decimal("150.00")
            )
        ]
    )

    # Accessing contract data
    print(f"Plan {plan.plan_id} has {len(plan.planned_orders)} orders")
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.domain.shared_kernel import ActionType
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol

from ._envelope import EnvelopeV1


class PlannedOrderV1(BaseModel):
    """Planned order within a rebalance plan contract.

    Represents a single order that should be executed as part of a rebalancing
    operation. Contains all information needed by Execution context.

    Attributes:
        order_id: Unique identifier for this planned order
        symbol: Stock/ETF symbol from shared kernel
        side: Order side (BUY/SELL) - HOLD not applicable for orders
        quantity: Number of shares to trade (always positive)
        limit_price: Optional limit price for the order

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    order_id: UUID = Field(default_factory=uuid4, description="Unique order identifier")
    symbol: Symbol = Field(..., description="Stock/ETF symbol")
    side: ActionType = Field(..., description="Order side: BUY or SELL")
    quantity: Decimal = Field(..., gt=0, description="Quantity to trade (positive)")
    limit_price: Decimal | None = Field(None, gt=0, description="Optional limit price")

    @field_validator("side")
    @classmethod
    def validate_side_not_hold(cls, v: ActionType) -> ActionType:
        """Validate that order side is not HOLD (orders must be actionable)."""
        if v == ActionType.HOLD:
            raise ValueError("Order side cannot be HOLD - orders must be BUY or SELL")
        return v


class RebalancePlanContractV1(EnvelopeV1):
    """Version 1 contract for rebalance plans crossing context boundaries.

    This contract enables Portfolio -> Execution communication without exposing
    internal domain objects. Contains planned orders ready for execution.

    Attributes:
        plan_id: Unique identifier for this rebalancing plan
        generated_at: When the rebalancing plan was generated
        planned_orders: List of orders to execute for rebalancing

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    plan_id: UUID = Field(default_factory=uuid4, description="Unique plan identifier")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When the plan was generated"
    )
    planned_orders: list[PlannedOrderV1] = Field(
        default_factory=list, description="Orders to execute for rebalancing"
    )


def rebalance_plan_from_domain(
    domain_plans: list[
        object
    ],  # List of RebalancePlan from domain - using object to avoid domain import
    correlation_id: UUID,
    causation_id: UUID | None = None,
) -> RebalancePlanContractV1:
    """Map domain RebalancePlan objects to a RebalancePlanContractV1.

    Args:
        domain_plans: List of domain RebalancePlan objects
        correlation_id: Root correlation ID for message tracing
        causation_id: Optional ID of the message that caused this plan

    Returns:
        RebalancePlanContractV1 ready for cross-context communication

    Note:
        This function intentionally uses object type to avoid importing domain
        objects into the application layer. The actual domain objects should have
        the expected attributes: symbol, trade_direction, trade_amount_abs, etc.

    """
    planned_orders = []

    for plan in domain_plans:
        # Skip plans that don't need rebalancing
        if not plan.needs_rebalance:  # type: ignore[attr-defined]
            continue

        # Map trade direction to ActionType
        direction = plan.trade_direction  # type: ignore[attr-defined]
        side = ActionType.BUY if direction == "BUY" else ActionType.SELL

        # Create Symbol from string
        symbol = Symbol(plan.symbol)  # type: ignore[attr-defined]

        # Get trade amount (always positive for quantity)
        quantity = plan.trade_amount_abs  # type: ignore[attr-defined]

        planned_order = PlannedOrderV1(
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=None,  # Market orders by default - execution context will determine pricing
        )
        planned_orders.append(planned_order)

    return RebalancePlanContractV1(
        correlation_id=correlation_id,
        causation_id=causation_id,
        planned_orders=planned_orders,
    )


# Note: to_domain() method intentionally omitted to avoid cross-context domain coupling.
# Execution context should translate contract data to its own domain representations
# rather than reconstructing Portfolio domain objects.
