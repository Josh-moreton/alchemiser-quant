"""Business Unit: shared | Status: current.

Simplified integration tests for event-driven workflow.

Tests basic event creation and flow using minimal dependencies.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

# Test imports with proper path setup
try:
    from the_alchemiser.shared.events import (
        SignalGenerated,
        StartupEvent,
        WorkflowCompleted,
        WorkflowFailed,
    )
    from the_alchemiser.shared.events.base import BaseEvent
    from the_alchemiser.shared.events.bus import EventBus
    from the_alchemiser.shared.events.handlers import EventHandler
    from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio

    EVENTS_AVAILABLE = True
except ImportError as e:
    EVENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class SimpleEventCollector:
    """Simple event collector for testing."""

    def __init__(self):
        self.events_received: list[BaseEvent] = []

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event by collecting it."""
        self.events_received.append(event)

    def can_handle(self, event_type: str) -> bool:
        """Can handle any event type."""
        return True


@pytest.mark.integration
class TestSimpleEventDrivenWorkflow:
    """Simple integration tests for event-driven workflow."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        if not EVENTS_AVAILABLE:
            pytest.skip(f"Event system not available: {IMPORT_ERROR}")

        self.event_bus = EventBus()
        self.event_collector = SimpleEventCollector()

        # Subscribe to all events
        self.event_bus.subscribe_global(self.event_collector)

        # Test data
        self.correlation_id = f"test-correlation-{uuid.uuid4()}"
        self.causation_id = f"test-causation-{uuid.uuid4()}"
        self.timestamp = datetime.now(UTC)

    def test_startup_event_creation_and_flow(self):
        """Test StartupEvent creation and basic flow."""
        startup_event = StartupEvent(
            startup_mode="test",
            configuration={"test_param": "test_value"},
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="orchestration",
        )

        # Publish the event
        self.event_bus.publish(startup_event)

        # Verify event was received
        assert len(self.event_collector.events_received) == 1
        received_event = self.event_collector.events_received[0]
        assert isinstance(received_event, StartupEvent)
        assert received_event.correlation_id == self.correlation_id
        assert received_event.startup_mode == "test"

    def test_signal_generated_event_creation(self):
        """Test SignalGenerated event creation with proper schema."""
        # Create the consolidated portfolio data as dict
        target_allocations = {
            "AAPL": "0.3",  # Use strings for Decimal serialization
            "GOOGL": "0.25",
            "MSFT": "0.2",
            "TSLA": "0.15",
            "NVDA": "0.1",
        }

        # Create consolidated portfolio
        consolidated_portfolio = ConsolidatedPortfolio(
            target_allocations={k: Decimal(v) for k, v in target_allocations.items()},
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            strategy_count=1,
            source_strategies=["test_strategy"],
        )

        # Create SignalGenerated event with proper schema
        signal_event = SignalGenerated(
            signals_data={
                "strategy_name": "test_strategy",
                "generated_at": self.timestamp.isoformat(),
                "target_allocations": target_allocations,
            },
            consolidated_portfolio=consolidated_portfolio.model_dump(),
            signal_count=len(target_allocations),
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="strategy_v2",
            schema_version="1.0",
        )

        # Publish the event
        self.event_bus.publish(signal_event)

        # Verify event was received
        assert len(self.event_collector.events_received) == 1
        received_event = self.event_collector.events_received[0]
        assert isinstance(received_event, SignalGenerated)
        assert received_event.correlation_id == self.correlation_id
        assert received_event.signal_count == len(target_allocations)
        assert received_event.signals_data["strategy_name"] == "test_strategy"

    def test_workflow_completion_event(self):
        """Test WorkflowCompleted event creation."""
        completion_event = WorkflowCompleted(
            workflow_type="test_workflow",
            workflow_duration_ms=1500,
            success=True,
            summary={"message": "Test workflow completed successfully", "trades_executed": 0},
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"completion-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="test_module",
        )

        # Publish the event
        self.event_bus.publish(completion_event)

        # Verify event was received
        assert len(self.event_collector.events_received) == 1
        received_event = self.event_collector.events_received[0]
        assert isinstance(received_event, WorkflowCompleted)
        assert received_event.success is True
        assert received_event.correlation_id == self.correlation_id
        assert received_event.workflow_type == "test_workflow"
        assert "successfully" in received_event.summary["message"]

    def test_workflow_failure_event(self):
        """Test WorkflowFailed event creation."""
        failure_event = WorkflowFailed(
            workflow_type="test_workflow",
            failure_reason="Simulated test failure",
            failure_step="test_step",
            error_details={
                "error_message": "Test workflow failed - simulated error",
                "error_code": "TEST_WORKFLOW_ERROR",
            },
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"failure-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="test_module",
        )

        # Publish the event
        self.event_bus.publish(failure_event)

        # Verify event was received
        assert len(self.event_collector.events_received) == 1
        received_event = self.event_collector.events_received[0]
        assert isinstance(received_event, WorkflowFailed)
        assert received_event.correlation_id == self.correlation_id
        assert "simulated error" in received_event.error_details["error_message"]
        assert received_event.error_details["error_code"] == "TEST_WORKFLOW_ERROR"
        assert received_event.failure_step == "test_step"

    def test_multiple_events_sequence(self):
        """Test publishing multiple events in sequence."""
        # Create and publish startup event
        startup_event = StartupEvent(
            startup_mode="test_sequence",
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=self.timestamp,
            source_module="orchestration",
        )
        self.event_bus.publish(startup_event)

        # Create and publish completion event
        completion_event = WorkflowCompleted(
            workflow_type="test_sequence",
            workflow_duration_ms=1000,
            success=True,
            summary={"message": "Sequence test completed", "events_processed": 1},
            correlation_id=self.correlation_id,
            causation_id=startup_event.event_id,  # Chain causation
            event_id=f"completion-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_module",
        )
        self.event_bus.publish(completion_event)

        # Verify both events were received
        assert len(self.event_collector.events_received) == 2

        # Verify event types and correlation ID propagation
        event_types = [type(event).__name__ for event in self.event_collector.events_received]
        assert event_types == ["StartupEvent", "WorkflowCompleted"]

        # Verify correlation ID propagation
        for event in self.event_collector.events_received:
            assert event.correlation_id == self.correlation_id

        # Verify causation chain
        assert self.event_collector.events_received[1].causation_id == startup_event.event_id
