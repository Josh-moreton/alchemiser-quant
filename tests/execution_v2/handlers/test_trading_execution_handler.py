"""Business Unit: execution | Status: current.

Comprehensive unit tests for TradingExecutionHandler.

Tests cover:
- Event handling and routing
- Idempotency key generation and duplicate detection
- Trade execution success and failure paths
- Event emission (TradeExecuted, WorkflowCompleted, WorkflowFailed)
- No-trade scenario handling
- Partial execution handling
- Error handling and resilience
- Resource cleanup
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.handlers.trading_execution_handler import (
    TradingExecutionHandler,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    OrderResult,
)
from the_alchemiser.shared.constants import DECIMAL_ZERO
from the_alchemiser.shared.events import (
    BaseEvent,
    RebalancePlanned,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
)
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


@pytest.fixture
def mock_container():
    """Create mock application container."""
    container = Mock()
    container.services.event_bus = Mock(return_value=Mock())
    container.infrastructure.alpaca_manager = Mock(return_value=Mock())
    container.config.execution = Mock(return_value=Mock(treat_partial_execution_as_failure=False))
    return container


@pytest.fixture
def handler(mock_container):
    """Create TradingExecutionHandler instance."""
    return TradingExecutionHandler(mock_container)


@pytest.fixture
def sample_rebalance_plan():
    """Create sample rebalance plan."""
    return RebalancePlan(
        plan_id="test-plan-123",
        correlation_id="test-correlation-456",
        causation_id="upstream-signal-789",
        timestamp=datetime.now(UTC),
        total_portfolio_value=Decimal("10000.00"),
        total_trade_value=Decimal("1000.00"),
        items=[
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.4"),
                weight_diff=Decimal("0.1"),
                target_value=Decimal("4000.00"),
                current_value=Decimal("3000.00"),
                trade_amount=Decimal("1000.00"),
                action="BUY",
                priority=1,
            ),
        ],
    )


@pytest.fixture
def sample_rebalance_planned_event(sample_rebalance_plan):
    """Create sample RebalancePlanned event."""
    return RebalancePlanned(
        event_id="event-123",
        correlation_id="test-correlation-456",
        causation_id="upstream-event-789",
        timestamp=datetime.now(UTC),
        source_module="portfolio_v2",
        source_component="RebalanceHandler",
        rebalance_plan=sample_rebalance_plan,
        allocation_comparison=AllocationComparison(
            target_values={"AAPL": Decimal("4000.00")},
            current_values={"AAPL": Decimal("3000.00")},
            deltas={"AAPL": Decimal("1000.00")},
        ),
        trades_required=True,
    )


class TestTradingExecutionHandlerInitialization:
    """Test handler initialization."""

    def test_handler_initialization(self, mock_container):
        """Test handler initializes correctly."""
        handler = TradingExecutionHandler(mock_container)

        assert handler.container == mock_container
        assert handler.logger is not None
        assert handler.event_bus is not None
        assert isinstance(handler._processed_keys, set)
        assert len(handler._processed_keys) == 0

    def test_event_bus_retrieved_from_container(self, mock_container):
        """Test event bus is retrieved from container services."""
        handler = TradingExecutionHandler(mock_container)

        mock_container.services.event_bus.assert_called_once()
        assert handler.event_bus == mock_container.services.event_bus()


class TestEventHandling:
    """Test event handling and routing."""

    def test_can_handle_rebalance_planned(self, handler):
        """Test handler can handle RebalancePlanned events."""
        assert handler.can_handle("RebalancePlanned") is True

    def test_cannot_handle_other_events(self, handler):
        """Test handler rejects other event types."""
        assert handler.can_handle("SignalGenerated") is False
        assert handler.can_handle("TradeExecuted") is False
        assert handler.can_handle("UnknownEvent") is False

    def test_handle_event_routes_to_rebalance_handler(
        self, handler, sample_rebalance_planned_event
    ):
        """Test handle_event routes RebalancePlanned to correct handler."""
        with patch.object(handler, "_handle_rebalance_planned") as mock_handle:
            handler.handle_event(sample_rebalance_planned_event)
            mock_handle.assert_called_once_with(sample_rebalance_planned_event)

    def test_handle_event_ignores_unsupported_events(self, handler):
        """Test handle_event ignores unsupported event types."""
        unsupported_event = BaseEvent(
            event_id="test-id",
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            event_type="UnsupportedEvent",
        )

        # Should not raise exception
        handler.handle_event(unsupported_event)

    def test_handle_event_emits_workflow_failure_on_exception(
        self, handler, sample_rebalance_planned_event
    ):
        """Test handle_event emits WorkflowFailed on exception."""
        with patch.object(
            handler, "_handle_rebalance_planned", side_effect=Exception("Test error")
        ), patch.object(handler, "_emit_workflow_failure") as mock_emit:
            handler.handle_event(sample_rebalance_planned_event)
            mock_emit.assert_called_once()
            args = mock_emit.call_args[0]
            assert args[0] == sample_rebalance_planned_event
            assert "Test error" in args[1]


class TestIdempotencyKey:
    """Test idempotency key generation and duplicate detection."""

    def test_generate_idempotency_key_deterministic(self, handler, sample_rebalance_planned_event):
        """Test idempotency key is deterministic for same event."""
        key1 = handler._generate_idempotency_key(sample_rebalance_planned_event)
        key2 = handler._generate_idempotency_key(sample_rebalance_planned_event)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 16  # 16-character hex hash

    def test_generate_idempotency_key_different_for_different_events(
        self, handler, sample_rebalance_planned_event
    ):
        """Test different events produce different idempotency keys."""
        key1 = handler._generate_idempotency_key(sample_rebalance_planned_event)

        # Create different event
        different_event = RebalancePlanned(
            event_id="different-event-id",
            correlation_id=sample_rebalance_planned_event.correlation_id,
            causation_id=sample_rebalance_planned_event.causation_id,
            timestamp=datetime.now(UTC),
            source_module="portfolio_v2",
            source_component="RebalanceHandler",
            rebalance_plan=sample_rebalance_planned_event.rebalance_plan,
            allocation_comparison=sample_rebalance_planned_event.allocation_comparison,
            trades_required=True,
        )

        key2 = handler._generate_idempotency_key(different_event)
        assert key1 != key2

    def test_is_duplicate_event_returns_false_for_new_key(self, handler):
        """Test is_duplicate_event returns False for new key."""
        assert handler._is_duplicate_event("new-key-123") is False

    def test_is_duplicate_event_returns_true_for_processed_key(self, handler):
        """Test is_duplicate_event returns True for already processed key."""
        handler._mark_event_processed("processed-key-456")
        assert handler._is_duplicate_event("processed-key-456") is True

    def test_mark_event_processed_adds_to_set(self, handler):
        """Test mark_event_processed adds key to processed set."""
        initial_count = len(handler._processed_keys)
        handler._mark_event_processed("new-key-789")

        assert len(handler._processed_keys) == initial_count + 1
        assert "new-key-789" in handler._processed_keys

    def test_duplicate_event_skips_execution(self, handler, sample_rebalance_planned_event):
        """Test duplicate event is skipped without executing trades."""
        # Mark event as processed
        idempotency_key = handler._generate_idempotency_key(sample_rebalance_planned_event)
        handler._mark_event_processed(idempotency_key)

        with patch.object(handler, "_create_execution_manager") as mock_create:
            handler._handle_rebalance_planned(sample_rebalance_planned_event)
            # Execution manager should not be created for duplicate
            mock_create.assert_not_called()


class TestNoTradeScenario:
    """Test no-trade scenario handling."""

    def test_no_trade_when_trades_not_required(self, handler, sample_rebalance_planned_event):
        """Test no-trade scenario when trades_required is False."""
        # Create new event with trades_required=False (frozen DTOs can't be mutated)
        no_trade_event = RebalancePlanned(
            event_id=sample_rebalance_planned_event.event_id,
            correlation_id=sample_rebalance_planned_event.correlation_id,
            causation_id=sample_rebalance_planned_event.causation_id,
            timestamp=sample_rebalance_planned_event.timestamp,
            source_module=sample_rebalance_planned_event.source_module,
            source_component=sample_rebalance_planned_event.source_component,
            rebalance_plan=sample_rebalance_planned_event.rebalance_plan,
            allocation_comparison=sample_rebalance_planned_event.allocation_comparison,
            trades_required=False,  # Set to False
        )

        with patch.object(handler, "_emit_trade_executed_event") as mock_trade:
            with patch.object(handler, "_emit_workflow_completed_event") as mock_complete:
                handler._handle_rebalance_planned(no_trade_event)

                # Should emit success events
                mock_trade.assert_called_once()
                mock_complete.assert_called_once()

                # Check execution result is empty
                execution_result = mock_trade.call_args[0][0]
                assert execution_result.orders_placed == 0
                assert execution_result.orders_succeeded == 0
                assert execution_result.success is True


class TestExecutionManagerCreation:
    """Test execution manager creation."""

    def test_create_execution_manager_returns_manager(self, handler):
        """Test _create_execution_manager returns ExecutionManager instance."""
        with patch(
            "the_alchemiser.execution_v2.core.execution_manager.ExecutionManager"
        ) as mock_em:
            manager = handler._create_execution_manager()

            mock_em.assert_called_once()
            assert manager == mock_em.return_value

    def test_create_execution_manager_uses_container_dependencies(self, handler, mock_container):
        """Test execution manager creation uses container dependencies."""
        with patch("the_alchemiser.execution_v2.core.execution_manager.ExecutionManager"):
            handler._create_execution_manager()

            # Verify alpaca_manager is retrieved from container
            mock_container.infrastructure.alpaca_manager.assert_called()


class TestFailureReasonBuilding:
    """Test failure reason building."""

    def test_extract_failed_symbols_returns_empty_for_success(self, handler):
        """Test extract_failed_symbols returns empty list for successful execution."""
        execution_result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[
                OrderResult(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1000"),
                    shares=Decimal("10"),
                    success=True,
                    timestamp=datetime.now(UTC),
                )
            ],
            orders_placed=1,
            orders_succeeded=1,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )

        failed_symbols = handler._extract_failed_symbols(execution_result)
        assert failed_symbols == []

    def test_extract_failed_symbols_returns_failed_symbols(self, handler):
        """Test extract_failed_symbols returns list of failed symbols."""
        execution_result = ExecutionResult(
            success=False,
            status=ExecutionStatus.PARTIAL_SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[
                OrderResult(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1000"),
                    shares=Decimal("10"),
                    success=True,
                    timestamp=datetime.now(UTC),
                ),
                OrderResult(
                    symbol="MSFT",
                    action="BUY",
                    trade_amount=Decimal("500"),
                    shares=Decimal("5"),
                    success=False,
                    error_message="Insufficient liquidity",
                    timestamp=datetime.now(UTC),
                ),
            ],
            orders_placed=2,
            orders_succeeded=1,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )

        failed_symbols = handler._extract_failed_symbols(execution_result)
        assert failed_symbols == ["MSFT"]

    def test_build_failure_reason_partial_success(self, handler):
        """Test build_failure_reason for partial success."""
        execution_result = ExecutionResult(
            success=False,
            status=ExecutionStatus.PARTIAL_SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[
                OrderResult(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1000"),
                    shares=Decimal("10"),
                    success=True,
                    timestamp=datetime.now(UTC),
                ),
                OrderResult(
                    symbol="MSFT",
                    action="BUY",
                    trade_amount=Decimal("500"),
                    shares=Decimal("5"),
                    success=False,
                    timestamp=datetime.now(UTC),
                ),
            ],
            orders_placed=2,
            orders_succeeded=1,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )

        reason = handler._build_failure_reason(execution_result)
        assert "partially failed" in reason
        assert "1/2" in reason
        assert "MSFT" in reason

    def test_build_failure_reason_complete_failure(self, handler):
        """Test build_failure_reason for complete failure."""
        execution_result = ExecutionResult(
            success=False,
            status=ExecutionStatus.FAILURE,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=2,
            orders_succeeded=0,
            total_trade_value=DECIMAL_ZERO,
            execution_timestamp=datetime.now(UTC),
        )

        reason = handler._build_failure_reason(execution_result)
        assert "0/2" in reason


class TestEventEmission:
    """Test event emission."""

    def test_emit_trade_executed_event_publishes_to_bus(self, handler):
        """Test _emit_trade_executed_event publishes event."""
        execution_result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=DECIMAL_ZERO,
            execution_timestamp=datetime.now(UTC),
        )

        handler._emit_trade_executed_event(execution_result, success=True)

        handler.event_bus.publish.assert_called_once()
        published_event = handler.event_bus.publish.call_args[0][0]
        assert isinstance(published_event, TradeExecuted)
        assert published_event.success is True

    def test_emit_workflow_completed_event_publishes_to_bus(self, handler):
        """Test _emit_workflow_completed_event publishes event."""
        execution_result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=DECIMAL_ZERO,
            execution_timestamp=datetime.now(UTC),
        )

        handler._emit_workflow_completed_event("test-corr", execution_result)

        handler.event_bus.publish.assert_called_once()
        published_event = handler.event_bus.publish.call_args[0][0]
        assert isinstance(published_event, WorkflowCompleted)
        assert published_event.success is True

    def test_emit_workflow_failure_publishes_to_bus(self, handler, sample_rebalance_planned_event):
        """Test _emit_workflow_failure publishes event."""
        handler._emit_workflow_failure(sample_rebalance_planned_event, "Test error")

        handler.event_bus.publish.assert_called_once()
        published_event = handler.event_bus.publish.call_args[0][0]
        assert isinstance(published_event, WorkflowFailed)
        assert "Test error" in published_event.failure_reason


class TestResourceCleanup:
    """Test resource cleanup."""

    def test_execution_manager_shutdown_called_on_success(
        self, handler, sample_rebalance_planned_event
    ):
        """Test execution manager shutdown is called on success."""
        mock_manager = Mock()
        mock_execution_result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=DECIMAL_ZERO,
            execution_timestamp=datetime.now(UTC),
        )
        mock_manager.execute_rebalance_plan.return_value = mock_execution_result

        with patch.object(handler, "_create_execution_manager", return_value=mock_manager):
            handler._handle_rebalance_planned(sample_rebalance_planned_event)

        mock_manager.shutdown.assert_called_once()

    def test_execution_manager_shutdown_called_on_failure(
        self, handler, sample_rebalance_planned_event
    ):
        """Test execution manager shutdown is called even on failure."""
        mock_manager = Mock()
        mock_manager.execute_rebalance_plan.side_effect = Exception("Execution failed")

        with patch.object(handler, "_create_execution_manager", return_value=mock_manager):
            with patch.object(handler, "_emit_workflow_failure"):
                handler._handle_rebalance_planned(sample_rebalance_planned_event)

        mock_manager.shutdown.assert_called_once()


class TestPartialExecutionHandling:
    """Test partial execution handling."""

    def test_partial_execution_treated_as_success_by_default(
        self, handler, sample_rebalance_planned_event, mock_container
    ):
        """Test partial execution treated as success when config is False."""
        mock_container.config.execution.return_value.treat_partial_execution_as_failure = False

        mock_manager = Mock()
        mock_execution_result = ExecutionResult(
            success=False,
            status=ExecutionStatus.PARTIAL_SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[
                OrderResult(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1000"),
                    shares=Decimal("10"),
                    success=True,
                    timestamp=datetime.now(UTC),
                )
            ],
            orders_placed=2,
            orders_succeeded=1,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )
        mock_manager.execute_rebalance_plan.return_value = mock_execution_result

        with patch.object(handler, "_create_execution_manager", return_value=mock_manager):
            with patch.object(handler, "_emit_workflow_completed_event") as mock_complete:
                handler._handle_rebalance_planned(sample_rebalance_planned_event)
                mock_complete.assert_called_once()

    def test_partial_execution_treated_as_failure_when_configured(
        self, handler, sample_rebalance_planned_event, mock_container
    ):
        """Test partial execution treated as failure when config is True."""
        mock_container.config.execution.return_value.treat_partial_execution_as_failure = True

        mock_manager = Mock()
        mock_execution_result = ExecutionResult(
            success=False,
            status=ExecutionStatus.PARTIAL_SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[
                OrderResult(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1000"),
                    shares=Decimal("10"),
                    success=True,
                    timestamp=datetime.now(UTC),
                )
            ],
            orders_placed=2,
            orders_succeeded=1,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )
        mock_manager.execute_rebalance_plan.return_value = mock_execution_result

        with patch.object(handler, "_create_execution_manager", return_value=mock_manager):
            with patch.object(handler, "_emit_workflow_failure") as mock_failure:
                handler._handle_rebalance_planned(sample_rebalance_planned_event)
                mock_failure.assert_called_once()


class TestMarketClosureHandling:
    """Test market closure detection and conditional execution."""

    def test_skips_order_placement_when_market_closed(
        self, handler, sample_rebalance_planned_event
    ):
        """Test that order placement is skipped when market is closed."""
        # Mock market check to return False (market closed)
        with patch.object(handler, "_check_market_status", return_value=False):
            with patch.object(handler, "_emit_trade_executed_event") as mock_trade_event:
                with patch.object(handler, "_emit_workflow_completed_event") as mock_complete:
                    handler._handle_rebalance_planned(sample_rebalance_planned_event)

                    # Verify TradeExecuted event was emitted
                    assert mock_trade_event.call_count == 1
                    # Extract arguments - first arg is ExecutionResult, success is keyword arg
                    execution_result = mock_trade_event.call_args[0][0]
                    success = mock_trade_event.call_args[1]["success"]
                    assert success is True
                    assert execution_result.orders_placed == 0
                    assert execution_result.orders_succeeded == 0
                    assert execution_result.metadata["scenario"] == "market_closed"
                    assert "market is closed" in execution_result.metadata["message"].lower()

                    # Verify WorkflowCompleted event was emitted
                    mock_complete.assert_called_once()

    def test_proceeds_with_execution_when_market_open(
        self, handler, sample_rebalance_planned_event, mock_container
    ):
        """Test that order placement proceeds when market is open."""
        mock_manager = Mock()
        mock_execution_result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[
                OrderResult(
                    symbol="AAPL",
                    action="BUY",
                    trade_amount=Decimal("1000"),
                    shares=Decimal("10"),
                    success=True,
                    timestamp=datetime.now(UTC),
                )
            ],
            orders_placed=1,
            orders_succeeded=1,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )
        mock_manager.execute_rebalance_plan.return_value = mock_execution_result

        # Mock market check to return True (market open)
        with patch.object(handler, "_check_market_status", return_value=True):
            with patch.object(handler, "_create_execution_manager", return_value=mock_manager):
                with patch.object(handler, "_emit_trade_executed_event") as mock_trade_event:
                    with patch.object(handler, "_emit_workflow_completed_event"):
                        handler._handle_rebalance_planned(sample_rebalance_planned_event)

                        # Verify execution happened
                        mock_manager.execute_rebalance_plan.assert_called_once()

                        # Verify TradeExecuted event was emitted with actual results
                        assert mock_trade_event.call_count == 1
                        execution_result = mock_trade_event.call_args[0][0]
                        success = mock_trade_event.call_args[1]["success"]
                        assert success is True
                        assert execution_result.orders_placed == 1
                        assert execution_result.orders_succeeded == 1

    def test_market_check_returns_true_on_failure(self, handler):
        """Test that _check_market_status returns True when market check fails."""
        # Mock trading client to raise exception
        handler.container.infrastructure.alpaca_trading_client.side_effect = Exception("API error")

        # Should return True (defaults to open on error)
        result = handler._check_market_status("test-correlation-id")
        assert result is True

