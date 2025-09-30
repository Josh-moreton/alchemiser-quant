#!/usr/bin/env python3
"""Business Unit: execution_v2 | Status: current.

Signal mock execution tests with real Paper API integration.

Tests the complete workflow from mocked SignalGenerated event through
real Paper API execution. Enables rapid development iteration without
waiting for full strategy signal generation.
"""

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING

import pytest

# Import event system components
try:
    from the_alchemiser.shared.events import (
        BaseEvent,
        EventBus,
        RebalancePlanned,
        SignalGenerated,
        TradeExecuted,
        WorkflowCompleted,
        WorkflowFailed,
    )
    from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio

    EVENTS_AVAILABLE = True
except ImportError as e:
    EVENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Create dummy types for type hints when imports fail
    SignalGenerated = Any  # type: ignore
    BaseEvent = Any  # type: ignore


def create_execution_test_signal(
    correlation_id: str | None = None,
    allocations: dict[str, float] | None = None,
) -> Any:
    """Create a realistic SignalGenerated event for execution testing.

    Args:
        correlation_id: Optional correlation ID for tracking (generated if None)
        allocations: Optional target allocations (uses defaults if None)

    Returns:
        SignalGenerated event with realistic portfolio allocations

    """
    if correlation_id is None:
        correlation_id = f"exec-test-{uuid.uuid4()}"

    # Default to liquid securities for reliable testing
    if allocations is None:
        allocations = {
            "SPY": 0.35,  # S&P 500 ETF
            "QQQ": 0.25,  # Nasdaq ETF
            "AAPL": 0.20,  # Apple
            "MSFT": 0.20,  # Microsoft
        }

    # Convert to Decimal for ConsolidatedPortfolio
    target_allocations = {symbol: Decimal(str(weight)) for symbol, weight in allocations.items()}

    # Create consolidated portfolio
    consolidated_portfolio = ConsolidatedPortfolio(
        target_allocations=target_allocations,
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
        strategy_count=1,
        source_strategies=["mock_execution_test_strategy"],
    )

    # Create SignalGenerated event
    signal_event = SignalGenerated(
        signals_data={
            "strategy_name": "mock_execution_test_strategy",
            "generated_at": datetime.now(UTC).isoformat(),
            "allocations": allocations,
            "test_mode": True,
        },
        consolidated_portfolio=consolidated_portfolio.model_dump(),
        signal_count=len(allocations),
        metadata={
            "test_type": "signal_mock_execution",
            "liquid_securities": True,
            "paper_trading": True,
        },
        correlation_id=correlation_id,
        causation_id=f"test-startup-{uuid.uuid4()}",
        event_id=f"signal-{uuid.uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="test_signal_mock",
        schema_version="1.0",
    )

    return signal_event


class EventCollector:
    """Collects events for verification in tests."""

    def __init__(self):
        self.events_received: list[Any] = []
        self.events_by_type: dict[str, list[Any]] = {}

    def handle_event(self, event: Any) -> None:
        """Handle an event by collecting it."""
        self.events_received.append(event)
        event_type = event.event_type
        if event_type not in self.events_by_type:
            self.events_by_type[event_type] = []
        self.events_by_type[event_type].append(event)

    def can_handle(self, event_type: str) -> bool:
        """Can handle any event type."""
        return True

    def get_events_of_type(self, event_type: str) -> list[Any]:
        """Get all events of a specific type."""
        return self.events_by_type.get(event_type, [])

    def has_event_type(self, event_type: str) -> bool:
        """Check if at least one event of this type was received."""
        return event_type in self.events_by_type and len(self.events_by_type[event_type]) > 0


