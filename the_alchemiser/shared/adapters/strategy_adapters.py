#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy signal adapters for converting between strategy domain objects and DTOs.

Provides conversion functions between internal StrategySignal objects and
StrategySignalDTO for inter-module communication.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO


def strategy_signal_to_dto(
    signal: Any,  # StrategySignal - avoid import to prevent circular dependency
    correlation_id: str | None = None,
    causation_id: str | None = None,
    strategy_name: str | None = None,
) -> StrategySignalDTO:
    """Convert internal StrategySignal to StrategySignalDTO.

    Args:
        signal: Internal StrategySignal domain object
        correlation_id: Optional correlation ID, generated if not provided
        causation_id: Optional causation ID, uses correlation_id if not provided
        strategy_name: Optional strategy name override

    Returns:
        StrategySignalDTO instance

    Raises:
        ValueError: If signal data is invalid

    """
    # Generate IDs if not provided
    if correlation_id is None:
        correlation_id = f"signal_{uuid.uuid4().hex[:12]}"
    if causation_id is None:
        causation_id = correlation_id

    # Extract symbol string from Symbol value object or string
    symbol_str = str(signal.symbol) if hasattr(signal.symbol, "__str__") else signal.symbol

    # Extract confidence value - could be Confidence object or Decimal/float
    confidence_value = signal.confidence
    if hasattr(confidence_value, "value"):
        confidence_decimal = Decimal(str(confidence_value.value))
    else:
        confidence_decimal = Decimal(str(confidence_value))

    # Extract allocation weight from Percentage or Decimal
    allocation_weight = None
    if hasattr(signal, "target_allocation") and signal.target_allocation is not None:
        if hasattr(signal.target_allocation, "value"):
            allocation_weight = Decimal(str(signal.target_allocation.value))
        else:
            allocation_weight = Decimal(str(signal.target_allocation))

    # Extract timestamp
    timestamp = signal.timestamp if hasattr(signal, "timestamp") else datetime.now(UTC)

    return StrategySignalDTO(
        correlation_id=correlation_id,
        causation_id=causation_id,
        timestamp=timestamp,
        symbol=symbol_str,
        action=str(signal.action).upper(),
        confidence=confidence_decimal,
        reasoning=signal.reasoning if hasattr(signal, "reasoning") else "No reasoning provided",
        strategy_name=strategy_name,
        allocation_weight=allocation_weight,
    )


def dto_to_strategy_signal_context(dto: StrategySignalDTO) -> dict[str, Any]:
    """Convert StrategySignalDTO to context dict for strategy modules.

    This provides a way for strategy modules to consume signals from other
    strategies without creating direct dependencies on strategy domain objects.

    Args:
        dto: StrategySignalDTO instance

    Returns:
        Dictionary with signal context data

    """
    return {
        "symbol": dto.symbol,
        "action": dto.action,
        "confidence": float(dto.confidence),
        "reasoning": dto.reasoning,
        "timestamp": dto.timestamp,
        "strategy_name": dto.strategy_name,
        "allocation_weight": float(dto.allocation_weight) if dto.allocation_weight else None,
        "correlation_id": dto.correlation_id,
        "causation_id": dto.causation_id,
        "metadata": dto.metadata,
    }


def batch_strategy_signals_to_dtos(
    signals: list[Any],  # list[StrategySignal]
    base_correlation_id: str | None = None,
    strategy_name: str | None = None,
) -> list[StrategySignalDTO]:
    """Convert a batch of strategy signals to DTOs.

    Args:
        signals: List of internal StrategySignal objects
        base_correlation_id: Base correlation ID for the batch
        strategy_name: Strategy name for all signals

    Returns:
        List of StrategySignalDTO instances

    """
    if base_correlation_id is None:
        base_correlation_id = f"batch_{uuid.uuid4().hex[:12]}"

    dtos = []
    for i, signal in enumerate(signals):
        # Create unique correlation ID for each signal in the batch
        signal_correlation_id = f"{base_correlation_id}_{i:03d}"
        dto = strategy_signal_to_dto(
            signal,
            correlation_id=signal_correlation_id,
            causation_id=base_correlation_id,  # All signals share the same causation
            strategy_name=strategy_name,
        )
        dtos.append(dto)

    return dtos


def validate_signal_conversion(
    original_signal: Any,  # StrategySignal
    converted_dto: StrategySignalDTO,
) -> bool:
    """Validate that signal conversion preserves semantic meaning.

    Args:
        original_signal: Original StrategySignal object
        converted_dto: Converted StrategySignalDTO

    Returns:
        True if conversion is valid, False otherwise

    """
    try:
        # Check symbol match
        original_symbol = (
            str(original_signal.symbol)
            if hasattr(original_signal.symbol, "__str__")
            else original_signal.symbol
        )
        if original_symbol.upper() != converted_dto.symbol.upper():
            return False

        # Check action match
        if str(original_signal.action).upper() != converted_dto.action.upper():
            return False

        # Check confidence roughly equal (within tolerance for Decimal conversion)
        original_confidence = original_signal.confidence
        if hasattr(original_confidence, "value"):
            original_confidence = original_confidence.value

        confidence_diff = abs(float(converted_dto.confidence) - float(original_confidence))
        if confidence_diff > 0.001:  # Allow small floating point differences
            return False

        # Check reasoning if present
        if (
            hasattr(original_signal, "reasoning")
            and original_signal.reasoning != converted_dto.reasoning
        ):
            return False

        return True

    except Exception:
        # If any validation fails due to missing attributes or type issues,
        # consider it an invalid conversion
        return False
