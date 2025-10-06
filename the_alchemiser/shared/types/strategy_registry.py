"""Business Unit: shared | Status: current.

Strategy registry bridge for migration.

Provides compatibility types and default allocations during migration to strategy_v2.
"""

from the_alchemiser.shared.types.strategy_types import StrategyType


class StrategyRegistry:
    """Strategy registry bridge for migration.
    
    Provides compatibility API during migration to strategy_v2.
    Currently configured for DSL-only operation phase.
    
    Example:
        >>> allocations = StrategyRegistry.get_default_allocations()
        >>> assert StrategyType.DSL in allocations
        >>> enabled = StrategyRegistry.is_strategy_enabled(StrategyType.DSL)
        >>> assert enabled is True

    """

    @staticmethod
    def get_default_allocations() -> dict[StrategyType, float]:
        """Get default strategy allocations.
        
        Returns the default allocation weights for each strategy type.
        In the current DSL-only phase, only DSL engine is active with full allocation.
        
        Returns:
            Dictionary mapping StrategyType to allocation weight (0.0 to 1.0).
            Allocation weights sum to 1.0 (100% of portfolio).
            
        Example:
            >>> allocations = StrategyRegistry.get_default_allocations()
            >>> assert allocations[StrategyType.DSL] == 1.0
            >>> assert sum(allocations.values()) == 1.0

        """
        return {
            # For this DSL-focused phase, we only use DSL engine
            StrategyType.DSL: 1.0,
        }

    @staticmethod
    def is_strategy_enabled(strategy_type: StrategyType) -> bool:
        """Check if a strategy is enabled.
        
        Args:
            strategy_type: The strategy type to check (StrategyType enum member).
        
        Returns:
            Always True in the current DSL-only phase. All strategies are
            considered enabled for API compatibility during migration.
            
        Note:
            Parameter currently unused but retained for API compatibility.
            Future versions may implement selective strategy enablement.
            
        Example:
            >>> StrategyRegistry.is_strategy_enabled(StrategyType.DSL)
            True
            >>> StrategyRegistry.is_strategy_enabled(StrategyType.NUCLEAR)
            True

        """
        return True
