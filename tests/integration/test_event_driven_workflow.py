"""Integration tests for the complete event-driven workflow.

Tests the full chain: Strategy → Portfolio → Execution via events.
Validates idempotency, replay scenarios, and failure handling.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch
from typing import Dict, List

import pytest

from the_alchemiser.shared.events import (
    EventBus,
    SignalGenerated,
    RebalancePlanned,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry
from the_alchemiser.orchestration.event_driven_orchestrator import EventDrivenOrchestrator


@pytest.fixture
def mock_container():
    """Create a mock container for testing."""
    container = Mock()
    
    # Mock event bus
    event_bus = EventBus()
    container.services.event_bus.return_value = event_bus
    
    # Mock registry
    registry = EventHandlerRegistry()
    container.services.event_handler_registry.return_value = registry
    
    # Mock config
    container.config.paper_trading.return_value = True
    
    return container


@pytest.fixture
def event_sequence_tracker():
    """Track event sequences for validation."""
    class EventTracker:
        def __init__(self):
            self.events: List[BaseEvent] = []
            self.event_counts: Dict[str, int] = {}
            
        def track_event(self, event: BaseEvent):
            self.events.append(event)
            self.event_counts[event.event_type] = self.event_counts.get(event.event_type, 0) + 1
            
        def get_events_of_type(self, event_type: str) -> List[BaseEvent]:
            return [e for e in self.events if e.event_type == event_type]
            
        def clear(self):
            self.events.clear()
            self.event_counts.clear()
    
    return EventTracker()


class MockStrategyHandler:
    """Mock strategy handler that emits SignalGenerated events."""
    
    def __init__(self):
        self.processed_events = []
        self.call_count = 0
        
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["WorkflowStarted"]
    
    def handle_event(self, event: BaseEvent) -> None:
        self.processed_events.append(event)
        self.call_count += 1
        
        if isinstance(event, WorkflowStarted):
            # Emit SignalGenerated event
            from the_alchemiser.shared.events.bus import _current_event_bus
            
            if _current_event_bus is not None:
                signal_event = SignalGenerated(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"signal-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="strategy_v2.mock_handler",
                    source_component="MockStrategyHandler",
                    signal_count=2,
                    signals_data={
                        "AAPL": {"allocation": 0.6, "confidence": 0.8},
                        "SPY": {"allocation": 0.4, "confidence": 0.7}
                    },
                    consolidated_portfolio={
                        "AAPL": 0.6,
                        "SPY": 0.4
                    },
                    signal_hash="test-signal-hash-123",
                    market_snapshot_id="market-snapshot-456",
                    metadata={"schema_version": "1.0"}
                )
                _current_event_bus.publish(signal_event)


class MockPortfolioHandler:
    """Mock portfolio handler that emits RebalancePlanned events."""
    
    def __init__(self):
        self.processed_events = []
        self.call_count = 0
        
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["SignalGenerated"]
    
    def handle_event(self, event: BaseEvent) -> None:
        self.processed_events.append(event)
        self.call_count += 1
        
        if isinstance(event, SignalGenerated):
            # Emit RebalancePlanned event
            from the_alchemiser.shared.events.bus import _current_event_bus
            from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItem
            from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
            from decimal import Decimal
            
            if _current_event_bus is not None:
                # Create minimal RebalancePlanDTO
                plan_items = [
                    RebalancePlanItem(
                        symbol="AAPL",
                        current_weight=Decimal("0.5"),
                        target_weight=Decimal("0.6"), 
                        weight_diff=Decimal("0.1"),
                        target_value=Decimal("3000"),
                        current_value=Decimal("2500"),
                        trade_amount=Decimal("500"),
                        action="BUY",
                        priority=1
                    ),
                    RebalancePlanItem(
                        symbol="SPY",
                        current_weight=Decimal("0.5"),
                        target_weight=Decimal("0.4"),
                        weight_diff=Decimal("-0.1"),
                        target_value=Decimal("2000"),
                        current_value=Decimal("2500"),
                        trade_amount=Decimal("-500"),
                        action="SELL",
                        priority=2
                    )
                ]
                
                rebalance_plan = RebalancePlanDTO(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    timestamp=datetime.now(UTC),
                    plan_id=f"plan-{uuid.uuid4()}",
                    items=plan_items,
                    total_portfolio_value=Decimal("5000"),
                    total_trade_value=Decimal("1000")
                )
                
                # Create minimal AllocationComparisonDTO
                allocation_comparison = AllocationComparisonDTO(
                    target_values={"AAPL": Decimal("0.6"), "SPY": Decimal("0.4")},
                    current_values={"AAPL": Decimal("0.5"), "SPY": Decimal("0.5")},
                    deltas={"AAPL": Decimal("0.1"), "SPY": Decimal("-0.1")}
                )
                
                rebalance_event = RebalancePlanned(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    event_id=f"rebalance-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="portfolio_v2.mock_handler",
                    source_component="MockPortfolioHandler",
                    trades_required=True,
                    rebalance_plan=rebalance_plan,
                    allocation_comparison=allocation_comparison,
                    plan_hash="test-plan-hash-123",
                    account_snapshot_id="account-snapshot-456",
                    metadata={"schema_version": "1.0"}
                )
                _current_event_bus.publish(rebalance_event)


class MockExecutionHandler:
    """Mock execution handler that emits TradeExecuted events."""
    
    def __init__(self, success: bool = True):
        self.processed_events = []
        self.call_count = 0
        self.success = success
        
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["RebalancePlanned"]
    
    def handle_event(self, event: BaseEvent) -> None:
        self.processed_events.append(event)
        self.call_count += 1
        
        if isinstance(event, RebalancePlanned):
            # Emit TradeExecuted event
            from the_alchemiser.shared.events.bus import _current_event_bus
            
            if _current_event_bus is not None:
                if self.success:
                    trade_event = TradeExecuted(
                        correlation_id=event.correlation_id,
                        causation_id=event.event_id,
                        event_id=f"trade-{uuid.uuid4()}",
                        timestamp=datetime.now(UTC),
                        source_module="execution_v2.mock_handler",
                        source_component="MockExecutionHandler",
                        success=True,
                        orders_placed=2,
                        orders_succeeded=2,
                        execution_data={
                            "orders": [
                                {"symbol": "AAPL", "side": "buy", "qty": 10, "status": "filled"},
                                {"symbol": "SPY", "side": "sell", "qty": 5, "status": "filled"}
                            ],
                            "total_trade_value": 1500.00
                        },
                        metadata={"schema_version": "1.0"}
                    )
                    _current_event_bus.publish(trade_event)
                    
                    # Emit workflow completed
                    completed_event = WorkflowCompleted(
                        correlation_id=event.correlation_id,
                        causation_id=trade_event.event_id,
                        event_id=f"completed-{uuid.uuid4()}",
                        timestamp=datetime.now(UTC),
                        source_module="execution_v2.mock_handler",
                        source_component="MockExecutionHandler",
                        workflow_type="trading",
                        workflow_duration_ms=1500,  # Mock duration
                        success=True,
                        summary={"trades_executed": 2}
                    )
                    _current_event_bus.publish(completed_event)
                else:
                    # Emit workflow failed
                    failed_event = WorkflowFailed(
                        correlation_id=event.correlation_id,
                        causation_id=event.event_id,
                        event_id=f"failed-{uuid.uuid4()}",
                        timestamp=datetime.now(UTC),
                        source_module="execution_v2.mock_handler",
                        source_component="MockExecutionHandler",
                        workflow_type="trading",
                        failure_reason="Mock execution failure",
                        failure_step="execution",
                        error_details={"error_code": "MOCK_FAILURE"}
                    )
                    _current_event_bus.publish(failed_event)


def setup_mock_handlers(registry: EventHandlerRegistry, 
                       strategy_handler: MockStrategyHandler,
                       portfolio_handler: MockPortfolioHandler,
                       execution_handler: MockExecutionHandler):
    """Set up mock handlers in the registry."""
    
    # Register strategy handler
    registry.register_handler(
        event_type="WorkflowStarted",
        handler_factory=lambda: strategy_handler,
        module_name="strategy_v2",
        priority=100
    )
    
    # Register portfolio handler
    registry.register_handler(
        event_type="SignalGenerated",
        handler_factory=lambda: portfolio_handler,
        module_name="portfolio_v2",
        priority=100
    )
    
    # Register execution handler
    registry.register_handler(
        event_type="RebalancePlanned",
        handler_factory=lambda: execution_handler,
        module_name="execution_v2",
        priority=100
    )


def test_full_event_chain_success(mock_container, event_sequence_tracker):
    """Test successful full event chain: WorkflowStarted → SignalGenerated → RebalancePlanned → TradeExecuted → WorkflowCompleted."""
    
    # Set up mock handlers
    strategy_handler = MockStrategyHandler()
    portfolio_handler = MockPortfolioHandler()
    execution_handler = MockExecutionHandler(success=True)
    
    registry = mock_container.services.event_handler_registry()
    setup_mock_handlers(registry, strategy_handler, portfolio_handler, execution_handler)
    
    # Patch the _current_event_bus to enable event emission from handlers
    event_bus = mock_container.services.event_bus()
    
    with patch('the_alchemiser.shared.events.bus._current_event_bus', event_bus):
        # Set up event tracking
        original_publish = event_bus.publish
        
        def tracking_publish(event):
            event_sequence_tracker.track_event(event)
            return original_publish(event)
        
        event_bus.publish = tracking_publish
        
        # Create orchestrator
        orchestrator = EventDrivenOrchestrator(mock_container)
        
        # Start workflow
        correlation_id = orchestrator.start_trading_workflow()
        
        # Wait for completion
        result = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=5)
        
        # Verify success
        assert result["success"] is True
        assert result["correlation_id"] == correlation_id
        
        # Verify event sequence
        assert event_sequence_tracker.event_counts["WorkflowStarted"] == 1
        assert event_sequence_tracker.event_counts["SignalGenerated"] == 1
        assert event_sequence_tracker.event_counts["RebalancePlanned"] == 1  
        assert event_sequence_tracker.event_counts["TradeExecuted"] == 1
        assert event_sequence_tracker.event_counts["WorkflowCompleted"] == 1
        
        # Verify handlers were called
        assert strategy_handler.call_count == 1
        assert portfolio_handler.call_count == 1
        assert execution_handler.call_count == 1
        
        # Verify correlation IDs are preserved
        signal_events = event_sequence_tracker.get_events_of_type("SignalGenerated")
        assert len(signal_events) == 1
        assert signal_events[0].correlation_id == correlation_id
        
        rebalance_events = event_sequence_tracker.get_events_of_type("RebalancePlanned")
        assert len(rebalance_events) == 1
        assert rebalance_events[0].correlation_id == correlation_id
        
        trade_events = event_sequence_tracker.get_events_of_type("TradeExecuted")
        assert len(trade_events) == 1
        assert trade_events[0].correlation_id == correlation_id


def test_full_event_chain_failure(mock_container, event_sequence_tracker):
    """Test event chain with execution failure leading to WorkflowFailed."""
    
    # Set up mock handlers with failing execution
    strategy_handler = MockStrategyHandler()
    portfolio_handler = MockPortfolioHandler()
    execution_handler = MockExecutionHandler(success=False)
    
    registry = mock_container.services.event_handler_registry()
    setup_mock_handlers(registry, strategy_handler, portfolio_handler, execution_handler)
    
    event_bus = mock_container.services.event_bus()
    
    with patch('the_alchemiser.shared.events.bus._current_event_bus', event_bus):
        # Set up event tracking
        original_publish = event_bus.publish
        
        def tracking_publish(event):
            event_sequence_tracker.track_event(event)
            return original_publish(event)
        
        event_bus.publish = tracking_publish
        
        # Create orchestrator
        orchestrator = EventDrivenOrchestrator(mock_container)
        
        # Start workflow
        correlation_id = orchestrator.start_trading_workflow()
        
        # Wait for completion (should complete with failure)
        result = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=5)
        
        # Verify failure is handled
        # The workflow should still complete but mark as failed
        workflow_failed_events = event_sequence_tracker.get_events_of_type("WorkflowFailed")
        assert len(workflow_failed_events) == 1
        assert workflow_failed_events[0].correlation_id == correlation_id
        assert workflow_failed_events[0].failure_reason == "Mock execution failure"


def test_event_replay_idempotency(mock_container, event_sequence_tracker):
    """Test that replaying duplicate events doesn't cause side effects."""
    
    # Set up mock handlers
    strategy_handler = MockStrategyHandler()
    portfolio_handler = MockPortfolioHandler()
    execution_handler = MockExecutionHandler(success=True)
    
    registry = mock_container.services.event_handler_registry()
    setup_mock_handlers(registry, strategy_handler, portfolio_handler, execution_handler)
    
    event_bus = mock_container.services.event_bus()
    
    with patch('the_alchemiser.shared.events.bus._current_event_bus', event_bus):
        # Set up event tracking
        original_publish = event_bus.publish
        
        def tracking_publish(event):
            event_sequence_tracker.track_event(event)
            return original_publish(event)
        
        event_bus.publish = tracking_publish
        
        # Create orchestrator
        orchestrator = EventDrivenOrchestrator(mock_container)
        
        # Start first workflow
        correlation_id = orchestrator.start_trading_workflow()
        result1 = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=5)
        
        # Clear tracking for second run
        first_run_event_count = len(event_sequence_tracker.events)
        event_sequence_tracker.clear()
        
        # Try to start same workflow again with same correlation ID
        # This should be ignored as it's already completed
        orchestrator.start_trading_workflow(correlation_id=correlation_id)
        result2 = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=2)
        
        # The second attempt should be ignored due to idempotency
        # We should see minimal events (just the duplicate WorkflowStarted that gets ignored)
        second_run_event_count = len(event_sequence_tracker.events)
        
        # Verify first run was successful
        assert result1["success"] is True
        
        # Verify idempotency - second run should have minimal activity
        assert second_run_event_count <= 1  # Only the ignored duplicate start event


@pytest.mark.parametrize("timeout_seconds", [1, 2])  
def test_workflow_timeout_handling(mock_container, timeout_seconds):
    """Test workflow timeout scenarios."""
    
    class SlowHandler:
        """Handler that doesn't emit events to simulate timeout."""
        def can_handle(self, event_type: str) -> bool:
            return event_type in ["WorkflowStarted"]
            
        def handle_event(self, event: BaseEvent) -> None:
            # Don't emit any follow-up events to simulate hanging
            pass
    
    registry = mock_container.services.event_handler_registry()
    slow_handler = SlowHandler()
    
    registry.register_handler(
        event_type="WorkflowStarted",
        handler_factory=lambda: slow_handler,
        module_name="strategy_v2",
        priority=100
    )
    
    # Create orchestrator
    orchestrator = EventDrivenOrchestrator(mock_container)
    
    # Start workflow
    correlation_id = orchestrator.start_trading_workflow()
    
    # Wait with short timeout
    result = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=timeout_seconds)
    
    # Verify timeout is handled gracefully
    assert result["success"] is False
    assert result["completion_status"] == "timeout"
    assert result["duration_seconds"] >= timeout_seconds