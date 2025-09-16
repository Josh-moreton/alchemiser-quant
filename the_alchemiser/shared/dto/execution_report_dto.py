#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Execution report data transfer objects for inter-module communication.

Provides typed DTOs for execution reports with correlation tracking and
serialization helpers for communication between execution and other modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.dto_conversion import (
    convert_datetime_fields_from_dict,
    convert_decimal_fields_from_dict,
    convert_nested_order_data,
)
from ..utils.timezone_utils import ensure_timezone_aware


class ExecutedOrderDTO(BaseModel):
    """DTO for individual executed order."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    action: str = Field(..., description="Trading action (BUY, SELL)")
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    filled_quantity: Decimal = Field(..., ge=0, description="Filled quantity")
    price: Decimal = Field(..., gt=0, description="Execution price")
    total_value: Decimal = Field(..., gt=0, description="Total execution value")
    status: str = Field(..., description="Order status (FILLED, PARTIAL, REJECTED, etc.)")
    execution_timestamp: datetime = Field(..., description="Order execution timestamp")

    # Optional fields
    commission: Decimal | None = Field(default=None, ge=0, description="Commission paid")
    fees: Decimal | None = Field(default=None, ge=0, description="Additional fees")
    error_message: str | None = Field(default=None, description="Error message if failed")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action is supported."""
        valid_actions = {"BUY", "SELL"}
        action_upper = v.strip().upper()
        if action_upper not in valid_actions:
            raise ValueError(f"Action must be one of {valid_actions}, got {action_upper}")
        return action_upper

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate order status."""
        valid_statuses = {
            "FILLED",
            "PARTIAL",
            "REJECTED",
            "CANCELLED",
            "CANCELED",
            "PENDING",
            "PENDING_NEW",
            "FAILED",
            "ACCEPTED",
        }
        status_upper = v.strip().upper()
        if status_upper not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}, got {status_upper}")
        return status_upper

    @field_validator("execution_timestamp")
    @classmethod
    def ensure_timezone_aware_execution_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("execution_timestamp cannot be None")
        return result


class ExecutionReportDTO(BaseModel):
    """DTO for execution report data transfer.

    Used for communication between execution module and other modules.
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
    timestamp: datetime = Field(..., description="Report generation timestamp")

    # Report identification
    execution_id: str = Field(..., min_length=1, description="Unique execution identifier")
    session_id: str | None = Field(default=None, description="Trading session identifier")

    # Execution summary
    total_orders: int = Field(..., ge=0, description="Total number of orders")
    successful_orders: int = Field(..., ge=0, description="Number of successful orders")
    failed_orders: int = Field(..., ge=0, description="Number of failed orders")

    # Financial summary
    total_value_traded: Decimal = Field(..., ge=0, description="Total value traded")
    total_commissions: Decimal = Field(..., ge=0, description="Total commissions paid")
    total_fees: Decimal = Field(..., ge=0, description="Total fees paid")
    net_cash_flow: Decimal = Field(..., description="Net cash flow (negative for net purchases)")

    # Timing
    execution_start_time: datetime = Field(..., description="Execution start timestamp")
    execution_end_time: datetime = Field(..., description="Execution end timestamp")
    total_duration_seconds: int = Field(..., ge=0, description="Total execution duration")

    # Order details
    orders: list[ExecutedOrderDTO] = Field(
        default_factory=list, description="List of executed orders"
    )

    # Performance metrics
    success_rate: Decimal = Field(..., ge=0, le=1, description="Success rate (0-1)")
    average_execution_time_seconds: Decimal | None = Field(
        default=None, ge=0, description="Average order execution time"
    )

    # Optional metadata
    broker_used: str | None = Field(default=None, description="Broker used for execution")
    execution_strategy: str | None = Field(default=None, description="Execution strategy used")
    market_conditions: str | None = Field(
        default=None, description="Market conditions during execution"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata"
    )

    @field_validator("timestamp", "execution_start_time", "execution_end_time")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("timestamp cannot be None")
        return result

    @field_validator("success_rate")
    @classmethod
    def validate_success_rate(cls, v: Decimal) -> Decimal:
        """Validate success rate is between 0 and 1."""
        if not (0 <= v <= 1):
            raise ValueError("Success rate must be between 0 and 1")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation of the DTO with properly serialized values.

        """
        data = self.model_dump()
        
        # Convert datetime fields to ISO strings
        self._convert_datetime_fields(data)
        
        # Convert Decimal fields to string for JSON serialization
        self._convert_decimal_fields(data)
        
        # Convert nested orders
        self._convert_nested_orders(data)
        
        return data

    def _convert_datetime_fields(self, data: dict[str, Any]) -> None:
        """Convert datetime fields to ISO string format."""
        datetime_fields = ["timestamp", "execution_start_time", "execution_end_time"]
        for field_name in datetime_fields:
            if data.get(field_name):
                data[field_name] = data[field_name].isoformat()

    def _convert_decimal_fields(self, data: dict[str, Any]) -> None:
        """Convert Decimal fields to string for JSON serialization."""
        decimal_fields = [
            "total_value_traded",
            "total_commissions", 
            "total_fees",
            "net_cash_flow",
            "success_rate",
            "average_execution_time_seconds",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

    def _convert_nested_orders(self, data: dict[str, Any]) -> None:
        """Convert nested order objects to dictionaries with proper serialization."""
        if "orders" not in data:
            return
        
        orders_data = []
        for order in data["orders"]:
            order_dict = dict(order)
            self._convert_order_datetime(order_dict)
            self._convert_order_decimals(order_dict)
            orders_data.append(order_dict)
        data["orders"] = orders_data

    def _convert_order_datetime(self, order_dict: dict[str, Any]) -> None:
        """Convert datetime fields in order dictionary."""
        if order_dict.get("execution_timestamp"):
            order_dict["execution_timestamp"] = order_dict["execution_timestamp"].isoformat()

    def _convert_order_decimals(self, order_dict: dict[str, Any]) -> None:
        """Convert Decimal fields in order dictionary."""
        order_decimal_fields = [
            "quantity",
            "filled_quantity", 
            "price",
            "total_value",
            "commission",
            "fees",
        ]
        for field_name in order_decimal_fields:
            if order_dict.get(field_name) is not None:
                order_dict[field_name] = str(order_dict[field_name])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionReportDTO:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing DTO data

        Returns:
            ExecutionReportDTO instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamps back to datetime
        datetime_fields = ["timestamp", "execution_start_time", "execution_end_time"]
        convert_datetime_fields_from_dict(data, datetime_fields)

        # Convert string decimal fields back to Decimal
        decimal_fields = [
            "total_value_traded",
            "total_commissions",
            "total_fees",
            "net_cash_flow",
            "success_rate",
            "average_execution_time_seconds",
        ]
        convert_decimal_fields_from_dict(data, decimal_fields)

        # Convert orders if present
        data["orders"] = cls._convert_orders_from_dict(data.get("orders", []))

        return cls(**data)

    @classmethod
    def _convert_orders_from_dict(cls, orders: list[Any]) -> list[ExecutedOrderDTO]:
        """Convert orders list from dictionary format.

        Args:
            orders: List of order data (dicts or DTOs)

        Returns:
            List of ExecutedOrderDTO instances

        """
        if not isinstance(orders, list):
            return []

        orders_data = []
        for order_data in orders:
            if isinstance(order_data, dict):
                converted_order = convert_nested_order_data(dict(order_data))
                orders_data.append(ExecutedOrderDTO(**converted_order))
            else:
                orders_data.append(order_data)  # Assume already a DTO

        return orders_data
