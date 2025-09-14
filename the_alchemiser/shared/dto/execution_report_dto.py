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
        return ensure_timezone_aware(v)


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
        return ensure_timezone_aware(v)

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
        datetime_fields = ["timestamp", "execution_start_time", "execution_end_time"]
        for field_name in datetime_fields:
            if data.get(field_name):
                data[field_name] = data[field_name].isoformat()

        # Convert Decimal fields to string for JSON serialization
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

        # Convert nested orders
        if "orders" in data:
            orders_data = []
            for order in data["orders"]:
                order_dict = dict(order)
                # Convert datetime in order
                if order_dict.get("execution_timestamp"):
                    order_dict["execution_timestamp"] = order_dict[
                        "execution_timestamp"
                    ].isoformat()
                # Convert Decimal fields in order
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
                orders_data.append(order_dict)
            data["orders"] = orders_data

        return data

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
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    timestamp_str = data[field_name]
                    if timestamp_str.endswith("Z"):
                        timestamp_str = timestamp_str[:-1] + "+00:00"
                    data[field_name] = datetime.fromisoformat(timestamp_str)
                except ValueError as e:
                    raise ValueError(f"Invalid {field_name} format: {data[field_name]}") from e

        # Convert string decimal fields back to Decimal
        decimal_fields = [
            "total_value_traded",
            "total_commissions",
            "total_fees",
            "net_cash_flow",
            "success_rate",
            "average_execution_time_seconds",
        ]
        for field_name in decimal_fields:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                try:
                    data[field_name] = Decimal(data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

        # Convert orders if present
        if "orders" in data and isinstance(data["orders"], list):
            orders_data = []
            for order_data in data["orders"]:
                if isinstance(order_data, dict):
                    # Convert execution timestamp in order
                    if "execution_timestamp" in order_data and isinstance(
                        order_data["execution_timestamp"], str
                    ):
                        try:
                            timestamp_str = order_data["execution_timestamp"]
                            if timestamp_str.endswith("Z"):
                                timestamp_str = timestamp_str[:-1] + "+00:00"
                            order_data["execution_timestamp"] = datetime.fromisoformat(
                                timestamp_str
                            )
                        except ValueError as e:
                            raise ValueError(
                                f"Invalid execution_timestamp format in order: {order_data['execution_timestamp']}"
                            ) from e

                    # Convert Decimal fields in order
                    order_decimal_fields = [
                        "quantity",
                        "filled_quantity",
                        "price",
                        "total_value",
                        "commission",
                        "fees",
                    ]
                    for field_name in order_decimal_fields:
                        if (
                            field_name in order_data
                            and order_data[field_name] is not None
                            and isinstance(order_data[field_name], str)
                        ):
                            try:
                                order_data[field_name] = Decimal(order_data[field_name])
                            except (ValueError, TypeError) as e:
                                raise ValueError(
                                    f"Invalid {field_name} value in order: {order_data[field_name]}"
                                ) from e
                    orders_data.append(ExecutedOrderDTO(**order_data))
                else:
                    orders_data.append(order_data)  # Assume already a DTO
            data["orders"] = orders_data

        return cls(**data)
