"""
Typed Nuclear Trading Strategy Implementation

This module provides the typed Nuclear energy trading strategy that extends the
typed StrategyEngine base class and consumes MarketDataPort while producing
typed StrategySignal objects.

The strategy implements the same hierarchical logic as the legacy Nuclear
strategy but with full type safety and clean dependency boundaries.

## Usage Examples

### Legacy Mode (Default - Backward Compatible)
```python
# Default behavior maintains compatibility with existing systems
strategy = TypedNuclearStrategy()
signals = strategy.generate_signals(market_data_port, datetime.now())
signal = signals[0]
# signal.confidence.value == 0.0 (legacy behavior)
# signal.target_allocation.value == 0.0 (legacy behavior)
```

### Dynamic Mode (New Features)
```python
# Enable dynamic confidence scoring and target allocation
strategy = TypedNuclearStrategy(enable_dynamic_allocation=True)
signals = strategy.generate_signals(market_data_port, datetime.now())
signal = signals[0]
# signal.confidence.value ranges from 0.3-0.9 based on signal type
# signal.target_allocation.value ranges from 0.0-0.75 based on signal type
```

The dynamic allocation feature provides:
- Confidence scoring: 0.3 (HOLD) to 0.9 (high-conviction volatility hedge)
- Target allocation: 0.0 (HOLD/SELL) to 0.75 (portfolio hedge strategies)
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
from the_alchemiser.domain.strategies.strategy_engine import (
    NuclearStrategyEngine as PureNuclearEngine,
)
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.services.errors.exceptions import StrategyExecutionError


class TypedNuclearStrategy(StrategyEngine):
    """Typed Nuclear Energy trading strategy with clean boundaries.

    This strategy implements the same logic as the legacy Nuclear strategy but:
    - Extends the typed StrategyEngine base class
    - Consumes MarketDataPort for clean data access
    - Produces typed StrategySignal objects
    - Has clear separation between data access and strategy logic

    The strategy maintains backward compatibility with legacy behavior by defaulting
    to zero confidence and allocation values unless explicitly enabled.
    """

    def __init__(self, enable_dynamic_allocation: bool = False) -> None:
        super().__init__("TypedNuclearStrategy")
        self.indicators = TechnicalIndicators()
        self.pure_strategy = PureNuclearEngine()

        # Backward compatibility: disable dynamic features by default
        self.enable_dynamic_allocation = enable_dynamic_allocation

        # Core symbols from the Nuclear strategy
        self.market_symbols = ["SPY", "IOO", "TQQQ", "VTV", "XLF", "VOX"]
        self.volatility_symbols = ["UVXY", "BTAL"]
        self.tech_symbols = ["QQQ", "SQQQ", "PSQ", "UPRO"]
        self.bond_symbols = ["TLT", "IEF"]
        self.nuclear_symbols = ["SMR", "BWXT", "LEU", "EXC", "NLR", "OKLO"]

        self.all_symbols = (
            self.market_symbols
            + self.volatility_symbols
            + self.tech_symbols
            + self.bond_symbols
            + self.nuclear_symbols
        )

    def get_required_symbols(self) -> list[str]:
        """Return symbols required by this strategy."""
        return self.all_symbols

    def generate_signals(self, port: MarketDataPort, now: datetime) -> list[StrategySignal]:
        """Generate Nuclear trading signals based on current market conditions.

        Args:
            port: Market data access interface
            now: Current timestamp for signal generation

        Returns:
            List of strategy signals based on Nuclear strategy analysis

        Raises:
            StrategyExecutionError: If signal generation fails
        """
        try:
            # Fetch market data for all symbols
            market_data = self._fetch_market_data(port)
            if not market_data:
                raise StrategyExecutionError(
                    "No market data available for Nuclear strategy",
                    strategy_name=self.strategy_name,
                )

            # Calculate technical indicators
            indicators = self._calculate_indicators(market_data)
            if not indicators:
                raise StrategyExecutionError(
                    "No indicators calculated for Nuclear strategy",
                    strategy_name=self.strategy_name,
                )

            # Generate strategy recommendation using pure logic
            symbol, action, reasoning = self._evaluate_nuclear_strategy(indicators, market_data)

            # Convert to typed signal
            signal = self._create_strategy_signal(symbol, action, reasoning, now)

            if self.enable_dynamic_allocation:
                self.logger.info(
                    f"Nuclear strategy generated signal: {signal.symbol.value} {signal.action} "
                    f"(confidence: {signal.confidence.value:.2f}, allocation: {signal.target_allocation.value:.2f})"
                )
            else:
                self.logger.info(
                    f"Nuclear strategy generated signal: {signal.symbol.value} {signal.action} "
                    f"(legacy mode - confidence and allocation disabled)"
                )

            return [signal]

        except Exception as e:
            raise StrategyExecutionError(
                f"Nuclear strategy signal generation failed: {e}", strategy_name=self.strategy_name
            ) from e

    def _fetch_market_data(self, port: MarketDataPort) -> dict[str, pd.DataFrame]:
        """Fetch market data for all required symbols."""
        market_data = {}

        for symbol in self.all_symbols:
            try:
                data = port.get_data(symbol, timeframe="1day", period="1y")
                if not data.empty:
                    market_data[symbol] = data
                else:
                    self.logger.warning(f"Could not fetch data for {symbol}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue

        return market_data

    def _calculate_indicators(self, market_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """Calculate all technical indicators required by the Nuclear strategy."""
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
                continue

        return indicators

    def _evaluate_nuclear_strategy(
        self, indicators: dict[str, Any], market_data: dict[str, pd.DataFrame] | None = None
    ) -> tuple[str, str, str]:
        """
        Evaluate the Nuclear Energy strategy using the shared logic.
        Returns: (recommended_symbol, action, detailed_reason)
        """
        from the_alchemiser.domain.strategies.nuclear_strategy_logic import (
            evaluate_nuclear_strategy_logic,
        )

        return evaluate_nuclear_strategy_logic(indicators, market_data, self.pure_strategy)

    def _create_strategy_signal(
        self, symbol: str, action: str, reasoning: str, timestamp: datetime
    ) -> StrategySignal:
        """Create a typed StrategySignal from strategy output."""

        # Backward compatibility: use legacy behavior by default
        if not self.enable_dynamic_allocation:
            # Legacy behavior: no confidence scoring or allocation changes
            confidence_value = 0.0
            allocation_value = 0.0
        else:
            # New dynamic behavior (optional)
            confidence_value = self._calculate_confidence(symbol, action, reasoning)
            allocation_value = self._calculate_target_allocation(symbol, action)

        # Handle special portfolio symbols
        if symbol == "UVXY_BTAL_PORTFOLIO":
            symbol = "PORTFOLIO"  # Use portfolio label for complex allocations

        return StrategySignal(
            symbol=Symbol(symbol),
            action=action,  # Already validated by StrategySignal
            confidence=Confidence(Decimal(str(confidence_value))),
            target_allocation=Percentage(Decimal(str(allocation_value))),
            reasoning=reasoning,
            timestamp=timestamp,
        )

    def _calculate_confidence(self, symbol: str, action: str, reasoning: str) -> float:
        """Calculate confidence level based on signal characteristics.

        Note: This is only used when enable_dynamic_allocation=True.
        For backward compatibility, defaults to 0.0 unless explicitly enabled.
        """
        if action == "HOLD":
            return 0.3  # Low confidence for hold signals

        # High confidence for volatility hedge signals
        if "UVXY" in symbol or "volatility hedge" in reasoning.lower():
            return 0.9

        # High confidence for oversold/overbought extremes
        if "extremely overbought" in reasoning.lower() or "oversold" in reasoning.lower():
            return 0.85

        # Medium-high confidence for trend-following signals
        if "bull market" in reasoning.lower() or "bear market" in reasoning.lower():
            return 0.75

        # Default medium confidence
        return 0.65

    def _calculate_target_allocation(self, symbol: str, action: str) -> float:
        """Calculate target allocation percentage based on signal type.

        Note: This is only used when enable_dynamic_allocation=True.
        For backward compatibility, defaults to 0.0 unless explicitly enabled.
        """
        if action == "HOLD":
            return 0.0

        if action == "SELL":
            return 0.0  # Sell signals have zero target allocation

        # BUY signals - vary allocation based on signal type
        if symbol == "PORTFOLIO":
            return 0.75  # High allocation for portfolio hedge strategies

        if "UVXY" in symbol:
            return 0.5  # High allocation for volatility hedge

        if symbol in ["UPRO", "TQQQ"]:
            return 0.4  # Moderate allocation for leveraged ETFs

        if symbol in self.nuclear_symbols:
            return 0.33  # Equal weight for nuclear stocks

        # Default allocation for other signals
        return 0.25
