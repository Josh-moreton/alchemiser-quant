"""Tests for typed StrategyEngine base class."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, call

import pytest

from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.engine import StrategyEngine
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.services.errors.exceptions import StrategyExecutionError, ValidationError


class ConcreteTestStrategy(StrategyEngine):
    """Concrete strategy implementation for testing."""

    def __init__(self, strategy_name: str = "TestStrategy"):
        super().__init__(strategy_name)
        self.should_fail = False
        self.signals_to_return: list[StrategySignal] = []
        self.required_symbols_list: list[str] = ["SPY", "QQQ"]

    def generate_signals(self, port: MarketDataPort, now: datetime) -> list[StrategySignal]:
        """Generate test signals."""
        if self.should_fail:
            raise StrategyExecutionError("Test strategy failure", strategy_name=self.strategy_name)
        return self.signals_to_return

    def get_required_symbols(self) -> list[str]:
        """Return required symbols for testing."""
        return self.required_symbols_list


@pytest.fixture
def strategy() -> ConcreteTestStrategy:
    """Create a test strategy instance."""
    return ConcreteTestStrategy()


@pytest.fixture
def mock_port() -> Mock:
    """Create a mock market data port."""
    port = Mock(spec=MarketDataPort)
    port.get_current_price.return_value = 100.0
    port.get_data.return_value = Mock()  # Mock DataFrame
    port.get_latest_quote.return_value = (99.5, 100.5)
    return port


@pytest.fixture
def valid_signal() -> StrategySignal:
    """Create a valid strategy signal for testing."""
    return StrategySignal(
        symbol=Symbol("SPY"),
        action="BUY",
        confidence=Confidence(Decimal("0.8")),
        target_allocation=Percentage(Decimal("0.25")),
        reasoning="Test signal",
        timestamp=datetime.now(UTC),
    )


class TestStrategyEngine:
    """Test cases for StrategyEngine base class."""

    def test_strategy_initialization(self) -> None:
        """Test strategy engine initialization."""
        strategy = ConcreteTestStrategy("MyStrategy")

        assert strategy.strategy_name == "MyStrategy"
        assert strategy.logger is not None
        assert strategy.error_handler is not None

    def test_generate_signals_abstract_method(self) -> None:
        """Test that generate_signals is abstract."""
        # This test verifies the abstract nature - ConcreteTestStrategy implements it
        strategy = ConcreteTestStrategy()
        mock_port = Mock(spec=MarketDataPort)
        now = datetime.now(UTC)

        # Should not raise NotImplementedError since we implemented it
        result = strategy.generate_signals(mock_port, now)
        assert isinstance(result, list)

    def test_validate_signals_empty_list(self, strategy: ConcreteTestStrategy) -> None:
        """Test validation of empty signal list."""
        result = strategy.validate_signals([])
        assert result is True

    def test_validate_signals_valid_signals(
        self, strategy: ConcreteTestStrategy, valid_signal: StrategySignal
    ) -> None:
        """Test validation of valid signals."""
        signals = [valid_signal]
        result = strategy.validate_signals(signals)
        assert result is True

    def test_validate_signals_invalid_signal_type(self, strategy: ConcreteTestStrategy) -> None:
        """Test validation fails with invalid signal type."""
        invalid_signals = ["not_a_signal"]  # type: ignore

        with pytest.raises(ValidationError, match="Expected StrategySignal"):
            strategy.validate_signals(invalid_signals)  # type: ignore

    def test_validate_single_signal_invalid_action(self, strategy: ConcreteTestStrategy) -> None:
        """Test validation fails with invalid action."""

        # Create a proper StrategySignal but with invalid action to test validation
        # Since StrategySignal validates in __post_init__, we need to create one that bypasses this
        # We'll create a mock that looks like StrategySignal
        class MockStrategySignal:
            def __init__(self):
                self.action = "INVALID"
                self.confidence = Confidence(Decimal("0.8"))
                self.target_allocation = Percentage(Decimal("0.25"))

        mock_signal = MockStrategySignal()
        mock_signal.__class__.__name__ = "StrategySignal"  # Make isinstance check pass

        with pytest.raises(ValidationError, match="Invalid action"):
            strategy._validate_single_signal(mock_signal)  # type: ignore

    def test_validate_single_signal_invalid_confidence(
        self, strategy: ConcreteTestStrategy
    ) -> None:
        """Test validation fails with invalid confidence."""

        class MockStrategySignal:
            def __init__(self):
                self.action = "BUY"
                self.confidence = type("MockConfidence", (), {"value": Decimal("1.5")})()
                self.target_allocation = Percentage(Decimal("0.25"))

        mock_signal = MockStrategySignal()
        mock_signal.__class__.__name__ = "StrategySignal"

        with pytest.raises(ValidationError, match="Confidence must be between 0 and 1"):
            strategy._validate_single_signal(mock_signal)  # type: ignore

    def test_validate_single_signal_negative_allocation(
        self, strategy: ConcreteTestStrategy
    ) -> None:
        """Test validation fails with negative allocation."""

        class MockStrategySignal:
            def __init__(self):
                self.action = "BUY"
                self.confidence = Confidence(Decimal("0.8"))
                self.target_allocation = type("MockPercentage", (), {"value": Decimal("-0.1")})()

        mock_signal = MockStrategySignal()
        mock_signal.__class__.__name__ = "StrategySignal"

        with pytest.raises(ValidationError, match="Target allocation cannot be negative"):
            strategy._validate_single_signal(mock_signal)  # type: ignore

    def test_safe_generate_signals_success(
        self, strategy: ConcreteTestStrategy, mock_port: Mock, valid_signal: StrategySignal
    ) -> None:
        """Test safe signal generation with successful generation."""
        strategy.signals_to_return = [valid_signal]
        now = datetime.now(UTC)

        result = strategy.safe_generate_signals(mock_port, now)

        assert len(result) == 1
        assert result[0] == valid_signal

    def test_safe_generate_signals_failure(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test safe signal generation with strategy failure."""
        strategy.should_fail = True
        now = datetime.now(UTC)

        result = strategy.safe_generate_signals(mock_port, now)

        assert result == []
        assert len(strategy.error_handler.errors) > 0

    def test_get_required_symbols_default(self) -> None:
        """Test default required symbols returns empty list."""

        # Create a strategy that doesn't override get_required_symbols
        class MinimalStrategy(StrategyEngine):
            def generate_signals(self, port: MarketDataPort, now: datetime) -> list[StrategySignal]:
                return []

        strategy = MinimalStrategy("minimal")
        assert strategy.get_required_symbols() == []

    def test_get_required_symbols_override(self, strategy: ConcreteTestStrategy) -> None:
        """Test overridden required symbols."""
        assert strategy.get_required_symbols() == ["SPY", "QQQ"]

    def test_validate_market_data_availability_success(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test market data availability validation success."""
        result = strategy.validate_market_data_availability(mock_port)
        assert result is True

        # Verify it called get_current_price for each required symbol
        expected_calls = [call("SPY"), call("QQQ")]
        mock_port.get_current_price.assert_has_calls(expected_calls, any_order=True)

    def test_validate_market_data_availability_failure(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test market data availability validation failure."""
        # Make one symbol return None (unavailable)
        mock_port.get_current_price.side_effect = lambda symbol: None if symbol == "SPY" else 100.0

        with pytest.raises(ValidationError, match="Required market data unavailable"):
            strategy.validate_market_data_availability(mock_port)

    def test_validate_market_data_availability_with_symbols(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test market data availability validation with custom symbols."""
        custom_symbols = ["AAPL", "MSFT"]

        result = strategy.validate_market_data_availability(mock_port, custom_symbols)
        assert result is True

        # Should check custom symbols, not required symbols
        expected_calls = [call("AAPL"), call("MSFT")]
        mock_port.get_current_price.assert_has_calls(expected_calls, any_order=True)

    def test_validate_market_data_availability_empty_symbols(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test market data availability with empty symbols list."""
        strategy.required_symbols_list = []

        result = strategy.validate_market_data_availability(mock_port)
        assert result is True

        # Should not call get_current_price
        mock_port.get_current_price.assert_not_called()

    def test_validate_market_data_availability_exception_handling(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test market data availability handles exceptions."""
        # Make get_current_price raise an exception
        mock_port.get_current_price.side_effect = Exception("Network error")

        with pytest.raises(ValidationError, match="Required market data unavailable"):
            strategy.validate_market_data_availability(mock_port)

    def test_log_strategy_state(
        self, strategy: ConcreteTestStrategy, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test strategy state logging."""
        additional_info = {"test_key": "test_value"}

        with caplog.at_level("INFO"):
            strategy.log_strategy_state(additional_info)

        # Check that log contains expected information
        assert "TestStrategy state:" in caplog.text
        assert "test_key" in caplog.text
        assert "test_value" in caplog.text

    def test_log_strategy_state_no_additional_info(
        self, strategy: ConcreteTestStrategy, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test strategy state logging without additional info."""
        with caplog.at_level("INFO"):
            strategy.log_strategy_state()

        assert "TestStrategy state:" in caplog.text
        assert "strategy_name" in caplog.text

    def test_error_handler_integration(
        self, strategy: ConcreteTestStrategy, mock_port: Mock
    ) -> None:
        """Test that error handler is properly integrated."""
        strategy.should_fail = True
        now = datetime.now(UTC)

        # This should handle errors gracefully
        result = strategy.safe_generate_signals(mock_port, now)

        assert result == []
        assert len(strategy.error_handler.errors) > 0

        # Check error details
        error = strategy.error_handler.errors[0]
        assert error.component == "TestStrategy.safe_generate_signals"
        assert error.context == "signal_generation"
