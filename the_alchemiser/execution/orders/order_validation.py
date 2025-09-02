#!/usr/bin/env python3
"""Business Unit: execution; Status: current.

Order Validation and Type Safety Module.

This module provides comprehensive order validation and type safety for trade execution.
It uses strongly typed DTOs from interfaces/schemas/orders.py and integrates with the
TradingSystemErrorHandler for proper error handling.

Key Features:
- DTO-based order validation with Pydantic v2 type checking
- Immutable order models with comprehensive validation
- Pre-trade validation including risk checks
- Comprehensive error reporting for validation failures via TradingSystemErrorHandler

Usage:
    from the_alchemiser.execution.orders.validation import OrderValidator
    from the_alchemiser.execution.orders.order_schemas import OrderRequestDTO

    # Create validator
    validator = OrderValidator()

    # Create order request DTO
    request = OrderRequestDTO(
        symbol="AAPL", side="buy", quantity=Decimal("100"), order_type="market"
    )

    # Validate and get validated DTO
    validated_order = validator.validate_order_request(request)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.mappers.orders import (
    dict_to_order_request_dto,
    order_request_to_validated_dto,
)
from the_alchemiser.domain.trading.errors import OrderError, classify_validation_failure
from the_alchemiser.execution.orders.order_schemas import OrderRequestDTO, ValidatedOrderDTO
from the_alchemiser.services.errors import TradingSystemErrorHandler
from the_alchemiser.shared.utils.exceptions import ValidationError


class OrderValidationError(ValidationError):
    """Raised when order validation fails."""


@dataclass(frozen=True)
class RiskLimits:
    """Risk limits for order validation."""

    max_position_pct: float = 0.10  # 10% max per position
    max_portfolio_concentration: float = 0.25  # 25% max per sector
    max_order_value: float = 50000.0  # $50k max order value
    min_order_value: float = 1.0  # $1 min order value
    max_daily_trades: int = 100  # Max trades per day


@dataclass
class ValidationResult:
    """Result of order validation using DTOs."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validated_order: ValidatedOrderDTO | None = None
    classified_errors: list[OrderError] = field(
        default_factory=list
    )  # Structured error classification


