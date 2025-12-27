"""Business Unit: shared | Status: current.

Strategy type enumeration for orchestration.

Central definition of strategy types used across the orchestration layer.
"""

from enum import Enum


class StrategyType(Enum):
    """Enumeration of available strategy types."""

    NUCLEAR = "nuclear"
    TECL = "tecl"
    KLM = "klm"
    DSL = "dsl"


__all__ = ["StrategyType"]
