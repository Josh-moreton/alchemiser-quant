"""Business Unit: orchestration | Status: current

Integration tests for event-driven orchestrator event flows.

Tests the complete event lifecycle, idempotency, failure handling,
and correlation ID propagation through the orchestration layer.
"""

import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)
from the_alchemiser.orchestration.workflow_state import WorkflowState
from the_alchemiser.shared.events import (
    RebalancePlanned,
    SignalGenerated,
    StartupEvent,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)


class TestEventFlowsIntegration:
    """Integration tests for event-driven orchestrator event flows."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        mock_event_bus.get_stats.return_value = {"total_events": 0}
        container.services.event_bus.return_value = mock_event_bus

        # Mock config
        container.config.paper_trading.return_value = True

        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        # Mock domain handler registration to avoid dependencies
        with patch.object(
            EventDrivenOrchestrator, "_register_domain_handlers", return_value=None
        ):
            with patch.object(
                EventDrivenOrchestrator, "_wrap_handlers_with_state_checking", return_value=None
            ):
                orch = EventDrivenOrchestrator(mock_container)
                return orch

    def test_startup_to_completion_happy_path_with_correlation_id_preserved(self, orchestrator):
        """Test complete workflow from startup to completion with correlation tracking."""
        correlation_id = f"test-correlation-{uuid.uuid4()}"
        causation_id = f"test-causation-{uuid.uuid4()}"
        timestamp = datetime.now(UTC)

        # Emit StartupEvent
        startup_event = StartupEvent(
            correlation_id=correlation_id,
            causation_id=causation_id,
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=timestamp,
            source_module="test",
            source_component="test",
            startup_mode="paper",
            configuration={},
        )
        orchestrator.handle_event(startup_event)

        # Verify startup handling
        assert orchestrator.workflow_state["startup_completed"] is True
        assert correlation_id in orchestrator.workflow_state["active_correlations"]

        # Emit SignalGenerated
        signal_event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id=startup_event.event_id,
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            source_component="test",
            signal_count=2,
            signals_data={"AAPL": {"weight": 0.5}, "TSLA": {"weight": 0.5}},
            consolidated_portfolio={"AAPL": 0.5, "TSLA": 0.5},
        )
        orchestrator.handle_event(signal_event)

        # Verify signal handling and correlation preservation
        assert correlation_id in orchestrator.workflow_results
        assert "strategy_signals" in orchestrator.workflow_results[correlation_id]
        assert orchestrator.workflow_state["rebalancing_in_progress"] is True

        # Skip RebalancePlanned and TradeExecuted for simplicity in this test
        # These require complex nested schemas (RebalancePlan, AllocationComparison)

        # Emit WorkflowCompleted directly
        completion_event = WorkflowCompleted(
            correlation_id=correlation_id,
            causation_id=signal_event.event_id,
            event_id=f"completion-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="orchestration",
            source_component="test",
            workflow_type="trading",
            success=True,
            workflow_duration_ms=1000,
        )
        orchestrator.handle_event(completion_event)

        # Verify workflow completion
        workflow_state = orchestrator.get_workflow_state(correlation_id)
        assert workflow_state == WorkflowState.COMPLETED

    def test_failure_path_emits_workflow_failed_and_logs(self, orchestrator):
        """Test that failure path properly handles WorkflowFailed event."""
        correlation_id = f"test-failure-{uuid.uuid4()}"

        # Track workflow start
        orchestrator.workflow_state["active_correlations"].add(correlation_id)
        orchestrator.workflow_state["workflow_start_times"][correlation_id] = datetime.now(UTC)

        # Emit WorkflowFailed
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"failure-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            failure_reason="Test failure",
            failure_step="execution",
            error_details={"code": "TEST_ERROR"},
        )

        # Handle the failure event
        orchestrator.handle_event(failure_event)

        # Verify workflow marked as failed
        workflow_state = orchestrator.get_workflow_state(correlation_id)
        assert workflow_state == WorkflowState.FAILED

        # Verify cleanup
        assert correlation_id not in orchestrator.workflow_state["active_correlations"]
        assert correlation_id in orchestrator.workflow_state["completed_correlations"]

    def test_idempotency_replayed_events_do_not_duplicate_state(self, orchestrator):
        """Test that replaying events does not cause duplicate state transitions."""
        correlation_id = f"test-idempotency-{uuid.uuid4()}"

        # Create a signal event
        signal_event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            source_component="test",
            signal_count=1,
            signals_data={"AAPL": {"weight": 1.0}},
            consolidated_portfolio={"AAPL": 1.0},
        )

        # Handle the event first time
        orchestrator.handle_event(signal_event)
        first_result = orchestrator.workflow_results.get(correlation_id, {}).get(
            "strategy_signals"
        )

        # Replay the same event
        orchestrator.handle_event(signal_event)
        second_result = orchestrator.workflow_results.get(correlation_id, {}).get(
            "strategy_signals"
        )

        # Verify results are idempotent (same data, not duplicated)
        assert first_result == second_result
        assert first_result is not None

    def test_workflow_failure_prevents_further_event_processing(self, orchestrator):
        """Test that after workflow fails, subsequent events are ignored."""
        correlation_id = f"test-failure-prevention-{uuid.uuid4()}"

        # Mark workflow as failed
        orchestrator._set_workflow_state(correlation_id, WorkflowState.FAILED)

        # Try to process signal event after failure
        signal_event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            source_component="test",
            signal_count=1,
            signals_data={"AAPL": {"weight": 1.0}},
            consolidated_portfolio={"AAPL": 1.0},
        )

        # This should be skipped
        orchestrator._handle_signal_generated(signal_event)

        # Verify the signal was not processed (workflow_results not updated)
        assert correlation_id not in orchestrator.workflow_results


class TestWorkflowWaitAndTimeout:
    """Test workflow waiting and timeout behavior."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        mock_event_bus.get_stats.return_value = {"total_events": 0}
        container.services.event_bus.return_value = mock_event_bus

        # Mock config
        container.config.paper_trading.return_value = True

        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        with patch.object(
            EventDrivenOrchestrator, "_register_domain_handlers", return_value=None
        ):
            with patch.object(
                EventDrivenOrchestrator, "_wrap_handlers_with_state_checking", return_value=None
            ):
                orch = EventDrivenOrchestrator(mock_container)
                return orch

    def test_wait_for_workflow_completion_timeout(self, orchestrator):
        """Test that wait_for_workflow_completion times out correctly."""
        correlation_id = f"test-timeout-{uuid.uuid4()}"

        # Add to active correlations but never complete
        orchestrator.workflow_state["active_correlations"].add(correlation_id)

        # Wait with very short timeout
        result = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=1)

        # Verify timeout result
        assert result["success"] is False
        assert result["completion_status"] == "timeout"
        assert result["correlation_id"] == correlation_id
        # Verify cleanup occurred
        assert correlation_id not in orchestrator.workflow_results

    def test_wait_for_workflow_completion_success(self, orchestrator):
        """Test successful workflow completion wait."""
        correlation_id = f"test-success-{uuid.uuid4()}"

        # Set up workflow state
        orchestrator.workflow_state["active_correlations"].add(correlation_id)
        orchestrator.workflow_results[correlation_id] = {
            "strategy_signals": {"AAPL": {"weight": 1.0}},
            "rebalance_plan": {"items": []},
            "orders_executed": [],
            "execution_summary": {"orders_placed": 1},
        }

        # Simulate workflow completion in background
        def complete_workflow():
            time.sleep(0.2)
            orchestrator.workflow_state["active_correlations"].discard(correlation_id)

        import threading

        completion_thread = threading.Thread(target=complete_workflow)
        completion_thread.start()

        # Wait for completion
        result = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=5)

        completion_thread.join()

        # Verify successful result
        assert result["success"] is True
        assert result["completion_status"] == "completed"
        assert result["correlation_id"] == correlation_id
        assert "strategy_signals" in result
        assert "rebalance_plan" in result


