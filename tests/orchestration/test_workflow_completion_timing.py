#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Tests for workflow completion timing to ensure proper event ordering.

Verifies that workflows remain "active" until WorkflowCompleted is processed,
not just when TradeExecuted is received.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from the_alchemiser.shared.events import (
    TradeExecuted,
    WorkflowCompleted,
    WorkflowStarted,
)


class TestWorkflowCompletionTiming:
    """Tests for workflow completion timing and state management."""

    @patch('the_alchemiser.strategy_v2.register_strategy_handlers')
    @patch('the_alchemiser.portfolio_v2.register_portfolio_handlers')
    @patch('the_alchemiser.execution_v2.register_execution_handlers')
    @patch('the_alchemiser.notifications_v2.register_notification_handlers')
    def test_workflow_remains_active_after_trade_executed(
        self, mock_notif, mock_exec, mock_port, mock_strat
    ):
        """Test that workflow remains in active_correlations after TradeExecuted."""
        from the_alchemiser.orchestration.event_driven_orchestrator import (
            EventDrivenOrchestrator,
        )
        
        # Create mock container
        mock_container = MagicMock()
        mock_container.config.paper_trading.return_value = True
        
        # Create orchestrator
        orchestrator = EventDrivenOrchestrator(mock_container)
        
        # Create correlation_id and start workflow
        correlation_id = str(uuid.uuid4())
        workflow_started = WorkflowStarted(
            correlation_id=correlation_id,
            causation_id=f"test-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="test",
            configuration={},
        )
        
        # Handle WorkflowStarted
        orchestrator._handle_workflow_started(workflow_started)
        
        # Verify workflow is active
        assert correlation_id in orchestrator.workflow_state["active_correlations"]
        assert correlation_id not in orchestrator.workflow_state["completed_correlations"]
        
        # Create and handle TradeExecuted event
        trade_executed = TradeExecuted(
            correlation_id=correlation_id,
            causation_id=workflow_started.event_id,
            event_id=f"trade-executed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            success=True,
            orders_placed=1,
            orders_succeeded=1,
            execution_data={},
        )
        
        orchestrator._handle_trade_executed(trade_executed)
        
        # CRITICAL: Workflow should STILL be in active_correlations after TradeExecuted
        # because the workflow isn't actually complete until WorkflowCompleted is processed
        assert correlation_id in orchestrator.workflow_state["active_correlations"], (
            "Workflow should remain active after TradeExecuted until WorkflowCompleted is processed"
        )
        assert correlation_id not in orchestrator.workflow_state["completed_correlations"]

    @patch('the_alchemiser.strategy_v2.register_strategy_handlers')
    @patch('the_alchemiser.portfolio_v2.register_portfolio_handlers')
    @patch('the_alchemiser.execution_v2.register_execution_handlers')
    @patch('the_alchemiser.notifications_v2.register_notification_handlers')
    def test_workflow_removed_from_active_after_workflow_completed(
        self, mock_notif, mock_exec, mock_port, mock_strat
    ):
        """Test that workflow is removed from active_correlations after WorkflowCompleted."""
        from the_alchemiser.orchestration.event_driven_orchestrator import (
            EventDrivenOrchestrator,
        )
        
        # Create mock container
        mock_container = MagicMock()
        mock_container.config.paper_trading.return_value = True
        
        # Create orchestrator
        orchestrator = EventDrivenOrchestrator(mock_container)
        
        # Create correlation_id and start workflow
        correlation_id = str(uuid.uuid4())
        workflow_started = WorkflowStarted(
            correlation_id=correlation_id,
            causation_id=f"test-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="test",
            configuration={},
        )
        
        # Handle WorkflowStarted
        orchestrator._handle_workflow_started(workflow_started)
        
        # Handle TradeExecuted
        trade_executed = TradeExecuted(
            correlation_id=correlation_id,
            causation_id=workflow_started.event_id,
            event_id=f"trade-executed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            success=True,
            orders_placed=1,
            orders_succeeded=1,
            execution_data={},
        )
        
        orchestrator._handle_trade_executed(trade_executed)
        
        # Workflow still active
        assert correlation_id in orchestrator.workflow_state["active_correlations"]
        
        # Now handle WorkflowCompleted
        workflow_completed = WorkflowCompleted(
            correlation_id=correlation_id,
            causation_id=trade_executed.event_id,
            event_id=f"workflow-completed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            workflow_duration_ms=1000,
            success=True,
            summary={},
        )
        
        orchestrator._handle_workflow_completed(workflow_completed)
        
        # Now workflow should be removed from active and added to completed
        assert correlation_id not in orchestrator.workflow_state["active_correlations"], (
            "Workflow should be removed from active_correlations after WorkflowCompleted"
        )
        assert correlation_id in orchestrator.workflow_state["completed_correlations"], (
            "Workflow should be added to completed_correlations after WorkflowCompleted"
        )

    @patch('the_alchemiser.strategy_v2.register_strategy_handlers')
    @patch('the_alchemiser.portfolio_v2.register_portfolio_handlers')
    @patch('the_alchemiser.execution_v2.register_execution_handlers')
    @patch('the_alchemiser.notifications_v2.register_notification_handlers')
    def test_duplicate_workflow_started_detection_after_completion(
        self, mock_notif, mock_exec, mock_port, mock_strat
    ):
        """Test that duplicate WorkflowStarted is properly detected after completion."""
        from the_alchemiser.orchestration.event_driven_orchestrator import (
            EventDrivenOrchestrator,
        )
        
        # Create mock container
        mock_container = MagicMock()
        mock_container.config.paper_trading.return_value = True
        
        # Create orchestrator
        orchestrator = EventDrivenOrchestrator(mock_container)
        
        # Create correlation_id
        correlation_id = str(uuid.uuid4())
        
        # Create WorkflowStarted event
        workflow_started = WorkflowStarted(
            correlation_id=correlation_id,
            causation_id=f"test-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="test",
            configuration={},
        )
        
        # Handle first WorkflowStarted - should process normally
        orchestrator._handle_workflow_started(workflow_started)
        assert correlation_id in orchestrator.workflow_state["active_correlations"]
        
        # Complete the workflow
        workflow_completed = WorkflowCompleted(
            correlation_id=correlation_id,
            causation_id=workflow_started.event_id,
            event_id=f"workflow-completed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            workflow_duration_ms=1000,
            success=True,
            summary={},
        )
        
        orchestrator._handle_workflow_completed(workflow_completed)
        assert correlation_id in orchestrator.workflow_state["completed_correlations"]
        assert correlation_id not in orchestrator.workflow_state["active_correlations"]
        
        # Try to handle another WorkflowStarted with SAME correlation_id
        # This should be detected as duplicate and ignored
        duplicate_workflow_started = WorkflowStarted(
            correlation_id=correlation_id,  # SAME correlation_id!
            causation_id=f"test-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="test",
            configuration={},
        )
        
        orchestrator._handle_workflow_started(duplicate_workflow_started)
        
        # Workflow should NOT be added back to active_correlations
        assert correlation_id not in orchestrator.workflow_state["active_correlations"], (
            "Duplicate WorkflowStarted should not add correlation_id back to active_correlations"
        )
        # Should still be in completed_correlations
        assert correlation_id in orchestrator.workflow_state["completed_correlations"]
