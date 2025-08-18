"""
Mapping utilities between Order DTOs and domain/infrastructure types.

This module provides mapping functions for the order validation refactor,
converting between OrderRequestDTO/ValidatedOrderDTO and other order representations.
Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast

from the_alchemiser.interfaces.schemas.orders import OrderRequestDTO, ValidatedOrderDTO


def dict_to_order_request_dto(order_data: dict[str, Any]) -> OrderRequestDTO:
    """
    Convert dictionary order data to OrderRequestDTO.
    
    Args:
        order_data: Raw order data dictionary
        
    Returns:
        OrderRequestDTO instance
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract required fields
    symbol = order_data.get("symbol")
    if not symbol:
        raise ValueError("Missing required field: symbol")
    
    side = order_data.get("side")
    if not side:
        raise ValueError("Missing required field: side")
    
    # Handle quantity from various field names
    quantity = None
    for qty_field in ["quantity", "qty"]:
        if qty_field in order_data and order_data[qty_field] is not None:
            quantity = order_data[qty_field]
            break
    
    if quantity is None:
        raise ValueError("Missing required field: quantity")
    
    # Normalize and validate values
    side_str = str(side).lower()
    if side_str not in ["buy", "sell"]:
        raise ValueError(f"Invalid side: {side_str}. Must be 'buy' or 'sell'")
    
    order_type_str = str(order_data.get("order_type", "market")).lower()
    if order_type_str not in ["market", "limit"]:
        raise ValueError(f"Invalid order_type: {order_type_str}. Must be 'market' or 'limit'")
    
    time_in_force_str = str(order_data.get("time_in_force", "day")).lower()
    if time_in_force_str not in ["day", "gtc", "ioc", "fok"]:
        raise ValueError(f"Invalid time_in_force: {time_in_force_str}. Must be one of 'day', 'gtc', 'ioc', 'fok'")

    # Convert to DTO with validation
    return OrderRequestDTO(
        symbol=str(symbol),
        side=cast(Literal["buy", "sell"], side_str),
        quantity=Decimal(str(quantity)),
        order_type=cast(Literal["market", "limit"], order_type_str),
        time_in_force=cast(Literal["day", "gtc", "ioc", "fok"], time_in_force_str),
        limit_price=(
            Decimal(str(order_data["limit_price"]))
            if order_data.get("limit_price") is not None
            else None
        ),
        client_order_id=order_data.get("client_order_id"),
    )


def order_request_to_validated_dto(
    request: OrderRequestDTO,
    estimated_value: Decimal | None = None,
    is_fractional: bool = False,
    normalized_quantity: Decimal | None = None,
    risk_score: Decimal | None = None,
) -> ValidatedOrderDTO:
    """
    Convert OrderRequestDTO to ValidatedOrderDTO with validation metadata.
    
    Args:
        request: The original order request
        estimated_value: Estimated order value
        is_fractional: Whether the order quantity is fractional
        normalized_quantity: Normalized quantity after validation
        risk_score: Risk score from validation
        
    Returns:
        ValidatedOrderDTO instance
    """
    return ValidatedOrderDTO(
        # Core order fields from request
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        time_in_force=request.time_in_force,
        limit_price=request.limit_price,
        client_order_id=request.client_order_id,
        # Derived validation fields
        estimated_value=estimated_value,
        is_fractional=is_fractional,
        normalized_quantity=normalized_quantity or request.quantity,
        risk_score=risk_score,
        validation_timestamp=datetime.now(UTC),
    )


def validated_dto_to_dict(validated_order: ValidatedOrderDTO) -> dict[str, Any]:
    """
    Convert ValidatedOrderDTO back to dictionary for backward compatibility.
    
    Args:
        validated_order: ValidatedOrderDTO instance
        
    Returns:
        Dictionary representation for legacy systems
    """
    return {
        "symbol": validated_order.symbol,
        "side": validated_order.side,
        "quantity": float(validated_order.quantity),
        "order_type": validated_order.order_type,
        "time_in_force": validated_order.time_in_force,
        "limit_price": float(validated_order.limit_price) if validated_order.limit_price else None,
        "client_order_id": validated_order.client_order_id,
        "estimated_value": float(validated_order.estimated_value) if validated_order.estimated_value else None,
        "is_fractional": validated_order.is_fractional,
        "normalized_quantity": float(validated_order.normalized_quantity) if validated_order.normalized_quantity else None,
        "risk_score": float(validated_order.risk_score) if validated_order.risk_score else None,
        "validation_timestamp": validated_order.validation_timestamp.isoformat(),
    }