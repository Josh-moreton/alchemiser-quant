"""Business Unit: shared | Status: current.

Strategy registry bridge for migration.

Provides compatibility types and default allocations during migration to strategy_v2.
"""

from the_alchemiser.shared.types.strategy_types import StrategyType


class StrategyRegistry:
    """Strategy registry bridge for migration."""

    @staticmethod
    def get_default_allocations() -> dict[StrategyType, float]:
        """Get default strategy allocations."""
        return {
            # For this DSL-focused PR, we only use DSL engine to test integration
            StrategyType.DSL: 1.0,
        }

    @staticmethod
    def is_strategy_enabled(_strategy_type: StrategyType) -> bool:
        """Check if a strategy is enabled.

        Always returns True (all strategies enabled during DSL-only phase).
        Parameter retained for API compatibility.
        """
        return True
