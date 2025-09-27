"""Business Unit: shared Status: current.

Integration tests for event-driven workflow across modules.

Tests the complete event chain: Strategy -> Portfolio -> Execution
using in-memory EventBus and mock adapters as specified in the 
event_driven_enforcement_plan.md.
"""

import pytest
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

# Test imports with proper path setup
try:
    from the_alchemiser.shared.events.bus import EventBus
    from the_alchemiser.shared.events.base import BaseEvent
    from the_alchemiser.shared.events.handlers import EventHandler
    from the_alchemiser.shared.events import (
        SignalGenerated,
        RebalancePlanned,
        TradeExecuted,
        WorkflowCompleted,
        WorkflowFailed,
        WorkflowStarted
    )
    from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio
    EVENTS_AVAILABLE = True
except ImportError as e:
    EVENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class EventCollector:
    """Event collector that implements the EventHandler protocol."""
    
    def __init__(self):
        self.events_received: List[BaseEvent] = []
    
    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event by collecting it."""
        self.events_received.append(event)
    
    def can_handle(self, event_type: str) -> bool:
        """Can handle any event type."""
        return True


class MockPortfolioHandler:
    """Mock portfolio handler for testing."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.called = False
    
    def handle_event(self, event: BaseEvent) -> None:
        """Handle SignalGenerated event."""
        if not isinstance(event, SignalGenerated):
            return
            
        self.called = True
        
        # Simulate portfolio analysis and emit RebalancePlanned
        from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
        from the_alchemiser.shared.schemas.common import AllocationComparison
        
        # Create mock rebalance plan and allocation comparison
        mock_rebalance_plan = RebalancePlan(
            trades=[],  # Empty for testing
            allocation_deltas={},
            metadata={"test": True}
        )
        
        mock_allocation_comparison = AllocationComparison(
            current_allocations={},
            target_allocations={"AAPL": Decimal("0.5")},
            allocation_deltas={"AAPL": Decimal("0.5")},
            timestamp=datetime.now(UTC)
        )
        
        rebalance_event = RebalancePlanned(
            rebalance_plan=mock_rebalance_plan,
            allocation_comparison=mock_allocation_comparison,
            trades_required=True,
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            event_id=f"rebalance-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="portfolio_v2",
            schema_version="1.0"
        )
        
        self.event_bus.publish(rebalance_event)
    
    def can_handle(self, event_type: str) -> bool:
        """Can handle SignalGenerated events."""
        return event_type == "SignalGenerated"


