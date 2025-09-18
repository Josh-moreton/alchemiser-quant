"""Business Unit: shared | Status: current.

Alpaca response mappers.

Functions to map Alpaca SDK responses to domain models and DTOs.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from alpaca.trading.models import Order, Position, TradeAccount

from ..dto.broker_dto import OrderExecutionResult
from ..dto.execution_report_dto import ExecutedOrderDTO
from .models import AccountInfoModel, OrderModel, PositionModel
from .utils import extract_enum_value, get_attribute_safe, safe_decimal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def map_account_to_model(account: TradeAccount) -> AccountInfoModel:
    """Map Alpaca TradeAccount to AccountInfoModel.
    
    Args:
        account: Alpaca TradeAccount object
        
    Returns:
        AccountInfoModel instance
    """
    return AccountInfoModel(
        id=get_attribute_safe(account, "id"),
        account_number=get_attribute_safe(account, "account_number"),
        status=get_attribute_safe(account, "status"),
        currency=get_attribute_safe(account, "currency"),
        buying_power=safe_decimal(get_attribute_safe(account, "buying_power")),
        cash=safe_decimal(get_attribute_safe(account, "cash")),
        equity=safe_decimal(get_attribute_safe(account, "equity")),
        portfolio_value=safe_decimal(get_attribute_safe(account, "portfolio_value")),
    )


def map_account_to_dict(account: TradeAccount) -> dict[str, Any]:
    """Map Alpaca TradeAccount to dictionary.
    
    Args:
        account: Alpaca TradeAccount object
        
    Returns:
        Dictionary representation
    """
    try:
        # Some SDK objects expose __dict__ with serializable fields
        data = account.__dict__ if hasattr(account, "__dict__") else None
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.debug(f"Falling back to manual account dict conversion: {exc}")
    
    # Fallback: build dict from known attributes
    return {
        "id": get_attribute_safe(account, "id"),
        "account_number": get_attribute_safe(account, "account_number"),
        "status": get_attribute_safe(account, "status"),
        "currency": get_attribute_safe(account, "currency"),
        "buying_power": get_attribute_safe(account, "buying_power"),
        "cash": get_attribute_safe(account, "cash"),
        "equity": get_attribute_safe(account, "equity"),
        "portfolio_value": get_attribute_safe(account, "portfolio_value"),
    }


def map_position_to_model(position: Position) -> PositionModel:
    """Map Alpaca Position to PositionModel.
    
    Args:
        position: Alpaca Position object
        
    Returns:
        PositionModel instance
    """
    return PositionModel(
        symbol=str(get_attribute_safe(position, "symbol", "")),
        qty=safe_decimal(get_attribute_safe(position, "qty", 0)) or Decimal("0"),
        qty_available=safe_decimal(get_attribute_safe(position, "qty_available")),
        market_value=safe_decimal(get_attribute_safe(position, "market_value")),
        cost_basis=safe_decimal(get_attribute_safe(position, "cost_basis")),
        unrealized_pl=safe_decimal(get_attribute_safe(position, "unrealized_pl")),
        unrealized_plpc=safe_decimal(get_attribute_safe(position, "unrealized_plpc")),
        current_price=safe_decimal(get_attribute_safe(position, "current_price")),
        lastday_price=safe_decimal(get_attribute_safe(position, "lastday_price")),
        change_today=safe_decimal(get_attribute_safe(position, "change_today")),
    )


def map_order_to_model(order: Order) -> OrderModel:
    """Map Alpaca Order to OrderModel.
    
    Args:
        order: Alpaca Order object
        
    Returns:
        OrderModel instance
    """
    return OrderModel(
        id=str(get_attribute_safe(order, "id", "")),
        client_order_id=get_attribute_safe(order, "client_order_id"),
        symbol=str(get_attribute_safe(order, "symbol", "")),
        asset_class=extract_enum_value(get_attribute_safe(order, "asset_class")),
        order_class=extract_enum_value(get_attribute_safe(order, "order_class")),
        order_type=extract_enum_value(get_attribute_safe(order, "order_type")),
        qty=safe_decimal(get_attribute_safe(order, "qty")),
        filled_qty=safe_decimal(get_attribute_safe(order, "filled_qty")),
        side=extract_enum_value(get_attribute_safe(order, "side")),
        time_in_force=extract_enum_value(get_attribute_safe(order, "time_in_force")),
        limit_price=safe_decimal(get_attribute_safe(order, "limit_price")),
        stop_price=safe_decimal(get_attribute_safe(order, "stop_price")),
        status=extract_enum_value(get_attribute_safe(order, "status")),
        created_at=get_attribute_safe(order, "created_at"),
        updated_at=get_attribute_safe(order, "updated_at"),
        submitted_at=get_attribute_safe(order, "submitted_at"),
        filled_at=get_attribute_safe(order, "filled_at"),
        expired_at=get_attribute_safe(order, "expired_at"),
        canceled_at=get_attribute_safe(order, "canceled_at"),
        failed_at=get_attribute_safe(order, "failed_at"),
        replaced_at=get_attribute_safe(order, "replaced_at"),
        avg_fill_price=safe_decimal(get_attribute_safe(order, "filled_avg_price")),
    )


def map_order_to_execution_result(order: Order) -> OrderExecutionResult:
    """Map Alpaca Order to OrderExecutionResult.
    
    Args:
        order: Alpaca Order object
        
    Returns:
        OrderExecutionResult instance
    """
    try:
        # Extract basic fields from order object
        order_id_raw = get_attribute_safe(order, "id")
        order_id = str(order_id_raw) if order_id_raw is not None else "unknown"
        status = get_attribute_safe(order, "status", "unknown")
        filled_qty = Decimal(str(get_attribute_safe(order, "filled_qty", 0)))
        avg_fill_price = get_attribute_safe(order, "filled_avg_price")
        submitted_at = get_attribute_safe(order, "submitted_at")
        filled_at = get_attribute_safe(order, "filled_at")

        # Map Alpaca status to OrderExecutionResult status
        status_str = str(status).upper()
        mapped_status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]
        if status_str in ["FILLED", "CLOSED"]:
            mapped_status = "filled"
        elif status_str == "CANCELED":
            mapped_status = "canceled"
        elif status_str in ["REJECTED", "EXPIRED", "STOPPED"]:
            mapped_status = "rejected"
        elif status_str in ["PARTIALLY_FILLED"]:
            mapped_status = "partially_filled"
        else:
            mapped_status = "accepted"

        # Handle timestamps
        submitted_dt = submitted_at if isinstance(submitted_at, datetime) else datetime.now(UTC)
        completed_dt = filled_at if isinstance(filled_at, datetime) else datetime.now(UTC)

        # Handle average fill price
        avg_price = None
        if avg_fill_price is not None:
            try:
                avg_price = Decimal(str(avg_fill_price))
            except (ValueError, TypeError):
                avg_price = None

        return OrderExecutionResult(
            success=True,
            order_id=order_id,
            status=mapped_status,
            filled_qty=filled_qty,
            avg_fill_price=avg_price,
            submitted_at=submitted_dt,
            completed_at=completed_dt,
            error=None,
        )

    except Exception as e:
        logger.error(f"Failed to convert order to execution result: {e}")
        return create_error_execution_result(e, "Order conversion")


def map_order_to_executed_dto(
    order: Order, 
    order_request: Any = None
) -> ExecutedOrderDTO:
    """Map Alpaca Order to ExecutedOrderDTO.
    
    Args:
        order: Alpaca Order object
        order_request: Optional original order request for fallback data
        
    Returns:
        ExecutedOrderDTO instance
    """
    # Avoid attribute assumptions for mypy
    order_id = str(get_attribute_safe(order, "id", ""))
    order_symbol = str(get_attribute_safe(order, "symbol", ""))
    order_qty = get_attribute_safe(order, "qty", "0")
    order_filled_qty = get_attribute_safe(order, "filled_qty", "0")
    order_filled_avg_price = get_attribute_safe(order, "filled_avg_price")
    order_side = get_attribute_safe(order, "side", "")
    order_status = get_attribute_safe(order, "status", "SUBMITTED")

    # Handle price - use filled_avg_price if available, otherwise estimate
    price = Decimal("0.01")  # Default minimal price
    if order_filled_avg_price:
        price = Decimal(str(order_filled_avg_price))
    elif order_request and hasattr(order_request, "limit_price") and order_request.limit_price:
        price = Decimal(str(order_request.limit_price))

    # Extract enum values properly
    action_value = extract_enum_value(order_side).upper()
    status_value = extract_enum_value(order_status).upper()

    # Calculate total_value: use filled_quantity if > 0, otherwise use order quantity
    # This ensures total_value > 0 for DTO validation even for unfilled orders
    filled_qty_decimal = Decimal(str(order_filled_qty))
    order_qty_decimal = Decimal(str(order_qty))
    if filled_qty_decimal > 0:
        total_value = filled_qty_decimal * price
    else:
        total_value = order_qty_decimal * price

    return ExecutedOrderDTO(
        order_id=order_id,
        symbol=order_symbol,
        action=action_value,
        quantity=order_qty_decimal,
        filled_quantity=filled_qty_decimal,
        price=price,
        total_value=total_value,
        status=status_value,
        execution_timestamp=datetime.now(UTC),
    )


def create_error_execution_result(
    error: Exception, context: str = "Operation", order_id: str = "unknown"
) -> OrderExecutionResult:
    """Create an error OrderExecutionResult.
    
    Args:
        error: Exception that occurred
        context: Context string for error message
        order_id: Order ID if available
        
    Returns:
        OrderExecutionResult with error details
    """
    status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = (
        "rejected"
    )
    return OrderExecutionResult(
        success=False,
        order_id=order_id,
        status=status,
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        error=f"{context} failed: {error!s}",
    )


def create_error_executed_dto(
    error: Exception,
    symbol: str = "UNKNOWN",
    action: str = "BUY",
    order_request: Any = None,
) -> ExecutedOrderDTO:
    """Create an error ExecutedOrderDTO.
    
    Args:
        error: Exception that occurred
        symbol: Symbol for the failed order
        action: Action for the failed order
        order_request: Optional original order request for data extraction
        
    Returns:
        ExecutedOrderDTO with error details
    """
    # Extract action from order request if available
    if order_request:
        side = get_attribute_safe(order_request, "side")
        if side:
            action_extracted = extract_enum_value(side).upper()
            if "SELL" in action_extracted:
                action = "SELL"
            elif "BUY" in action_extracted:
                action = "BUY"

    return ExecutedOrderDTO(
        order_id="FAILED",  # Must be non-empty
        symbol=symbol,
        action=action,
        quantity=Decimal("0.01"),  # Must be > 0
        filled_quantity=Decimal("0"),
        price=Decimal("0.01"),
        total_value=Decimal("0.01"),  # Must be > 0
        status="REJECTED",
        execution_timestamp=datetime.now(UTC),
        error_message=str(error),
    )