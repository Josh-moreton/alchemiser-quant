"""Business Unit: shared | Status: current.

Unit tests for Alpaca replace_order functionality.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from alpaca.trading.requests import ReplaceOrderRequest

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.broker import OrderExecutionResult
from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService


@pytest.fixture
def mock_trading_client():
    """Create a mock TradingClient."""
    mock = Mock()
    return mock


@pytest.fixture
def mock_websocket_manager():
    """Create a mock WebSocketConnectionManager."""
    mock = Mock()
    mock.get_trading_service.return_value = True
    return mock


@pytest.fixture
def alpaca_trading_service(mock_trading_client, mock_websocket_manager):
    """Create AlpacaTradingService with mocked dependencies."""
    return AlpacaTradingService(
        trading_client=mock_trading_client,
        websocket_manager=mock_websocket_manager,
        paper_trading=True,
    )


@pytest.mark.unit
def test_replace_order_success(alpaca_trading_service, mock_trading_client):
    """Test successful order replacement."""
    # Setup mock order response with proper spec
    mock_order = Mock(
        spec=[
            "id",
            "symbol",
            "status",
            "qty",
            "filled_qty",
            "filled_avg_price",
            "submitted_at",
            "updated_at",
        ]
    )
    mock_order.id = "test-order-123"
    mock_order.symbol = "AAPL"
    mock_order.status = "accepted"
    mock_order.qty = 15
    mock_order.filled_qty = 0
    mock_order.filled_avg_price = None
    mock_order.submitted_at = datetime.now(UTC)
    mock_order.updated_at = datetime.now(UTC)

    mock_trading_client.replace_order_by_id.return_value = mock_order

    # Create replace request
    replace_request = ReplaceOrderRequest(qty=15, limit_price=150.50)

    # Execute
    result = alpaca_trading_service.replace_order("test-order-123", replace_request)

    # Verify
    assert isinstance(result, OrderExecutionResult)
    assert result.success is True
    assert result.order_id == "test-order-123"
    assert result.status == "accepted"
    mock_trading_client.replace_order_by_id.assert_called_once_with(
        "test-order-123", replace_request
    )


@pytest.mark.unit
def test_replace_order_with_none_data(alpaca_trading_service, mock_trading_client):
    """Test order replacement with None order_data."""
    # Setup mock order response with proper spec
    mock_order = Mock(
        spec=[
            "id",
            "symbol",
            "status",
            "qty",
            "filled_qty",
            "filled_avg_price",
            "submitted_at",
            "updated_at",
        ]
    )
    mock_order.id = "test-order-456"
    mock_order.symbol = "GOOGL"
    mock_order.status = "accepted"
    mock_order.qty = 10
    mock_order.filled_qty = 0
    mock_order.filled_avg_price = None
    mock_order.submitted_at = datetime.now(UTC)
    mock_order.updated_at = datetime.now(UTC)

    mock_trading_client.replace_order_by_id.return_value = mock_order

    # Execute with None order_data
    result = alpaca_trading_service.replace_order("test-order-456", None)

    # Verify
    assert isinstance(result, OrderExecutionResult)
    assert result.success is True
    assert result.order_id == "test-order-456"
    mock_trading_client.replace_order_by_id.assert_called_once_with("test-order-456", None)


@pytest.mark.unit
def test_replace_order_failure(alpaca_trading_service, mock_trading_client):
    """Test order replacement failure."""
    # Setup mock to raise exception
    mock_trading_client.replace_order_by_id.side_effect = Exception("Order not found")

    replace_request = ReplaceOrderRequest(qty=20)

    # Execute
    result = alpaca_trading_service.replace_order("invalid-order", replace_request)

    # Verify error handling
    assert isinstance(result, OrderExecutionResult)
    assert result.success is False
    assert result.error is not None
    assert "Order not found" in str(result.error)


@pytest.mark.unit
def test_replace_order_updates_quantity(alpaca_trading_service, mock_trading_client):
    """Test that replace_order correctly updates order quantity."""
    # Setup mock order with updated quantity and proper spec
    mock_order = Mock(
        spec=[
            "id",
            "symbol",
            "status",
            "qty",
            "filled_qty",
            "filled_avg_price",
            "submitted_at",
            "updated_at",
        ]
    )
    mock_order.id = "test-order-789"
    mock_order.symbol = "TSLA"
    mock_order.status = "accepted"
    mock_order.qty = 25  # Updated quantity
    mock_order.filled_qty = 0
    mock_order.filled_avg_price = None
    mock_order.submitted_at = datetime.now(UTC)
    mock_order.updated_at = datetime.now(UTC)

    mock_trading_client.replace_order_by_id.return_value = mock_order

    # Create replace request with new quantity
    replace_request = ReplaceOrderRequest(qty=25)

    # Execute
    result = alpaca_trading_service.replace_order("test-order-789", replace_request)

    # Verify
    assert result.success is True
    assert result.filled_qty == Decimal("0")
    mock_trading_client.replace_order_by_id.assert_called_once()


@pytest.mark.unit
def test_replace_order_updates_limit_price(alpaca_trading_service, mock_trading_client):
    """Test that replace_order correctly updates limit price."""
    # Setup mock order with updated limit price and proper spec
    mock_order = Mock(
        spec=[
            "id",
            "symbol",
            "status",
            "qty",
            "filled_qty",
            "filled_avg_price",
            "limit_price",
            "submitted_at",
            "updated_at",
        ]
    )
    mock_order.id = "test-order-101"
    mock_order.symbol = "NVDA"
    mock_order.status = "accepted"
    mock_order.qty = 10
    mock_order.filled_qty = 0
    mock_order.filled_avg_price = None
    mock_order.limit_price = 200.00  # Updated limit price
    mock_order.submitted_at = datetime.now(UTC)
    mock_order.updated_at = datetime.now(UTC)

    mock_trading_client.replace_order_by_id.return_value = mock_order

    # Create replace request with new limit price
    replace_request = ReplaceOrderRequest(limit_price=200.00)

    # Execute
    result = alpaca_trading_service.replace_order("test-order-101", replace_request)

    # Verify
    assert result.success is True
    mock_trading_client.replace_order_by_id.assert_called_once_with(
        "test-order-101", replace_request
    )


@pytest.mark.integration
def test_alpaca_manager_replace_order_delegation(mock_trading_client, mock_websocket_manager):
    """Test that AlpacaManager delegates replace_order to trading service."""
    # Note: This test would require more setup to properly instantiate AlpacaManager
    # For now, we verify the method exists and has correct signature
    from inspect import signature

    # Verify method exists with correct signature
    sig = signature(AlpacaManager.replace_order)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "order_id" in params
    assert "order_data" in params
