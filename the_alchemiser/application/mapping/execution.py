#!/usr/bin/env python3
"""Execution mapping utilities for anti-corruption layer.

This module provides pure functions for converting between execution DTOs
and domain types. Part of the anti-corruption layer for clean boundaries
between Pydantic DTOs and domain models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.types import AccountInfo, OrderDetails
from the_alchemiser.interfaces.schemas.execution import (
    ExecutionResultDTO,
    LambdaEventDTO,
    OrderHistoryDTO,
    QuoteDTO,
    TradingAction,
    TradingPlanDTO,
    WebSocketResultDTO,
    WebSocketStatus,
)


def ensure_decimal_precision(value: float | str | Decimal | None) -> Decimal:
    """Ensure value is converted to Decimal with appropriate precision."""
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"))


def normalize_timestamp(ts: str | datetime) -> datetime:
    """Normalize timestamp to timezone-aware datetime."""
    if isinstance(ts, str):
        # Handle ISO format with 'Z' suffix
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    
    # Ensure timezone awareness
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts


def execution_result_dto_to_dict(dto: ExecutionResultDTO) -> dict[str, Any]:
    """Convert ExecutionResultDTO to dictionary for external reporting.
    
    Args:
        dto: ExecutionResultDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "orders_executed": [dict(order) if isinstance(order, dict) else order for order in dto.orders_executed],
        "account_info_before": dict(dto.account_info_before),
        "account_info_after": dict(dto.account_info_after),
        "execution_summary": dto.execution_summary,
        "final_portfolio_state": dto.final_portfolio_state,
        # Additional metadata for reporting
        "execution_type": "trading_cycle",
        "orders_count": len(dto.orders_executed),
        "source": "execution_mapping",
    }


def dict_to_execution_result_dto(data: dict[str, Any]) -> ExecutionResultDTO:
    """Convert dictionary to ExecutionResultDTO.
    
    Args:
        data: Dictionary containing execution result data
        
    Returns:
        ExecutionResultDTO instance
    """
    return ExecutionResultDTO(
        orders_executed=data.get("orders_executed", []),
        account_info_before=data["account_info_before"],
        account_info_after=data["account_info_after"],
        execution_summary=data.get("execution_summary", {}),
        final_portfolio_state=data.get("final_portfolio_state"),
    )


def trading_plan_dto_to_dict(dto: TradingPlanDTO) -> dict[str, Any]:
    """Convert TradingPlanDTO to dictionary for external reporting.
    
    Args:
        dto: TradingPlanDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "symbol": dto.symbol,
        "action": dto.action.value if hasattr(dto.action, "value") else str(dto.action),
        "quantity": float(dto.quantity),  # Convert Decimal to float for JSON serialization
        "estimated_price": float(dto.estimated_price),
        "reasoning": dto.reasoning,
        # Additional metadata for reporting
        "plan_type": "trading_plan",
        "estimated_value": float(dto.quantity * dto.estimated_price),
        "source": "execution_mapping",
    }


def dict_to_trading_plan_dto(data: dict[str, Any]) -> TradingPlanDTO:
    """Convert dictionary to TradingPlanDTO.
    
    Args:
        data: Dictionary containing trading plan data
        
    Returns:
        TradingPlanDTO instance
    """
    # Normalize action to TradingAction enum
    action = data["action"]
    if isinstance(action, str):
        action = TradingAction(action.upper())
    
    return TradingPlanDTO(
        symbol=data["symbol"],
        action=action,
        quantity=ensure_decimal_precision(data["quantity"]),
        estimated_price=ensure_decimal_precision(data["estimated_price"]),
        reasoning=data.get("reasoning", ""),
    )


def websocket_result_dto_to_dict(dto: WebSocketResultDTO) -> dict[str, Any]:
    """Convert WebSocketResultDTO to dictionary for external reporting.
    
    Args:
        dto: WebSocketResultDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "status": dto.status.value if hasattr(dto.status, "value") else str(dto.status),
        "message": dto.message,
        "orders_completed": dto.orders_completed,
        # Additional metadata for reporting
        "result_type": "websocket_result",
        "orders_count": len(dto.orders_completed),
        "source": "execution_mapping",
    }


def dict_to_websocket_result_dto(data: dict[str, Any]) -> WebSocketResultDTO:
    """Convert dictionary to WebSocketResultDTO.
    
    Args:
        data: Dictionary containing websocket result data
        
    Returns:
        WebSocketResultDTO instance
    """
    # Normalize status to WebSocketStatus enum
    status = data["status"]
    if isinstance(status, str):
        status = WebSocketStatus(status.lower())
    
    return WebSocketResultDTO(
        status=status,
        message=data["message"],
        orders_completed=data.get("orders_completed", []),
    )


