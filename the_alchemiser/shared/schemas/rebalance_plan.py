#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Rebalance plan data transfer objects for inter-module communication.

Provides typed DTOs for portfolio rebalancing plans with correlation tracking
and serialization helpers for communication between portfolio and execution modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.data_conversion import (
    convert_datetime_fields_from_dict,
    convert_decimal_fields_from_dict,
    convert_nested_rebalance_item_data,
)
from ..utils.timezone_utils import ensure_timezone_aware
from .types import MoneyDecimal, WeightDecimal, UtcDatetime


class RebalancePlanItem(BaseModel):
    """DTO for individual rebalance plan item."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    current_weight: WeightDecimal = Field(
        ..., ge=0, le=1, description="Current portfolio weight (0-1)"
    )
    target_weight: WeightDecimal = Field(
        ..., ge=0, le=1, description="Target portfolio weight (0-1)"
    )
    weight_diff: WeightDecimal = Field(..., description="Weight difference (target - current)")
    target_value: MoneyDecimal = Field(..., ge=0, description="Target dollar value")
    current_value: MoneyDecimal = Field(..., ge=0, description="Current dollar value")
    trade_amount: MoneyDecimal = Field(
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
    def validate_action(cls, v: str) -> str:
        """Validate action is supported."""
        valid_actions = {"BUY", "SELL", "HOLD"}
        action_upper = v.strip().upper()
        if action_upper not in valid_actions:
            raise ValueError(f"Action must be one of {valid_actions}, got {action_upper}")
        return action_upper


class RebalancePlan(BaseModel):
    """DTO for complete rebalance plan data transfer.

    Used for communication between portfolio and execution modules.
    Includes correlation tracking and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema versioning for evolution tracking
    schema_version: str = Field(default="1.0", description="DTO schema version")

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: UtcDatetime = Field(..., description="Plan generation timestamp")

    # Plan identification
    plan_id: str = Field(..., min_length=1, description="Unique plan identifier")

    # Plan content
    items: list[RebalancePlanItem] = Field(
        ..., min_length=1, description="List of rebalance plan items"
    )

    # Plan metadata
    total_portfolio_value: MoneyDecimal = Field(..., ge=0, description="Total portfolio value")
    total_trade_value: MoneyDecimal = Field(..., description="Total absolute trade value")
    max_drift_tolerance: WeightDecimal = Field(
        default=Decimal("0.05"), ge=0, le=1, description="Maximum drift tolerance (0-1)"
    )

    # Optional execution hints
    execution_urgency: str = Field(
        default="NORMAL", description="Execution urgency (LOW, NORMAL, HIGH, URGENT)"
    )
    estimated_duration_minutes: int | None = Field(
        default=None, ge=1, description="Estimated execution duration in minutes"
    )

    # Optional metadata
    metadata: dict[str, Any] | None = Field(default=None, description="Additional plan metadata")

    @field_validator("execution_urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        """Validate execution urgency."""
        valid_urgencies = {"LOW", "NORMAL", "HIGH", "URGENT"}
        urgency_upper = v.strip().upper()
        if urgency_upper not in valid_urgencies:
            raise ValueError(f"Urgency must be one of {valid_urgencies}, got {urgency_upper}")
        return urgency_upper

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation of the DTO with properly serialized values.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal fields to string for JSON serialization
        decimal_fields = [
            "total_portfolio_value",
            "total_trade_value",
            "max_drift_tolerance",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        # Convert nested items
        if "items" in data:
            items_data = []
            for item in data["items"]:
                item_dict = dict(item)
                # Convert Decimal fields in items
                item_decimal_fields = [
                    "current_weight",
                    "target_weight",
                    "weight_diff",
                    "target_value",
                    "current_value",
                    "trade_amount",
                ]
                for field_name in item_decimal_fields:
                    if item_dict.get(field_name) is not None:
                        item_dict[field_name] = str(item_dict[field_name])
                items_data.append(item_dict)
            data["items"] = items_data

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RebalancePlan:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing DTO data

        Returns:
            RebalancePlan instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamp back to datetime
        datetime_fields = ["timestamp"]
        convert_datetime_fields_from_dict(data, datetime_fields)

        # Convert string decimal fields back to Decimal
        decimal_fields = [
            "total_portfolio_value",
            "total_trade_value",
            "max_drift_tolerance",
        ]
        convert_decimal_fields_from_dict(data, decimal_fields)

        # Validate items exist and non-empty before conversion
        if "items" not in data or not data["items"]:
            raise ValueError("RebalancePlan requires at least one item")

        # Convert items
        data["items"] = cls._convert_items_from_dict(data["items"])

        return cls(**data)

    @classmethod
    def _convert_items_from_dict(cls, items: list[Any]) -> list[RebalancePlanItem]:
        """Convert items list from dictionary format.

        Args:
            items: List of item data (dicts or DTOs)

        Returns:
            List of RebalancePlanItem instances

        Raises:
            TypeError: If items is not a list or contains invalid types

        """
        if not isinstance(items, list):
            raise TypeError(f"Items must be a list, got {type(items).__name__}")

        items_data = []
        for item_data in items:
            if isinstance(item_data, dict):
                converted_item = convert_nested_rebalance_item_data(dict(item_data))
                items_data.append(RebalancePlanItem(**converted_item))
            elif isinstance(item_data, RebalancePlanItem):
                items_data.append(item_data)
            else:
                raise TypeError(
                    f"Expected dict or RebalancePlanItem, got {type(item_data).__name__}"
                )

        return items_data
