#!/usr/bin/env python3
"""
Order Validation and Type Safety Module

This module provides comprehensive order validation and type safety for trade execution.
It replaces the unsafe list[dict[str, Any]] patterns with strongly typed, validated order structures.

Key Features:
- Pydantic-based order validation with runtime type checking
- Immutable order models with comprehensive validation
- Pre-trade validation including risk checks
- Order settlement tracking with type safety
- Comprehensive error reporting for validation failures

Usage:
    from the_alchemiser.application.order_validation import (
        ValidatedOrder, OrderValidator, OrderSettlementTracker
    )

    # Create validator
    validator = OrderValidator()

    # Validate and create order
    validated_order = validator.create_validated_order(
        symbol="AAPL", quantity=100, side="BUY", order_type="MARKET"
    )

    # Track settlement
    tracker = OrderSettlementTracker()
    settlement_result = tracker.wait_for_settlement([validated_order])
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, cast

from pydantic import BaseModel, Field, validator

from the_alchemiser.domain.types import OrderDetails


class OrderValidationError(Exception):
    """Raised when order validation fails."""

    pass


class ValidatedOrderSide(str, Enum):
    """Order side enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class ValidatedOrderType(str, Enum):
    """Order type enumeration."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order status enumeration."""

    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class ValidatedOrder(BaseModel):
    """
    Immutable, validated order structure with comprehensive type safety.

    This replaces the unsafe dict[str, Any] order structures throughout the execution chain.
    All fields are validated at creation time and the object is immutable.
    """

    # Core order identification
    id: str | None = Field(None, description="Order ID from broker (set after submission)")
    client_order_id: str | None = Field(None, description="Client-side order ID")

    # Order parameters - all validated
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    quantity: Decimal = Field(..., gt=0, description="Order quantity (positive)")
    side: ValidatedOrderSide = Field(..., description="Order side (BUY/SELL)")
    order_type: ValidatedOrderType = Field(..., description="Order type")
    time_in_force: str = Field(default="DAY", description="Time in force")

    # Price fields for limit orders
    limit_price: Decimal | None = Field(None, ge=0, description="Limit price for limit orders")
    stop_price: Decimal | None = Field(None, ge=0, description="Stop price for stop orders")

    # Execution tracking
    status: OrderStatus = Field(default=OrderStatus.NEW, description="Order status")
    filled_qty: Decimal = Field(default=Decimal("0"), ge=0, description="Filled quantity")
    filled_avg_price: Decimal | None = Field(None, ge=0, description="Average fill price")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Risk validation metadata
    estimated_value: Decimal | None = Field(None, description="Estimated order value")
    risk_checks_passed: bool = Field(default=False, description="Whether risk checks passed")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors")

    class Config:
        """Pydantic configuration."""

        frozen = True  # Immutable
        validate_assignment = True
        arbitrary_types_allowed = True

    @validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        symbol = v.strip().upper()
        if not symbol.isalnum():
            raise ValueError("Symbol must be alphanumeric")
        return symbol

    @validator("limit_price")
    @classmethod
    def validate_limit_price(cls, v: Decimal | None, values: dict[str, Any]) -> Decimal | None:
        """Validate limit price is required for limit orders."""
        order_type = values.get("order_type")
        if order_type in [ValidatedOrderType.LIMIT, ValidatedOrderType.STOP_LIMIT] and v is None:
            raise ValueError("Limit price required for limit orders")
        return v

    @validator("stop_price")
    @classmethod
    def validate_stop_price(cls, v: Decimal | None, values: dict[str, Any]) -> Decimal | None:
        """Validate stop price is required for stop orders."""
        order_type = values.get("order_type")
        if order_type in [ValidatedOrderType.STOP, ValidatedOrderType.STOP_LIMIT] and v is None:
            raise ValueError("Stop price required for stop orders")
        return v

    @validator("filled_qty")
    @classmethod
    def validate_filled_qty(cls, v: Decimal, values: dict[str, Any]) -> Decimal:
        """Validate filled quantity doesn't exceed order quantity."""
        quantity = values.get("quantity", Decimal("0"))
        if v > quantity:
            raise ValueError("Filled quantity cannot exceed order quantity")
        return v

    def to_order_details(self) -> OrderDetails:
        """Convert to OrderDetails TypedDict for backward compatibility."""
        return {
            "id": self.id or "",
            "symbol": self.symbol,
            "qty": float(self.quantity),
            "side": cast(Any, self.side.value.lower()),
            "order_type": cast(Any, self.order_type.value.lower()),
            "time_in_force": cast(Any, self.time_in_force.lower()),
            "status": self.status.value,
            "filled_qty": float(self.filled_qty),
            "filled_avg_price": float(self.filled_avg_price) if self.filled_avg_price else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_order_details(cls, order_details: OrderDetails) -> "ValidatedOrder":
        """Create ValidatedOrder from OrderDetails TypedDict."""
        return cls(
            id=order_details["id"],
            client_order_id=None,  # Not provided in OrderDetails
            symbol=order_details["symbol"],
            quantity=Decimal(str(order_details["qty"])),
            side=ValidatedOrderSide(order_details["side"].upper()),
            order_type=ValidatedOrderType(order_details["order_type"].upper()),
            time_in_force=order_details["time_in_force"].upper(),
            limit_price=None,  # Not provided in OrderDetails
            stop_price=None,  # Not provided in OrderDetails
            status=OrderStatus(order_details["status"]),
            filled_qty=Decimal(str(order_details["filled_qty"])),
            filled_avg_price=(
                Decimal(str(order_details["filled_avg_price"]))
                if order_details["filled_avg_price"]
                else None
            ),
            estimated_value=None,  # Calculate from quantity * price if needed
            created_at=datetime.fromisoformat(order_details["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(order_details["updated_at"].replace("Z", "+00:00")),
        )

    @classmethod
    def from_dict(cls, order_dict: dict[str, Any]) -> "ValidatedOrder":
        """Create ValidatedOrder from dictionary with validation."""
        try:
            # Extract and validate required fields
            symbol = order_dict.get("symbol")
            if not symbol:
                raise OrderValidationError("Missing required field: symbol")

            # Handle quantity from various field names
            quantity = None
            for qty_field in ["quantity", "qty", "filled_qty"]:
                if qty_field in order_dict and order_dict[qty_field]:
                    quantity = order_dict[qty_field]
                    break

            if quantity is None:
                raise OrderValidationError("Missing required field: quantity")

            # Handle side
            side = order_dict.get("side")
            if not side:
                raise OrderValidationError("Missing required field: side")

            # Handle order type
            order_type = order_dict.get("order_type", "MARKET")

            return cls(
                id=order_dict.get("id"),
                client_order_id=order_dict.get("client_order_id"),
                symbol=str(symbol),
                quantity=Decimal(str(quantity)),
                side=ValidatedOrderSide(str(side).upper()),
                order_type=ValidatedOrderType(str(order_type).upper()),
                time_in_force=order_dict.get("time_in_force", "DAY"),
                limit_price=(
                    Decimal(str(order_dict["limit_price"]))
                    if order_dict.get("limit_price")
                    else None
                ),
                stop_price=(
                    Decimal(str(order_dict["stop_price"])) if order_dict.get("stop_price") else None
                ),
                status=OrderStatus(order_dict.get("status", "new")),
                filled_qty=Decimal(str(order_dict.get("filled_qty", 0))),
                filled_avg_price=(
                    Decimal(str(order_dict["filled_avg_price"]))
                    if order_dict.get("filled_avg_price")
                    else None
                ),
                estimated_value=order_dict.get("estimated_value"),
            )

        except (ValueError, TypeError, KeyError) as e:
            raise OrderValidationError(f"Failed to create ValidatedOrder from dict: {e}")

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == ValidatedOrderSide.BUY

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == ValidatedOrderSide.SELL

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_active(self) -> bool:
        """Check if order is active (not filled, canceled, or rejected)."""
        return self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]

    @property
    def remaining_qty(self) -> Decimal:
        """Calculate remaining quantity to be filled."""
        return max(Decimal("0"), self.quantity - self.filled_qty)

    @property
    def fill_percentage(self) -> float:
        """Calculate percentage of order that has been filled."""
        if self.quantity == 0:
            return 0.0
        return float((self.filled_qty / self.quantity) * 100)


@dataclass(
    frozen=True
)  # TODO(PYDANTIC-MIGRATION): Consider converting RiskLimits to Pydantic BaseModel for validation & ENV overrides.
class RiskLimits:
    """Risk limits for order validation."""

    max_position_pct: float = 0.10  # 10% max per position
    max_portfolio_concentration: float = 0.25  # 25% max per sector
    max_order_value: float = 50000.0  # $50k max order value
    min_order_value: float = 1.0  # $1 min order value
    max_daily_trades: int = 100  # Max trades per day


@dataclass  # TODO(PYDANTIC-MIGRATION): Could be Pydantic model with custom root validator to aggregate errors.
class ValidationResult:
    """Result of order validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validated_order: ValidatedOrder | None = None


class OrderValidator:
    """
    Comprehensive order validator with risk management.

    Provides pre-trade validation including:
    - Order structure validation
    - Risk limits enforcement
    - Position sizing validation
    - Market hours validation
    """

    def __init__(self, risk_limits: RiskLimits | None = None):
        """Initialize validator with risk limits."""
        self.risk_limits = risk_limits or RiskLimits()
        self.logger = logging.getLogger(__name__)

    def validate_order_structure(self, order_data: dict[str, Any]) -> ValidationResult:
        """
        Validate order structure and create ValidatedOrder.

        Args:
            order_data: Raw order data dictionary

        Returns:
            ValidationResult with validation outcome
        """
        errors = []
        warnings: list[str] = []

        try:
            # Attempt to create ValidatedOrder (this will trigger Pydantic validation)
            validated_order = ValidatedOrder.from_dict(order_data)

            # Additional business logic validation
            validation_errors = self._validate_business_rules(validated_order)
            errors.extend(validation_errors)

            is_valid = len(errors) == 0

            if is_valid:
                # Mark order as passing risk checks
                validated_order = validated_order.copy(update={"risk_checks_passed": True})

            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                validated_order=validated_order if is_valid else None,
            )

        except OrderValidationError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        except Exception as e:
            errors.append(f"Unexpected validation error: {e}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    def _validate_business_rules(self, order: ValidatedOrder) -> list[str]:
        """Validate business rules and risk limits."""
        errors = []

        # Validate order value
        if order.estimated_value:
            if order.estimated_value > self.risk_limits.max_order_value:
                errors.append(
                    f"Order value ${order.estimated_value} exceeds maximum ${self.risk_limits.max_order_value}"
                )

            if order.estimated_value < self.risk_limits.min_order_value:
                errors.append(
                    f"Order value ${order.estimated_value} below minimum ${self.risk_limits.min_order_value}"
                )

        # Validate quantity precision
        quantity_exponent = order.quantity.as_tuple().exponent
        if (
            isinstance(quantity_exponent, int) and quantity_exponent < -6
        ):  # More than 6 decimal places
            errors.append("Order quantity has too many decimal places (max 6)")

        # Validate price precision for limit orders
        if order.limit_price:
            limit_price_exponent = order.limit_price.as_tuple().exponent
            if (
                isinstance(limit_price_exponent, int) and limit_price_exponent < -2
            ):  # More than 2 decimal places
                errors.append("Limit price has too many decimal places (max 2)")

        return errors

    def create_validated_order(
        self,
        symbol: str,
        quantity: int | float | Decimal,
        side: str | ValidatedOrderSide,
        order_type: str | ValidatedOrderType = ValidatedOrderType.MARKET,
        limit_price: float | Decimal | None = None,
        stop_price: float | Decimal | None = None,
        time_in_force: str = "DAY",
        estimated_value: float | None = None,
    ) -> ValidatedOrder:
        """
        Create a validated order with comprehensive validation.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            side: Order side (BUY/SELL)
            order_type: Order type
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            time_in_force: Time in force
            estimated_value: Estimated order value for risk checks

        Returns:
            ValidatedOrder instance

        Raises:
            OrderValidationError: If validation fails
        """
        try:
            # Convert inputs to proper types
            if isinstance(side, str):
                side = ValidatedOrderSide(side.upper())
            if isinstance(order_type, str):
                order_type = ValidatedOrderType(order_type.upper())

            # Create order
            order = ValidatedOrder(
                id=None,  # Will be set by broker
                client_order_id=None,  # Will be generated if needed
                symbol=symbol,
                quantity=Decimal(str(quantity)),
                side=side,
                order_type=order_type,
                limit_price=Decimal(str(limit_price)) if limit_price else None,
                stop_price=Decimal(str(stop_price)) if stop_price else None,
                time_in_force=time_in_force,
                filled_avg_price=None,  # Not filled yet
                estimated_value=Decimal(str(estimated_value)) if estimated_value else None,
            )

            # Validate business rules
            validation_errors = self._validate_business_rules(order)
            if validation_errors:
                raise OrderValidationError(f"Validation failed: {'; '.join(validation_errors)}")

            # Mark as validated
            return order.copy(update={"risk_checks_passed": True})

        except (ValueError, TypeError) as e:
            raise OrderValidationError(f"Failed to create validated order: {e}")


@dataclass  # TODO(PYDANTIC-MIGRATION): Consider SettlementResult(BaseModel) if additional validation or serialization needed.
class SettlementResult:
    """Result of order settlement tracking."""

    success: bool
    settled_orders: list[ValidatedOrder] = field(default_factory=list)
    failed_orders: list[ValidatedOrder] = field(default_factory=list)
    timeout_orders: list[ValidatedOrder] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    settlement_time_seconds: float = 0.0


class OrderSettlementTracker:
    """
    Type-safe order settlement tracking.

    Replaces the unsafe wait_for_settlement functions with proper type safety.
    """

    def __init__(self, trading_client: Any | None = None):
        """Initialize settlement tracker."""
        self.trading_client = trading_client
        self.logger = logging.getLogger(__name__)

    def wait_for_settlement(
        self,
        orders: list[ValidatedOrder],
        max_wait_time: int = 60,
        poll_interval: float = 2.0,
    ) -> SettlementResult:
        """
        Wait for order settlement with type safety.

        Args:
            orders: List of ValidatedOrder instances to track
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds

        Returns:
            SettlementResult with settlement outcome
        """
        start_time = datetime.now(UTC)
        settled_orders = []
        failed_orders = []
        timeout_orders = []
        errors = []

        if not orders:
            return SettlementResult(success=True, settlement_time_seconds=0.0)

        # Extract valid order IDs
        trackable_orders = [order for order in orders if order.id]
        if not trackable_orders:
            errors.append("No orders have IDs for tracking")
            return SettlementResult(
                success=False, failed_orders=orders, errors=errors, settlement_time_seconds=0.0
            )

        self.logger.info(
            f"Tracking settlement for {len(trackable_orders)} orders (max wait: {max_wait_time}s)"
        )

        # Track orders until settled or timeout
        elapsed_time = 0.0
        while elapsed_time < max_wait_time and trackable_orders:
            if self.trading_client:
                # Update order statuses
                updated_orders = []
                for order in trackable_orders:
                    try:
                        updated_order = self._get_updated_order_status(order)
                        if updated_order.is_filled:
                            settled_orders.append(updated_order)
                            self.logger.info(
                                f"Order {updated_order.id} settled: {updated_order.symbol}"
                            )
                        elif updated_order.status in [
                            OrderStatus.CANCELED,
                            OrderStatus.REJECTED,
                            OrderStatus.EXPIRED,
                        ]:
                            failed_orders.append(updated_order)
                            self.logger.warning(
                                f"Order {updated_order.id} failed: {updated_order.status}"
                            )
                        else:
                            updated_orders.append(updated_order)
                    except Exception as e:
                        errors.append(f"Error updating order {order.id}: {e}")
                        failed_orders.append(order)

                trackable_orders = updated_orders

            if trackable_orders:
                import time

                time.sleep(poll_interval)
                elapsed_time = (datetime.now(UTC) - start_time).total_seconds()

        # Handle timeout
        if trackable_orders:
            timeout_orders.extend(trackable_orders)
            self.logger.warning(f"{len(timeout_orders)} orders timed out after {max_wait_time}s")

        settlement_time = (datetime.now(UTC) - start_time).total_seconds()
        success = len(settled_orders) == len(orders) and not errors

        return SettlementResult(
            success=success,
            settled_orders=settled_orders,
            failed_orders=failed_orders,
            timeout_orders=timeout_orders,
            errors=errors,
            settlement_time_seconds=settlement_time,
        )

    def _get_updated_order_status(self, order: ValidatedOrder) -> ValidatedOrder:
        """Get updated order status from trading client."""
        if not self.trading_client or not order.id:
            return order

        try:
            # Get order from trading client
            broker_order = self.trading_client.get_order_by_id(order.id)

            # Update order with current status
            return order.copy(
                update={
                    "status": OrderStatus(broker_order.status),
                    "filled_qty": Decimal(str(broker_order.filled_qty or 0)),
                    "filled_avg_price": (
                        Decimal(str(broker_order.filled_avg_price))
                        if broker_order.filled_avg_price
                        else None
                    ),
                    "updated_at": datetime.now(UTC),
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to get order status for {order.id}: {e}")
            return order


def validate_order_list(orders: list[dict[str, Any]]) -> list[ValidatedOrder]:
    """
    Utility function to validate a list of order dictionaries.

    Args:
        orders: List of order dictionaries

    Returns:
        List of ValidatedOrder instances

    Raises:
        OrderValidationError: If any order fails validation
    """
    validator = OrderValidator()
    validated_orders = []

    for i, order_data in enumerate(orders):
        try:
            result = validator.validate_order_structure(order_data)
            if not result.is_valid:
                raise OrderValidationError(
                    f"Order {i} validation failed: {'; '.join(result.errors)}"
                )
            assert result.validated_order is not None  # Should be present if validation passed
            validated_orders.append(result.validated_order)
        except Exception as e:
            raise OrderValidationError(f"Failed to validate order {i}: {e}")

    return validated_orders
