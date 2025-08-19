"""
Mapping utilities between Strategy Tracking DTOs and external reporting formats.

This module provides mapping functions for strategy tracking DTOs, converting
between StrategyOrderEventDTO/StrategyExecutionSummaryDTO and external reporting
payloads or domain structures as needed.
Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

from typing import Any
from decimal import Decimal

from the_alchemiser.interfaces.schemas.tracking import (
    StrategyOrderEventDTO,
    StrategyExecutionSummaryDTO,
)


def strategy_order_event_dto_to_dict(event: StrategyOrderEventDTO) -> dict[str, Any]:
    """
    Convert StrategyOrderEventDTO to dictionary for external reporting.
    
    Args:
        event: StrategyOrderEventDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/logging
    """
    return {
        "event_id": event.event_id,
        "strategy": event.strategy,
        "symbol": event.symbol,
        "side": event.side,
        "quantity": float(event.quantity),  # Convert Decimal to float for JSON serialization
        "status": event.status.value if hasattr(event.status, 'value') else str(event.status),
        "price": float(event.price) if event.price is not None else None,
        "timestamp": event.ts.isoformat(),
        "error": event.error,
        # Additional metadata for reporting
        "event_type": "order_event",
        "source": "strategy_tracking",
    }


def strategy_execution_summary_dto_to_dict(summary: StrategyExecutionSummaryDTO) -> dict[str, Any]:
    """
    Convert StrategyExecutionSummaryDTO to dictionary for external reporting.
    
    Args:
        summary: StrategyExecutionSummaryDTO instance to convert
        
    Returns:
        Dictionary representation suitable for external reporting/dashboards
    """
    # Convert event details to dictionaries
    event_details = [
        strategy_order_event_dto_to_dict(event) 
        for event in summary.details
    ]
    
    return {
        "strategy": summary.strategy,
        "symbol": summary.symbol,
        "total_quantity": float(summary.total_qty),
        "average_price": float(summary.avg_price) if summary.avg_price is not None else None,
        "pnl": float(summary.pnl) if summary.pnl is not None else None,
        "status": summary.status.value if hasattr(summary.status, 'value') else str(summary.status),
        "event_count": len(summary.details),
        "event_details": event_details,
        # Additional metadata for reporting
        "summary_type": "execution_summary",
        "source": "strategy_tracking",
    }


def dict_to_strategy_order_event_dto(data: dict[str, Any]) -> StrategyOrderEventDTO:
    """
    Convert dictionary data to StrategyOrderEventDTO.
    
    Args:
        data: Raw event data dictionary
        
    Returns:
        StrategyOrderEventDTO instance
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract and validate required fields
    required_fields = ["event_id", "strategy", "symbol", "side", "quantity", "status", "ts"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Handle timestamp - could be string or datetime
    timestamp = data["ts"]
    if isinstance(timestamp, str):
        from datetime import datetime
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    return StrategyOrderEventDTO(
        event_id=data["event_id"],
        strategy=data["strategy"],
        symbol=data["symbol"],
        side=data["side"],
        quantity=Decimal(str(data["quantity"])),
        status=data["status"],
        price=Decimal(str(data["price"])) if data.get("price") is not None else None,
        ts=timestamp,
        error=data.get("error"),
    )


def dict_to_strategy_execution_summary_dto(data: dict[str, Any]) -> StrategyExecutionSummaryDTO:
    """
    Convert dictionary data to StrategyExecutionSummaryDTO.
    
    Args:
        data: Raw summary data dictionary
        
    Returns:
        StrategyExecutionSummaryDTO instance
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract and validate required fields
    required_fields = ["strategy", "symbol", "total_qty", "status"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Convert event details if present
    event_details = []
    if "event_details" in data and data["event_details"]:
        event_details = [
            dict_to_strategy_order_event_dto(event_data) 
            for event_data in data["event_details"]
        ]
    
    return StrategyExecutionSummaryDTO(
        strategy=data["strategy"],
        symbol=data["symbol"],
        total_qty=Decimal(str(data["total_qty"])),
        avg_price=Decimal(str(data["avg_price"])) if data.get("avg_price") is not None else None,
        pnl=Decimal(str(data["pnl"])) if data.get("pnl") is not None else None,
        status=data["status"],
        details=event_details,
    )