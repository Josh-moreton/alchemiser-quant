"""Tests for StrategySignal value object."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class TestStrategySignal:
    """Test cases for StrategySignal value object."""

    def test_valid_strategy_signal_creation(self) -> None:
        """Test creating a valid strategy signal."""
        symbol = Symbol("AAPL")
        confidence = Confidence(Decimal("0.8"))
        target_allocation = Percentage(Decimal("0.25"))  # 25%

        signal = StrategySignal(
            symbol=symbol,
            action="BUY",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Strong earnings forecast",
        )

        assert signal.symbol == symbol
        assert signal.action == "BUY"
        assert signal.confidence == confidence
        assert signal.target_allocation == target_allocation
        assert signal.reasoning == "Strong earnings forecast"
        assert isinstance(signal.timestamp, datetime)
        assert signal.timestamp.tzinfo == UTC

    def test_all_valid_actions(self) -> None:
        """Test all valid action types."""
        symbol = Symbol("SPY")
        confidence = Confidence(Decimal("0.7"))
        target_allocation = Percentage(Decimal("0.1"))

        actions = ["BUY", "SELL", "HOLD"]

        for action in actions:
            signal = StrategySignal(
                symbol=symbol,
                action=action,  # type: ignore
                confidence=confidence,
                target_allocation=target_allocation,
                reasoning=f"Test {action} signal",
            )
            assert signal.action == action

    def test_invalid_action(self) -> None:
        """Test that invalid actions raise errors."""
        symbol = Symbol("TSLA")
        confidence = Confidence(Decimal("0.6"))
        target_allocation = Percentage(Decimal("0.2"))

        with pytest.raises(ValueError, match="Invalid signal action"):
            StrategySignal(
                symbol=symbol,
                action="INVALID",  # type: ignore
                confidence=confidence,
                target_allocation=target_allocation,
                reasoning="Test reasoning",
            )

    def test_strategy_signal_with_custom_timestamp(self) -> None:
        """Test strategy signal with custom timestamp."""
        symbol = Symbol("BTC")
        confidence = Confidence(Decimal("0.9"))
        target_allocation = Percentage(Decimal("0.05"))
        custom_time = datetime(2023, 6, 15, 14, 30, 0, tzinfo=UTC)

        signal = StrategySignal(
            symbol=symbol,
            action="SELL",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Crypto volatility concern",
            timestamp=custom_time,
        )

        assert signal.timestamp == custom_time

    def test_default_timestamp_is_recent(self) -> None:
        """Test that default timestamp is recent and in UTC."""
        symbol = Symbol("QQQ")
        confidence = Confidence(Decimal("0.75"))
        target_allocation = Percentage(Decimal("0.3"))

        signal = StrategySignal(
            symbol=symbol,
            action="HOLD",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Market uncertainty",
        )

        now = datetime.now(UTC)
        time_diff = (now - signal.timestamp).total_seconds()
        assert time_diff < 5  # Should be created within 5 seconds

    def test_strategy_signal_immutability(self) -> None:
        """Test that StrategySignal objects are immutable."""
        symbol = Symbol("GOLD")
        confidence = Confidence(Decimal("0.65"))
        target_allocation = Percentage(Decimal("0.15"))

        signal = StrategySignal(
            symbol=symbol,
            action="BUY",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Inflation hedge",
        )

        # Should not be able to modify any field
        with pytest.raises(AttributeError):
            signal.action = "SELL"  # type: ignore

        with pytest.raises(AttributeError):
            signal.reasoning = "Modified"  # type: ignore

    def test_strategy_signal_equality(self) -> None:
        """Test strategy signal equality comparison."""
        symbol = Symbol("MSFT")
        confidence = Confidence(Decimal("0.85"))
        target_allocation = Percentage(Decimal("0.4"))
        timestamp = datetime.now(UTC)

        signal1 = StrategySignal(
            symbol=symbol,
            action="BUY",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Cloud growth",
            timestamp=timestamp,
        )
        signal2 = StrategySignal(
            symbol=symbol,
            action="BUY",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Cloud growth",
            timestamp=timestamp,
        )
        signal3 = StrategySignal(
            symbol=symbol,
            action="SELL",  # Different action
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="Cloud growth",
            timestamp=timestamp,
        )

        assert signal1 == signal2
        assert signal1 != signal3

    def test_strategy_signal_with_different_value_objects(self) -> None:
        """Test strategy signal with various value object combinations."""
        # High confidence, large allocation
        high_conf_signal = StrategySignal(
            symbol=Symbol("AMZN"),
            action="BUY",
            confidence=Confidence(Decimal("0.95")),
            target_allocation=Percentage(Decimal("0.5")),
            reasoning="Strong Q4 expected",
        )

        assert high_conf_signal.confidence.is_high
        assert high_conf_signal.target_allocation.to_percent() == Decimal("50")

        # Low confidence, small allocation
        low_conf_signal = StrategySignal(
            symbol=Symbol("RISKY"),
            action="HOLD",
            confidence=Confidence(Decimal("0.2")),
            target_allocation=Percentage(Decimal("0.01")),
            reasoning="Uncertain outlook",
        )

        assert low_conf_signal.confidence.is_low
        assert low_conf_signal.target_allocation.to_percent() == Decimal("1")

    def test_strategy_signal_reasoning_variations(self) -> None:
        """Test strategy signal with different reasoning strings."""
        symbol = Symbol("TEST")
        confidence = Confidence(Decimal("0.7"))
        target_allocation = Percentage(Decimal("0.1"))

        # Empty reasoning
        signal_empty = StrategySignal(
            symbol=symbol,
            action="HOLD",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning="",
        )
        assert signal_empty.reasoning == ""

        # Long reasoning
        long_reasoning = "This is a very detailed reasoning that explains the complex analysis behind this trading signal, including technical indicators, fundamental analysis, and market sentiment."
        signal_long = StrategySignal(
            symbol=symbol,
            action="BUY",
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning=long_reasoning,
        )
        assert signal_long.reasoning == long_reasoning
