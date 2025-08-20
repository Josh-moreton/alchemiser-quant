"""
Typed Nuclear Strategy Engine

Typed implementation of the Nuclear energy trading strategy that inherits from
StrategyEngine and uses MarketDataPort for data access. Produces StrategySignal
objects with proper confidence values and target allocations.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.domain.math.indicator_utils import safe_get_indicator
from the_alchemiser.domain.math.indicators import TechnicalIndicators
from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.engine import StrategyEngine
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort

# Import the pure strategy logic
from the_alchemiser.domain.strategies.strategy_engine import (
    NuclearStrategyEngine as PureStrategyEngine,
)
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.services.errors.exceptions import StrategyExecutionError


class NuclearTypedEngine(StrategyEngine):
    """Typed Nuclear Strategy Engine using MarketDataPort and producing StrategySignal objects."""

    def __init__(self) -> None:
        super().__init__("Nuclear")
        self.indicators = TechnicalIndicators()
        self.pure_strategy = PureStrategyEngine()

        # Symbol lists from original Nuclear strategy
        self.market_symbols = ["SPY", "IOO", "TQQQ", "VTV", "XLF", "VOX"]
        self.volatility_symbols = ["UVXY", "BTAL"]
        self.tech_symbols = ["QQQ", "SQQQ", "PSQ", "UPRO"]
        self.bond_symbols = ["TLT", "IEF"]
        self.nuclear_symbols = ["SMR", "BWXT", "LEU", "EXC", "NLR", "OKLO"]

        # All required symbols
        self._all_symbols = (
            self.market_symbols
            + self.volatility_symbols
            + self.tech_symbols
            + self.bond_symbols
            + self.nuclear_symbols
        )

    def get_required_symbols(self) -> list[str]:
        """Return all symbols required by the Nuclear strategy."""
        return self._all_symbols

    def generate_signals(self, port: MarketDataPort, now: datetime) -> list[StrategySignal]:
        """Generate Nuclear strategy signals using MarketDataPort.

        Args:
            port: Market data access interface
            now: Current timestamp for signal generation

        Returns:
            List of StrategySignal objects

        Raises:
            StrategyExecutionError: If signal generation fails
        """
        try:
            # Fetch market data for all symbols
            market_data = self._fetch_market_data(port)
            if not market_data:
                self.logger.warning("No market data available for Nuclear strategy")
                return []

            # Calculate technical indicators
            indicators = self._calculate_indicators(market_data)
            if not indicators:
                self.logger.warning("No indicators calculated for Nuclear strategy")
                return []

            # Evaluate strategy using existing logic
            symbol, action, reason = self._evaluate_nuclear_strategy(indicators, market_data)

            # Convert to typed StrategySignal
            signal = self._create_strategy_signal(symbol, action, reason, now)
            return [signal]

        except Exception as e:
            raise StrategyExecutionError(f"Nuclear strategy generation failed: {e}") from e

    def _fetch_market_data(self, port: MarketDataPort) -> dict[str, pd.DataFrame]:
        """Fetch market data for all required symbols."""
        market_data = {}
        for symbol in self._all_symbols:
            try:
                data = port.get_data(symbol, timeframe="1day", period="1y")
                if not data.empty:
                    market_data[symbol] = data
                else:
                    self.logger.warning(f"Empty data for {symbol}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch data for {symbol}: {e}")

        return market_data

    def _calculate_indicators(self, market_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """Calculate technical indicators for all symbols."""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue

            try:
                close = df["Close"]
                indicators[symbol] = {
                    "rsi_10": safe_get_indicator(close, self.indicators.rsi, 10),
                    "rsi_20": safe_get_indicator(close, self.indicators.rsi, 20),
                    "ma_200": safe_get_indicator(close, self.indicators.moving_average, 200),
                    "ma_20": safe_get_indicator(close, self.indicators.moving_average, 20),
                    "ma_return_90": safe_get_indicator(
                        close, self.indicators.moving_average_return, 90
                    ),
                    "cum_return_60": safe_get_indicator(
                        close, self.indicators.cumulative_return, 60
                    ),
                    "current_price": float(close.iloc[-1]),
                }
            except Exception as e:
                self.logger.warning(f"Failed to calculate indicators for {symbol}: {e}")

        return indicators

    def _evaluate_nuclear_strategy(
        self, indicators: dict[str, Any], market_data: dict[str, Any] | None = None
    ) -> tuple[str, str, str]:
        """
        Evaluate Nuclear strategy using the shared strategy logic.
        Returns: (recommended_symbol, action, detailed_reason)
        """
        # Import the shared evaluation logic
        from the_alchemiser.domain.strategies.nuclear_signals import NuclearStrategyEngine

        # Create a mock data provider for the legacy engine
        class MockDataProvider:
            def get_data(self, symbol: str) -> pd.DataFrame:
                # Return empty DataFrame - indicators are already calculated
                return pd.DataFrame()

        # Use the existing evaluation logic
        legacy_engine = NuclearStrategyEngine(MockDataProvider())
        return legacy_engine.evaluate_nuclear_strategy(indicators, market_data)

    def _create_strategy_signal(
        self, symbol: str, action: str, reasoning: str, timestamp: datetime
    ) -> StrategySignal:
        """Convert legacy signal format to typed StrategySignal."""

        # Normalize symbol - handle portfolio cases and invalid symbol names
        if symbol == "UVXY_BTAL_PORTFOLIO":
            signal_symbol = "UVXY"  # Primary symbol for portfolio signals
        elif symbol == "NUCLEAR_PORTFOLIO":
            signal_symbol = "SMR"  # Primary nuclear stock
        elif "_" in symbol or not symbol.isalpha():
            # Handle other portfolio or invalid symbols - extract first valid symbol
            parts = symbol.replace("_", " ").split()
            valid_symbols = [p for p in parts if p.isalpha() and len(p) <= 5]
            signal_symbol = valid_symbols[0] if valid_symbols else "SPY"
        else:
            signal_symbol = symbol

        # Determine confidence based on signal strength
        confidence_value = self._calculate_confidence(symbol, action, reasoning)

        # Determine target allocation based on signal type
        allocation_value = self._calculate_target_allocation(symbol, action)

        return StrategySignal(
            symbol=Symbol(signal_symbol),
            action=action,  # type: ignore  # Already validated by strategy logic
            confidence=Confidence(Decimal(str(confidence_value))),
            target_allocation=Percentage(Decimal(str(allocation_value))),
            reasoning=reasoning,
            timestamp=timestamp,
        )

    def _calculate_confidence(self, symbol: str, action: str, reasoning: str) -> float:
        """Calculate confidence based on signal characteristics."""
        base_confidence = 0.5

        # High confidence conditions
        if "extremely overbought" in reasoning.lower():
            return 0.9
        elif "oversold" in reasoning.lower() and action == "BUY":
            return 0.85
        elif "volatility hedge" in reasoning.lower():
            return 0.8
        elif "bull market" in reasoning.lower() or "bear market" in reasoning.lower():
            return 0.7
        elif action == "HOLD":
            return 0.6

        return base_confidence

    def _calculate_target_allocation(self, symbol: str, action: str) -> float:
        """Calculate target allocation percentage based on signal."""
        if action == "HOLD":
            return 0.0
        elif symbol == "UVXY_BTAL_PORTFOLIO" or symbol == "NUCLEAR_PORTFOLIO":
            return 1.0  # 100% allocation for portfolio strategies
        elif symbol in ["UVXY", "SQQQ", "PSQ"]:
            return 0.25  # 25% for volatility/hedging positions
        elif symbol in ["TQQQ", "UPRO"]:
            return 0.30  # 30% for leveraged growth positions
        elif symbol in self.nuclear_symbols:
            return 0.20  # 20% for individual nuclear stocks
        else:
            return 0.15  # 15% default allocation
