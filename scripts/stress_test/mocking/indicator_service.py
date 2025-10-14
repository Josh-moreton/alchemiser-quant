"""Business Unit: utilities | Status: current.

Mock indicator service for stress testing.

This service returns controlled indicator values based on market condition
scenarios, allowing us to test all possible market states.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator

from ..models.conditions import MarketCondition


class MockIndicatorService:
    """Mock IndicatorService that returns controlled values for stress testing.

    This service returns indicator values based on the current market condition
    scenario, allowing us to test all possible market states.
    """

    def __init__(self, market_condition: MarketCondition) -> None:
        """Initialize mock indicator service with a market condition.

        Args:
            market_condition: The market condition to simulate

        """
        self.market_condition = market_condition
        self.call_count = 0

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Return controlled indicator values based on market condition.

        Args:
            request: Indicator request

        Returns:
            TechnicalIndicator with controlled values

        """
        self.call_count += 1

        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters

        # Generate deterministic but varied values based on scenario
        rsi_min, rsi_max = self.market_condition.rsi_range
        # Use symbol hash for deterministic variation within range
        symbol_hash = sum(ord(c) for c in symbol)
        rsi_offset = (symbol_hash % 20) - 10  # +/- 10 from midpoint
        rsi_midpoint = (rsi_min + rsi_max) / 2
        rsi_value = max(rsi_min, min(rsi_max, rsi_midpoint + rsi_offset))

        # Base price with multiplier and symbol variation
        base_price = 100.0 + (symbol_hash % 50)
        current_price = base_price * self.market_condition.price_multiplier

        # Common timestamp and base structure
        timestamp = datetime.now(UTC)
        current_price_decimal = Decimal(str(current_price))

        # Create indicator based on type
        if indicator_type == "rsi":
            window = int(parameters.get("window", 14))
            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                rsi_14=rsi_value if window == 14 else None,
                rsi_10=rsi_value if window == 10 else None,
                rsi_20=rsi_value if window == 20 else None,
                rsi_21=rsi_value if window == 21 else None,
                current_price=current_price_decimal,
                data_source="stress_test_mock",
                metadata={
                    "value": rsi_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "current_price":
            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                data_source="stress_test_mock",
                metadata={
                    "value": current_price,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "moving_average":
            window = int(parameters.get("window", 200))
            # Generate realistic MA value relative to current price
            ma_offset = (symbol_hash % 10) - 5  # +/- 5% variation
            ma_value = current_price * (1 + ma_offset / 100)

            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                ma_20=ma_value if window == 20 else None,
                ma_50=ma_value if window == 50 else None,
                ma_200=ma_value if window == 200 else None,
                data_source="stress_test_mock",
                metadata={
                    "value": ma_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "cumulative_return":
            window = int(parameters.get("window", 60))
            # Generate return based on market condition (-50% to +150% scaled down)
            base_return = (
                self.market_condition.price_multiplier - 1
            ) * 100  # Convert to percentage
            # Add symbol-specific variation
            return_variation = (symbol_hash % 20) - 10  # +/- 10%
            cumulative_return_value = base_return + return_variation

            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                cum_return_60=cumulative_return_value if window == 60 else None,
                data_source="stress_test_mock",
                metadata={
                    "value": cumulative_return_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "moving_average_return":
            window = int(parameters.get("window", 21))
            # Generate smaller return values (typical daily returns)
            base_return = (
                self.market_condition.price_multiplier - 1
            ) * 10  # Scale down for MA return
            return_variation = (symbol_hash % 6) - 3  # +/- 3%
            ma_return_value = base_return + return_variation

            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                ma_return_90=ma_return_value if window == 90 else None,
                data_source="stress_test_mock",
                metadata={
                    "value": ma_return_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "exponential_moving_average_price":
            window = int(parameters.get("window", 12))
            # EMA should be closer to current price than SMA
            ema_offset = (symbol_hash % 6) - 3  # +/- 3% variation
            ema_value = current_price * (1 + ema_offset / 100)

            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                ema_12=ema_value if window == 12 else None,
                ema_26=ema_value if window == 26 else None,
                data_source="stress_test_mock",
                metadata={
                    "value": ema_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "stdev_return":
            window = int(parameters.get("window", 6))
            # Generate volatility measure (always positive)
            base_volatility = (
                15.0
                if self.market_condition.volatility_regime == "high"
                else (10.0 if self.market_condition.volatility_regime == "medium" else 5.0)
            )
            volatility_variation = symbol_hash % 10  # 0-10% additional variation
            stdev_value = base_volatility + volatility_variation

            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                stdev_return_6=stdev_value if window == 6 else None,
                data_source="stress_test_mock",
                metadata={
                    "value": stdev_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "max_drawdown":
            window = int(parameters.get("window", 60))
            # Generate drawdown (negative value representing max loss)
            base_drawdown = (
                -20.0
                if self.market_condition.volatility_regime == "high"
                else (-10.0 if self.market_condition.volatility_regime == "medium" else -5.0)
            )
            drawdown_variation = -(symbol_hash % 10)  # Additional 0-10% drawdown
            max_drawdown_value = base_drawdown + drawdown_variation

            return TechnicalIndicator(
                symbol=symbol,
                timestamp=timestamp,
                current_price=current_price_decimal,
                data_source="stress_test_mock",
                metadata={
                    "value": max_drawdown_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        # For other indicators, return reasonable defaults
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=timestamp,
            current_price=current_price_decimal,
            data_source="stress_test_mock",
            metadata={"scenario": self.market_condition.scenario_id},
        )
