"""Symbol classification for strategy attribution."""

from the_alchemiser.domain.registry import StrategyType


class SymbolClassifier:
    """Classifies symbols to their primary strategy.

    This class contains the business rules for determining which strategy
    is responsible for each symbol in the portfolio.
    """

    NUCLEAR_SYMBOLS = frozenset(
        ["SMR", "LEU", "OKLO", "NLR", "BWXT", "PSQ", "SQQQ", "UUP", "UVXY", "BTAL"]
    )

    TECL_SYMBOLS = frozenset(["TECL", "TQQQ", "UPRO", "BIL", "QQQ"])

    def classify_symbol(self, symbol: str) -> StrategyType:
        """Classify symbol to its primary strategy.

        Args:
            symbol: The symbol to classify

        Returns:
            StrategyType for the symbol's primary strategy
        """
        if symbol in self.NUCLEAR_SYMBOLS:
            return StrategyType.NUCLEAR
        elif symbol in self.TECL_SYMBOLS:
            return StrategyType.TECL
        else:
            return StrategyType.NUCLEAR  # Default fallback

    def is_nuclear_symbol(self, symbol: str) -> bool:
        """Check if symbol belongs to Nuclear strategy."""
        return symbol in self.NUCLEAR_SYMBOLS

    def is_tecl_symbol(self, symbol: str) -> bool:
        """Check if symbol belongs to TECL strategy."""
        return symbol in self.TECL_SYMBOLS

    def get_symbols_for_strategy(self, strategy: StrategyType) -> frozenset[str]:
        """Get all symbols for a given strategy.

        Args:
            strategy: The strategy type to get symbols for

        Returns:
            Frozenset of symbols for the strategy
        """
        if strategy == StrategyType.NUCLEAR:
            return self.NUCLEAR_SYMBOLS
        elif strategy == StrategyType.TECL:
            return self.TECL_SYMBOLS
        else:
            return frozenset()

    def classify_symbols(self, symbols: list[str]) -> dict[str, StrategyType]:
        """Classify multiple symbols at once.

        Args:
            symbols: List of symbols to classify

        Returns:
            Dictionary mapping symbols to their StrategyType
        """
        return {symbol: self.classify_symbol(symbol) for symbol in symbols}
