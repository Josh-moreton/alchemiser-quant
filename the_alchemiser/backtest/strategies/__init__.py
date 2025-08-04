#!/usr/bin/env python3
"""
Strategy adapters and wrappers for backtest engine

This module provides adapters that wrap the individual strategy engines
to provide a consistent interface for backtesting.
"""

import datetime as dt
from dataclasses import dataclass

import pandas as pd


@dataclass
class StrategyPosition:
    """Represents a position in a strategy"""

    symbol: str
    weight: float
    price: float
    timestamp: dt.datetime


class StrategyAdapter:
    """Base adapter for strategy engines"""

    def __init__(self, name: str):
        self.name = name
        self.current_positions: dict[str, StrategyPosition] = {}

    def get_signals(self, date: dt.datetime, data: dict[str, pd.DataFrame]) -> dict[str, float]:
        """
        Get strategy signals for a given date

        Args:
            date: Date to get signals for
            data: Historical data for all symbols

        Returns:
            Dictionary of symbol -> weight signals
        """
        raise NotImplementedError("Subclasses must implement get_signals")

    def update_positions(
        self, signals: dict[str, float], date: dt.datetime, data: dict[str, pd.DataFrame]
    ):
        """Update current positions based on signals"""
        for symbol, weight in signals.items():
            if symbol in data and date in data[symbol].index:
                price = float(data[symbol].at[date, "close"])
                self.current_positions[symbol] = StrategyPosition(
                    symbol=symbol, weight=weight, price=price, timestamp=date
                )

    def get_portfolio_value(self, date: dt.datetime, data: dict[str, pd.DataFrame]) -> float:
        """Calculate current portfolio value"""
        total_value = 0.0
        for position in self.current_positions.values():
            if position.symbol in data and date in data[position.symbol].index:
                current_price = float(data[position.symbol].at[date, "close"])
                value = position.weight * current_price / position.price
                total_value += value
        return total_value


class NuclearStrategyAdapter(StrategyAdapter):
    """Adapter for Nuclear strategy"""

    def __init__(self):
        super().__init__("Nuclear")
        self.nuclear_symbols = ["OKLO", "SMR", "LEU", "URA", "URNM", "DNN", "CCJ", "NXE"]

    def get_signals(self, date: dt.datetime, data: dict[str, pd.DataFrame]) -> dict[str, float]:
        """Get Nuclear strategy signals"""
        # Simplified nuclear strategy logic
        signals = {}

        # Equal weight across available nuclear symbols
        available_symbols = [
            sym for sym in self.nuclear_symbols if sym in data and date in data[sym].index
        ]

        if available_symbols:
            weight_per_symbol = 1.0 / len(available_symbols)
            for symbol in available_symbols:
                signals[symbol] = weight_per_symbol

        return signals


class TECLStrategyAdapter(StrategyAdapter):
    """Adapter for TECL strategy"""

    def __init__(self):
        super().__init__("TECL")
        self.tecl_symbols = ["TECL", "TECS", "XLK", "QQQ", "TQQQ", "SQQQ"]

    def get_signals(self, date: dt.datetime, data: dict[str, pd.DataFrame]) -> dict[str, float]:
        """Get TECL strategy signals"""
        # Simplified TECL strategy logic
        signals = {}

        # Primary focus on TECL if available
        if "TECL" in data and date in data["TECL"].index:
            signals["TECL"] = 0.7

            # Secondary allocation to QQQ
            if "QQQ" in data and date in data["QQQ"].index:
                signals["QQQ"] = 0.3
        elif "QQQ" in data and date in data["QQQ"].index:
            # Fallback to QQQ if TECL not available
            signals["QQQ"] = 1.0

        return signals


class KLMStrategyAdapter(StrategyAdapter):
    """Adapter for KLM strategy"""

    def __init__(self):
        super().__init__("KLM")
        self.leveraged_etfs = [
            "FNGU",
            "FNGD",
            "TECL",
            "TECS",
            "TQQQ",
            "SQQQ",
            "UVXY",
            "SVXY",
            "SPXU",
            "SPXL",
            "TNA",
            "TZA",
            "FAS",
            "FAZ",
            "NUGT",
            "DUST",
            "LABU",
            "LABD",
            "CURE",
            "SH",
            "UPRO",
            "SPDN",
        ]
        self.sector_etfs = ["XLK", "KMLM", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE"]

    def get_signals(self, date: dt.datetime, data: dict[str, pd.DataFrame]) -> dict[str, float]:
        """Get KLM strategy signals"""
        # Simplified KLM strategy logic
        signals = {}

        # Focus on key leveraged ETFs with momentum
        available_leveraged = [
            sym for sym in ["TQQQ", "TECL", "SPXL"] if sym in data and date in data[sym].index
        ]

        if available_leveraged:
            weight_per_symbol = 1.0 / len(available_leveraged)
            for symbol in available_leveraged:
                signals[symbol] = weight_per_symbol

        return signals


class MultiStrategyAdapter:
    """Adapter that combines multiple strategies"""

    def __init__(self, strategy_weights: dict[str, float]):
        """
        Initialize multi-strategy adapter

        Args:
            strategy_weights: Weights for each strategy {'nuclear': 0.3, 'tecl': 0.4, 'klm': 0.3}
        """
        self.strategy_weights = strategy_weights
        self.strategies = {
            "nuclear": NuclearStrategyAdapter(),
            "tecl": TECLStrategyAdapter(),
            "klm": KLMStrategyAdapter(),
        }

    def get_combined_signals(
        self, date: dt.datetime, data: dict[str, pd.DataFrame]
    ) -> dict[str, float]:
        """Get combined signals from all strategies"""
        combined_signals = {}

        for strategy_name, strategy_weight in self.strategy_weights.items():
            if strategy_weight > 0 and strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                strategy_signals = strategy.get_signals(date, data)

                # Apply strategy weight to all signals
                for symbol, signal_weight in strategy_signals.items():
                    if symbol in combined_signals:
                        combined_signals[symbol] += signal_weight * strategy_weight
                    else:
                        combined_signals[symbol] = signal_weight * strategy_weight

        return combined_signals

    def update_all_positions(self, date: dt.datetime, data: dict[str, pd.DataFrame]):
        """Update positions for all strategies"""
        for strategy in self.strategies.values():
            signals = strategy.get_signals(date, data)
            strategy.update_positions(signals, date, data)

    def get_total_portfolio_value(self, date: dt.datetime, data: dict[str, pd.DataFrame]) -> float:
        """Get total portfolio value across all strategies"""
        total_value = 0.0

        for strategy_name, strategy_weight in self.strategy_weights.items():
            if strategy_weight > 0 and strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                strategy_value = strategy.get_portfolio_value(date, data)
                total_value += strategy_value * strategy_weight

        return total_value
