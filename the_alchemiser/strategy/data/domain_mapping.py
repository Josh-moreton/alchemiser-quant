"""Business Unit: strategy & signal generation; Status: current.

Mapping utilities between strategy DTOs and domain objects.

This module provides conversion functions between TypedDict DTOs (used at interface
boundaries) and domain value objects/models (used in business logic).
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.value_objects.core_types import (
    StrategyPositionData as StrategyPositionDTO,
)
from the_alchemiser.shared.value_objects.core_types import (
    StrategySignal as StrategySignalDTO,
)
# Updated to use canonical types
from the_alchemiser.strategy.types.strategy import (
    StrategyPosition,
    StrategySignal,
)
from the_alchemiser.strategy.registry.strategy_registry import StrategyType


def dto_to_strategy_signal_model(dto: StrategySignalDTO) -> StrategySignal:
    """Convert StrategySignal DTO to domain model."""
    return StrategySignal.from_dto(dto)


def strategy_signal_model_to_dto(model: StrategySignal) -> StrategySignalDTO:
    """Convert domain model to StrategySignal DTO."""
    return model.to_dto()


def dto_to_strategy_position_model(dto: StrategyPositionDTO) -> StrategyPosition:
    """Convert StrategyPositionData DTO to domain model."""
    return StrategyPosition.from_dto(dto)


def strategy_position_model_to_dto(model: StrategyPosition) -> StrategyPositionDTO:
    """Convert domain model to StrategyPositionData DTO."""
    return model.to_dto()


def map_strategy_signals_to_models(
    signals_dict: dict[StrategyType, StrategySignalDTO],
) -> dict[StrategyType, StrategySignal]:
    """Convert dict of StrategySignal DTOs to domain models."""
    return {
        strategy_type: dto_to_strategy_signal_model(signal_dto)
        for strategy_type, signal_dto in signals_dict.items()
    }


def map_strategy_models_to_dtos(
    models_dict: dict[StrategyType, StrategySignal],
) -> dict[StrategyType, StrategySignalDTO]:
    """Convert dict of domain models to StrategySignal DTOs."""
    return {
        strategy_type: strategy_signal_model_to_dto(model)
        for strategy_type, model in models_dict.items()
    }


def map_strategy_positions_to_models(
    positions_dict: dict[str, StrategyPositionDTO],
) -> dict[str, StrategyPosition]:
    """Convert dict of StrategyPositionData DTOs to domain models."""
    return {
        key: dto_to_strategy_position_model(position_dto)
        for key, position_dto in positions_dict.items()
    }


def map_strategy_position_models_to_dtos(
    models_dict: dict[str, StrategyPosition],
) -> dict[str, StrategyPositionDTO]:
    """Convert dict of domain models to StrategyPositionData DTOs."""
    return {key: strategy_position_model_to_dto(model) for key, model in models_dict.items()}


# Legacy signal normalization (for backward compatibility)
def normalize_legacy_signal_dict(legacy_signal: dict[str, Any]) -> StrategySignalDTO:
    """Normalize a legacy signal dict to StrategySignal DTO format.

    This function provides the same normalization as the existing
    strategy_signal_mapping module for backward compatibility.
    """
    from the_alchemiser.strategy.mappers.strategy_signal_mapping import (
        legacy_signal_to_typed,
    )

    return legacy_signal_to_typed(legacy_signal)
