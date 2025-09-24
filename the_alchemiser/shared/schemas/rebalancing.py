#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Rebalance plan schemas for inter-module communication.

Provides typed schemas for portfolio rebalancing plans with correlation tracking
and serialization helpers for communication between portfolio and execution modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.dto_conversion import (
    convert_datetime_fields_from_dict,
    convert_decimal_fields_from_dict,
    convert_nested_rebalance_item_data,
)
from ..utils.timezone_utils import ensure_timezone_aware


class RebalancePlanItem(BaseModel):
    """Schema for individual rebalance plan item."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    current_weight: Decimal = Field(..., ge=0, le=1, description="Current portfolio weight (0-1)")
    target_weight: Decimal = Field(..., ge=0, le=1, description="Target portfolio weight (0-1)")
    weight_diff: Decimal = Field(..., description="Weight difference (target - current)")
    target_value: Decimal = Field(..., ge=0, description="Target dollar value")
    current_value: Decimal = Field(..., ge=0, description="Current dollar value")
    trade_amount: Decimal = Field(
        ..., description="Dollar amount to trade (positive=buy, negative=sell)"
    )
    action: str = Field(..., description="Trading action (BUY, SELL, HOLD)")
    priority: int = Field(..., ge=1, le=5, description="Execution priority (1=highest)")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("action")
    @classmethod
    def normalize_action(cls, v: str) -> str:
        """Normalize action to uppercase."""
        return v.strip().upper()


class RebalancePlan(BaseModel):
    """Schema for complete rebalance plan data transfer.

    Used for communication between portfolio and execution modules.
    Includes correlation tracking and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="Plan creation timestamp")

    # Plan metadata
    plan_id: str = Field(..., min_length=1, description="Unique plan identifier")
    portfolio_id: str = Field(..., min_length=1, description="Portfolio identifier")
    strategy_name: str | None = Field(default=None, description="Strategy that generated the plan")

    # Plan data
    items: list[RebalancePlanItem] = Field(
        ..., min_size=1, description="List of rebalance plan items"
    )
    total_trades: int = Field(..., ge=0, description="Total number of trades required")
    estimated_cost: Decimal = Field(..., ge=0, description="Estimated execution cost")

    # Plan status
    is_valid: bool = Field(..., description="Whether the plan is valid for execution")
    validation_errors: list[str] = Field(
        default_factory=list, description="Plan validation error messages"
    )

    # Execution metadata
    priority_levels: int = Field(..., ge=1, le=5, description="Number of priority levels")
    requires_manual_review: bool = Field(
        default=False, description="Whether plan requires manual review"
    )

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RebalancePlan:
        """Create RebalancePlan from dictionary data with type conversion.

        Args:
            data: Dictionary containing rebalance plan data

        Returns:
            RebalancePlan instance with properly typed fields

        """
        # Create a copy to avoid mutating the original
        processed_data = data.copy()

        # Convert datetime fields from strings if needed
        convert_datetime_fields_from_dict(processed_data, ["timestamp"])

        # Convert decimal fields from strings if needed
        convert_decimal_fields_from_dict(processed_data, ["estimated_cost"])

        # Convert items data to RebalancePlanItem objects
        cls._convert_items(processed_data)

        return cls(**processed_data)

    @classmethod
    def _convert_items(cls, data: dict[str, Any]) -> None:
        """Convert items data to RebalancePlanItem objects."""
        if "items" in data and isinstance(data["items"], list):
            items_data = []
            for item_data in data["items"]:
                if isinstance(item_data, dict):
                    # Convert nested item data using utility function
                    convert_nested_rebalance_item_data(item_data)
                    items_data.append(RebalancePlanItem(**item_data))
                else:
                    items_data.append(item_data)  # Assume already a schema
            data["items"] = items_data

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary for serialization.

        Returns:
            Dictionary representation with properly serialized values.

        """
        data = self.model_dump()

        # Convert datetime fields to ISO strings
        if data.get("timestamp"):
            data["timestamp"] = data["timestamp"].isoformat()

        # Convert decimal fields to strings
        if data.get("estimated_cost") is not None:
            data["estimated_cost"] = str(data["estimated_cost"])

        # Convert items data to dictionaries
        if data.get("items"):
            for item_data in data["items"]:
                if isinstance(item_data, dict):
                    # Convert decimals to strings
                    decimal_fields = [
                        "current_weight",
                        "target_weight",
                        "weight_diff",
                        "target_value",
                        "current_value",
                        "trade_amount",
                    ]
                    for field_name in decimal_fields:
                        if item_data.get(field_name) is not None:
                            item_data[field_name] = str(item_data[field_name])

        return data