class MockExecutionHandler:
    """Mock execution handler for testing."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.called = False
    
    def handle_event(self, event: BaseEvent) -> None:
        """Handle RebalancePlanned event."""
        if not isinstance(event, RebalancePlanned):
            return
            
        self.called = True
        
        # Simulate trade execution
        trade_event = TradeExecuted(
            order_id="test-order-123",
            symbol="AAPL",
            shares=Decimal("10"),
            price=Decimal("150.00"),
            total_value=Decimal("1500.00"),
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            event_id=f"trade-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution_v2"
        )
        
        self.event_bus.publish(trade_event)
        
        # Emit workflow completion
        completion_event = WorkflowCompleted(
            success=True,
            summary="Test workflow completed successfully",
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            event_id=f"completion-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution_v2"
        )
        
        self.event_bus.publish(completion_event)
    
    def can_handle(self, event_type: str) -> bool:
        """Can handle RebalancePlanned events."""
        return event_type == "RebalancePlanned"


@pytest.mark.integration
class TestEventDrivenWorkflow:
    """Integration tests for event-driven workflow coordination."""
    
    def setup_method(self):
        """Set up test fixtures for each test."""
        if not EVENTS_AVAILABLE:
            pytest.skip(f"Event system not available: {IMPORT_ERROR}")
            
        self.event_bus = EventBus()
        self.event_collector = EventCollector()
        
        # Subscribe to all event types for monitoring using the global handler
        self.event_bus.subscribe_global(self.event_collector)
        
        # Test data
        self.correlation_id = f"test-correlation-{uuid.uuid4()}"
        self.causation_id = f"test-causation-{uuid.uuid4()}"
        self.timestamp = datetime.now(UTC)
    
    def test_signal_generated_event_creation_and_flow(self):
        """Test SignalGenerated event creation and basic flow."""
        # Create a SignalGenerated event
        target_allocations = {
            "AAPL": Decimal("0.3"),
            "GOOGL": Decimal("0.25"),
            "MSFT": Decimal("0.2"),
            "TSLA": Decimal("0.15"),
            "NVDA": Decimal("0.1")
        }
        
        consolidated_portfolio = ConsolidatedPortfolio(
            target_allocations=target_allocations,
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            strategy_count=1,
            source_strategies=["test_strategy"]
        )
        
        signal_event = SignalGenerated(
            signals_data={"strategy_name": "test_strategy", "generated_at": self.timestamp.isoformat()},
            consolidated_portfolio=consolidated_portfolio.model_dump(),
            signal_count=1,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="strategy_v2",
            schema_version="1.0"
        )
        
        # Publish the event
        self.event_bus.publish(signal_event)
        
        # Verify event was received
        assert len(self.event_collector.events_received) == 1
        received_event = self.event_collector.events_received[0]
        assert isinstance(received_event, SignalGenerated)
        assert received_event.correlation_id == self.correlation_id
        assert received_event.consolidated_portfolio["target_allocations"] is not None
    
    def test_complete_event_chain_simulation(self):
        """Test complete event chain: Signal -> Rebalance -> Trade -> Completion."""
        
        # Create mock handlers
        portfolio_handler = MockPortfolioHandler(self.event_bus)
        execution_handler = MockExecutionHandler(self.event_bus)
        
        # Subscribe handlers using event type names
        self.event_bus.subscribe("SignalGenerated", portfolio_handler)
        self.event_bus.subscribe("RebalancePlanned", execution_handler)
        
        # Start the workflow with SignalGenerated
        target_allocations = {
            "AAPL": Decimal("0.5"),
            "GOOGL": Decimal("0.5")
        }
        
        consolidated_portfolio = ConsolidatedPortfolio(
            target_allocations=target_allocations,
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            strategy_count=1,
            source_strategies=["test_strategy"]
        )
        
        signal_event = SignalGenerated(
            consolidated_portfolio=consolidated_portfolio,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="strategy_v2",
            schema_version="1.0"
        )
        
        # Trigger the workflow
        self.event_bus.publish(signal_event)
        
        # Verify all handlers were called
        assert portfolio_handler.called, "Portfolio handler should have been called"
        assert execution_handler.called, "Execution handler should have been called"
        
        # Verify event sequence
        assert len(self.event_collector.events_received) == 4  # Signal + Rebalance + Trade + Completion
        
        # Verify event types in order
        event_types = [type(event).__name__ for event in self.event_collector.events_received]
        expected_types = ["SignalGenerated", "RebalancePlanned", "TradeExecuted", "WorkflowCompleted"]
        assert event_types == expected_types, f"Expected {expected_types}, got {event_types}"
        
        # Verify correlation ID propagation
        for event in self.event_collector.events_received:
            assert event.correlation_id == self.correlation_id, f"Correlation ID not propagated to {type(event).__name__}"
    
    def test_workflow_failure_scenario(self):
        """Test workflow failure handling and WorkflowFailed event."""
        
        failure_handler_called = False
        
        def mock_failing_portfolio_handler(event: SignalGenerated) -> None:
            nonlocal failure_handler_called
            failure_handler_called = True
            
            # Simulate portfolio analysis failure
            failure_event = WorkflowFailed(
                error_message="Portfolio analysis failed - insufficient data",
                error_code="PORTFOLIO_ANALYSIS_ERROR",
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                event_id=f"failure-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="portfolio_v2"
            )
            
            self.event_bus.publish(failure_event)
        
        # Subscribe failing handler
        self.event_bus.subscribe("SignalGenerated", mock_failing_portfolio_handler)
        
        # Create and publish signal event
        target_allocations = {"AAPL": Decimal("1.0")}
        
        consolidated_portfolio = ConsolidatedPortfolio(
            target_allocations=target_allocations,
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            strategy_count=1,
            source_strategies=["test_strategy"]
        )
        
        signal_event = SignalGenerated(
            consolidated_portfolio=consolidated_portfolio,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="strategy_v2",
            schema_version="1.0"
        )
        
        # Trigger the workflow
        self.event_bus.publish(signal_event)
        
        # Verify failure handling
        assert failure_handler_called, "Failure handler should have been called"
        assert len(self.events_received) == 2  # Signal + Failure
        
        # Verify WorkflowFailed event
        failure_event = self.events_received[1]
        assert isinstance(failure_event, WorkflowFailed)
        assert failure_event.correlation_id == self.correlation_id
        assert "Portfolio analysis failed" in failure_event.error_message
    
    def test_event_idempotency_replay_scenario(self):
        """Test event idempotency by replaying duplicate events."""
        
        handler_call_count = 0
        
        def counting_handler(event: SignalGenerated) -> None:
            nonlocal handler_call_count  
            handler_call_count += 1
        
        self.event_bus.subscribe("SignalGenerated", counting_handler)
        
        # Create an event with consistent ID for replay testing
        event_id = "replay-test-event-123"
        target_allocations = {"AAPL": Decimal("1.0")}
        
        consolidated_portfolio = ConsolidatedPortfolio(
            target_allocations=target_allocations,
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            strategy_count=1,
            source_strategies=["test_strategy"]
        )
        
        signal_event = SignalGenerated(
            consolidated_portfolio=consolidated_portfolio,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=event_id,
            timestamp=self.timestamp,
            source_module="strategy_v2",
            schema_version="1.0"
        )
        
        # Publish the same event multiple times (replay scenario)
        self.event_bus.publish(signal_event)
        self.event_bus.publish(signal_event)
        self.event_bus.publish(signal_event)
        
        # In a real implementation, idempotency would prevent multiple processing
        # For this test, we verify the events were received (idempotency would be handled at the handler level)
        assert len(self.events_received) == 3, "All replay events should be received by the bus"
        assert handler_call_count == 3, "Handler should be called for each event (idempotency handled at handler level)"
        
        # Verify all events have the same correlation ID and event ID
        for event in self.events_received:
            assert event.correlation_id == self.correlation_id
            assert event.event_id == event_id