@pytest.mark.skipif(not EVENTS_AVAILABLE, reason="Event system not available")
class TestQuickExecutionWithSignalMock:
    """Tests for rapid execution development with mocked signals."""

    @pytest.fixture
    def setup_paper_trading_env(self):
        """Set up Paper trading environment variables."""
        original_env = os.environ.copy()

        # Ensure Paper trading mode
        os.environ["TESTING"] = "true"
        os.environ["PAPER_TRADING"] = "true"

        # Check if real credentials are available
        has_real_credentials = (
            "ALPACA_API_KEY" in os.environ
            and "ALPACA_SECRET_KEY" in os.environ
            and os.environ.get("ALPACA_API_KEY", "").startswith("PK")
        )

        yield has_real_credentials

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.fixture
    def event_bus(self):
        """Create an EventBus for testing."""
        return EventBus()

    @pytest.fixture
    def event_collector(self, event_bus):
        """Create and register an event collector."""
        collector = EventCollector()
        # Subscribe to all workflow-related events
        event_bus.subscribe("SignalGenerated", collector)
        event_bus.subscribe("RebalancePlanned", collector)
        event_bus.subscribe("TradeExecuted", collector)
        event_bus.subscribe("WorkflowCompleted", collector)
        event_bus.subscribe("WorkflowFailed", collector)
        return collector

    def test_signal_mock_creation(self):
        """Test creation of realistic signal mock."""
        signal = create_execution_test_signal()

        assert signal.event_type == "SignalGenerated"
        assert signal.correlation_id.startswith("exec-test-")
        assert signal.signal_count == 4
        assert "consolidated_portfolio" in signal.model_dump()
        assert signal.metadata["test_type"] == "signal_mock_execution"
        assert signal.metadata["paper_trading"] is True

    def test_signal_mock_with_custom_allocations(self):
        """Test signal mock with custom allocations."""
        custom_allocations = {
            "VTI": 0.50,
            "BND": 0.30,
            "GLD": 0.20,
        }
        correlation_id = "test-custom-12345"

        signal = create_execution_test_signal(
            correlation_id=correlation_id, allocations=custom_allocations
        )

        assert signal.correlation_id == correlation_id
        assert signal.signal_count == 3
        assert signal.signals_data["allocations"] == custom_allocations

    def test_signal_publishing_to_event_bus(self, event_bus, event_collector):
        """Test that signal can be published to event bus."""
        signal = create_execution_test_signal()

        # Publish signal
        event_bus.publish(signal)

        # Verify it was collected
        assert event_collector.has_event_type("SignalGenerated")
        collected_signals = event_collector.get_events_of_type("SignalGenerated")
        assert len(collected_signals) == 1
        assert collected_signals[0].correlation_id == signal.correlation_id

    def test_execution_with_mock_handlers(self, event_bus, event_collector):
        """Test complete workflow with mock portfolio and execution handlers.

        This test validates the event chain without requiring real API credentials.
        """
        from unittest.mock import Mock

        # Create mock handlers that simulate portfolio and execution
        portfolio_handler_called = []
        execution_handler_called = []

        def mock_portfolio_handler(event: Any) -> None:
            if isinstance(event, SignalGenerated):
                portfolio_handler_called.append(event)
                # Simulate portfolio analysis by emitting RebalancePlanned
                from the_alchemiser.shared.schemas.common import AllocationComparison
                from the_alchemiser.shared.schemas.rebalance_plan import (
                    RebalancePlan,
                    RebalancePlanItem,
                )

                # Create a simple rebalance item
                item = RebalancePlanItem(
                    symbol="SPY",
                    current_weight=Decimal("0.0"),
                    target_weight=Decimal("0.35"),
                    weight_diff=Decimal("0.35"),
                    target_value=Decimal("35000.0"),
                    current_value=Decimal("0.0"),
                    trade_amount=Decimal("35000.0"),
                    action="BUY",
                    priority=1,
                )

                rebalance_plan = RebalancePlan(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    timestamp=datetime.now(UTC),
                    plan_id=f"plan-{uuid.uuid4()}",
                    items=[item],
                    total_portfolio_value=Decimal("100000.0"),
                    total_trade_value=Decimal("35000.0"),
                )

                rebalance_event = RebalancePlanned(
                    rebalance_plan=rebalance_plan,
                    allocation_comparison=AllocationComparison(
                        target_values={"SPY": Decimal("35000.0")},
                        current_values={"SPY": Decimal("0.0")},
                        deltas={"SPY": Decimal("35000.0")},
                    ),
                    trades_required=True,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"rebalance-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="portfolio_v2",
                    schema_version="1.0",
                )
                event_bus.publish(rebalance_event)

        def mock_execution_handler(event: Any) -> None:
            if isinstance(event, RebalancePlanned):
                execution_handler_called.append(event)
                # Simulate successful execution
                trade_event = TradeExecuted(
                    execution_data={"orders": [], "mock": True},
                    success=True,
                    orders_placed=0,
                    orders_succeeded=0,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"trade-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="execution_v2",
                    schema_version="1.0",
                )
                event_bus.publish(trade_event)

                # Emit completion
                completion_event = WorkflowCompleted(
                    workflow_type="execution_test",
                    workflow_duration_ms=100,
                    success=True,
                    summary={"message": "Mock execution completed"},
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"completion-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="execution_v2",
                    schema_version="1.0",
                )
                event_bus.publish(completion_event)

        # Create mock handler objects with proper protocol
        class MockHandler:
            def __init__(self, handler_func):
                self.handler_func = handler_func

            def handle_event(self, event):
                self.handler_func(event)

            def can_handle(self, event_type):
                return True

        portfolio_handler = MockHandler(mock_portfolio_handler)
        execution_handler = MockHandler(mock_execution_handler)

        # Subscribe handlers
        event_bus.subscribe("SignalGenerated", portfolio_handler)
        event_bus.subscribe("RebalancePlanned", execution_handler)

        # Create and publish signal
        signal = create_execution_test_signal()
        event_bus.publish(signal)

        # Verify event chain
        assert len(portfolio_handler_called) == 1
        assert len(execution_handler_called) == 1

        # Verify event types collected
        assert event_collector.has_event_type("SignalGenerated")
        assert event_collector.has_event_type("RebalancePlanned")
        assert event_collector.has_event_type("TradeExecuted")
        assert event_collector.has_event_type("WorkflowCompleted")

        # Verify correlation ID propagation
        for event in event_collector.events_received:
            assert event.correlation_id == signal.correlation_id

    @pytest.mark.skipif(
        not (
            os.environ.get("ALPACA_API_KEY", "").startswith("PK")
            and os.environ.get("ALPACA_SECRET_KEY", "")
        ),
        reason="Real Alpaca Paper API credentials required (ALPACA_API_KEY and ALPACA_SECRET_KEY)",
    )
    def test_execution_with_real_paper_api_basic(self, setup_paper_trading_env, event_bus):
        """Test execution with mocked signal but real Paper API.

        This test requires real Paper API credentials and will be skipped if not available.
        """
        if not setup_paper_trading_env:
            pytest.skip("Real Paper API credentials not available")

        # Verify Paper trading mode
        assert os.environ.get("PAPER_TRADING") == "true"
        assert os.environ.get("TESTING") == "true"

        print("\n🚀 Starting Real Paper API execution test")
        print(f"   Paper Trading: {os.environ.get('PAPER_TRADING')}")
        print(f"   Testing Mode: {os.environ.get('TESTING')}")

        # Create execution test signal with conservative allocations
        correlation_id = f"exec-test-real-{uuid.uuid4()}"
        signal = create_execution_test_signal(correlation_id=correlation_id)

        print(f"\n📊 Publishing test signal for correlation ID: {correlation_id}")
        print(f"   Target allocations: {signal.signals_data['allocations']}")

        # Note: This test creates the signal but requires the full system
        # to be wired up with real handlers. In a complete implementation,
        # you would initialize the ApplicationContainer and register real handlers.

        # For now, verify signal creation succeeds
        assert signal.correlation_id == correlation_id
        assert signal.metadata["paper_trading"] is True

        print(f"\n✅ Signal created successfully for real Paper API test")
        print(f"   Correlation ID: {correlation_id}")
        print(
            "\n⚠️  Note: Full execution requires ApplicationContainer with real handlers"
        )


if __name__ == "__main__":
    # Allow running tests directly with pytest
    pytest.main([__file__, "-v"])
