"""
Symbol-Specific Lookback Calculator

This utility calculates the minimum required historical data lookback period for each symbol
based on the technical indicators actually used by all trading strategies. This optimizes
data fetching by only requesting the necessary amount of historical data for each symbol.

Key Benefits:
- Reduces API calls and data transfer
- Faster backtesting with symbol-specific data requirements
- More efficient memory usage
- Prevents over-fetching data for symbols that only need basic indicators

Strategy Analysis:
- Nuclear Strategy: RSI(10,20), MA(20,200), MA_return(90), Cumulative_return(60)
- TECL Strategy: RSI(9,10), MA(200)
- KLM Strategy: RSI(10,20,21,70), MA(3,200), MA_return(20), Stdev_return(5,6)
"""

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class IndicatorRequirement:
    """Represents an indicator and its data requirements"""

    name: str
    window: int
    buffer_days: int = 20  # Extra days for calculation stability


class SymbolLookbackCalculator:
    """Calculate symbol-specific lookback requirements based on strategy indicator usage"""

    def __init__(self):
        self.logger = logging.getLogger("SymbolLookback")

        # Define common indicator requirements
        self._indicator_requirements = {
            "rsi_9": IndicatorRequirement("rsi", 9, 20),
            "rsi_10": IndicatorRequirement("rsi", 10, 20),
            "rsi_15": IndicatorRequirement("rsi", 15, 20),
            "rsi_20": IndicatorRequirement("rsi", 20, 20),
            "rsi_21": IndicatorRequirement("rsi", 21, 20),
            "rsi_70": IndicatorRequirement("rsi", 70, 30),
            "ma_3": IndicatorRequirement("ma", 3, 5),
            "ma_20": IndicatorRequirement("ma", 20, 10),
            "ma_200": IndicatorRequirement("ma", 200, 20),
            "ma_return_90": IndicatorRequirement("ma_return", 90, 30),
            "cum_return_60": IndicatorRequirement("cum_return", 60, 10),
            "stdev_return": IndicatorRequirement("stdev_return", 5, 5),
        }

        # STRATEGY-SPECIFIC SYMBOL-INDICATOR MAPPINGS (based on actual code analysis)

        # Nuclear Strategy: SPY only for market regime, specific symbols for signals
        self._nuclear_symbol_indicators = {
            "SPY": {"ma_200", "rsi_10"},  # Market regime + overbought detection
            "TQQQ": {"rsi_10"},  # Oversold detection
            "UPRO": set(),  # Just price (no indicators)
            "UVXY": set(),  # Just price (target symbol)
            "BTAL": set(),  # Just price (target symbol)
            "VOX": {"rsi_10"},  # Overbought detection
            "IOO": {"rsi_10"},  # Overbought detection
            "VTV": {"rsi_10"},  # Overbought detection
            "XLF": {"rsi_10"},  # Overbought detection
            # Other nuclear symbols use basic indicators
            "QQQ": {"rsi_10"},
            "SQQQ": {"rsi_10"},
            "PSQ": set(),
            "TLT": set(),
            "IEF": set(),
            "SMR": set(),  # Nuclear energy stocks (price only)
            "BWXT": set(),
            "LEU": set(),
            "EXC": set(),
            "NLR": set(),
            "OKLO": set(),
        }

        # TECL Strategy: SPY for market regime, specific indicators per symbol role
        self._tecl_symbol_indicators = {
            "SPY": {"ma_200", "rsi_10"},  # Market regime detection only
            "TQQQ": {"rsi_10"},  # Overbought/oversold detection
            "SPXL": {"rsi_10"},  # Oversold detection
            "UVXY": {"rsi_10"},  # Volatility spike detection
            "XLK": {"rsi_10"},  # KMLM switcher technology sector
            "KMLM": {"rsi_10"},  # KMLM switcher materials sector
            "SQQQ": {"rsi_9"},  # Bond vs short selection
            "BSV": {"rsi_9"},  # Bond vs short selection
            "BIL": set(),  # Cash equivalent (no indicators)
            "TECL": set(),  # Target symbol (no indicators)
        }

        # KLM Strategy: Complex system - only map symbols that actually use specific indicators
        self._klm_symbol_indicators = {
            # Market regime and core logic
            "SPY": {"ma_200", "ma_20", "ma_3", "rsi_10", "rsi_21", "rsi_70"},  # Heavy usage
            "TQQQ": {"rsi_10", "rsi_20", "rsi_21", "ma_20"},  # Multi-variant checks
            "SPXL": {"rsi_10", "rsi_20", "rsi_21"},  # RSI checks
            "SOXL": {"rsi_10", "rsi_20", "rsi_21"},  # RSI checks
            "TECL": {"rsi_10", "rsi_20", "rsi_21"},  # RSI checks
            "UVXY": {"rsi_10", "rsi_21"},  # Volatility detection
            "VXX": {"rsi_10", "rsi_21"},  # Volatility detection
            "VIXM": {"rsi_10", "rsi_21"},  # Volatility detection
            "KMLM": {"rsi_10", "rsi_15"},  # Materials detection
            "QQQ": {"rsi_15"},  # Comparison logic
            "AGG": {"rsi_15"},  # Bond comparison
            # Defensive/Cash positions
            "BIL": set(),  # Cash (no indicators)
            "BSV": {"rsi_9"},  # Bond selection
            "SQQQ": {"rsi_9"},  # Short selection
            # Additional symbols with basic RSI
            "XLK": {"rsi_10"},
            "XLF": {"rsi_10"},
            "XLP": {"rsi_10"},
            "XLY": {"rsi_10"},
            "TLT": {"rsi_10"},
            "SSO": {"rsi_10"},
            "FNGU": {"rsi_10"},
            "LABU": {"rsi_10"},
            "LABD": {"rsi_10"},
            "RETL": {"rsi_10"},
            "FTLS": {"rsi_10"},
            "FAS": {"rsi_10"},
            "BTAL": {"rsi_10"},
            "SPLV": {"rsi_10"},
            "QQQE": {"rsi_10"},
            "VOOG": {"rsi_10"},
            "VOOV": {"rsi_10"},
            "VTV": {"rsi_10"},
            "IOO": {"rsi_10"},
            "VOX": {"rsi_10"},
            "TZA": {"rsi_10"},
            "UUP": {"rsi_10"},
            "SVXY": {"rsi_10"},
            "SVIX": {"rsi_10"},
            "VIXY": {"rsi_10"},
            "BND": {"rsi_10"},
        }

    def get_symbol_lookback_days(self, symbol: str, strategies: list[str] | None = None) -> int:
        """
        Calculate the minimum lookback days required for a specific symbol.

        Args:
            symbol: The symbol to calculate lookback for
            strategies: List of strategies to consider ('nuclear', 'tecl', 'klm').
                       If None, considers all strategies.

        Returns:
            int: Minimum lookback days required for this symbol
        """
        if strategies is None:
            strategies = ["nuclear", "tecl", "klm"]

        max_lookback = 0
        used_indicators = set()

        # Check each strategy for this symbol's specific indicators
        for strategy in strategies:
            symbol_indicators = self._get_symbol_indicators_for_strategy(symbol, strategy)

            for indicator_name in symbol_indicators:
                if indicator_name in self._indicator_requirements:
                    requirement = self._indicator_requirements[indicator_name]
                    lookback_needed = requirement.window + requirement.buffer_days
                    max_lookback = max(max_lookback, lookback_needed)
                    used_indicators.add(f"{strategy}:{indicator_name}")

        # If symbol not used in any strategy, provide minimal lookback
        if max_lookback == 0:
            max_lookback = 30  # 30 days for basic price data

        self.logger.debug(
            f"Symbol {symbol}: {max_lookback} days lookback "
            f"(indicators: {', '.join(sorted(used_indicators))})"
        )

        return max_lookback

    def get_all_symbols_lookback_map(self, strategies: list[str] | None = None) -> dict[str, int]:
        """
        Get a complete mapping of all symbols to their required lookback days.

        Args:
            strategies: List of strategies to consider. If None, considers all.

        Returns:
            Dict mapping symbol -> lookback_days
        """
        if strategies is None:
            strategies = ["nuclear", "tecl", "klm"]

        # Get all unique symbols across strategies
        all_symbols = set()
        for strategy in strategies:
            all_symbols.update(self._get_strategy_symbols(strategy))

        lookback_map = {}
        for symbol in sorted(all_symbols):
            lookback_map[symbol] = self.get_symbol_lookback_days(symbol, strategies)

        self.logger.info(
            f"Generated lookback map for {len(lookback_map)} symbols "
            f"across strategies: {', '.join(strategies)}"
        )

        return lookback_map

    def _get_symbol_indicators_for_strategy(self, symbol: str, strategy: str) -> set[str]:
        """Get the specific indicators used for a symbol in a strategy"""
        if strategy == "nuclear":
            return self._nuclear_symbol_indicators.get(symbol, set())
        elif strategy == "tecl":
            return self._tecl_symbol_indicators.get(symbol, set())
        elif strategy == "klm":
            return self._klm_symbol_indicators.get(symbol, set())
        else:
            return set()

    def _get_strategy_symbols(self, strategy: str) -> set[str]:
        """Get all symbols used by a strategy"""
        if strategy == "nuclear":
            return set(self._nuclear_symbol_indicators.keys())
        elif strategy == "tecl":
            return set(self._tecl_symbol_indicators.keys())
        elif strategy == "klm":
            return set(self._klm_symbol_indicators.keys())
        else:
            return set()

    def _get_strategy_indicators(self, strategy: str) -> dict[str, IndicatorRequirement]:
        """Get all indicators used by a strategy (deprecated - use symbol-specific version)"""
        # This method is deprecated but kept for compatibility
        all_indicators = set()
        strategy_symbols = self._get_strategy_symbols(strategy)

        for symbol in strategy_symbols:
            symbol_indicators = self._get_symbol_indicators_for_strategy(symbol, strategy)
            all_indicators.update(symbol_indicators)

        return {
            name: self._indicator_requirements[name]
            for name in all_indicators
            if name in self._indicator_requirements
        }

    def get_lookback_summary(self, strategies: list[str] | None = None) -> dict[str, Any]:
        """
        Get a summary of lookback requirements across all symbols.

        Returns:
            Dict with summary statistics
        """
        lookback_map = self.get_all_symbols_lookback_map(strategies)

        if not lookback_map:
            return {"total_symbols": 0}

        lookback_values = list(lookback_map.values())

        return {
            "total_symbols": len(lookback_map),
            "min_lookback": min(lookback_values),
            "max_lookback": max(lookback_values),
            "avg_lookback": sum(lookback_values) / len(lookback_values),
            "distribution": {
                "short_term": len([v for v in lookback_values if v <= 50]),
                "medium_term": len([v for v in lookback_values if 50 < v <= 150]),
                "long_term": len([v for v in lookback_values if v > 150]),
            },
            "symbols_by_lookback": dict(sorted(lookback_map.items(), key=lambda x: x[1])),
        }

    def optimize_data_fetching(
        self, symbols: list[str], strategies: list[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Optimize data fetching by grouping symbols with similar lookback requirements.

        Args:
            symbols: List of symbols to fetch data for
            strategies: List of strategies to consider

        Returns:
            Dict with optimization recommendations
        """
        lookback_map = {}
        for symbol in symbols:
            lookback_map[symbol] = self.get_symbol_lookback_days(symbol, strategies)

        # Group symbols by lookback requirements
        lookback_groups: dict[str, Any] = {}
        for symbol, days in lookback_map.items():
            days_key = str(days)
            if days_key not in lookback_groups:
                lookback_groups[days_key] = []
            lookback_groups[days_key].append(symbol)

        # Calculate efficiency gains
        total_symbols = len(symbols)
        max_lookback = max(lookback_map.values()) if lookback_map else 0

        # If all symbols used max lookback (current approach)
        total_days_naive = total_symbols * max_lookback

        # With optimized lookback
        total_days_optimized = sum(
            days * len(symbols_list) for days, symbols_list in lookback_groups.items()
        )

        efficiency_gain = (
            (total_days_naive - total_days_optimized) / total_days_naive * 100
            if total_days_naive > 0
            else 0
        )

        return {
            "lookback_groups": lookback_groups,
            "efficiency_metrics": {
                "total_symbols": total_symbols,
                "naive_total_days": total_days_naive,
                "optimized_total_days": total_days_optimized,
                "efficiency_gain_percent": efficiency_gain,
                "data_reduction_ratio": (
                    total_days_optimized / total_days_naive if total_days_naive > 0 else 1
                ),
            },
        }


def get_symbol_lookback_days(symbol: str, strategies: list[str] | None = None) -> int:
    """
    Convenience function to get lookback days for a single symbol.

    Args:
        symbol: Symbol to get lookback for
        strategies: List of strategies to consider ('nuclear', 'tecl', 'klm')

    Returns:
        int: Required lookback days for this symbol
    """
    calculator = SymbolLookbackCalculator()
    return calculator.get_symbol_lookback_days(symbol, strategies)


def get_optimized_lookback_map(
    symbols: list[str], strategies: list[str] | None = None
) -> dict[str, int]:
    """
    Convenience function to get optimized lookback map for a list of symbols.

    Args:
        symbols: List of symbols to get lookback for
        strategies: List of strategies to consider

    Returns:
        Dict mapping symbol -> required_lookback_days
    """
    calculator = SymbolLookbackCalculator()

    lookback_map = {}
    for symbol in symbols:
        lookback_map[symbol] = calculator.get_symbol_lookback_days(symbol, strategies)

    return lookback_map


def main():
    """Test the symbol lookback calculator"""
    calculator = SymbolLookbackCalculator()

    print("🔍 Symbol Lookback Calculator Test")
    print("=" * 50)

    # Test specific symbols with strategy breakdown
    test_symbols = ["SPY", "TECL", "UVXY", "SMR", "BIL"]

    print("\n📊 Symbol-Specific Lookback Requirements:")
    for symbol in test_symbols:
        lookback = calculator.get_symbol_lookback_days(symbol)

        # Show which strategies use this symbol
        strategies_using = []
        for strategy in ["nuclear", "tecl", "klm"]:
            symbol_indicators = calculator._get_symbol_indicators_for_strategy(symbol, strategy)
            if symbol_indicators:  # If symbol has any indicators in this strategy
                strategies_using.append(strategy.upper())

        print(f"  {symbol}: {lookback} days (used by: {', '.join(strategies_using)})")

    # Test individual strategy requirements
    print("\n🔬 Per-Strategy Lookback Analysis:")
    for strategy in ["nuclear", "tecl", "klm"]:
        strategy_symbols = calculator._get_strategy_symbols(strategy)
        strategy_lookback = calculator.get_all_symbols_lookback_map([strategy])

        if strategy_lookback:
            min_days = min(strategy_lookback.values())
            max_days = max(strategy_lookback.values())
            avg_days = sum(strategy_lookback.values()) / len(strategy_lookback.values())

            print(
                f"  {strategy.upper()}: {len(strategy_symbols)} symbols, "
                f"{min_days}-{max_days} days (avg: {avg_days:.0f})"
            )

    # Get summary for all strategies
    print("\n📈 Complete Lookback Summary:")
    summary = calculator.get_lookback_summary()
    print(f"  Total Symbols: {summary['total_symbols']}")
    print(f"  Lookback Range: {summary['min_lookback']}-{summary['max_lookback']} days")
    print(f"  Average Lookback: {summary['avg_lookback']:.1f} days")
    print(f"  Distribution: {summary['distribution']}")

    # Test optimization potential
    print("\n⚡ Data Fetching Optimization Analysis:")
    all_symbols = list(summary["symbols_by_lookback"].keys())
    optimization = calculator.optimize_data_fetching(all_symbols)

    # Calculate correct savings vs current 1200-day approach
    current_approach_days = len(all_symbols) * 1200
    optimized_days = optimization["efficiency_metrics"]["optimized_total_days"]
    actual_savings_pct = (current_approach_days - optimized_days) / current_approach_days * 100

    print(f"  Current Approach (1200 days for all): {current_approach_days:,} symbol-days")
    print(f"  Optimized Approach: {optimized_days:,} symbol-days")
    print(f"  Savings: {actual_savings_pct:.1f}%")
    print(f"  Data Reduction Ratio: {current_approach_days / optimized_days:.1f}x")

    # Show some example groupings
    print("\n📋 Lookback Groupings:")
    for days, symbols in sorted(optimization["lookback_groups"].items()):
        if len(symbols) <= 5:
            symbol_list = ", ".join(symbols)
        else:
            symbol_list = f"{', '.join(symbols[:3])} + {len(symbols)-3} more"
        print(f"  {days} days: {symbol_list}")


if __name__ == "__main__":
    main()