def quote_dto_to_dict(dto: QuoteDTO) -> dict[str, Any]:
    """Convert QuoteDTO to dictionary for external reporting.
    
    Args:
        dto: QuoteDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "bid_price": float(dto.bid_price),
        "ask_price": float(dto.ask_price),
        "bid_size": float(dto.bid_size),
        "ask_size": float(dto.ask_size),
        "timestamp": dto.timestamp,
        # Additional metadata for reporting
        "quote_type": "real_time_quote",
        "spread": float(dto.ask_price - dto.bid_price),
        "mid_price": float((dto.bid_price + dto.ask_price) / 2),
        "source": "execution_mapping",
    }


def dict_to_quote_dto(data: dict[str, Any]) -> QuoteDTO:
    """Convert dictionary to QuoteDTO.
    
    Args:
        data: Dictionary containing quote data
        
    Returns:
        QuoteDTO instance
    """
    return QuoteDTO(
        bid_price=ensure_decimal_precision(data["bid_price"]),
        ask_price=ensure_decimal_precision(data["ask_price"]),
        bid_size=ensure_decimal_precision(data["bid_size"]),
        ask_size=ensure_decimal_precision(data["ask_size"]),
        timestamp=data["timestamp"],
    )


def lambda_event_dto_to_dict(dto: LambdaEventDTO) -> dict[str, Any]:
    """Convert LambdaEventDTO to dictionary for external reporting.
    
    Args:
        dto: LambdaEventDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "mode": dto.mode,
        "trading_mode": dto.trading_mode,
        "ignore_market_hours": dto.ignore_market_hours,
        "arguments": dto.arguments,
        # Additional metadata for reporting
        "event_type": "lambda_event",
        "has_arguments": bool(dto.arguments),
        "source": "execution_mapping",
    }


def dict_to_lambda_event_dto(data: dict[str, Any]) -> LambdaEventDTO:
    """Convert dictionary to LambdaEventDTO.
    
    Args:
        data: Dictionary containing lambda event data
        
    Returns:
        LambdaEventDTO instance
    """
    return LambdaEventDTO(
        mode=data.get("mode"),
        trading_mode=data.get("trading_mode"),
        ignore_market_hours=data.get("ignore_market_hours"),
        arguments=data.get("arguments"),
    )


def order_history_dto_to_dict(dto: OrderHistoryDTO) -> dict[str, Any]:
    """Convert OrderHistoryDTO to dictionary for external reporting.
    
    Args:
        dto: OrderHistoryDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "orders": [dict(order) if isinstance(order, dict) else order for order in dto.orders],
        "metadata": dto.metadata,
        # Additional metadata for reporting
        "history_type": "order_history",
        "orders_count": len(dto.orders),
        "source": "execution_mapping",
    }


def dict_to_order_history_dto(data: dict[str, Any]) -> OrderHistoryDTO:
    """Convert dictionary to OrderHistoryDTO.
    
    Args:
        data: Dictionary containing order history data
        
    Returns:
        OrderHistoryDTO instance
    """
    return OrderHistoryDTO(
        orders=data.get("orders", []),
        metadata=data.get("metadata", {}),
    )


# Domain model to DTO conversions
def account_info_to_execution_result_dto(
    orders_executed: list[OrderDetails],
    account_before: AccountInfo,
    account_after: AccountInfo,
    execution_summary: dict[str, Any] | None = None,
    final_portfolio_state: dict[str, Any] | None = None,
) -> ExecutionResultDTO:
    """Create ExecutionResultDTO from domain models.
    
    Args:
        orders_executed: List of OrderDetails executed
        account_before: Account state before execution
        account_after: Account state after execution
        execution_summary: Optional execution summary
        final_portfolio_state: Optional portfolio state
        
    Returns:
        ExecutionResultDTO instance
    """
    return ExecutionResultDTO(
        orders_executed=orders_executed,
        account_info_before=account_before,
        account_info_after=account_after,
        execution_summary=execution_summary or {},
        final_portfolio_state=final_portfolio_state,
    )


def create_trading_plan_dto(
    symbol: str,
    action: str,
    quantity: float | Decimal,
    estimated_price: float | Decimal,
    reasoning: str = "",
) -> TradingPlanDTO:
    """Create TradingPlanDTO from basic parameters.
    
    Args:
        symbol: Trading symbol
        action: Trading action ("BUY" or "SELL")
        quantity: Quantity to trade
        estimated_price: Estimated execution price
        reasoning: Reasoning behind the trading decision
        
    Returns:
        TradingPlanDTO instance
    """
    return TradingPlanDTO(
        symbol=symbol.upper().strip(),
        action=TradingAction(action.upper()),
        quantity=ensure_decimal_precision(quantity),
        estimated_price=ensure_decimal_precision(estimated_price),
        reasoning=reasoning,
    )


def create_quote_dto(
    bid_price: float | Decimal,
    ask_price: float | Decimal,
    bid_size: float | Decimal,
    ask_size: float | Decimal,
    timestamp: str | datetime | None = None,
) -> QuoteDTO:
    """Create QuoteDTO from basic parameters.
    
    Args:
        bid_price: Bid price
        ask_price: Ask price
        bid_size: Bid size
        ask_size: Ask size
        timestamp: Quote timestamp (defaults to current UTC time)
        
    Returns:
        QuoteDTO instance
    """
    if timestamp is None:
        timestamp = datetime.now(UTC).isoformat()
    elif isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()
    
    return QuoteDTO(
        bid_price=ensure_decimal_precision(bid_price),
        ask_price=ensure_decimal_precision(ask_price),
        bid_size=ensure_decimal_precision(bid_size),
        ask_size=ensure_decimal_precision(ask_size),
        timestamp=timestamp,
    )