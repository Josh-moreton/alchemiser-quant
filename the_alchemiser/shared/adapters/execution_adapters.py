#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Execution adapter functions for converting between internal objects and DTOs.

Provides adapter functions for execution-related data transformations,
supporting communication between portfolio and execution modules.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.dto import OrderRequestDTO, RebalancePlanDTO


def batch_order_requests_to_contexts(
    order_requests: list[OrderRequestDTO],
) -> list[dict[str, Any]]:
    """Convert batch of order requests to execution contexts.
    
    Args:
        order_requests: List of OrderRequestDTO objects
        
    Returns:
        List of execution context dictionaries
    """
    contexts = []
    for request in order_requests:
        context = {
            "symbol": request.symbol,
            "quantity": request.quantity,
            "side": request.side,
            "order_type": request.order_type,
            "correlation_id": request.correlation_id,
        }
        if hasattr(request, "limit_price") and request.limit_price is not None:
            context["limit_price"] = request.limit_price
        contexts.append(context)
    return contexts


def create_execution_report_dto(
    execution_results: list[dict[str, Any]],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Create execution report DTO from execution results.
    
    Args:
        execution_results: List of execution result dictionaries
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        Execution report DTO as dictionary
    """
    return {
        "correlation_id": correlation_id,
        "execution_results": execution_results,
        "total_orders": len(execution_results),
        "successful_orders": len([r for r in execution_results if r.get("status") == "filled"]),
        "failed_orders": len([r for r in execution_results if r.get("status") == "failed"]),
    }


def order_request_to_context(order_request: OrderRequestDTO) -> dict[str, Any]:
    """Convert single order request to execution context.
    
    Args:
        order_request: OrderRequestDTO object
        
    Returns:
        Execution context dictionary
    """
    context = {
        "symbol": order_request.symbol,
        "quantity": order_request.quantity,
        "side": order_request.side,
        "order_type": order_request.order_type,
        "correlation_id": order_request.correlation_id,
    }
    if hasattr(order_request, "limit_price") and order_request.limit_price is not None:
        context["limit_price"] = order_request.limit_price
    return context


def order_result_to_executed_order_dto(
    order_result: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Convert order execution result to executed order DTO.
    
    Args:
        order_result: Order result dictionary
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        Executed order DTO as dictionary
    """
    return {
        "order_id": order_result.get("order_id"),
        "symbol": order_result.get("symbol"),
        "quantity": order_result.get("quantity"),
        "side": order_result.get("side"),
        "status": order_result.get("status"),
        "filled_quantity": order_result.get("filled_quantity", 0),
        "average_fill_price": order_result.get("average_fill_price"),
        "correlation_id": correlation_id,
    }


def rebalance_plan_to_order_requests(
    rebalance_plan: RebalancePlanDTO,
    portfolio_id: str = "main_portfolio",
    execution_priority: str = "BALANCE",
    time_in_force: str = "DAY",
) -> list[OrderRequestDTO]:
    """Convert rebalance plan DTO to list of order request DTOs.
    
    Args:
        rebalance_plan: RebalancePlanDTO to convert
        portfolio_id: Portfolio identifier
        execution_priority: Execution priority level
        time_in_force: Time in force for orders
        
    Returns:
        List of OrderRequestDTO objects
    """
    order_requests = []
    
    # Generate correlation ID for this rebalance operation
    correlation_id = f"rebalance_{portfolio_id}_{rebalance_plan.correlation_id or 'unknown'}"
    
    for item in rebalance_plan.plan_items:
        # Skip if no trade needed
        if item.target_quantity == item.current_quantity:
            continue
            
        # Determine order side and quantity
        quantity_delta = item.target_quantity - item.current_quantity
        if quantity_delta > 0:
            side = "buy"
            quantity = quantity_delta
        else:
            side = "sell"
            quantity = abs(quantity_delta)
            
        # Create order request
        order_request = OrderRequestDTO(
            symbol=item.symbol,
            quantity=quantity,
            side=side,
            order_type="market",  # Default to market orders for rebalancing
            time_in_force=time_in_force,
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            execution_priority=execution_priority,
            created_at=rebalance_plan.created_at,
        )
        order_requests.append(order_request)
    
    return order_requests