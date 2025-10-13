"""Business Unit: orchestration | Status: current

Integration test for workflow failure propagation.

Tests the end-to-end scenario where a workflow fails (e.g., negative cash balance)
and ensures subsequent event handlers properly skip processing.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch
import uuid

import pytest

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)
from the_alchemiser.orchestration.workflow_state import WorkflowState
from the_alchemiser.shared.events import (
    BaseEvent,
    SignalGenerated,
    RebalancePlanned,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan


class MockHandler:
    """Mock event handler for testing that properly implements EventHandler protocol."""

    def __init__(self, name: str = "MockHandler"):
        """Initialize mock handler.

        Args:
            name: Name for this handler instance

        """
        self.name = name
        self.handle_event_calls = []
        self.can_handle_calls = []

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event.

        Args:
            event: The event to handle

        """
        self.handle_event_calls.append(event)

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            Always returns True for testing

        """
        self.can_handle_calls.append(event_type)
        return True

    def reset_mock(self) -> None:
        """Reset call tracking."""
        self.handle_event_calls = []
        self.can_handle_calls = []


class TestWorkflowFailurePropagation:
    """Integration tests for workflow failure propagation."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock application container with event bus."""
        container = Mock()

        # Create a real event bus for integration testing
        from the_alchemiser.shared.events.bus import EventBus

        event_bus = EventBus()
        container.services.event_bus.return_value = event_bus

        # Mock config
        container.config.paper_trading.return_value = True

        return container

    @pytest.fixture
    def orchestrator_with_mocked_handlers(self, mock_container):
        """Create orchestrator with mocked domain handler registration."""
        # Mock the domain handler registration to avoid dependencies
        with patch.object(EventDrivenOrchestrator, "_register_domain_handlers"):
            orch = EventDrivenOrchestrator(mock_container)
            return orch

    def test_negative_cash_balance_scenario_prevents_further_processing(
        self, orchestrator_with_mocked_handlers
    ):
        """Test that negative cash balance failure prevents downstream event processing.

        This simulates the scenario from the issue:
        1. Workflow starts (SignalGenerated event is processed)
        2. Portfolio analysis fails with negative cash balance
        3. WorkflowFailed event is published
        4. Subsequent handlers should skip processing for this correlation_id
        """
        orchestrator = orchestrator_with_mocked_handlers
        correlation_id = str(uuid.uuid4())

        # Create mock handlers to track calls
        signal_handler = MockHandler("SignalHandler")
        portfolio_handler = MockHandler("PortfolioHandler")
        execution_handler = MockHandler("ExecutionHandler")

        # Register handlers with event bus
        event_bus = orchestrator.event_bus
        event_bus.subscribe("SignalGenerated", signal_handler)
        event_bus.subscribe("SignalGenerated", portfolio_handler)
        event_bus.subscribe("RebalancePlanned", execution_handler)

        # Wrap handlers with state checking as the orchestrator would
        orchestrator._wrap_handlers_with_state_checking()

        # Step 1: Start workflow (set to RUNNING state)
        orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)

        # Verify workflow is RUNNING
        assert orchestrator.is_workflow_active(correlation_id)

        # Step 2: Emit SignalGenerated event
        signal_event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id="test",
            event_id=f"signal-generated-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy_v2",
            source_component="SignalGenerationHandler",
            signals_data={"DSL": {"symbol": "SPY", "action": "BUY"}},
            consolidated_portfolio={"target_allocations": {"SPY": 1.0}},
            signal_count=1,
            metadata={},
        )
        event_bus.publish(signal_event)

        # Handlers should be called for RUNNING workflow
        assert len(signal_handler.handle_event_calls) > 0
        assert len(portfolio_handler.handle_event_calls) > 0

        # Reset call counts
        signal_handler.reset_mock()
        portfolio_handler.reset_mock()

        # Step 3: Portfolio analysis fails with negative cash balance
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=signal_event.event_id,
            event_id=f"workflow-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="portfolio_v2",
            source_component="PortfolioAnalysisHandler",
            workflow_type="portfolio_analysis",
            failure_reason="Account has non-positive cash balance: $-7920.51",
            failure_step="portfolio_analysis",
            error_details={"cash_balance": -7920.51},
        )
        orchestrator._handle_workflow_failed(failure_event)

        # Verify workflow is now FAILED
        assert orchestrator.is_workflow_failed(correlation_id)
        assert not orchestrator.is_workflow_active(correlation_id)

        # Step 4: Try to emit another SignalGenerated event (should be skipped)
        another_signal_event = SignalGenerated(
            correlation_id=correlation_id,
            causation_id="test",
            event_id=f"signal-generated-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy_v2",
            source_component="SignalGenerationHandler",
            signals_data={"DSL": {"symbol": "SPY", "action": "BUY"}},
            consolidated_portfolio={"target_allocations": {"SPY": 1.0}},
            signal_count=1,
            metadata={},
        )
        event_bus.publish(another_signal_event)

        # Handlers should NOT be called for FAILED workflow
        assert len(signal_handler.handle_event_calls) == 0
        assert len(portfolio_handler.handle_event_calls) == 0

        # Step 5: Try to emit RebalancePlanned event (should also be skipped)
        rebalance_event = RebalancePlanned(
            correlation_id=correlation_id,
            causation_id=signal_event.event_id,
            event_id=f"rebalance-planned-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="portfolio_v2",
            source_component="PortfolioAnalysisHandler",
            rebalance_plan=RebalancePlan(
                plan_id=f"plan-{uuid.uuid4()}",
                correlation_id=correlation_id,
                causation_id=signal_event.event_id,
                timestamp=datetime.now(UTC),
                items=[
                    # Add a dummy item since RebalancePlan requires at least one
                    {
                        "symbol": "SPY",
                        "current_weight": Decimal("0"),
                        "target_weight": Decimal("1.0"),
                        "weight_diff": Decimal("1.0"),
                        "target_value": Decimal("1000"),
                        "current_value": Decimal("0"),
                        "trade_amount": Decimal("1000"),
                        "action": "BUY",
                        "priority": 1,
                    }
                ],
                total_portfolio_value=Decimal("1000"),
                total_trade_value=Decimal("1000"),
                metadata={},
            ),
            allocation_comparison={
                "target_values": {},
                "current_values": {},
                "deltas": {},
            },
            trades_required=True,
            metadata={},
        )
        event_bus.publish(rebalance_event)

        # Execution handler should NOT be called for FAILED workflow
        assert len(execution_handler.handle_event_calls) == 0

    def test_multiple_concurrent_workflows_independent_failure(
        self, orchestrator_with_mocked_handlers
    ):
        """Test that failure in one workflow doesn't affect other workflows."""
        orchestrator = orchestrator_with_mocked_handlers

        # Create two different workflows
        correlation_id_1 = str(uuid.uuid4())
        correlation_id_2 = str(uuid.uuid4())

        # Start both workflows (set to RUNNING state)
        for correlation_id in [correlation_id_1, correlation_id_2]:
            orchestrator._set_workflow_state(correlation_id, WorkflowState.RUNNING)

        # Both workflows should be RUNNING
        assert orchestrator.is_workflow_active(correlation_id_1)
        assert orchestrator.is_workflow_active(correlation_id_2)

        # Fail the first workflow
        failure_event = WorkflowFailed(
            correlation_id=correlation_id_1,
            causation_id="test",
            event_id=f"workflow-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            failure_reason="Test failure",
            failure_step="test",
            error_details={},
        )
        orchestrator._handle_workflow_failed(failure_event)

        # First workflow should be FAILED, second should still be RUNNING
        assert orchestrator.is_workflow_failed(correlation_id_1)
        assert not orchestrator.is_workflow_active(correlation_id_1)

        assert orchestrator.is_workflow_active(correlation_id_2)
        assert not orchestrator.is_workflow_failed(correlation_id_2)

        # Create mock handler
        mock_handler = MockHandler("TestHandler")

        # Register handler
        orchestrator.event_bus.subscribe("SignalGenerated", mock_handler)
        orchestrator._wrap_handlers_with_state_checking()

        # Emit events for both workflows
        for correlation_id in [correlation_id_1, correlation_id_2]:
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
            orchestrator.event_bus.publish(event)

        # Handler should be called only once (for the active workflow)
        assert len(mock_handler.handle_event_calls) == 1

        # Verify it was called with the correct correlation_id
        called_event = mock_handler.handle_event_calls[0]
        assert called_event.correlation_id == correlation_id_2

    def test_workflow_failure_during_different_stages(
        self, orchestrator_with_mocked_handlers
    ):
        """Test that workflow can fail at any stage and prevent subsequent processing."""
        orchestrator = orchestrator_with_mocked_handlers

        # Test failure during signal generation
        correlation_id_1 = str(uuid.uuid4())
        orchestrator._set_workflow_state(correlation_id_1, WorkflowState.RUNNING)

        failure_event = WorkflowFailed(
            correlation_id=correlation_id_1,
            causation_id="test",
            event_id=f"workflow-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy_v2",
            source_component="SignalGenerationHandler",
            workflow_type="signal_generation",
            failure_reason="Failed to fetch market data",
            failure_step="signal_generation",
            error_details={},
        )
        orchestrator._handle_workflow_failed(failure_event)
        assert orchestrator.is_workflow_failed(correlation_id_1)

        # Test failure during portfolio analysis
        correlation_id_2 = str(uuid.uuid4())
        orchestrator._set_workflow_state(correlation_id_2, WorkflowState.RUNNING)

        failure_event = WorkflowFailed(
            correlation_id=correlation_id_2,
            causation_id="test",
            event_id=f"workflow-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="portfolio_v2",
            source_component="PortfolioAnalysisHandler",
            workflow_type="portfolio_analysis",
            failure_reason="Negative cash balance",
            failure_step="portfolio_analysis",
            error_details={},
        )
        orchestrator._handle_workflow_failed(failure_event)
        assert orchestrator.is_workflow_failed(correlation_id_2)

        # Test failure during trade execution
        correlation_id_3 = str(uuid.uuid4())
        orchestrator._set_workflow_state(correlation_id_3, WorkflowState.RUNNING)

        failure_event = WorkflowFailed(
            correlation_id=correlation_id_3,
            causation_id="test",
            event_id=f"workflow-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution_v2",
            source_component="TradingExecutionHandler",
            workflow_type="trading_execution",
            failure_reason="API rate limit exceeded",
            failure_step="trade_execution",
            error_details={},
        )
        orchestrator._handle_workflow_failed(failure_event)
        assert orchestrator.is_workflow_failed(correlation_id_3)

        # All three workflows should be independently marked as FAILED
        assert orchestrator.is_workflow_failed(correlation_id_1)
        assert orchestrator.is_workflow_failed(correlation_id_2)
        assert orchestrator.is_workflow_failed(correlation_id_3)
