"""Business Unit: shared | Status: current.

Alpaca SDK to DTO mapping utilities.

This module provides conversion functions between Alpaca SDK objects and
domain DTOs, centralizing the mapping logic and ensuring consistent
transformations across the application.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.dto.broker_dto import OrderExecutionResult
from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO

if TYPE_CHECKING:
    from alpaca.trading.models import Order
    from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

logger = logging.getLogger(__name__)


def alpaca_order_to_execution_result(order: Order) -> OrderExecutionResult:
    """Convert Alpaca order object to OrderExecutionResult.
    
    Args:
        order: Alpaca Order object
        
    Returns:
        OrderExecutionResult with mapped fields
    """
    try:
        # Extract basic fields from order object
        order_id_raw = getattr(order, "id", None)
        order_id = str(order_id_raw) if order_id_raw is not None else "unknown"
        status = getattr(order, "status", "unknown")
        
        # Convert to string for consistent type
        status_str = str(status).lower() if status else "unknown"
        
        # Extract symbol
        symbol = str(getattr(order, "symbol", "unknown"))
        
        # Extract quantities and prices
        qty_raw = getattr(order, "qty", None)
        filled_qty_raw = getattr(order, "filled_qty", None)
        avg_price_raw = getattr(order, "filled_avg_price", None)
        
        qty = float(qty_raw) if qty_raw is not None else 0.0
        filled_qty = float(filled_qty_raw) if filled_qty_raw is not None else 0.0
        avg_price = float(avg_price_raw) if avg_price_raw is not None else 0.0
        
        # Extract side
        side_raw = getattr(order, "side", None)
        side = str(side_raw).lower() if side_raw else "unknown"
        
        # Extract timestamps
        created_at = getattr(order, "created_at", None)
        updated_at = getattr(order, "updated_at", None)
        
        logger.debug(f"Mapped order {order_id}: {status_str} - {symbol} {side} {qty}")
        
        return OrderExecutionResult(
            order_id=order_id,
            status=status_str,
            symbol=symbol,
            side=side,
            qty=qty,
            filled_qty=filled_qty,
            avg_price=avg_price,
            created_at=created_at,
            updated_at=updated_at,
        )
        
    except Exception as e:
        logger.error(f"Failed to convert order to execution result: {e}")
        return create_error_execution_result(
            error_message=f"Conversion failed: {e}",
            order_id=getattr(order, "id", "unknown") if order else "unknown"
        )


def create_error_execution_result(
    error_message: str,
    order_id: str = "unknown",
    symbol: str = "unknown",
) -> OrderExecutionResult:
    """Create an error OrderExecutionResult.
    
    Args:
        error_message: Error description
        order_id: Order ID if available
        symbol: Symbol if available
        
    Returns:
        OrderExecutionResult indicating error
    """
    return OrderExecutionResult(
        order_id=order_id,
        status="error",
        symbol=symbol,
        side="unknown",
        qty=0.0,
        filled_qty=0.0,
        avg_price=0.0,
        error_message=error_message,
    )


def create_success_order_dto(
    order: Order,
    action: str = "unknown",
) -> ExecutedOrderDTO:
    """Create successful ExecutedOrderDTO from Alpaca order.
    
    Args:
        order: Alpaca Order object
        action: Action type (buy/sell)
        
    Returns:
        ExecutedOrderDTO with success status
    """
    try:
        order_attrs = extract_order_attributes(order)
        
        return ExecutedOrderDTO(
            success=True,
            order_id=order_attrs["order_id"],
            symbol=order_attrs["symbol"],
            action=action,
            quantity=order_attrs["quantity"],
            price=order_attrs["price"],
            total_value=order_attrs["total_value"],
            status=order_attrs["status"],
            message=f"Order {order_attrs['order_id']} placed successfully",
            timestamp=order_attrs["created_at"],
            side=order_attrs["side"],
            order_type=order_attrs["order_type"],
            time_in_force=order_attrs["time_in_force"],
        )
        
    except Exception as e:
        logger.error(f"Failed to create success order DTO: {e}")
        return create_failed_order_dto(
            symbol=getattr(order, "symbol", "unknown") if order else "unknown",
            action=action,
            error_message=f"DTO creation failed: {e}"
        )


def create_failed_order_dto(
    symbol: str,
    action: str,
    error_message: str,
    quantity: float = 0.0,
    order_id: str | None = None,
) -> ExecutedOrderDTO:
    """Create failed ExecutedOrderDTO.
    
    Args:
        symbol: Stock symbol
        action: Action type (buy/sell)
        error_message: Error description
        quantity: Attempted quantity
        order_id: Order ID if available
        
    Returns:
        ExecutedOrderDTO with failure status
    """
    return ExecutedOrderDTO(
        success=False,
        order_id=order_id or "failed",
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=0.0,
        total_value=0.0,
        status="failed",
        message=error_message,
        error_message=error_message,
    )


def extract_order_attributes(order: Order) -> dict[str, Any]:
    """Extract attributes from Alpaca order object.
    
    Args:
        order: Alpaca Order object
        
    Returns:
        Dictionary with extracted attributes
    """
    try:
        # Basic order information
        order_id = str(getattr(order, "id", "unknown"))
        symbol = str(getattr(order, "symbol", "unknown"))
        status = str(getattr(order, "status", "unknown"))
        
        # Side and type
        side = extract_enum_value(getattr(order, "side", None))
        order_type = extract_enum_value(getattr(order, "order_type", None))
        time_in_force = extract_enum_value(getattr(order, "time_in_force", None))
        
        # Quantities and prices
        quantity = float(getattr(order, "qty", 0))
        price = calculate_order_price(order)
        total_value = calculate_total_value(order)
        
        # Timestamps
        created_at = getattr(order, "created_at", None)
        
        return {
            "order_id": order_id,
            "symbol": symbol,
            "status": status,
            "side": side,
            "order_type": order_type,
            "time_in_force": time_in_force,
            "quantity": quantity,
            "price": price,
            "total_value": total_value,
            "created_at": created_at,
        }
        
    except Exception as e:
        logger.error(f"Failed to extract order attributes: {e}")
        return {
            "order_id": "unknown",
            "symbol": "unknown",
            "status": "error",
            "side": "unknown",
            "order_type": "unknown",
            "time_in_force": "unknown",
            "quantity": 0.0,
            "price": 0.0,
            "total_value": 0.0,
            "created_at": None,
        }


def extract_enum_value(enum_obj: object) -> str:
    """Extract string value from Alpaca enum object.
    
    Args:
        enum_obj: Alpaca enum object
        
    Returns:
        String representation of enum value
    """
    if enum_obj is None:
        return "unknown"
    return str(enum_obj).lower()


def calculate_order_price(order: Order) -> float:
    """Calculate representative price from order object.
    
    Args:
        order: Alpaca Order object
        
    Returns:
        Representative price (limit price, filled avg price, or 0.0)
    """
    try:
        # Try filled average price first
        filled_avg = getattr(order, "filled_avg_price", None)
        if filled_avg is not None:
            return float(filled_avg)
            
        # Fall back to limit price
        limit_price = getattr(order, "limit_price", None)
        if limit_price is not None:
            return float(limit_price)
            
        return 0.0
    except (ValueError, TypeError):
        return 0.0


def calculate_total_value(order: Order) -> float:
    """Calculate total value from order object.
    
    Args:
        order: Alpaca Order object
        
    Returns:
        Total value (quantity * price)
    """
    try:
        qty = float(getattr(order, "qty", 0))
        price = calculate_order_price(order)
        return qty * price
    except (ValueError, TypeError):
        return 0.0


def extract_action_from_request(
    order_request: LimitOrderRequest | MarketOrderRequest,
) -> str:
    """Extract action (buy/sell) from order request.
    
    Args:
        order_request: Alpaca order request object
        
    Returns:
        Action string ("buy" or "sell")
    """
    try:
        side = getattr(order_request, "side", None)
        if side:
            side_str = str(side).lower()
            return "buy" if "buy" in side_str else "sell"
    except Exception:
        pass
    return "unknown"


def create_error_dto(
    symbol: str,
    action: str,
    error_message: str,
    quantity: float = 0.0,
) -> ExecutedOrderDTO:
    """Create error ExecutedOrderDTO for various failure scenarios.
    
    Args:
        symbol: Stock symbol
        action: Action type
        error_message: Error description
        quantity: Attempted quantity
        
    Returns:
        ExecutedOrderDTO with error status
    """
    return ExecutedOrderDTO(
        success=False,
        order_id="error",
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=0.0,
        total_value=0.0,
        status="error",
        message=error_message,
        error_message=error_message,
    )