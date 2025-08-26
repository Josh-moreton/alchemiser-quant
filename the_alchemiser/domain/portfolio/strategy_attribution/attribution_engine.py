"""Strategy attribution engine for determining symbol ownership."""

from decimal import Decimal
from typing import Any

from the_alchemiser.domain.portfolio.strategy_attribution.symbol_classifier import (
    SymbolClassifier,
)
from the_alchemiser.domain.registry import StrategyType


class StrategyAttributionEngine:
    """Determines which strategy is responsible for each symbol.

    This engine uses both explicit strategy attribution data and fallback
    classification rules to determine the primary strategy for each symbol.
    """

    def __init__(self, symbol_classifier: SymbolClassifier | None = None) -> None:
        """Initialize the attribution engine.

        Args:
            symbol_classifier: Optional classifier, creates default if not provided

        """
        self.classifier = symbol_classifier or SymbolClassifier()

    def classify_symbol(self, symbol: str) -> str:
        """Classify a symbol to its primary strategy.

        Args:
            symbol: The symbol to classify

        Returns:
            String identifier for the symbol's primary strategy

        """
        return self.classifier.classify_symbol(symbol)

    def get_primary_strategy(
        self,
        symbol: str,
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> StrategyType:
        """Determine the primary strategy responsible for a symbol.

        Args:
            symbol: The symbol to determine strategy for
            strategy_attribution: Optional explicit attribution mapping

        Returns:
            StrategyType for the primary strategy

        """
        if strategy_attribution and symbol in strategy_attribution:
            strategies = strategy_attribution[symbol]
            if strategies:
                return strategies[0]  # Use first strategy as primary

        # Convert string classification back to StrategyType for backwards compatibility
        classification = self.classifier.classify_symbol(symbol)
        if classification == "nuclear":
            return StrategyType.NUCLEAR
        if classification == "tecl":
            return StrategyType.TECL
        return StrategyType.NUCLEAR  # Default fallback

    def get_all_strategies_for_symbol(
        self,
        symbol: str,
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[StrategyType]:
        """Get all strategies that have an interest in a symbol.

        Args:
            symbol: The symbol to get strategies for
            strategy_attribution: Optional explicit attribution mapping

        Returns:
            List of StrategyType objects interested in the symbol

        """
        if strategy_attribution and symbol in strategy_attribution:
            return strategy_attribution[symbol]

        # Fallback to single strategy from classifier
        return [self.get_primary_strategy(symbol, strategy_attribution)]

    def group_symbols_by_strategy(
        self,
        symbols: list[str],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> dict[StrategyType, list[str]]:
        """Group symbols by their primary strategy.

        Args:
            symbols: List of symbols to group
            strategy_attribution: Optional explicit attribution mapping

        Returns:
            Dictionary mapping StrategyType to list of symbols

        """
        strategy_groups: dict[StrategyType, list[str]] = {}

        for symbol in symbols:
            strategy = self.get_primary_strategy(symbol, strategy_attribution)
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(symbol)

        return strategy_groups

    def group_positions_by_strategy(
        self, positions: dict[str, Decimal]
    ) -> dict[str, dict[str, Decimal]]:
        """Group position values by their classified strategy.

        Args:
            positions: Dictionary mapping symbols to position values

        Returns:
            Dictionary mapping strategy names to symbol-value dictionaries

        """
        strategy_groups: dict[str, dict[str, Decimal]] = {}

        for symbol, value in positions.items():
            strategy = self.classifier.classify_symbol(symbol)
            if strategy not in strategy_groups:
                strategy_groups[strategy] = {}
            strategy_groups[strategy][symbol] = value

        return strategy_groups

    def get_symbols_for_strategy(
        self,
        strategy: StrategyType,
        symbols: list[str],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[str]:
        """Get all symbols that belong to a specific strategy.

        Args:
            strategy: The strategy to get symbols for
            symbols: List of all symbols to check
            strategy_attribution: Optional explicit attribution mapping

        Returns:
            List of symbols belonging to the strategy

        """
        return [
            symbol
            for symbol in symbols
            if self.get_primary_strategy(symbol, strategy_attribution) == strategy
        ]

    def get_strategy_exposures(
        self, positions: dict[str, Decimal], portfolio_value: Decimal
    ) -> dict[str, dict[str, Any]]:
        """Calculate strategy exposures from position values.

        Args:
            positions: Dictionary mapping symbols to position values
            portfolio_value: Total portfolio value

        Returns:
            Dictionary mapping strategy names to exposure information

        """
        # portfolio_value is Decimal; direct comparison acceptable
        if portfolio_value == Decimal("0"):
            return {}

        strategy_groups = self.group_positions_by_strategy(positions)
        exposures = {}

        for strategy, strategy_positions in strategy_groups.items():
            strategy_value = sum(strategy_positions.values())
            allocation_percentage = strategy_value / portfolio_value

            exposures[strategy] = {
                "total_value": strategy_value,
                "allocation_percentage": allocation_percentage,
                "position_count": len(strategy_positions),
                "positions": strategy_positions,
            }

        return exposures

    def calculate_strategy_allocations(
        self, positions: dict[str, Decimal], portfolio_value: Decimal
    ) -> dict[str, Decimal]:
        """Calculate allocation percentages by strategy.

        Args:
            positions: Dictionary mapping symbols to position values
            portfolio_value: Total portfolio value

        Returns:
            Dictionary mapping strategy names to allocation percentages

        """
        if portfolio_value == Decimal("0"):
            return {}

        strategy_groups = self.group_positions_by_strategy(positions)
        allocations = {}

        for strategy, strategy_positions in strategy_groups.items():
            strategy_value = sum(strategy_positions.values())
            allocations[strategy] = strategy_value / portfolio_value

        return allocations
