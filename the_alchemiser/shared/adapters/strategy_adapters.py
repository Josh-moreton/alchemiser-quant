#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy adapter functions for converting between internal objects and DTOs.

Provides adapter functions for strategy-related data transformations,
supporting communication between strategy and other modules.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.dto import StrategySignalDTO


def batch_strategy_signals_to_dtos(
    signals: list[dict[str, Any]],
) -> list[StrategySignalDTO]:
    """Convert batch of strategy signal dictionaries to StrategySignalDTO objects.
    
    Args:
        signals: List of strategy signal dictionaries
        
    Returns:
        List of StrategySignalDTO objects
    """
    return [strategy_signal_to_dto(signal) for signal in signals]


def dto_to_strategy_signal_context(
    signal_dto: StrategySignalDTO,
) -> dict[str, Any]:
    """Convert StrategySignalDTO to strategy signal context dictionary.
    
    Args:
        signal_dto: StrategySignalDTO object
        
    Returns:
        Strategy signal context as dictionary
    """
    return {
        "symbol": signal_dto.symbol,
        "signal_type": signal_dto.signal_type,
        "strength": signal_dto.strength,
        "confidence": signal_dto.confidence,
        "strategy_name": signal_dto.strategy_name,
        "signal_source": signal_dto.signal_source,
        "metadata": signal_dto.metadata,
        "correlation_id": signal_dto.correlation_id,
        "created_at": signal_dto.created_at,
    }


def strategy_signal_to_dto(
    signal: dict[str, Any],
    correlation_id: str | None = None,
) -> StrategySignalDTO:
    """Convert strategy signal dictionary to StrategySignalDTO.
    
    Args:
        signal: Strategy signal as dictionary
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        StrategySignalDTO object
    """
    from decimal import Decimal
    from datetime import datetime, UTC
    
    return StrategySignalDTO(
        symbol=signal.get("symbol", ""),
        signal_type=signal.get("signal_type", "unknown"),
        strength=Decimal(str(signal.get("strength", 0.0))),
        confidence=Decimal(str(signal.get("confidence", 0.0))),
        strategy_name=signal.get("strategy_name", "unknown"),
        signal_source=signal.get("signal_source", "unknown"),
        metadata=signal.get("metadata", {}),
        correlation_id=correlation_id or signal.get("correlation_id"),
        created_at=signal.get("created_at") or datetime.now(UTC),
    )


def validate_signal_conversion(
    original_signal: dict[str, Any],
    converted_dto: StrategySignalDTO,
) -> bool:
    """Validate that signal conversion was successful.
    
    Args:
        original_signal: Original signal dictionary
        converted_dto: Converted StrategySignalDTO
        
    Returns:
        True if conversion is valid, False otherwise
    """
    try:
        # Check required fields match
        if original_signal.get("symbol") != converted_dto.symbol:
            return False
        if original_signal.get("signal_type") != converted_dto.signal_type:
            return False
        if original_signal.get("strategy_name") != converted_dto.strategy_name:
            return False
            
        # Check numeric fields are close (accounting for decimal conversion)
        original_strength = float(original_signal.get("strength", 0.0))
        converted_strength = float(converted_dto.strength)
        if abs(original_strength - converted_strength) > 1e-6:
            return False
            
        original_confidence = float(original_signal.get("confidence", 0.0))
        converted_confidence = float(converted_dto.confidence)
        if abs(original_confidence - converted_confidence) > 1e-6:
            return False
            
        return True
    except (ValueError, TypeError, AttributeError):
        return False