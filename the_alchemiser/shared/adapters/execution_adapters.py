#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Execution adapters for converting between execution domain objects and DTOs.

Provides conversion functions between internal execution objects and 
OrderRequestDTO/ExecutionReportDTO for inter-module communication.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from the_alchemiser.shared.dto.execution_report_dto import (
    ExecutedOrderDTO,
    ExecutionReportDTO,
)
from the_alchemiser.shared.dto.order_request_dto import OrderRequestDTO
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO


def rebalance_plan_to_order_requests(
    rebalance_plan: RebalancePlanDTO,
    portfolio_id: str,
    execution_priority: Literal["SPEED", "COST", "BALANCE"] = "BALANCE",
    time_in_force: Literal["DAY", "GTC", "IOC", "FOK"] = "DAY",
) -> list[OrderRequestDTO]:
    """Convert RebalancePlanDTO to list of OrderRequestDTO.
    
    Args:
        rebalance_plan: RebalancePlanDTO containing rebalancing instructions
        portfolio_id: Portfolio identifier for the orders
        execution_priority: Execution priority preference
        time_in_force: Time in force for orders
        
    Returns:
        List of OrderRequestDTO instances
        
    Raises:
        ValueError: If rebalance plan data is invalid
    """
    order_requests = []
    
    for item in rebalance_plan.items:
        # Skip items with HOLD action or zero trade amount
        if item.action == "HOLD" or item.trade_amount == 0:
            continue
            
        # Determine order side and quantity from trade amount and action
        side: Literal["BUY", "SELL"] = item.action  # type: ignore[assignment]
        
        # Calculate quantity from trade amount (this is simplified - in practice you'd need current price)
        # For now, assume we can calculate a reasonable quantity
        # In a real implementation, you'd get the current price and calculate quantity = trade_amount / price
        estimated_price = Decimal('100')  # Placeholder - would get real price from market data
        order_quantity = abs(item.trade_amount) / estimated_price
        
        # Generate unique request ID
        request_id = f"rebal_{rebalance_plan.plan_id}_{item.symbol}_{uuid.uuid4().hex[:8]}"
        
        # Determine position intent based on action
        if item.action == "BUY":
            position_intent: Literal["OPEN", "CLOSE", "INCREASE", "DECREASE"] = "INCREASE"
        else:  # SELL
            position_intent = "DECREASE"
        
        order_request = OrderRequestDTO(
            correlation_id=rebalance_plan.correlation_id,
            causation_id=rebalance_plan.causation_id,
            timestamp=datetime.now(UTC),
            request_id=request_id,
            portfolio_id=portfolio_id,
            strategy_id=None,  # Not specified in RebalancePlanItemDTO
            symbol=item.symbol,
            side=side,
            quantity=order_quantity,
            order_type="MARKET",  # Default to market orders for rebalancing
            time_in_force=time_in_force,
            extended_hours=False,  # Default to regular hours
            execution_priority=execution_priority,
            position_intent=position_intent,
            reason=f"Portfolio rebalancing - {item.action} ${item.trade_amount}",
            rebalance_plan_id=rebalance_plan.plan_id,
        )
        
        order_requests.append(order_request)
    
    return order_requests