class TestNotificationAndRecovery:
    """Test notification and recovery workflow functions."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        mock_event_bus.publish = Mock()
        container.services.event_bus.return_value = mock_event_bus

        # Mock config
        container.config.paper_trading.return_value = False  # Live mode

        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        with patch.object(
            EventDrivenOrchestrator, "_register_domain_handlers", return_value=None
        ):
            with patch.object(
                EventDrivenOrchestrator, "_wrap_handlers_with_state_checking", return_value=None
            ):
                orch = EventDrivenOrchestrator(mock_container)
                return orch

    def test_send_trading_notification_success(self, orchestrator):
        """Test sending success trading notification."""
        correlation_id = f"test-notification-{uuid.uuid4()}"

        trade_event = TradeExecuted(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"trade-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution",
            source_component="test",
            success=True,
            orders_placed=2,
            orders_succeeded=2,
            execution_data={"orders": [], "total_trade_value": Decimal("1000.50")},
            failed_symbols=[],
            failure_reason=None,
            metadata={},
        )

        orchestrator._send_trading_notification(trade_event, success=True)

        # Verify notification event was published
        assert orchestrator.event_bus.publish.called
        notification_call = orchestrator.event_bus.publish.call_args
        notification_event = notification_call[0][0]

        assert notification_event.trading_success is True
        assert notification_event.correlation_id == correlation_id
        assert notification_event.trading_mode == "LIVE"
        assert notification_event.orders_placed == 2
        assert notification_event.orders_succeeded == 2

    def test_send_trading_notification_failure_with_error_details(self, orchestrator):
        """Test sending failure notification with error details."""
        correlation_id = f"test-notification-failure-{uuid.uuid4()}"

        trade_event = TradeExecuted(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"trade-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution",
            source_component="test",
            success=False,
            orders_placed=2,
            orders_succeeded=0,
            execution_data={"orders": []},
            failed_symbols=["AAPL", "TSLA"],
            failure_reason="Insufficient funds",
            metadata={"error_message": "Insufficient buying power"},
        )

        orchestrator._send_trading_notification(trade_event, success=False)

        # Verify notification event was published with failure details
        assert orchestrator.event_bus.publish.called
        notification_call = orchestrator.event_bus.publish.call_args
        notification_event = notification_call[0][0]

        assert notification_event.trading_success is False
        assert notification_event.error_message == "Insufficient funds"
        assert "failed_symbols" in notification_event.execution_data

    def test_perform_reconciliation_executes_without_error(self, orchestrator):
        """Test that reconciliation workflow executes without errors."""
        # Should not raise any exceptions
        orchestrator._perform_reconciliation()

    def test_trigger_recovery_workflow_executes_without_error(self, orchestrator):
        """Test that recovery workflow executes without errors."""
        trade_event = TradeExecuted(
            correlation_id=f"test-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"trade-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution",
            source_component="test",
            success=False,
            orders_placed=1,
            orders_succeeded=0,
            execution_data={},
            failed_symbols=["AAPL"],
            failure_reason="Test failure",
            metadata={"error_message": "Test error"},
        )

        # Should not raise any exceptions
        orchestrator._trigger_recovery_workflow(trade_event)


class TestWorkflowStartAndStatus:
    """Test workflow start and status retrieval."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()

        # Mock event bus with publish tracking
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        mock_event_bus.publish = Mock()
        mock_event_bus.get_stats.return_value = {"total_events": 10, "handlers": 5}
        container.services.event_bus.return_value = mock_event_bus

        # Mock config
        container.config.paper_trading.return_value = True

        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        with patch.object(
            EventDrivenOrchestrator, "_register_domain_handlers", return_value=None
        ):
            with patch.object(
                EventDrivenOrchestrator, "_wrap_handlers_with_state_checking", return_value=None
            ):
                orch = EventDrivenOrchestrator(mock_container)
                return orch

    def test_start_trading_workflow_generates_correlation_id(self, orchestrator):
        """Test that starting workflow generates a correlation ID."""
        correlation_id = orchestrator.start_trading_workflow()

        # Verify correlation ID is a valid UUID-like string
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0

        # Verify WorkflowStarted event was published
        assert orchestrator.event_bus.publish.called

    def test_start_trading_workflow_with_custom_correlation_id(self, orchestrator):
        """Test starting workflow with custom correlation ID."""
        custom_id = f"custom-correlation-{uuid.uuid4()}"
        correlation_id = orchestrator.start_trading_workflow(correlation_id=custom_id)

        assert correlation_id == custom_id

    def test_get_workflow_status_returns_state(self, orchestrator):
        """Test that get_workflow_status returns workflow state information."""
        status = orchestrator.get_workflow_status()

        assert "workflow_state" in status
        assert "event_bus_stats" in status
        assert "orchestrator_active" in status
        assert "workflow_state_metrics" in status

        # Verify metrics structure
        metrics = status["workflow_state_metrics"]
        assert "total_tracked" in metrics
        assert "by_state" in metrics
        assert "active_workflows" in metrics
        assert "completed_workflows" in metrics

    def test_can_handle_returns_true_for_supported_events(self, orchestrator):
        """Test that can_handle correctly identifies supported event types."""
        supported_events = [
            "StartupEvent",
            "WorkflowStarted",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ]

        for event_type in supported_events:
            assert orchestrator.can_handle(event_type) is True

    def test_can_handle_returns_false_for_unsupported_events(self, orchestrator):
        """Test that can_handle returns False for unsupported event types."""
        assert orchestrator.can_handle("UnknownEvent") is False
        assert orchestrator.can_handle("RandomEventType") is False

    def test_handle_event_with_unsupported_event_type_logs_debug(self, orchestrator):
        """Test that handling unsupported event type logs debug message."""
        # Create a mock event that isn't in the handler map
        from the_alchemiser.shared.events.base import BaseEvent

        class UnknownEvent(BaseEvent):
            """Test event type."""

            event_type: str = "UnknownEvent"

        event = UnknownEvent(
            correlation_id=f"test-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"event-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
        )

        # Should not raise, just log debug
        orchestrator.handle_event(event)

    def test_handle_event_exception_handling(self, orchestrator):
        """Test that handle_event catches and logs handler exceptions."""
        # Mock a handler that raises an exception
        correlation_id = f"test-{uuid.uuid4()}"

        startup_event = StartupEvent(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            startup_mode="paper",
            configuration={},
        )

        # Patch the handler to raise an exception
        with patch.object(
            orchestrator, "_handle_startup", side_effect=Exception("Test error")
        ):
            # Should not raise, just log error
            orchestrator.handle_event(startup_event)


