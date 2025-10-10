"""Business Unit: shared | Status: current.

Tests for StrategyEngine protocol conformance.

Validates that the StrategyEngine protocol is correctly defined and that
implementations can conform to it properly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest

from the_alchemiser.shared.schemas import StrategySignal
from the_alchemiser.shared.types import StrategyEngine
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol


class MockMarketDataPort:
    """Mock implementation for testing."""

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list:
        """Mock get_bars."""
        return []

    def get_latest_quote(self, symbol: Symbol):
        """Mock get_latest_quote."""
        return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Mock get_mid_price."""
        return 100.0


class ConformingEngine:
    """Test implementation that conforms to protocol."""

    def __init__(self, market_data_port: MarketDataPort) -> None:
        """Initialize with market data port."""
        self.market_data_port = market_data_port

    def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Generate test signals."""
        if timestamp.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return [
            StrategySignal(
                correlation_id="test-corr-123",
                causation_id="test-cause-456",
                symbol="SPY",
                action="BUY",
                timestamp=timestamp,
                reasoning="Test signal generation",
            )
        ]

    def validate_signals(self, signals: list[StrategySignal]) -> None:
        """Validate test signals."""
        if not signals:
            raise ValueError("Must generate at least one signal")
        for signal in signals:
            if not signal.symbol:
                raise ValueError("Signal must have a symbol")
            if signal.action not in ["BUY", "SELL", "HOLD"]:
                raise ValueError(f"Invalid action: {signal.action}")


class NonConformingEngine:
    """Test implementation that doesn't conform to protocol (missing methods)."""

    def __init__(self, market_data_port: MarketDataPort) -> None:
        """Initialize with market data port."""
        self.market_data_port = market_data_port

    def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Generate test signals."""
        return []
    # Missing validate_signals method


def test_protocol_conformance():
    """Test that conforming implementation is recognized."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]
    assert isinstance(engine, StrategyEngine)


def test_non_conforming_rejected():
    """Test that non-conforming implementation is rejected."""
    engine = NonConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]
    # Non-conforming engines should not pass isinstance check
    assert not isinstance(engine, StrategyEngine)


def test_generate_signals_timezone_awareness():
    """Test that implementations handle timezone-aware timestamps."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    # Should work with timezone-aware datetime
    aware_ts = datetime.now(timezone.utc)
    signals = engine.generate_signals(aware_ts)
    assert isinstance(signals, list)
    assert len(signals) > 0
    assert all(isinstance(s, StrategySignal) for s in signals)


def test_generate_signals_naive_datetime_raises():
    """Test that naive datetime raises ValueError."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    # Should raise with naive datetime
    naive_ts = datetime.now()  # No timezone
    with pytest.raises(ValueError, match="timezone-aware"):
        engine.generate_signals(naive_ts)


def test_validate_signals_empty_list():
    """Test validation of empty signal list."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="at least one signal"):
        engine.validate_signals([])


def test_validate_signals_invalid_symbol():
    """Test validation of signal with empty symbol - caught by Pydantic."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    # StrategySignal itself validates and will raise during construction
    with pytest.raises(Exception):  # Pydantic ValidationError
        invalid_signal = StrategySignal(
            correlation_id="test-corr-123",
            causation_id="test-cause-456",
            symbol="",  # Empty symbol - caught by Pydantic validation
            action="BUY",
            timestamp=datetime.now(timezone.utc),
            reasoning="Test invalid symbol",
        )


def test_validate_signals_invalid_action():
    """Test validation of signal with invalid action - caught by Pydantic."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    # StrategySignal itself validates action and will raise during construction
    with pytest.raises(Exception):  # Pydantic ValidationError
        invalid_signal = StrategySignal(
            correlation_id="test-corr-123",
            causation_id="test-cause-456",
            symbol="SPY",
            action="INVALID",  # Invalid action - caught by Pydantic validation
            timestamp=datetime.now(timezone.utc),
            reasoning="Test invalid action",
        )


def test_validate_signals_valid():
    """Test validation of valid signals."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    valid_signals = [
        StrategySignal(
            correlation_id="test-corr-123",
            causation_id="test-cause-456",
            symbol="SPY",
            action="BUY",
            timestamp=datetime.now(timezone.utc),
            reasoning="Test valid signal 1",
        ),
        StrategySignal(
            correlation_id="test-corr-789",
            causation_id="test-cause-012",
            symbol="QQQ",
            action="HOLD",
            timestamp=datetime.now(timezone.utc),
            reasoning="Test valid signal 2",
        ),
    ]

    # Should not raise
    engine.validate_signals(valid_signals)


def test_protocol_idempotency():
    """Test that generate_signals is idempotent for same timestamp."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    ts = datetime.now(timezone.utc)

    # Call multiple times with same timestamp
    signals1 = engine.generate_signals(ts)
    signals2 = engine.generate_signals(ts)

    # Should produce equivalent results
    assert len(signals1) == len(signals2)
    assert signals1[0].symbol == signals2[0].symbol
    assert signals1[0].action == signals2[0].action


def test_protocol_thread_safety_basic():
    """Basic test that protocol methods can be called from different contexts."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]

    # Generate signals with different timestamps (simulating concurrent calls)
    ts1 = datetime.now(timezone.utc)
    ts2 = datetime.now(timezone.utc)

    signals1 = engine.generate_signals(ts1)
    signals2 = engine.generate_signals(ts2)

    # Both should succeed
    assert isinstance(signals1, list)
    assert isinstance(signals2, list)

    # Validate both
    engine.validate_signals(signals1)
    engine.validate_signals(signals2)
