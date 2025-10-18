"""Business Unit: orchestration | Status: current

Workflow state management tests.

Tests workflow state tracking and failure prevention logic to ensure
handlers don't process events after workflow failures.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)
from the_alchemiser.orchestration.workflow_state import (
    StateCheckingHandlerWrapper,
    WorkflowState,
)
from the_alchemiser.shared.events import (
    SignalGenerated,
    WorkflowCompleted,
    WorkflowFailed,
)


class TestWorkflowStateManagement:
    """Test workflow state tracking and failure prevention."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container."""
        container = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        mock_event_bus._handlers = {}
        container.services.event_bus.return_value = mock_event_bus

        # Mock config
        container.config.paper_trading.return_value = True

        return container

    @pytest.fixture
    def orchestrator(self, mock_container):
        """Create an orchestrator instance for testing."""
        # We need to mock the domain handler registration to avoid dependencies
        original_register = EventDrivenOrchestrator._register_domain_handlers
        EventDrivenOrchestrator._register_domain_handlers = Mock()

        try:
            orch = EventDrivenOrchestrator(mock_container)
            return orch
        finally:
            EventDrivenOrchestrator._register_domain_handlers = original_register

    def test_workflow_starts_in_running_state(self, orchestrator):
        """Test that new workflows are marked as RUNNING."""
        correlation_id = str(uuid.uuid4())

        # Set workflow state to RUNNING (simulating workflow start)
        orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)

        # Verify state is RUNNING
        assert orchestrator.is_workflow_active(correlation_id)
        assert not orchestrator.is_workflow_failed(correlation_id)
        assert orchestrator.workflow_states[correlation_id] == WorkflowState.RUNNING

    def test_workflow_failure_marks_as_failed(self, orchestrator):
        """Test that workflow failures are marked correctly."""
        correlation_id = str(uuid.uuid4())

        # Start workflow first (set to RUNNING state)
        orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)

        # Create and handle WorkflowFailed event
        fail_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id="test",
            event_id=f"workflow-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            failure_reason="Account has negative cash balance",
            failure_step="portfolio_analysis",
            error_details={},
        )

        orchestrator._handle_workflow_failed(fail_event)

        # Verify state is FAILED
        assert orchestrator.is_workflow_failed(correlation_id)
        assert not orchestrator.is_workflow_active(correlation_id)
        assert orchestrator.workflow_states[correlation_id] == WorkflowState.FAILED

    def test_workflow_completion_marks_as_completed(self, orchestrator):
        """Test that workflow completion is marked correctly."""
        correlation_id = str(uuid.uuid4())

        # Start workflow first (set to RUNNING state)
        orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)

        # Create and handle WorkflowCompleted event
        complete_event = WorkflowCompleted(
            correlation_id=correlation_id,
            causation_id="test",
            event_id=f"workflow-completed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            workflow_duration_ms=1000,
            success=True,
            summary={},
        )

        orchestrator._handle_workflow_completed(complete_event)

        # Verify state is COMPLETED
        assert not orchestrator.is_workflow_active(correlation_id)
        assert not orchestrator.is_workflow_failed(correlation_id)
        assert orchestrator.workflow_states[correlation_id] == WorkflowState.COMPLETED

    def test_state_checking_wrapper_skips_failed_workflows(self, orchestrator):
        """Test that StateCheckingHandlerWrapper skips events for failed workflows."""
        correlation_id = str(uuid.uuid4())

        # Mark workflow as failed
        orchestrator._set_workflow_state(correlation_id, WorkflowState.FAILED)

        # Create a mock handler
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True

        # Wrap the handler
        wrapper = StateCheckingHandlerWrapper(
            mock_handler,
            orchestrator,
            "SignalGenerated",
            orchestrator.logger,
        )

        # Create an event
        event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id="test",
            event_id=f"signal-generated-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
            metadata={},
        )

        # Handle the event through wrapper
        wrapper.handle_event(event)

        # Verify the wrapped handler was NOT called
        mock_handler.handle_event.assert_not_called()

    def test_state_checking_wrapper_allows_active_workflows(self, orchestrator):
        """Test that StateCheckingHandlerWrapper allows events for active workflows."""
        correlation_id = str(uuid.uuid4())

        # Mark workflow as running
        orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)

        # Create a mock handler
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True

        # Wrap the handler
        wrapper = StateCheckingHandlerWrapper(
            mock_handler,
            orchestrator,
            "SignalGenerated",
            orchestrator.logger,
        )

        # Create an event
        event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id="test",
            event_id=f"signal-generated-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
            metadata={},
        )

        # Handle the event through wrapper
        wrapper.handle_event(event)

        # Verify the wrapped handler WAS called
        mock_handler.handle_event.assert_called_once_with(event)

    def test_thread_safety_of_state_checking(self, orchestrator):
        """Test that workflow state checking is thread-safe."""
        correlation_id = str(uuid.uuid4())

        # Test concurrent access to state checking methods
        import threading

        results = []

        def check_state():
            for _ in range(100):
                orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)
                is_failed = orchestrator.is_workflow_failed(correlation_id)
                is_active = orchestrator.is_workflow_active(correlation_id)
                results.append((is_failed, is_active))

        # Run multiple threads
        threads = [threading.Thread(target=check_state) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Verify no exceptions and state is consistent
        assert len(results) == 500  # 5 threads * 100 iterations

    def test_multiple_workflows_have_independent_states(self, orchestrator):
        """Test that different workflows have independent states."""
        correlation_id_1 = str(uuid.uuid4())
        correlation_id_2 = str(uuid.uuid4())

        # Set different states for different workflows
        orchestrator._set_workflow_state(correlation_id_1, WorkflowState.RUNNING)
        orchestrator._set_workflow_state(correlation_id_2, WorkflowState.FAILED)

        # Verify states are independent
        assert orchestrator.is_workflow_active(correlation_id_1)
        assert not orchestrator.is_workflow_failed(correlation_id_1)

        assert orchestrator.is_workflow_failed(correlation_id_2)
        assert not orchestrator.is_workflow_active(correlation_id_2)

    def test_get_workflow_state(self, orchestrator):
        """Test getting workflow state directly."""
        correlation_id = str(uuid.uuid4())

        # Initially, state should be None
        assert orchestrator.get_workflow_state(correlation_id) is None

        # Set state to RUNNING
        orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)
        assert orchestrator.get_workflow_state(correlation_id) == WorkflowState.RUNNING

        # Set state to FAILED
        orchestrator._set_workflow_state(correlation_id, WorkflowState.FAILED)
        assert orchestrator.get_workflow_state(correlation_id) == WorkflowState.FAILED

        # Set state to COMPLETED
        orchestrator._set_workflow_state(correlation_id, WorkflowState.COMPLETED)
        assert orchestrator.get_workflow_state(correlation_id) == WorkflowState.COMPLETED

    def test_cleanup_workflow_state(self, orchestrator):
        """Test cleaning up workflow state."""
        correlation_id = str(uuid.uuid4())

        # Set a workflow state
        orchestrator._set_workflow_state(correlation_id, WorkflowState.COMPLETED)
        assert orchestrator.get_workflow_state(correlation_id) == WorkflowState.COMPLETED

        # Clean up the state
        result = orchestrator.cleanup_workflow_state(correlation_id)
        assert result is True
        assert orchestrator.get_workflow_state(correlation_id) is None

        # Try to clean up non-existent state
        result = orchestrator.cleanup_workflow_state(correlation_id)
        assert result is False

    def test_workflow_state_metrics(self, orchestrator):
        """Test workflow state metrics collection."""
        # Create workflows in different states
        running_id = str(uuid.uuid4())
        failed_id = str(uuid.uuid4())
        completed_id = str(uuid.uuid4())

        orchestrator._set_workflow_state(running_id, WorkflowState.RUNNING)
        orchestrator._set_workflow_state(failed_id, WorkflowState.FAILED)
        orchestrator._set_workflow_state(completed_id, WorkflowState.COMPLETED)

        # Get workflow status
        status = orchestrator.get_workflow_status()

        # Verify metrics are included
        assert "workflow_state_metrics" in status
        metrics = status["workflow_state_metrics"]

        assert metrics["total_tracked"] == 3
        assert metrics["by_state"]["running"] == 1
        assert metrics["by_state"]["failed"] == 1
        assert metrics["by_state"]["completed"] == 1
