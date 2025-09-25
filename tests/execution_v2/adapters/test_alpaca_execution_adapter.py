"""Tests for AlpacaExecutionAdapter."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.adapters.alpaca_execution_adapter import AlpacaExecutionAdapter
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.schemas.execution_report import ExecutedOrderDTO
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItemDTO


@pytest.fixture
def mock_alpaca_manager():
    """Mock AlpacaManager for testing."""
    return Mock()


@pytest.fixture
def sample_rebalance_plan():
    """Sample rebalance plan for testing."""
    from datetime import datetime, UTC
    
    return RebalancePlanDTO(
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
            RebalancePlanItemDTO(
                symbol="MSFT",
                current_weight=Decimal("0.2"),
                target_weight=Decimal("0.1"),
                weight_diff=Decimal("-0.1"),
                target_value=Decimal("500.00"),
                current_value=Decimal("1000.00"),
                trade_amount=Decimal("-500.00"),
                action="SELL",
                priority=2,
            ),
        ],
        total_portfolio_value=Decimal("5000.00"),
        total_trade_value=Decimal("1000.00"),
    )


@pytest.fixture
def sample_executed_order():
    """Sample executed order DTO."""
    from datetime import datetime, UTC
    
    return ExecutedOrderDTO(
        order_id="order-123",
        symbol="AAPL",
        action="BUY",
        quantity=Decimal("10"),
        filled_quantity=Decimal("10"),
        price=Decimal("50.00"),
        total_value=Decimal("500.00"),
        status="FILLED",
        execution_timestamp=datetime.now(UTC),
        error_message=None,
    )


def test_adapter_initialization(mock_alpaca_manager):
    """Test adapter initialization."""
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    assert adapter._alpaca_manager is mock_alpaca_manager


def test_execute_orders_successful(mock_alpaca_manager, sample_rebalance_plan, sample_executed_order):
    """Test successful order execution."""
    # Setup mock trading service to return successful executed orders
    mock_trading_service = Mock()
    mock_trading_service.place_market_order.return_value = sample_executed_order
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    result = adapter.execute_orders(sample_rebalance_plan)
    
    # Verify result structure
    assert isinstance(result, ExecutionResultDTO)
    assert result.success is True
    assert result.plan_id == "test-plan-123"
    assert result.correlation_id == "test-correlation-456"
    assert result.orders_placed == 2
    assert result.orders_succeeded == 2
    assert result.total_trade_value == Decimal("1000.00")  # 500 + 500 (both successful)
    
    # Verify trading service was called correctly
    assert mock_trading_service.place_market_order.call_count == 2
    
    # Check first call (BUY)
    first_call = mock_trading_service.place_market_order.call_args_list[0]
    assert first_call.kwargs["symbol"] == "AAPL"
    assert first_call.kwargs["side"] == "buy"
    assert first_call.kwargs["notional"] == 500.0
    
    # Check second call (SELL)
    second_call = mock_trading_service.place_market_order.call_args_list[1]
    assert second_call.kwargs["symbol"] == "MSFT"
    assert second_call.kwargs["side"] == "sell"
    assert second_call.kwargs["notional"] == 500.0  # abs(-500)


def test_execute_orders_partial_failure(mock_alpaca_manager, sample_rebalance_plan):
    """Test execution with some failed orders."""
    from datetime import datetime, UTC
    
    # Setup mock trading service to return success for first order, failure for second
    successful_order = ExecutedOrderDTO(
        order_id="order-123",
        symbol="AAPL",
        action="BUY",
        quantity=Decimal("10"),
        filled_quantity=Decimal("10"),
        price=Decimal("50.00"),
        total_value=Decimal("500.00"),
        status="FILLED",
        execution_timestamp=datetime.now(UTC),
        error_message=None,
    )
    
    failed_order = ExecutedOrderDTO(
        order_id="order-456",
        symbol="MSFT",
        action="SELL",
        quantity=Decimal("10"),
        filled_quantity=Decimal("0"),  # No shares filled
        price=Decimal("50.00"),
        total_value=Decimal("0.00"),  # No trade value for failed order
        status="REJECTED",
        execution_timestamp=datetime.now(UTC),
        error_message="Insufficient shares",
    )
    
    mock_trading_service = Mock()
    mock_trading_service.place_market_order.side_effect = [successful_order, failed_order]
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    result = adapter.execute_orders(sample_rebalance_plan)
    
    # Verify result reflects partial success
    assert result.success is False  # Not all orders succeeded
    assert result.orders_placed == 2
    assert result.orders_succeeded == 1  # Only FILLED orders are successful
    assert result.total_trade_value == Decimal("500.00")  # Only successful order
    
    # Check order results
    assert len(result.orders) == 2
    assert result.orders[0].success is True
    assert result.orders[1].success is False
    assert result.orders[1].error_message == "Insufficient shares"


def test_execute_orders_all_failures(mock_alpaca_manager, sample_rebalance_plan):
    """Test execution where all orders fail."""
    # Setup mock trading service to throw exceptions for all orders
    mock_trading_service = Mock()
    mock_trading_service.place_market_order.side_effect = Exception("Market closed")
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    result = adapter.execute_orders(sample_rebalance_plan)
    
    # Verify result reflects complete failure
    assert result.success is False
    assert result.orders_placed == 2
    assert result.orders_succeeded == 0
    assert result.total_trade_value == Decimal("0.00")
    
    # Check all order results are failures
    assert len(result.orders) == 2
    assert all(not order.success for order in result.orders)
    assert all("Market closed" in (order.error_message or "") for order in result.orders)


def test_execute_orders_empty_plan(mock_alpaca_manager):
    """Test execution with rebalance plan with no actual trades needed."""
    from datetime import datetime, UTC
    
    # Create a plan with items but zero trade amounts (effectively no trades)
    no_trade_plan = RebalancePlanDTO(
        plan_id="no-trade-plan",
        correlation_id="test-correlation",
        causation_id="test-causation",
        timestamp=datetime.now(UTC),
        items=[
            RebalancePlanItemDTO(
                symbol="AAPL",
                current_weight=Decimal("0.4"),
                target_weight=Decimal("0.4"),
                weight_diff=Decimal("0.0"),
                target_value=Decimal("2000.00"),
                current_value=Decimal("2000.00"),
                trade_amount=Decimal("0.00"),  # No trade needed
                action="BUY",  # Use valid action even though amount is zero
                priority=1,
            ),
        ],
        total_portfolio_value=Decimal("5000.00"),
        total_trade_value=Decimal("0.00"),
    )
    
    # Setup mock trading service (won't be called for zero amounts)
    mock_trading_service = Mock()
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    result = adapter.execute_orders(no_trade_plan)
    
    # Verify result for no-trade plan
    assert result.success is True  # Successfully handled no-trade scenario
    assert result.orders_placed == 1  # One "order" was processed
    assert result.orders_succeeded == 1  # The no-op order succeeded
    assert result.total_trade_value == Decimal("0.00")
    assert len(result.orders) == 1
    
    # Should NOT be called for zero amounts
    mock_trading_service.place_market_order.assert_not_called()


def test_execute_single_order(mock_alpaca_manager, sample_executed_order):
    """Test _execute_single_order method."""
    # Setup mock trading service
    mock_trading_service = Mock()
    mock_trading_service.place_market_order.return_value = sample_executed_order
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    # Create a mock rebalance item
    mock_item = Mock()
    mock_item.symbol = "AAPL"
    mock_item.action = "BUY"
    mock_item.trade_amount = Decimal("500.00")
    
    result = adapter._execute_single_order(mock_item)
    
    assert result is sample_executed_order
    mock_trading_service.place_market_order.assert_called_once_with(
        symbol="AAPL",
        side="buy",
        qty=None,
        notional=500.0,
    )


def test_convert_executed_order_to_dto(mock_alpaca_manager, sample_executed_order):
    """Test _convert_executed_order_to_dto method."""
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    # Create a mock original item
    mock_item = Mock()
    mock_item.symbol = "AAPL"
    mock_item.action = "BUY"
    
    result = adapter._convert_executed_order_to_dto(sample_executed_order, mock_item)
    
    # Verify conversion preserves all fields
    assert result.symbol == sample_executed_order.symbol
    assert result.action == sample_executed_order.action
    assert result.shares == sample_executed_order.shares
    assert result.trade_amount == sample_executed_order.trade_amount
    assert result.price == sample_executed_order.price
    assert result.order_id == sample_executed_order.order_id
    assert result.success == sample_executed_order.success
    assert result.error_message == sample_executed_order.error_message
    assert result.timestamp == sample_executed_order.timestamp


@patch('the_alchemiser.execution_v2.adapters.alpaca_execution_adapter.log_with_context')
def test_execute_orders_logging(mock_log, mock_alpaca_manager, sample_rebalance_plan, sample_executed_order):
    """Test that proper logging occurs during execution."""
    mock_trading_service = Mock()
    mock_trading_service.place_market_order.return_value = sample_executed_order
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    adapter.execute_orders(sample_rebalance_plan)
    
    # Verify logging was called (should be called multiple times for different events)
    assert mock_log.call_count >= 3  # Start, individual orders, completion
    
    # Check some specific log calls
    log_calls = [call[0] for call in mock_log.call_args_list]
    
    # Should have start log
    start_messages = [args[2] for args in log_calls if "Executing" in str(args[2])]
    assert len(start_messages) > 0
    
    # Should have completion log
    completion_messages = [args[2] for args in log_calls if "completed" in str(args[2])]
    assert len(completion_messages) > 0


def test_metadata_in_execution_result(mock_alpaca_manager, sample_rebalance_plan, sample_executed_order):
    """Test that metadata is properly set in execution result."""
    mock_trading_service = Mock()
    mock_trading_service.place_market_order.return_value = sample_executed_order
    mock_alpaca_manager._get_trading_service.return_value = mock_trading_service
    
    adapter = AlpacaExecutionAdapter(mock_alpaca_manager)
    
    result = adapter.execute_orders(sample_rebalance_plan)
    
    # Verify metadata contains expected information
    assert result.metadata is not None
    assert "adapter" in result.metadata
    assert result.metadata["adapter"] == "execution_v2.adapters.alpaca_execution_adapter"
    assert "original_plan_items" in result.metadata
    assert result.metadata["original_plan_items"] == 2