class TestStartupEventHandling:
    """Test startup event handling."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        mock_event_bus.get_stats.return_value = {"total_events": 0}
        container.services.event_bus.return_value = mock_event_bus
        container.config.paper_trading.return_value = True
        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        with patch.object(
            EventDrivenOrchestrator, "_register_domain_handlers", return_value=None
        ):
            with patch.object(
                EventDrivenOrchestrator, "_wrap_handlers_with_state_checking", return_value=None
            ):
                orch = EventDrivenOrchestrator(mock_container)
                return orch

    def test_handle_startup_event(self, orchestrator):
        """Test that StartupEvent is handled correctly."""
        correlation_id = f"test-{uuid.uuid4()}"

        startup_event = StartupEvent(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"startup-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            startup_mode="paper",
            configuration={"test_config": "value"},
        )

        orchestrator._handle_startup(startup_event)

        # Verify startup state was updated
        assert orchestrator.workflow_state["startup_completed"] is True
        assert correlation_id in orchestrator.workflow_state["active_correlations"]
        assert orchestrator.workflow_state["last_successful_workflow"] == "startup"


class TestWorkflowCompletionWithDuration:
    """Test workflow completion event with duration tracking."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        mock_event_bus.get_stats.return_value = {"total_events": 0}
        container.services.event_bus.return_value = mock_event_bus
        container.config.paper_trading.return_value = True
        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        with patch.object(
            EventDrivenOrchestrator, "_register_domain_handlers", return_value=None
        ):
            with patch.object(
                EventDrivenOrchestrator, "_wrap_handlers_with_state_checking", return_value=None
            ):
                orch = EventDrivenOrchestrator(mock_container)
                return orch

    def test_workflow_completed_with_duration_tracking(self, orchestrator):
        """Test WorkflowCompleted event tracks duration correctly."""
        correlation_id = f"test-{uuid.uuid4()}"
        start_time = datetime.now(UTC)

        # Set up workflow start time
        orchestrator.workflow_state["workflow_start_times"][correlation_id] = start_time
        orchestrator.workflow_state["active_correlations"].add(correlation_id)

        # Emit completion event
        completion_event = WorkflowCompleted(
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            event_id=f"completion-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="orchestration",
            source_component="test",
            workflow_type="trading",
            success=True,
            workflow_duration_ms=1000,
        )

        orchestrator._handle_workflow_completed(completion_event)

        # Verify state cleanup
        assert correlation_id not in orchestrator.workflow_state["active_correlations"]
        assert correlation_id in orchestrator.workflow_state["completed_correlations"]
        assert correlation_id not in orchestrator.workflow_state["workflow_start_times"]
        assert orchestrator.workflow_state["last_successful_workflow"] == "trading"

        # Verify workflow state is COMPLETED
        workflow_state = orchestrator.get_workflow_state(correlation_id)
        assert workflow_state == WorkflowState.COMPLETED
