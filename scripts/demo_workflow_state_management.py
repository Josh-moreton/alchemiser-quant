#!/usr/bin/env python3
"""Demonstration of workflow state management feature.

This script demonstrates how the workflow state management prevents event
processing after failures, eliminating race conditions and misleading logs.
"""

from datetime import UTC, datetime
from unittest.mock import Mock
import uuid

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
    WorkflowState,
)
from the_alchemiser.shared.events import (
    SignalGenerated,
    WorkflowFailed,
    WorkflowStarted,
)


def create_mock_container():
    """Create a mock application container."""
    container = Mock()
    
    # Create a real event bus for demonstration
    from the_alchemiser.shared.events.bus import EventBus
    event_bus = EventBus()
    container.services.event_bus.return_value = event_bus
    
    # Mock config
    container.config.paper_trading.return_value = True
    
    return container


def demonstrate_workflow_state_management():
    """Demonstrate workflow state management preventing post-failure processing."""
    print("=" * 80)
    print("WORKFLOW STATE MANAGEMENT DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Create orchestrator with mocked domain handlers
    container = create_mock_container()
    
    # Mock the domain handler registration
    original_register = EventDrivenOrchestrator._register_domain_handlers
    EventDrivenOrchestrator._register_domain_handlers = Mock()
    
    try:
        orchestrator = EventDrivenOrchestrator(container)
    finally:
        EventDrivenOrchestrator._register_domain_handlers = original_register
    
    # Create mock handlers to demonstrate skipping
    signal_handler = Mock()
    signal_handler.can_handle.return_value = True
    portfolio_handler = Mock()
    portfolio_handler.can_handle.return_value = True
    
    # Register handlers
    event_bus = orchestrator.event_bus
    event_bus.subscribe("SignalGenerated", signal_handler)
    event_bus.subscribe("SignalGenerated", portfolio_handler)
    
    # Wrap handlers with state checking
    orchestrator._wrap_handlers_with_state_checking()
    
    # Scenario: Negative cash balance failure
    correlation_id = str(uuid.uuid4())
    
    print("SCENARIO: Portfolio analysis fails due to negative cash balance")
    print()
    
    # Step 1: Start workflow
    print("1. Starting workflow...")
    start_event = WorkflowStarted(
        correlation_id=correlation_id,
        causation_id="demo",
        event_id=f"workflow-started-{uuid.uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="demo",
        source_component="demo",
        workflow_type="trading",
        requested_by="demo",
        configuration={},
    )
    orchestrator._handle_workflow_started(start_event)
    print(f"   ✅ Workflow {correlation_id[:8]}... marked as RUNNING")
    print(f"   is_workflow_active: {orchestrator.is_workflow_active(correlation_id)}")
    print(f"   is_workflow_failed: {orchestrator.is_workflow_failed(correlation_id)}")
    print()
    
    # Step 2: Process SignalGenerated event (should succeed)
    print("2. Processing SignalGenerated event (workflow is RUNNING)...")
    signal_event = SignalGenerated(
        correlation_id=correlation_id,
        causation_id="demo",
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
    print(f"   ✅ SignalGenerationHandler called: {signal_handler.handle_event.call_count} times")
    print(f"   ✅ PortfolioAnalysisHandler called: {portfolio_handler.handle_event.call_count} times")
    print()
    
    # Reset call counts
    signal_handler.reset_mock()
    portfolio_handler.reset_mock()
    
    # Step 3: Workflow fails
    print("3. Portfolio analysis fails with negative cash balance...")
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
    print(f"   ❌ Workflow failed: portfolio_analysis - {failure_event.failure_reason}")
    print(f"   🚫 Workflow {correlation_id[:8]}... marked as FAILED")
    print(f"   is_workflow_active: {orchestrator.is_workflow_active(correlation_id)}")
    print(f"   is_workflow_failed: {orchestrator.is_workflow_failed(correlation_id)}")
    print()
    
    # Step 4: Try to process another event (should be skipped)
    print("4. Attempting to process another SignalGenerated event (should be SKIPPED)...")
    another_signal_event = SignalGenerated(
        correlation_id=correlation_id,
        causation_id="demo",
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
    print(f"   🚫 SignalGenerationHandler called: {signal_handler.handle_event.call_count} times (SKIPPED)")
    print(f"   🚫 PortfolioAnalysisHandler called: {portfolio_handler.handle_event.call_count} times (SKIPPED)")
    print()
    
    # Step 5: Show the benefit
    print("=" * 80)
    print("BENEFITS:")
    print("=" * 80)
    print()
    print("✅ No misleading 'success' messages after workflow has failed")
    print("✅ Immediate halt on critical failures (negative cash, API errors)")
    print("✅ Clear audit trail of what stopped when")
    print("✅ Prevents wasted processing and API calls")
    print("✅ Resource efficient - stops work immediately after failure")
    print()
    
    # Step 6: Show log messages that would be produced
    print("=" * 80)
    print("EXPECTED LOG MESSAGES:")
    print("=" * 80)
    print()
    print("BEFORE this feature (confusing):")
    print("  12:51:12,224 - ERROR - Account has non-positive cash balance: $-7920.51")
    print("  12:51:12,226 - ERROR - ❌ Workflow failed: portfolio_analysis")
    print("  12:51:12,227 - INFO - ✅ Signal generation completed successfully  ← MISLEADING!")
    print()
    print("AFTER this feature (clear):")
    print("  12:51:12,224 - ERROR - Account has non-positive cash balance: $-7920.51")
    print("  12:51:12,226 - ERROR - ❌ Workflow failed: portfolio_analysis")
    print(f"  12:51:12,226 - INFO - 🚫 Workflow {correlation_id[:8]}... marked as FAILED - future events will be skipped")
    print(f"  12:51:12,227 - INFO - 🚫 Skipping SignalGenerationHandler - workflow {correlation_id[:8]}... already failed")
    print()


if __name__ == "__main__":
    demonstrate_workflow_state_management()