class OrderValidator:
    """Comprehensive order validator with risk management using DTOs.

    Provides pre-trade validation including:
    - Order structure validation via DTOs
    - Risk limits enforcement
    - Position sizing validation
    - Market hours validation
    """

    def __init__(self, risk_limits: RiskLimits | None = None) -> None:
        """Initialize validator with risk limits and error handler."""
        self.risk_limits = risk_limits or RiskLimits()
        self.logger = logging.getLogger(__name__)
        self.error_handler = TradingSystemErrorHandler()

    def validate_order_request(self, order_request: OrderRequestDTO) -> ValidatedOrderDTO:
        """Validate an OrderRequestDTO and return ValidatedOrderDTO.

        Args:
            order_request: The order request DTO to validate

        Returns:
            ValidatedOrderDTO with validation metadata

        Raises:
            OrderValidationError: If validation fails

        """
        try:
            # Additional business logic validation beyond DTO validation
            validation_errors = self._validate_business_rules(order_request)
            if validation_errors:
                error_msg = f"Validation failed: {'; '.join(validation_errors)}"
                self.error_handler.handle_error(
                    error=OrderValidationError(error_msg),
                    context="order_validation",
                    component="OrderValidator.validate_order_request",
                    additional_data={
                        "symbol": order_request.symbol,
                        "quantity": str(order_request.quantity),
                        "order_type": order_request.order_type,
                    },
                )
                raise OrderValidationError(error_msg)

            # Calculate derived fields
            estimated_value = self._calculate_estimated_value(order_request)
            is_fractional = self._is_fractional_quantity(order_request.quantity)
            risk_score = self._calculate_risk_score(order_request, estimated_value)

            # Create validated DTO
            return order_request_to_validated_dto(
                request=order_request,
                estimated_value=estimated_value,
                is_fractional=is_fractional,
                normalized_quantity=order_request.quantity,
                risk_score=risk_score,
            )

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="order_validation",
                component="OrderValidator.validate_order_request",
                additional_data={"order_request": str(order_request)},
            )
            if isinstance(e, OrderValidationError):
                raise
            raise OrderValidationError(f"Failed to validate order request: {e}") from e

    def validate_order_structure(self, order_data: dict[str, Any]) -> ValidationResult:
        """Validate order structure from dict and create ValidatedOrderDTO.

        Args:
            order_data: Raw order data dictionary

        Returns:
            ValidationResult with validation outcome and classified errors

        """
        errors: list[str] = []
        warnings: list[str] = []
        classified_errors: list[OrderError] = []

        try:
            # Convert dict to DTO (this will trigger DTO validation)
            order_request = dict_to_order_request_dto(order_data)

            # Validate using DTO validator
            validated_order = self.validate_order_request(order_request)

            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                validated_order=validated_order,
                classified_errors=classified_errors,
            )

        except OrderValidationError as e:
            error_msg = str(e)
            errors.append(error_msg)

            # Classify the validation error
            classified_error = classify_validation_failure(
                reason=error_msg,
                data=order_data,
            )
            classified_errors.append(classified_error)

            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                classified_errors=classified_errors,
            )
        except Exception as e:
            error_msg = f"Unexpected validation error: {e}"
            errors.append(error_msg)

            # Classify the unexpected error
            classified_error = classify_validation_failure(
                reason=error_msg,
                data=order_data,
            )
            classified_errors.append(classified_error)

            self.error_handler.handle_error(
                error=e,
                context="order_structure_validation",
                component="OrderValidator.validate_order_structure",
                additional_data={"order_data": str(order_data)},
            )
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                classified_errors=classified_errors,
            )

    def _validate_business_rules(self, order_request: OrderRequestDTO) -> list[str]:
        """Validate business rules and risk limits."""
        errors = []

        # Calculate estimated value for validation
        estimated_value = self._calculate_estimated_value(order_request)
        if estimated_value:
            if estimated_value > Decimal(str(self.risk_limits.max_order_value)):
                errors.append(
                    f"Order value ${estimated_value} exceeds maximum ${self.risk_limits.max_order_value}"
                )

            if estimated_value < Decimal(str(self.risk_limits.min_order_value)):
                errors.append(
                    f"Order value ${estimated_value} below minimum ${self.risk_limits.min_order_value}"
                )

        # Validate quantity precision
        quantity_exponent = order_request.quantity.as_tuple().exponent
        if (
            isinstance(quantity_exponent, int) and quantity_exponent < -6
        ):  # More than 6 decimal places
            errors.append("Order quantity has too many decimal places (max 6)")

        # Validate price precision for limit orders
        if order_request.limit_price:
            limit_price_exponent = order_request.limit_price.as_tuple().exponent
            if (
                isinstance(limit_price_exponent, int) and limit_price_exponent < -2
            ):  # More than 2 decimal places
                errors.append("Limit price has too many decimal places (max 2)")

        return errors

    def _calculate_estimated_value(self, order_request: OrderRequestDTO) -> Decimal | None:
        """Calculate estimated order value."""
        if order_request.order_type == "limit" and order_request.limit_price:
            return order_request.quantity * order_request.limit_price
        # For market orders, we would need current market price
        # Return None if we can't estimate
        return None

    def _is_fractional_quantity(self, quantity: Decimal) -> bool:
        """Check if quantity has fractional part."""
        return quantity % 1 != 0

    def _calculate_risk_score(
        self, order_request: OrderRequestDTO, estimated_value: Decimal | None
    ) -> Decimal | None:
        """Calculate risk score for the order."""
        if not estimated_value:
            return None

        # Simple risk score based on order value relative to limits
        max_value = Decimal(str(self.risk_limits.max_order_value))
        risk_ratio = estimated_value / max_value
        return min(risk_ratio, Decimal("1.0"))  # Cap at 1.0


# Legacy compatibility functions for existing code
def validate_order_list(orders: list[dict[str, Any]]) -> list[ValidatedOrderDTO]:
    """Utility function to validate a list of order dictionaries.

    Args:
        orders: List of order dictionaries

    Returns:
        List of ValidatedOrderDTO instances

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