def order_result_to_executed_order_dto(
    order_result: Any,  # Order result object from broker/execution
    correlation_context: dict[str, Any] | None = None,
) -> ExecutedOrderDTO:
    """Convert internal order result to ExecutedOrderDTO.
    
    Args:
        order_result: Internal order result object
        correlation_context: Optional correlation context
        
    Returns:
        ExecutedOrderDTO instance
        
    Raises:
        ValueError: If order result data is invalid
    """
    def get_attr_value(obj: Any, attr_name: str, default: Any = None) -> Any:
        """Get attribute value from object, handling both attr access and dict access."""
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        elif isinstance(obj, dict) and attr_name in obj:
            return obj[attr_name]
        else:
            return default
    
    # Extract order data with fallbacks for different naming conventions
    order_id = get_attr_value(order_result, 'order_id') or get_attr_value(order_result, 'id') or "unknown"
    symbol = get_attr_value(order_result, 'symbol') or get_attr_value(order_result, 'Symbol') or "UNKNOWN"
    
    # Side/action
    side = get_attr_value(order_result, 'side') or get_attr_value(order_result, 'action')
    if isinstance(side, str):
        side = side.upper()
    elif hasattr(side, 'value'):  # Enum-like object
        side = str(side.value).upper()
    else:
        side = "BUY"  # Default fallback
    
    # Quantities
    quantity = get_attr_value(order_result, 'quantity') or get_attr_value(order_result, 'qty') or Decimal('0')
    filled_quantity = (
        get_attr_value(order_result, 'filled_quantity') or
        get_attr_value(order_result, 'filled_qty') or
        get_attr_value(order_result, 'qty_filled') or
        quantity  # Assume fully filled if no filled quantity provided
    )
    
    # Price
    price = (
        get_attr_value(order_result, 'price') or
        get_attr_value(order_result, 'filled_price') or
        get_attr_value(order_result, 'avg_fill_price') or
        get_attr_value(order_result, 'limit_price') or
        Decimal('0')
    )
    
    # Total value
    total_value = get_attr_value(order_result, 'total_value')
    if total_value is None:
        total_value = Decimal(str(filled_quantity)) * Decimal(str(price))
    
    # Status
    status = get_attr_value(order_result, 'status') or get_attr_value(order_result, 'state') or "FILLED"
    if isinstance(status, str):
        status = status.upper()
    elif hasattr(status, 'value'):  # Enum-like object
        status = str(status.value).upper()
    
    # Timestamp
    execution_timestamp = (
        get_attr_value(order_result, 'execution_timestamp') or
        get_attr_value(order_result, 'filled_at') or
        get_attr_value(order_result, 'updated_at') or
        datetime.now(UTC)
    )
    
    if isinstance(execution_timestamp, str):
        try:
            execution_timestamp = datetime.fromisoformat(execution_timestamp.replace('Z', '+00:00'))
        except ValueError:
            execution_timestamp = datetime.now(UTC)
    
    # Optional fields
    commission = get_attr_value(order_result, 'commission') or get_attr_value(order_result, 'fees')
    if commission is not None:
        commission = Decimal(str(commission))
    
    fees = get_attr_value(order_result, 'fees') or get_attr_value(order_result, 'regulatory_fees')
    if fees is not None:
        fees = Decimal(str(fees))
    
    error_message = get_attr_value(order_result, 'error_message') or get_attr_value(order_result, 'reject_reason')
    
    return ExecutedOrderDTO(
        order_id=str(order_id),
        symbol=str(symbol).upper(),
        action=side,
        quantity=Decimal(str(quantity)),
        filled_quantity=Decimal(str(filled_quantity)),
        price=Decimal(str(price)),
        total_value=Decimal(str(total_value)),
        status=status,
        execution_timestamp=execution_timestamp,
        commission=commission,
        fees=fees,
        error_message=str(error_message) if error_message else None,
    )


