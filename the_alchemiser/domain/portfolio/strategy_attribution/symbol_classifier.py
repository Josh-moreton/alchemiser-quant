"""Business Unit: strategy & signal generation; Status: current.

Symbol classification for strategy attribution.
"""

from __future__ import annotations


class SymbolClassifier:
    """Classifies symbols to their primary strategy.

    This class contains the business rules for determining which strategy
    is responsible for each symbol in the portfolio.
    """

    # Symbol mappings for different categories
    LARGE_CAP_SYMBOLS = frozenset(
        [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "NVDA",
            "META",
            "TSLA",
            "JPM",
            "BAC",
            "WFC",
            "JNJ",
            "PG",
            "KO",
            "V",
            "MA",
            "HD",
            "DIS",
            "NFLX",
            "CRM",
            "ADBE",
        ]
    )

    MID_CAP_SYMBOLS = frozenset(
        ["ROKU", "SNAP", "PINS", "SPOT", "TWLO", "SQ", "PYPL", "ZM", "DOCU", "OKTA"]
    )

    SMALL_CAP_SYMBOLS = frozenset(
        ["RBLX", "HOOD", "COIN", "PLTR", "SNOW", "DKNG", "AFRM", "SOFI", "RIVN", "LCID"]
    )

    CRYPTO_SYMBOLS = frozenset(
        ["BTC", "ETH", "ADA", "SOL", "DOGE", "MATIC", "DOT", "AVAX", "LINK", "UNI"]
    )

    BOND_SYMBOLS = frozenset(
        ["TLT", "IEF", "SHY", "LQD", "HYG", "AGG", "BND", "VCIT", "VGIT", "EMB"]
    )

    INDEX_FUND_SYMBOLS = frozenset(
        ["SPY", "QQQ", "IWM", "VTI", "VOO", "VEA", "VWO", "EFA", "EEM", "IEFA"]
    )

    # Legacy nuclear and TECL symbols
    NUCLEAR_SYMBOLS = frozenset(
        ["SMR", "LEU", "OKLO", "NLR", "BWXT", "PSQ", "SQQQ", "UUP", "UVXY", "BTAL"]
    )

    TECL_SYMBOLS = frozenset(["TECL", "TQQQ", "UPRO", "BIL", "QQQ"])

    def classify_symbol(self, symbol: str | None) -> str:
        """Classify symbol to its primary strategy.

        Args:
            symbol: The symbol to classify (case insensitive)

        Returns:
            String identifier for the symbol's primary strategy

        """
        if symbol is None:
            return "unknown"

        symbol_upper = symbol.upper()

        # Check legacy nuclear/TECL first for backwards compatibility
        if symbol_upper in self.NUCLEAR_SYMBOLS:
            return "nuclear"
        if symbol_upper in self.TECL_SYMBOLS:
            return "tecl"
        # Check new categorizations
        if symbol_upper in self.LARGE_CAP_SYMBOLS:
            return "large_cap"
        if symbol_upper in self.MID_CAP_SYMBOLS:
            return "mid_cap"
        if symbol_upper in self.SMALL_CAP_SYMBOLS:
            return "small_cap"
        if symbol_upper in self.CRYPTO_SYMBOLS:
            return "crypto"
        if symbol_upper in self.BOND_SYMBOLS:
            return "bonds"
        if symbol_upper in self.INDEX_FUND_SYMBOLS:
            return "index_funds"
        return "unknown"

    def is_nuclear_symbol(self, symbol: str) -> bool:
        """Check if symbol belongs to Nuclear strategy."""
        return symbol.upper() in self.NUCLEAR_SYMBOLS if symbol else False

    def is_tecl_symbol(self, symbol: str) -> bool:
        """Check if symbol belongs to TECL strategy."""
        return symbol.upper() in self.TECL_SYMBOLS if symbol else False

    def is_equity_strategy(self, strategy: str) -> bool:
        """Check if a strategy is equity-based.

        Args:
            strategy: Strategy name to check

        Returns:
            True if the strategy is equity-based, False otherwise

        """
        equity_strategies = {"large_cap", "mid_cap", "small_cap"}
        return strategy in equity_strategies

    def get_symbols_for_strategy(self, strategy: str) -> frozenset[str]:
        """Get all symbols for a given strategy.

        Args:
            strategy: The strategy type to get symbols for

        Returns:
            Frozenset of symbols for the strategy

        """
        strategy_mapping = {
            "nuclear": self.NUCLEAR_SYMBOLS,
            "tecl": self.TECL_SYMBOLS,
            "large_cap": self.LARGE_CAP_SYMBOLS,
            "mid_cap": self.MID_CAP_SYMBOLS,
            "small_cap": self.SMALL_CAP_SYMBOLS,
            "crypto": self.CRYPTO_SYMBOLS,
            "bonds": self.BOND_SYMBOLS,
            "index_funds": self.INDEX_FUND_SYMBOLS,
        }
        return strategy_mapping.get(strategy, frozenset())

    def get_all_strategies(self) -> set[str]:
        """Get all available strategies.

        Returns:
            Set of all available strategy names

        """
        return {
            "large_cap",
            "mid_cap",
            "small_cap",
            "crypto",
            "bonds",
            "index_funds",
            "nuclear",
            "tecl",
            "unknown",
        }

    def get_strategy_description(self, strategy: str) -> str:
        """Get human-readable description of a strategy.

        Args:
            strategy: Strategy name

        Returns:
            Human-readable description of the strategy

        """
        descriptions = {
            "large_cap": "Large cap stocks (market cap > $10B)",
            "mid_cap": "Mid cap stocks (market cap $2B - $10B)",
            "small_cap": "Small cap stocks (market cap < $2B)",
            "crypto": "Cryptocurrency assets",
            "bonds": "Fixed income securities",
            "index_funds": "Broad market index funds",
            "nuclear": "Nuclear energy strategy symbols",
            "tecl": "Technology leveraged strategy symbols",
            "unknown": "Unclassified securities",
        }
        return descriptions.get(strategy, "Unknown strategy")

    def classify_symbols(self, symbols: list[str]) -> dict[str, str]:
        """Classify multiple symbols at once.

        Args:
            symbols: List of symbols to classify

        Returns:
            Dictionary mapping symbols to their strategy names

        """
        return {symbol: self.classify_symbol(symbol) for symbol in symbols}
