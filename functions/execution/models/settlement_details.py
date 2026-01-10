"""Business Unit: execution | Status: current.

Settlement details schema for tracking order completion and buying power release.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SettlementDetails(BaseModel):
    """Settlement details for a completed order.

    This model captures the settlement information for an order that has reached
    a final state (FILLED, CANCELED, REJECTED, or EXPIRED).
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="Schema version")
    symbol: str = Field(
        ...,
        max_length=50,
        description="Trading symbol (supports extended notation like EQUITIES::SYMBOL//USD)",
    )
    side: Literal["BUY", "SELL"] = Field(..., description="Order side")
    settled_quantity: Decimal = Field(..., ge=Decimal("0"), description="Quantity settled")
    settlement_price: Decimal = Field(..., ge=Decimal("0"), description="Average fill price")
    settled_value: Decimal = Field(
        ..., ge=Decimal("0"), description="Total settlement value (quantity * price)"
    )
    status: str = Field(..., max_length=20, description="Final order status")
    order_id: str = Field(..., max_length=100, description="Order ID")
