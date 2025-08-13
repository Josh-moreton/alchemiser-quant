"""Strategy attribution engine for determining symbol ownership."""

from the_alchemiser.domain.portfolio.strategy_attribution.symbol_classifier import SymbolClassifier
from the_alchemiser.domain.registry import StrategyType


class StrategyAttributionEngine:
    """Determines which strategy is responsible for each symbol.

    This engine uses both explicit strategy attribution data and fallback
    classification rules to determine the primary strategy for each symbol.
    """

    def __init__(self, symbol_classifier: SymbolClassifier | None = None):
        """Initialize the attribution engine.

        Args:
            symbol_classifier: Optional classifier, creates default if not provided
        """
        self._classifier = symbol_classifier or SymbolClassifier()

    def get_primary_strategy(
        self,
        symbol: str,
        strategy_attribution: dict[str, list[StrategyType]] | None = None
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

        return self._classifier.classify_symbol(symbol)

    def get_all_strategies_for_symbol(
        self,
        symbol: str,
        strategy_attribution: dict[str, list[StrategyType]] | None = None
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
        return [self._classifier.classify_symbol(symbol)]

    def group_symbols_by_strategy(
        self,
        symbols: list[str],
        strategy_attribution: dict[str, list[StrategyType]] | None = None
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

    def get_symbols_for_strategy(
        self,
        strategy: StrategyType,
        symbols: list[str],
        strategy_attribution: dict[str, list[StrategyType]] | None = None
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
            symbol for symbol in symbols
            if self.get_primary_strategy(symbol, strategy_attribution) == strategy
        ]
