"""
Example Strategy Implementation using the new typed StrategyEngine base.

This example demonstrates how to implement a concrete strategy using the new
StrategyEngine abstract base class with full type safety and error handling.
"""

from datetime import datetime
from decimal import Decimal

from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.engine import StrategyEngine
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class ExampleMomentumStrategy(StrategyEngine):
    """Example momentum strategy implementation.

    This strategy generates BUY signals when the current price is above
    the 20-day moving average and SELL signals when below.
    """

    def __init__(self) -> None:
        super().__init__("ExampleMomentumStrategy")
        self.symbols = ["SPY", "QQQ", "IWM"]  # Example symbols

    def get_required_symbols(self) -> list[str]:
        """Return symbols required by this strategy."""
        return self.symbols

    def generate_signals(
        self, port: MarketDataPort, now: datetime
    ) -> list[StrategySignal]:
        """Generate momentum-based trading signals.

        Args:
            port: Market data access interface
            now: Current timestamp for signal generation

        Returns:
            List of strategy signals based on momentum analysis
        """
        signals = []

        for symbol in self.symbols:
            try:
                # Get current price
                current_price = port.get_current_price(symbol)
                if current_price is None:
                    self.logger.warning(f"No current price available for {symbol}")
                    continue

                # Get historical data for moving average calculation
                data = port.get_data(symbol, timeframe="1day", period="1m")
                if data.empty or len(data) < 20:
                    self.logger.warning(f"Insufficient data for {symbol}")
                    continue

                # Calculate 20-day moving average
                ma_20 = data["Close"].rolling(window=20).mean().iloc[-1]

                # Generate signal based on momentum
                if current_price > ma_20:
                    action = "BUY"
                    confidence_value = min(
                        0.9, (current_price - ma_20) / ma_20 * 2 + 0.5
                    )  # Scale confidence
                    reasoning = f"Price ${current_price:.2f} above MA20 ${ma_20:.2f}"
                    allocation = Decimal("0.33")  # Equal weight across 3 symbols
                elif current_price < ma_20 * 0.95:  # 5% below MA
                    action = "SELL"
                    confidence_value = min(
                        0.9, (ma_20 - current_price) / ma_20 * 2 + 0.5
                    )
                    reasoning = f"Price ${current_price:.2f} significantly below MA20 ${ma_20:.2f}"
                    allocation = Decimal("0.0")
                else:
                    action = "HOLD"
                    confidence_value = 0.3  # Low confidence for hold signals
                    reasoning = f"Price ${current_price:.2f} near MA20 ${ma_20:.2f}"
                    allocation = Decimal("0.1")  # Small position

                # Create signal
                signal = StrategySignal(
                    symbol=Symbol(symbol),
                    action=action,
                    confidence=Confidence(Decimal(str(confidence_value))),
                    target_allocation=Percentage(allocation),
                    reasoning=reasoning,
                    timestamp=now,
                )

                signals.append(signal)

            except Exception as e:
                # Log error but continue with other symbols
                self.logger.error(f"Error processing {symbol}: {e}")
                continue

        return signals


# Example usage:
def example_usage():
    """Example of how to use the strategy with a market data port."""
    from unittest.mock import Mock
    import pandas as pd

    # Create mock market data port
    mock_port = Mock(spec=MarketDataPort)
    mock_port.get_current_price.return_value = 450.0

    # Mock historical data
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    mock_data = pd.DataFrame(
        {"Close": [440 + i for i in range(30)]}, index=dates
    )
    mock_port.get_data.return_value = mock_data

    # Create and run strategy
    strategy = ExampleMomentumStrategy()
    now = datetime.now()

    # Validate market data availability
    try:
        strategy.validate_market_data_availability(mock_port)
        print("✅ Market data validation passed")
    except Exception as e:
        print(f"❌ Market data validation failed: {e}")
        return

    # Generate signals safely
    signals = strategy.safe_generate_signals(mock_port, now)

    print(f"\n📊 Generated {len(signals)} signals:")
    for signal in signals:
        print(
            f"  {signal.symbol.value}: {signal.action} "
            f"(confidence: {signal.confidence.value:.2f}, "
            f"allocation: {signal.target_allocation.to_percent():.1f}%)"
        )
        print(f"    Reasoning: {signal.reasoning}")

    # Log strategy state
    strategy.log_strategy_state({"signals_generated": len(signals)})


if __name__ == "__main__":
    example_usage()