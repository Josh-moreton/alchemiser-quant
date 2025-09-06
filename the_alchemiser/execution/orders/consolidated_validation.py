"""Business Unit: execution | Status: current

Consolidated order validation utilities and type safety module.

This module consolidates order validation functionality including:
- Order parameter validation utilities
- DTO-based validation with Pydantic models
- Pre-trade validation and risk checks
- Error handling and reporting
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from typing import Any

from the_alchemiser.execution.orders.schemas import OrderRequestDTO, ValidatedOrderDTO
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.types.exceptions import ValidationError
from the_alchemiser.shared.types.trading_errors import OrderError

# Validation Utilities


def validate_quantity(qty: Any, symbol: str) -> float | None:
    """Validate and normalize quantity parameter.

    Args:
        qty: Quantity to validate (accepts any type for validation,
             but expects float, string, or None for valid inputs)
        symbol: Symbol for logging context

    Returns:
        Validated float quantity or None if invalid

    """
    if qty is None:
        return None

    # Check for invalid types first (before float conversion)
    if isinstance(qty, bool | list | dict):
        logging.warning(f"Invalid quantity type for {symbol}: {qty}")
        return None

    # Convert qty to float if it's a string
    try:
        qty_float = float(qty)
    except (ValueError, TypeError):
        logging.warning(f"Invalid quantity type for {symbol}: {qty}")
        return None

    # Check for invalid numeric values
    if math.isnan(qty_float) or math.isinf(qty_float) or qty_float <= 0:
        logging.warning(f"Invalid quantity for {symbol}: {qty_float}")
        return None

    return qty_float


def validate_price(price: Any, symbol: str, price_type: str = "price") -> float | None:
    """Validate and normalize price parameter.

    Args:
        price: Price to validate
        symbol: Symbol for logging context
        price_type: Type of price for logging ("price", "limit_price", etc.)

    Returns:
        Validated float price or None if invalid

    """
    if price is None:
        return None

    # Check for invalid types
    if isinstance(price, bool | list | dict):
        logging.warning(f"Invalid {price_type} type for {symbol}: {price}")
        return None

    try:
        price_float = float(price)
    except (ValueError, TypeError):
        logging.warning(f"Invalid {price_type} type for {symbol}: {price}")
        return None

    # Check for invalid numeric values
    if math.isnan(price_float) or math.isinf(price_float) or price_float <= 0:
        logging.warning(f"Invalid {price_type} for {symbol}: {price_float}")
        return None

    return price_float


def normalize_symbol(symbol: Any) -> str | None:
    """Normalize symbol to uppercase string.

    Args:
        symbol: Symbol to normalize

    Returns:
        Normalized symbol string or None if invalid

    """
    if symbol is None:
        return None

    if not isinstance(symbol, str):
        logging.warning(f"Invalid symbol type: {symbol}")
        return None

    symbol_str = symbol.strip().upper()
    if not symbol_str or not symbol_str.isalnum():
        logging.warning(f"Invalid symbol format: {symbol}")
        return None

    return symbol_str


def validate_side(side: Any) -> str | None:
    """Validate order side.

    Args:
        side: Side to validate

    Returns:
        Validated side string or None if invalid

    """
    if side is None:
        return None

    if not isinstance(side, str):
        logging.warning(f"Invalid side type: {side}")
        return None

    side_lower = side.strip().lower()
    if side_lower not in {"buy", "sell"}:
        logging.warning(f"Invalid side value: {side}")
        return None

    return side_lower


def truncate_to_precision(value: float, precision: int) -> Decimal:
    """Truncate a float to specified decimal precision.

    Args:
        value: Value to truncate
        precision: Number of decimal places

    Returns:
        Truncated Decimal value

    """
    decimal_value = Decimal(str(value))
    quantize_exp = Decimal("0.1") ** precision
    return decimal_value.quantize(quantize_exp, rounding=ROUND_DOWN)


# DTO-based Validation Classes


@dataclass
class ValidationConfig:
    """Configuration for order validation."""

    # Risk limits
    max_position_size: Decimal = Decimal("1000000")  # $1M max position
    max_order_value: Decimal = Decimal("100000")  # $100K max single order
    max_daily_orders: int = 100
    min_order_value: Decimal = Decimal("1.00")  # $1 minimum

    # Price validation
    max_price_deviation: Decimal = Decimal("0.10")  # 10% from market price
    require_limit_price_for_limit_orders: bool = True

    # Quantity validation
    min_quantity: Decimal = Decimal("0.01")
    max_quantity: Decimal = Decimal("10000")

    # Enabled validations
    enable_risk_checks: bool = True
    enable_price_validation: bool = True
    enable_market_hours_check: bool = True


@dataclass
class ValidationResult:
    """Result of order validation."""

    is_valid: bool
    validated_order: ValidatedOrderDTO | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_score: Decimal | None = None


class OrderValidator:
    """Comprehensive order validator using DTOs and type safety.

    This validator provides comprehensive order validation including:
    - Basic parameter validation (symbol, quantity, price)
    - Business rule validation (limits, risk checks)
    - Type safety through Pydantic DTOs
    - Integration with error handling system
    """

    def __init__(
        self,
        config: ValidationConfig | None = None,
        error_handler: TradingSystemErrorHandler | None = None,
    ) -> None:
        """Initialize the order validator.

        Args:
            config: Validation configuration, uses defaults if None
            error_handler: Error handler for reporting validation failures

        """
        self.config = config or ValidationConfig()
        self.error_handler = error_handler or TradingSystemErrorHandler()
        self.logger = logging.getLogger(__name__)

    def validate_order_request(self, order_request: OrderRequestDTO) -> ValidatedOrderDTO:
        """Validate an order request DTO and return validated DTO.

        Args:
            order_request: Order request to validate

        Returns:
            Validated order DTO

        Raises:
            ValidationError: If validation fails

        """
        try:
            # Convert to validated DTO using mapper
            from the_alchemiser.execution.mappers.order_domain_mappers import order_request_to_validated_dto
            validated_order = order_request_to_validated_dto(order_request)

            # Perform additional business rule validation
            validation_result = self._perform_business_validation(validated_order)

            if not validation_result.is_valid:
                error_msg = f"Order validation failed: {'; '.join(validation_result.errors)}"
                self.error_handler.handle_error(
                    OrderError(error_msg), context={"order_request": order_request.model_dump()}
                )
                raise ValidationError(error_msg)

            return validated_order

        except Exception as e:
            self.logger.error(f"Order validation failed: {e}")
            self.error_handler.handle_error(
                OrderError(f"Validation error: {e}"),
                context={"order_request": order_request.model_dump()},
            )
            raise

    def validate_dict_to_dto(self, order_dict: dict[str, Any]) -> ValidatedOrderDTO:
        """Validate a dictionary and convert to DTO.

        Args:
            order_dict: Dictionary containing order parameters

        Returns:
            Validated order DTO

        Raises:
            ValidationError: If validation fails

        """
        try:
            # Convert dict to DTO
            from the_alchemiser.execution.mappers.order_domain_mappers import dict_to_order_request_dto
            order_request = dict_to_order_request_dto(order_dict)
            return self.validate_order_request(order_request)

        except Exception as e:
            self.logger.error(f"Dict to DTO validation failed: {e}")
            self.error_handler.handle_error(
                OrderError(f"Dict validation error: {e}"), context={"order_dict": order_dict}
            )
            raise

    def _perform_business_validation(self, order: ValidatedOrderDTO) -> ValidationResult:
        """Perform business rule validation on validated order.

        Args:
            order: Validated order DTO

        Returns:
            Validation result with any errors or warnings

        """
        errors = []
        warnings = []
        risk_score = Decimal("0")

        if self.config.enable_risk_checks:
            # Validate order value limits
            if order.estimated_value and order.estimated_value > self.config.max_order_value:
                errors.append(
                    f"Order value {order.estimated_value} exceeds maximum {self.config.max_order_value}"
                )

            if order.estimated_value and order.estimated_value < self.config.min_order_value:
                errors.append(
                    f"Order value {order.estimated_value} below minimum {self.config.min_order_value}"
                )

            # Validate quantity limits
            if order.quantity > self.config.max_quantity:
                errors.append(
                    f"Quantity {order.quantity} exceeds maximum {self.config.max_quantity}"
                )

            if order.quantity < self.config.min_quantity:
                errors.append(f"Quantity {order.quantity} below minimum {self.config.min_quantity}")

            # Calculate risk score
            if order.estimated_value:
                risk_score = order.estimated_value / self.config.max_order_value

        # Validate limit price requirements
        if (
            self.config.require_limit_price_for_limit_orders
            and order.order_type == "limit"
            and order.limit_price is None
        ):
            errors.append("Limit price required for limit orders")

        return ValidationResult(
            is_valid=len(errors) == 0,
            validated_order=order if len(errors) == 0 else None,
            errors=errors,
            warnings=warnings,
            risk_score=risk_score,
        )


__all__ = [
    # Utility functions
    "validate_quantity",
    "validate_price",
    "normalize_symbol",
    "validate_side",
    "truncate_to_precision",
    # Classes
    "ValidationConfig",
    "ValidationResult",
    "OrderValidator",
]
