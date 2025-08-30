#!/usr/bin/env python3
"""Business Unit: order execution/placement | Status: current

Alpaca DTO mapping utilities for anti-corruption layer.

This module provides mapping functions to convert between Alpaca API responses
and OrderExecutionResultDTO, ensuring proper type conversion and validation
at the infrastructure boundary.

Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast

from the_alchemiser.anti_corruption.brokers.order_status_mapping import normalize_order_status
from the_alchemiser.interfaces.schemas.alpaca import AlpacaErrorDTO, AlpacaOrderDTO
from the_alchemiser.interfaces.schemas.orders import OrderExecutionResultDTO

logger = logging.getLogger(__name__)


def alpaca_order_to_dto(order: Any) -> AlpacaOrderDTO:
    """Convert raw Alpaca order object to AlpacaOrderDTO.

    Handles both attribute-based objects and dict responses from Alpaca API.

    Args:
        order: Raw Alpaca order object or dict

    Returns:
        AlpacaOrderDTO with validated and converted fields

    Raises:
        ValueError: If required fields are missing or invalid

    """

    # Extract helper function to handle both attribute access and dict access
    def get_attr(name: str, default: Any = None) -> Any:
        if isinstance(order, dict):
            return order.get(name, default)
        return getattr(order, name, default)

    # Extract required fields
    order_id = get_attr("id")
    if not order_id:
        raise ValueError("Order ID is required")

    symbol = get_attr("symbol")
    if not symbol:
        raise ValueError("Symbol is required")

    # Extract financial values with proper Decimal conversion
    def to_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert {value} to Decimal: {e}")
            raise

    # Extract timestamps with proper datetime handling
    def to_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        try:
            dt = datetime.fromisoformat(str(value))
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {value} to datetime: {e}")
            return None

    # Build DTO with proper type conversion
    return AlpacaOrderDTO(
        id=str(order_id),
        symbol=str(symbol),
        asset_class=str(get_attr("asset_class", "equity")),
        notional=to_decimal(get_attr("notional")),
        qty=to_decimal(get_attr("qty")),
        filled_qty=to_decimal(get_attr("filled_qty")),
        filled_avg_price=to_decimal(get_attr("filled_avg_price")),
        order_class=str(get_attr("order_class", "simple")),
        order_type=str(get_attr("order_type", "market")),
        type=str(get_attr("type") or get_attr("order_type", "market")),
        side=cast(Literal["buy", "sell"], str(get_attr("side", "buy")).lower()),
        time_in_force=str(get_attr("time_in_force", "day")),
        status=str(get_attr("status", "new")),
        created_at=to_datetime(get_attr("created_at")) or datetime.now(UTC),
        updated_at=to_datetime(get_attr("updated_at")) or datetime.now(UTC),
        submitted_at=to_datetime(get_attr("submitted_at")),
        filled_at=to_datetime(get_attr("filled_at")),
        expired_at=to_datetime(get_attr("expired_at")),
        canceled_at=to_datetime(get_attr("canceled_at")),
    )


def alpaca_dto_to_execution_result(alpaca_dto: AlpacaOrderDTO) -> OrderExecutionResultDTO:
    """Convert AlpacaOrderDTO to OrderExecutionResultDTO.

    Maps Alpaca-specific fields to standardized execution result format
    with proper status normalization and success determination.

    Args:
        alpaca_dto: Validated Alpaca order DTO

    Returns:
        OrderExecutionResultDTO with standardized fields

    """
    # Normalize status using existing logic
    normalized_status = normalize_order_status(alpaca_dto.status)

    # Map to execution result status literals with proper handling
    # OrderExecutionResultDTO expects: "accepted", "filled", "partially_filled", "rejected", "canceled"
    status_mapping = {
        "new": "accepted",  # Map 'new' status to 'accepted' for OrderExecutionResultDTO
        "partially_filled": "partially_filled",
        "filled": "filled",
        "canceled": "canceled",
        "expired": "rejected",  # Map expired to rejected
        "rejected": "rejected",
    }

    mapped_status = status_mapping.get(normalized_status, "rejected")
    if normalized_status not in status_mapping:
        logger.warning(
            f"Unmapped Alpaca order status '{normalized_status}' encountered for order ID '{alpaca_dto.id}', defaulting to 'rejected'."
        )
    status_literal = cast(
        Literal["accepted", "filled", "partially_filled", "rejected", "canceled"],
        mapped_status,
    )

    # Determine success based on status
    success = status_literal not in {"rejected", "canceled"}

    # Determine error message for failed orders
    error_message = None
    if not success:
        error_message = f"Order {status_literal}"

    # Use filled quantity or default to 0
    filled_qty = alpaca_dto.filled_qty or Decimal("0")

    # Determine completion time based on status
    completed_at = None
    if status_literal in {"filled", "canceled", "rejected"}:
        if alpaca_dto.filled_at:
            completed_at = alpaca_dto.filled_at
        elif alpaca_dto.canceled_at:
            completed_at = alpaca_dto.canceled_at
        elif alpaca_dto.expired_at:
            completed_at = alpaca_dto.expired_at
        else:
            completed_at = alpaca_dto.updated_at

    return OrderExecutionResultDTO(
        success=success,
        error=error_message,
        order_id=alpaca_dto.id,
        status=status_literal,
        filled_qty=filled_qty,
        avg_fill_price=alpaca_dto.filled_avg_price,
        submitted_at=alpaca_dto.submitted_at or alpaca_dto.created_at,
        completed_at=completed_at,
    )


def alpaca_order_to_execution_result(order: Any) -> OrderExecutionResultDTO:
    """Direct conversion from raw Alpaca order to OrderExecutionResultDTO.

    Convenience function that combines alpaca_order_to_dto and
    alpaca_dto_to_execution_result in a single step.

    Args:
        order: Raw Alpaca order object or dict

    Returns:
        OrderExecutionResultDTO with validated and converted fields

    Raises:
        ValueError: If order conversion fails

    """
    try:
        alpaca_dto = alpaca_order_to_dto(order)
        return alpaca_dto_to_execution_result(alpaca_dto)
    except Exception as e:
        # Fallback to error DTO for failed conversions
        logger.error(f"Failed to convert Alpaca order to execution result: {e}")
        return OrderExecutionResultDTO(
            success=False,
            error=f"Order conversion failed: {e}",
            order_id=str(getattr(order, "id", "unknown")),
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )


def create_error_execution_result(
    error: Exception,
    context: str = "Order execution",
    order_id: str = "",
) -> OrderExecutionResultDTO:
    """Create an OrderExecutionResultDTO for error scenarios.

    Provides consistent error handling across AlpacaManager methods.

    Args:
        error: The exception that occurred
        context: Context description for the error
        order_id: Order ID if available

    Returns:
        OrderExecutionResultDTO with error details

    """
    return OrderExecutionResultDTO(
        success=False,
        error=f"{context} failed: {error}",
        order_id=order_id,
        status="rejected",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def alpaca_exception_to_error_dto(
    exception: Exception,
    default_code: int = 500,
    request_id: str | None = None,
) -> AlpacaErrorDTO:
    """Convert Alpaca API exception to AlpacaErrorDTO.

    Extracts error information from Alpaca API exceptions and formats
    them into structured error DTOs.

    Args:
        exception: The Alpaca API exception
        default_code: Default HTTP code if not extractable
        request_id: Request ID for tracking

    Returns:
        AlpacaErrorDTO with structured error information

    """
    # Try to extract error code from exception
    error_code = default_code
    if hasattr(exception, "status_code"):
        error_code = exception.status_code
    elif hasattr(exception, "code"):
        error_code = exception.code

    # Extract error message
    error_message = str(exception)
    if hasattr(exception, "message"):
        error_message = exception.message

    # Extract additional details if available
    details = None
    if hasattr(exception, "details"):
        details = exception.details
    elif hasattr(exception, "response"):
        response = exception.response
        if hasattr(response, "json"):
            with contextlib.suppress(Exception):
                details = response.json()

    return AlpacaErrorDTO(
        code=error_code,
        message=error_message,
        details=details,
        request_id=request_id,
    )
