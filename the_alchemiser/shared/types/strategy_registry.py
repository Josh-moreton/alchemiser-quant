"""Business Unit: shared | Status: current

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
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.3,
            StrategyType.KLM: 0.2,
        }
    
    @staticmethod
    def is_strategy_enabled(strategy_type: StrategyType) -> bool:
        """Check if strategy is enabled."""
        return True  # All strategies enabled by default