def create_execution_report_dto(
    execution_id: str,
    orders: list[Any],  # List of order result objects
    correlation_id: str,
    causation_id: str,
    session_id: str | None = None,
    broker_used: str | None = None,
    execution_strategy: str | None = None,
    market_conditions: str | None = None,
) -> ExecutionReportDTO:
    """Create ExecutionReportDTO from execution results.
    
    Args:
        execution_id: Unique execution identifier
        orders: List of order result objects
        correlation_id: Correlation identifier
        causation_id: Causation identifier
        session_id: Optional trading session identifier
        broker_used: Optional broker identifier
        execution_strategy: Optional execution strategy used
        market_conditions: Optional market conditions description
        
    Returns:
        ExecutionReportDTO instance
    """
    # Convert orders to DTOs
    executed_orders = []
    for order in orders:
        try:
            executed_order = order_result_to_executed_order_dto(order)
            executed_orders.append(executed_order)
        except Exception as e:
            # Log warning but continue with other orders
            print(f"Warning: Failed to convert order {order}: {e}")
    
    # Calculate summary statistics
    total_orders = len(executed_orders)
    successful_orders = len([o for o in executed_orders if o.status in ["FILLED", "PARTIAL"]])
    failed_orders = total_orders - successful_orders
    
    # Calculate financial summary
    total_value_traded = sum(o.total_value for o in executed_orders if o.status == "FILLED")
    total_commissions = sum(o.commission or Decimal('0') for o in executed_orders)
    total_fees = sum(o.fees or Decimal('0') for o in executed_orders)
    
    # Calculate net cash flow (negative for net purchases)
    net_cash_flow = Decimal('0')
    for order in executed_orders:
        if order.status == "FILLED":
            if order.action == "BUY":
                net_cash_flow -= order.total_value
            else:  # SELL
                net_cash_flow += order.total_value
    
    # Subtract costs
    net_cash_flow -= (total_commissions + total_fees)
    
    # Calculate timing
    execution_start_time = min(o.execution_timestamp for o in executed_orders) if executed_orders else datetime.now(UTC)
    execution_end_time = max(o.execution_timestamp for o in executed_orders) if executed_orders else datetime.now(UTC)
    total_duration_seconds = int((execution_end_time - execution_start_time).total_seconds())
    
    # Calculate performance metrics
    success_rate = Decimal(str(successful_orders / total_orders)) if total_orders > 0 else Decimal('0')
    
    average_execution_time_seconds = None
    if total_orders > 1:
        # This is a simplification - in practice you'd measure actual execution times
        average_execution_time_seconds = Decimal(str(total_duration_seconds / total_orders))
    
    return ExecutionReportDTO(
        correlation_id=correlation_id,
        causation_id=causation_id,
        timestamp=datetime.now(UTC),
        execution_id=execution_id,
        session_id=session_id,
        total_orders=total_orders,
        successful_orders=successful_orders,
        failed_orders=failed_orders,
        total_value_traded=total_value_traded,
        total_commissions=total_commissions,
        total_fees=total_fees,
        net_cash_flow=net_cash_flow,
        execution_start_time=execution_start_time,
        execution_end_time=execution_end_time,
        total_duration_seconds=total_duration_seconds,
        orders=executed_orders,
        success_rate=success_rate,
        average_execution_time_seconds=average_execution_time_seconds,
        broker_used=broker_used,
        execution_strategy=execution_strategy,
        market_conditions=market_conditions,
    )


def order_request_to_context(dto: OrderRequestDTO) -> dict[str, Any]:
    """Convert OrderRequestDTO to context dict for execution modules.
    
    Args:
        dto: OrderRequestDTO instance
        
    Returns:
        Dictionary with order request context data
    """
    return {
        'request_id': dto.request_id,
        'portfolio_id': dto.portfolio_id,
        'strategy_id': dto.strategy_id,
        'symbol': dto.symbol,
        'side': dto.side,
        'quantity': float(dto.quantity),
        'order_type': dto.order_type,
        'limit_price': float(dto.limit_price) if dto.limit_price else None,
        'stop_price': float(dto.stop_price) if dto.stop_price else None,
        'time_in_force': dto.time_in_force,
        'extended_hours': dto.extended_hours,
        'execution_priority': dto.execution_priority,
        'position_intent': dto.position_intent,
        'max_slippage_percent': float(dto.max_slippage_percent) if dto.max_slippage_percent else None,
        'risk_budget': float(dto.risk_budget) if dto.risk_budget else None,
        'reason': dto.reason,
        'rebalance_plan_id': dto.rebalance_plan_id,
        'timestamp': dto.timestamp,
        'correlation_id': dto.correlation_id,
        'causation_id': dto.causation_id,
        'metadata': dto.metadata,
    }


def batch_order_requests_to_contexts(
    order_requests: list[OrderRequestDTO],
) -> list[dict[str, Any]]:
    """Convert batch of OrderRequestDTO to context dicts.
    
    Args:
        order_requests: List of OrderRequestDTO instances
        
    Returns:
        List of context dictionaries
    """
    return [order_request_to_context(dto) for dto in order_requests]