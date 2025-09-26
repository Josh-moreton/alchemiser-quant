"""Tests for TradingExecutionHandler."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.handlers.trading_execution_handler import TradingExecutionHandler
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.events import RebalancePlanned, TradeExecuted
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItemDTO


@pytest.fixture
def mock_container():
    """Mock application container."""
    container = Mock()
    container.services.event_bus.return_value = Mock()
    container.services.persistence_handler.return_value = Mock()
    container.infrastructure.alpaca_manager.return_value = Mock()
    return container


@pytest.fixture
def sample_rebalance_planned_event():
    """Sample RebalancePlanned event."""
    from datetime import datetime, UTC
    
    rebalance_plan = RebalancePlanDTO(
        plan_id="test-plan-123",
        correlation_id="test-correlation-456",
        causation_id="test-causation-789",
        timestamp=datetime.now(UTC),
        items=[
            RebalancePlanItemDTO(
                symbol="AAPL",
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.4"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("2000.00"),
                current_value=Decimal("1500.00"),
                trade_amount=Decimal("500.00"),
                action="BUY",
                priority=1,
            ),
        ],
        total_portfolio_value=Decimal("5000.00"),
        total_trade_value=Decimal("500.00"),
    )
    
    return RebalancePlanned(
        correlation_id="test-correlation-456",
        causation_id="test-causation-123",
        event_id="rebalance-planned-789",
        timestamp="2024-01-01T00:00:00Z",
        source_module="portfolio_v2",
        source_component="TestComponent",
        rebalance_plan=rebalance_plan,
        allocation_comparison={},
        trades_required=True,
        metadata={},
    )


@pytest.fixture
def sample_execution_result():
    """Sample execution result."""
    return ExecutionResultDTO(
        success=True,
        plan_id="test-plan-123",
        correlation_id="test-correlation-456",
        orders=[],
        orders_placed=1,
        orders_succeeded=1,
        total_trade_value=Decimal("1500.00"),
        execution_timestamp="2024-01-01T00:00:00Z",
        metadata={},
    )


def test_handler_initialization(mock_container):
    """Test handler initialization."""
    handler = TradingExecutionHandler(mock_container)
    
    assert handler.container is mock_container
    assert handler.event_bus is not None
    assert handler._execution_adapter is not None
    assert handler._idempotency_store is not None


def test_can_handle_rebalance_planned(mock_container):
    """Test that handler can handle RebalancePlanned events."""
    handler = TradingExecutionHandler(mock_container)
    
    assert handler.can_handle("RebalancePlanned") is True
    assert handler.can_handle("SignalGenerated") is False
    assert handler.can_handle("WorkflowCompleted") is False


@patch('the_alchemiser.execution_v2.handlers.trading_execution_handler.generate_execution_plan_hash')
def test_handle_rebalance_planned_idempotent_skip(
    mock_hash_func, mock_container, sample_rebalance_planned_event
):
    """Test that handler skips execution if already attempted (idempotent behavior)."""
    mock_hash_func.return_value = "test-hash-123"
    
    handler = TradingExecutionHandler(mock_container)
    
    # Mock idempotency store to return True (already executed)
    handler._idempotency_store.has_been_executed.return_value = True
    
    # Handle the event
    handler.handle_event(sample_rebalance_planned_event)
    
    # Verify idempotency check was performed
    handler._idempotency_store.has_been_executed.assert_called_once_with(
        "test-correlation-456", "test-hash-123"
    )
    
    # Verify execution adapter was NOT called
    handler._execution_adapter.execute_orders.assert_not_called()
    
    # Verify no events were published
    handler.event_bus.publish.assert_not_called()


@patch('the_alchemiser.execution_v2.handlers.trading_execution_handler.generate_execution_plan_hash')
def test_handle_rebalance_planned_no_trades_required(
    mock_hash_func, mock_container, sample_rebalance_planned_event
):
    """Test handling event when no trades are required."""
    mock_hash_func.return_value = "test-hash-123"
    
    # Modify event to indicate no trades required
    sample_rebalance_planned_event.trades_required = False
    
    handler = TradingExecutionHandler(mock_container)
    handler._idempotency_store.has_been_executed.return_value = False
    
    # Handle the event
    handler.handle_event(sample_rebalance_planned_event)
    
    # Verify idempotency was recorded
    handler._idempotency_store.record_execution_attempt.assert_called_once()
    
    # Verify execution adapter was NOT called
    handler._execution_adapter.execute_orders.assert_not_called()
    
    # Verify TradeExecuted and WorkflowCompleted events were published
    assert handler.event_bus.publish.call_count == 2
    
    published_events = [call[0][0] for call in handler.event_bus.publish.call_args_list]
    assert any(isinstance(event, TradeExecuted) for event in published_events)


@patch('the_alchemiser.execution_v2.handlers.trading_execution_handler.generate_execution_plan_hash')
def test_handle_rebalance_planned_successful_execution(
    mock_hash_func, mock_container, sample_rebalance_planned_event, sample_execution_result
):
    """Test successful execution of rebalance plan."""
    mock_hash_func.return_value = "test-hash-123"
    
    handler = TradingExecutionHandler(mock_container)
    handler._idempotency_store.has_been_executed.return_value = False
    handler._execution_adapter.execute_orders.return_value = sample_execution_result
    
    # Handle the event
    handler.handle_event(sample_rebalance_planned_event)
    
    # Verify execution adapter was called
    handler._execution_adapter.execute_orders.assert_called_once()
    
    # Verify idempotency was recorded
    handler._idempotency_store.record_execution_attempt.assert_called_once_with(
        correlation_id="test-correlation-456",
        execution_plan_hash="test-hash-123",
        success=True,
        metadata={
            "orders_placed": 1,
            "orders_succeeded": 1,
            "total_trade_value": "1500.00",
        }
    )
    
    # Verify TradeExecuted and WorkflowCompleted events were published
    assert handler.event_bus.publish.call_count == 2
    
    published_events = [call[0][0] for call in handler.event_bus.publish.call_args_list]
    trade_executed_events = [event for event in published_events if isinstance(event, TradeExecuted)]
    
    assert len(trade_executed_events) == 1
    trade_event = trade_executed_events[0]
    
    # Verify enhanced TradeExecuted event structure
    assert trade_event.schema_version == "1.0"
    assert trade_event.execution_plan_hash == "test-hash-123"
    assert trade_event.fill_summaries is not None
    assert trade_event.settlement_details is not None
    assert "adapter_used" in trade_event.metadata
    assert "idempotency_enabled" in trade_event.metadata


@patch('the_alchemiser.execution_v2.handlers.trading_execution_handler.generate_execution_plan_hash')
def test_handle_rebalance_planned_execution_failure(
    mock_hash_func, mock_container, sample_rebalance_planned_event
):
    """Test handling execution failure."""
    mock_hash_func.return_value = "test-hash-123"
    
    handler = TradingExecutionHandler(mock_container)
    handler._idempotency_store.has_been_executed.return_value = False
    handler._execution_adapter.execute_orders.side_effect = Exception("Execution failed")
    
    # Handle the event
    handler.handle_event(sample_rebalance_planned_event)
    
    # Verify execution adapter was called
    handler._execution_adapter.execute_orders.assert_called_once()
    
    # Verify WorkflowFailed event was published
    handler.event_bus.publish.assert_called()
    
    published_events = [call[0][0] for call in handler.event_bus.publish.call_args_list]
    workflow_failed_events = [event for event in published_events if event.event_type == "WorkflowFailed"]
    
    assert len(workflow_failed_events) == 1
    failed_event = workflow_failed_events[0]
    assert "Execution failed" in failed_event.failure_reason


def test_emit_trade_executed_event_structure(mock_container, sample_execution_result):
    """Test the structure of emitted TradeExecuted event."""
    handler = TradingExecutionHandler(mock_container)
    
    # Call the private method directly for testing
    handler._emit_trade_executed_event(
        execution_result=sample_execution_result,
        execution_plan_hash="test-hash-123",
        success=True
    )
    
    # Verify event was published
    handler.event_bus.publish.assert_called_once()
    
    published_event = handler.event_bus.publish.call_args[0][0]
    
    # Verify it's a TradeExecuted event with proper structure
    assert isinstance(published_event, TradeExecuted)
    assert published_event.schema_version == "1.0"
    assert published_event.execution_plan_hash == "test-hash-123"
    assert published_event.settlement_event_type == "execution.order.settled.v1"
    
    # Verify fill summaries structure
    assert isinstance(published_event.fill_summaries, dict)
    
    # Verify settlement details structure
    assert isinstance(published_event.settlement_details, dict)
    assert "settlement_type" in published_event.settlement_details
    assert "total_orders" in published_event.settlement_details
    
    # Verify metadata structure
    assert "adapter_used" in published_event.metadata
    assert "idempotency_enabled" in published_event.metadata
    assert published_event.metadata["adapter_used"] == "AlpacaExecutionAdapter"
    assert published_event.metadata["idempotency_enabled"] is True


def test_emit_workflow_completed_event(mock_container, sample_execution_result):
    """Test emission of WorkflowCompleted event."""
    handler = TradingExecutionHandler(mock_container)
    
    # Call the private method directly
    handler._emit_workflow_completed_event("test-correlation-456", sample_execution_result)
    
    # Verify event was published
    handler.event_bus.publish.assert_called_once()
    
    published_event = handler.event_bus.publish.call_args[0][0]
    
    # Verify event structure
    assert published_event.event_type == "WorkflowCompleted"
    assert published_event.correlation_id == "test-correlation-456"
    assert published_event.workflow_type == "trade_execution"
    assert published_event.success is True
    
    # Verify summary contains execution details
    assert "orders_placed" in published_event.summary
    assert "orders_succeeded" in published_event.summary
    assert "total_trade_value" in published_event.summary
    assert "plan_id" in published_event.summary


def test_emit_workflow_failure_event(mock_container, sample_rebalance_planned_event):
    """Test emission of WorkflowFailed event."""
    handler = TradingExecutionHandler(mock_container)
    
    # Call the private method directly
    handler._emit_workflow_failure(sample_rebalance_planned_event, "Test failure")
    
    # Verify event was published
    handler.event_bus.publish.assert_called_once()
    
    published_event = handler.event_bus.publish.call_args[0][0]
    
    # Verify event structure
    assert published_event.event_type == "WorkflowFailed"
    assert published_event.correlation_id == sample_rebalance_planned_event.correlation_id
    assert published_event.causation_id == sample_rebalance_planned_event.event_id
    assert published_event.workflow_type == "trade_execution"
    assert published_event.failure_reason == "Test failure"
    assert published_event.failure_step == "trade_execution"


def test_handle_unsupported_event(mock_container):
    """Test handling unsupported event types."""
    handler = TradingExecutionHandler(mock_container)
    
    # Create a mock unsupported event
    unsupported_event = Mock()
    unsupported_event.__class__.__name__ = "UnsupportedEvent"
    
    # Handle the event (should log warning and do nothing)
    handler.handle_event(unsupported_event)
    
    # Verify no execution occurred
    handler._execution_adapter.execute_orders.assert_not_called()
    handler.event_bus.publish.assert_not_called()


@patch('the_alchemiser.execution_v2.handlers.trading_execution_handler.get_logger')
def test_logging_with_correlation_ids(mock_logger, mock_container, sample_rebalance_planned_event):
    """Test that logging includes correlation and causation IDs."""
    mock_logger_instance = Mock()
    mock_logger.return_value = mock_logger_instance
    
    handler = TradingExecutionHandler(mock_container)
    handler._idempotency_store.has_been_executed.return_value = True  # Skip execution
    
    # Handle the event
    handler.handle_event(sample_rebalance_planned_event)
    
    # Verify logger was called with correlation/causation IDs in extra
    mock_logger_instance.info.assert_called()
    
    # Check that at least one log call included the correlation_id in extra
    log_calls = mock_logger_instance.info.call_args_list
    found_correlation_id = False
    
    for call in log_calls:
        if len(call) > 1 and 'extra' in call[1]:
            extra = call[1]['extra']
            if 'correlation_id' in extra and extra['correlation_id'] == 'test-correlation-456':
                found_correlation_id = True
                break
    
    assert found_correlation_id, "Expected correlation_id in logging extra data"