"""Tests for TypedStrategyManager."""

from __future__ import annotations

import pytest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from the_alchemiser.domain.registry.strategy_registry import StrategyType
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.typed_strategy_manager import (
    TypedStrategyManager,
    AggregatedSignals,
)
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


@pytest.fixture
def mock_market_data_port():
    """Create a mock MarketDataPort."""
    mock_port = Mock(spec=MarketDataPort)
    # Add any common mock behavior here
    return mock_port


@pytest.fixture
def sample_strategy_allocations():
    """Sample strategy allocations for testing."""
    return {
        StrategyType.NUCLEAR: 0.4,
        StrategyType.TECL: 0.6,
    }


@pytest.fixture
def sample_signal():
    """Create a sample StrategySignal for testing."""
    return StrategySignal(
        symbol=Symbol("AAPL"),
        action="BUY",
        confidence=Confidence(Decimal("0.8")),
        target_allocation=Percentage(Decimal("0.5")),
        reasoning="Test signal",
    )


class TestAggregatedSignals:
    """Test the AggregatedSignals data structure."""

    def test_add_strategy_signals(self, sample_signal):
        """Test adding signals for a strategy."""
        aggregated = AggregatedSignals()
        signals = [sample_signal]

        aggregated.add_strategy_signals(StrategyType.NUCLEAR, signals)

        assert StrategyType.NUCLEAR in aggregated.signals_by_strategy
        assert aggregated.signals_by_strategy[StrategyType.NUCLEAR] == signals

    def test_get_all_signals(self, sample_signal):
        """Test getting all signals from multiple strategies."""
        aggregated = AggregatedSignals()

        signal1 = sample_signal
        signal2 = StrategySignal(
            symbol=Symbol("MSFT"),
            action="SELL",
            confidence=Confidence(Decimal("0.7")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Test signal 2",
        )

        aggregated.add_strategy_signals(StrategyType.NUCLEAR, [signal1])
        aggregated.add_strategy_signals(StrategyType.TECL, [signal2])

        all_signals = aggregated.get_all_signals()
        assert len(all_signals) == 2
        assert signal1 in all_signals
        assert signal2 in all_signals

    def test_get_signals_by_strategy(self, sample_signal):
        """Test getting signals grouped by strategy."""
        aggregated = AggregatedSignals()
        signals = [sample_signal]

        aggregated.add_strategy_signals(StrategyType.NUCLEAR, signals)

        by_strategy = aggregated.get_signals_by_strategy()
        assert StrategyType.NUCLEAR in by_strategy
        assert by_strategy[StrategyType.NUCLEAR] == signals

        # Ensure it's a copy
        by_strategy[StrategyType.TECL] = []
        assert StrategyType.TECL not in aggregated.signals_by_strategy


class TestTypedStrategyManager:
    """Test the TypedStrategyManager."""

    def test_initialization_with_default_allocations(self, mock_market_data_port, monkeypatch):
        """Test manager initialization with default allocations."""
        # Mock the strategy engines to avoid actual instantiation
        mock_engine = Mock()
        monkeypatch.setattr(
            "the_alchemiser.domain.strategies.typed_strategy_manager.TypedStrategyManager._create_typed_engine",
            lambda self, strategy_type: mock_engine,
        )

        manager = TypedStrategyManager(mock_market_data_port)

        assert manager.market_data_port == mock_market_data_port
        assert len(manager.strategy_allocations) > 0

        # Allocations should sum to approximately 1.0
        total = sum(manager.strategy_allocations.values())
        assert abs(total - 1.0) < 0.01

    def test_initialization_with_custom_allocations(
        self, mock_market_data_port, sample_strategy_allocations, monkeypatch
    ):
        """Test manager initialization with custom allocations."""
        mock_engine = Mock()
        monkeypatch.setattr(
            "the_alchemiser.domain.strategies.typed_strategy_manager.TypedStrategyManager._create_typed_engine",
            lambda self, strategy_type: mock_engine,
        )

        manager = TypedStrategyManager(mock_market_data_port, sample_strategy_allocations)

        assert manager.strategy_allocations == sample_strategy_allocations

    def test_invalid_allocations_raises_error(self, mock_market_data_port):
        """Test that invalid allocations raise ValueError."""
        invalid_allocations = {
            StrategyType.NUCLEAR: 0.7,
            StrategyType.TECL: 0.8,  # Sum > 1.0
        }

        with pytest.raises(ValueError, match="Strategy allocations must sum to 1.0"):
            TypedStrategyManager(mock_market_data_port, invalid_allocations)

    def test_create_typed_engine_nuclear(self, mock_market_data_port, monkeypatch):
        """Test creating Nuclear typed engine."""
        manager = TypedStrategyManager.__new__(TypedStrategyManager)
        manager.market_data_port = mock_market_data_port

        mock_nuclear = Mock()
        monkeypatch.setattr(
            "the_alchemiser.domain.strategies.typed_strategy_manager.NuclearTypedEngine",
            lambda: mock_nuclear,
        )

        engine = manager._create_typed_engine(StrategyType.NUCLEAR)
        assert engine == mock_nuclear

    def test_create_typed_engine_klm(self, mock_market_data_port, monkeypatch):
        """Test creating KLM typed engine."""
        manager = TypedStrategyManager.__new__(TypedStrategyManager)
        manager.market_data_port = mock_market_data_port

        mock_klm = Mock()
        monkeypatch.setattr(
            "the_alchemiser.domain.strategies.typed_strategy_manager.TypedKLMStrategyEngine",
            lambda: mock_klm,
        )

        engine = manager._create_typed_engine(StrategyType.KLM)
        assert engine == mock_klm

    def test_create_typed_engine_unknown_raises_error(self, mock_market_data_port):
        """Test that unknown strategy type raises error."""
        manager = TypedStrategyManager.__new__(TypedStrategyManager)
        manager.market_data_port = mock_market_data_port

        # Create a fake strategy type
        fake_strategy = Mock()
        fake_strategy.value = "FAKE"

        with pytest.raises(ValueError, match="Unknown strategy type"):
            manager._create_typed_engine(fake_strategy)


class TestSignalAggregation:
    """Test signal aggregation and conflict resolution."""

    @pytest.fixture
    def manager_with_mocked_engines(self, mock_market_data_port):
        """Create a manager with mocked engines for testing."""
        manager = TypedStrategyManager.__new__(TypedStrategyManager)
        manager.market_data_port = mock_market_data_port
        manager.strategy_allocations = {StrategyType.NUCLEAR: 0.6, StrategyType.TECL: 0.4}
        manager.logger = Mock()

        # Create mock engines
        mock_nuclear = Mock()
        mock_tecl = Mock()

        manager.strategy_engines = {
            StrategyType.NUCLEAR: mock_nuclear,
            StrategyType.TECL: mock_tecl,
        }

        return manager, mock_nuclear, mock_tecl

    def test_generate_all_signals_success(self, manager_with_mocked_engines):
        """Test successful signal generation from all strategies."""
        manager, mock_nuclear, mock_tecl = manager_with_mocked_engines

        # Setup mock signals
        nuclear_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.5")),
            reasoning="Nuclear buy signal",
        )

        tecl_signal = StrategySignal(
            symbol=Symbol("MSFT"),
            action="SELL",
            confidence=Confidence(Decimal("0.7")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="TECL sell signal",
        )

        # Configure mocks
        mock_nuclear.generate_signals.return_value = [nuclear_signal]
        mock_nuclear.validate_signals.return_value = True

        mock_tecl.generate_signals.return_value = [tecl_signal]
        mock_tecl.validate_signals.return_value = True

        # Generate signals
        timestamp = datetime.now(UTC)
        aggregated = manager.generate_all_signals(timestamp)

        # Verify results
        assert len(aggregated.signals_by_strategy) == 2
        assert aggregated.signals_by_strategy[StrategyType.NUCLEAR] == [nuclear_signal]
        assert aggregated.signals_by_strategy[StrategyType.TECL] == [tecl_signal]

        # Both signals should be in consolidated (no conflicts)
        assert len(aggregated.consolidated_signals) == 2
        assert len(aggregated.conflicts) == 0

    def test_signal_conflict_resolution_same_action(self, manager_with_mocked_engines):
        """Test conflict resolution when strategies agree on action."""
        manager, mock_nuclear, mock_tecl = manager_with_mocked_engines

        # Both strategies want to BUY AAPL
        nuclear_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.5")),
            reasoning="Nuclear buy signal",
        )

        tecl_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.6")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="TECL buy signal",
        )

        # Configure mocks
        mock_nuclear.generate_signals.return_value = [nuclear_signal]
        mock_nuclear.validate_signals.return_value = True

        mock_tecl.generate_signals.return_value = [tecl_signal]
        mock_tecl.validate_signals.return_value = True

        # Generate signals
        aggregated = manager.generate_all_signals()

        # Should have one consolidated signal and one conflict
        assert len(aggregated.consolidated_signals) == 1
        assert len(aggregated.conflicts) == 1

        # Check conflict resolution
        consolidated = aggregated.consolidated_signals[0]
        assert consolidated.symbol.value == "AAPL"
        assert consolidated.action == "BUY"

        # Confidence should be weighted average: (0.8 * 0.6 + 0.6 * 0.4) / 1.0 = 0.72
        expected_confidence = Decimal("0.8") * Decimal("0.6") + Decimal("0.6") * Decimal("0.4")
        assert float(consolidated.confidence.value) == pytest.approx(
            float(expected_confidence), rel=1e-2
        )

    def test_signal_conflict_resolution_different_actions(self, manager_with_mocked_engines):
        """Test conflict resolution when strategies disagree on action."""
        manager, mock_nuclear, mock_tecl = manager_with_mocked_engines

        # Nuclear wants to BUY, TECL wants to SELL
        nuclear_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.9")),  # High confidence
            target_allocation=Percentage(Decimal("0.5")),
            reasoning="Nuclear buy signal",
        )

        tecl_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="SELL",
            confidence=Confidence(Decimal("0.7")),  # Lower confidence
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="TECL sell signal",
        )

        # Configure mocks
        mock_nuclear.generate_signals.return_value = [nuclear_signal]
        mock_nuclear.validate_signals.return_value = True

        mock_tecl.generate_signals.return_value = [tecl_signal]
        mock_tecl.validate_signals.return_value = True

        # Generate signals
        aggregated = manager.generate_all_signals()

        # Should have one consolidated signal and one conflict
        assert len(aggregated.consolidated_signals) == 1
        assert len(aggregated.conflicts) == 1

        # Check conflict resolution - Nuclear should win due to higher weighted score
        # Nuclear: 0.9 * 0.6 = 0.54, TECL: 0.7 * 0.4 = 0.28
        consolidated = aggregated.consolidated_signals[0]
        assert consolidated.symbol.value == "AAPL"
        assert consolidated.action == "BUY"  # Nuclear should win
        assert float(consolidated.confidence.value) == pytest.approx(0.9, rel=1e-2)

        # Check conflict recording
        conflict = aggregated.conflicts[0]
        assert conflict["symbol"] == "AAPL"
        assert set(conflict["strategies"]) == {"NUCLEAR", "TECL"}
        assert set(conflict["actions"]) == {"BUY", "SELL"}
        assert conflict["resolution"] == "BUY"

    def test_engine_error_handling(self, manager_with_mocked_engines):
        """Test that engine errors are handled gracefully."""
        manager, mock_nuclear, mock_tecl = manager_with_mocked_engines

        # Nuclear engine throws an error
        mock_nuclear.generate_signals.side_effect = Exception("Nuclear engine error")

        # TECL works fine
        tecl_signal = StrategySignal(
            symbol=Symbol("MSFT"),
            action="SELL",
            confidence=Confidence(Decimal("0.7")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="TECL sell signal",
        )
        mock_tecl.generate_signals.return_value = [tecl_signal]
        mock_tecl.validate_signals.return_value = True

        # Generate signals
        aggregated = manager.generate_all_signals()

        # Should have signals from TECL only
        assert len(aggregated.signals_by_strategy) == 2  # Both strategies attempted
        assert aggregated.signals_by_strategy[StrategyType.NUCLEAR] == []  # Empty due to error
        assert aggregated.signals_by_strategy[StrategyType.TECL] == [tecl_signal]

        # Only TECL signal should be consolidated
        assert len(aggregated.consolidated_signals) == 1
        assert aggregated.consolidated_signals[0] == tecl_signal

    def test_empty_signals_handling(self, manager_with_mocked_engines):
        """Test handling when engines return no signals."""
        manager, mock_nuclear, mock_tecl = manager_with_mocked_engines

        # Both engines return empty signals
        mock_nuclear.generate_signals.return_value = []
        mock_tecl.generate_signals.return_value = []

        # Generate signals
        aggregated = manager.generate_all_signals()

        # Should have empty results
        assert len(aggregated.signals_by_strategy) == 2
        assert aggregated.signals_by_strategy[StrategyType.NUCLEAR] == []
        assert aggregated.signals_by_strategy[StrategyType.TECL] == []
        assert len(aggregated.consolidated_signals) == 0
        assert len(aggregated.conflicts) == 0

    def test_get_strategy_allocations(self, mock_market_data_port, monkeypatch):
        """Test getting strategy allocations."""
        allocations = {StrategyType.NUCLEAR: 0.7, StrategyType.TECL: 0.3}

        monkeypatch.setattr(
            "the_alchemiser.domain.strategies.typed_strategy_manager.TypedStrategyManager._create_typed_engine",
            lambda self, strategy_type: Mock(),
        )

        manager = TypedStrategyManager(mock_market_data_port, allocations)

        returned_allocations = manager.get_strategy_allocations()
        assert returned_allocations == allocations

        # Ensure it's a copy
        returned_allocations[StrategyType.KLM] = 0.1
        assert StrategyType.KLM not in manager.strategy_allocations

    def test_get_enabled_strategies(self, mock_market_data_port, monkeypatch):
        """Test getting enabled strategy types."""
        allocations = {StrategyType.NUCLEAR: 0.7, StrategyType.TECL: 0.3}

        monkeypatch.setattr(
            "the_alchemiser.domain.strategies.typed_strategy_manager.TypedStrategyManager._create_typed_engine",
            lambda self, strategy_type: Mock(),
        )

        manager = TypedStrategyManager(mock_market_data_port, allocations)

        enabled = manager.get_enabled_strategies()
        assert set(enabled) == {StrategyType.NUCLEAR, StrategyType.TECL}
