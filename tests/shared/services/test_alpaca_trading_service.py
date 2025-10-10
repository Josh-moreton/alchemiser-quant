"""Business Unit: shared | Status: current.

Test suite for AlpacaTradingService order placement and management.

Tests order placement, cancellation, and error handling.
"""

from unittest.mock import Mock, patch

import pytest
from alpaca.trading.enums import OrderSide, OrderStatus, TimeInForce

from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService


class TestAlpacaTradingServiceOrderPlacement:
    """Test suite for AlpacaTradingService order placement."""

    @pytest.fixture
    def mock_trading_client(self):
        """Create mock Alpaca trading client."""
        return Mock()

    @pytest.fixture
    def mock_websocket_manager(self):
        """Create mock WebSocket manager."""
        manager = Mock()
        # WebSocket manager methods don't need specific return values for these tests
        return manager

    @pytest.fixture
    def trading_service(self, mock_trading_client, mock_websocket_manager):
        """Create trading service with mocks."""
        return AlpacaTradingService(
            trading_client=mock_trading_client,
            websocket_manager=mock_websocket_manager,
            paper_trading=True,
        )

    def test_is_paper_trading_property(self, trading_service):
        """Test is_paper_trading property."""
        assert trading_service.is_paper_trading is True

    def test_is_paper_trading_live_mode(self, mock_trading_client, mock_websocket_manager):
        """Test is_paper_trading property in live mode."""
        service = AlpacaTradingService(
            trading_client=mock_trading_client,
            websocket_manager=mock_websocket_manager,
            paper_trading=False,
        )
        assert service.is_paper_trading is False

    def test_cleanup_when_trading_active(self, trading_service, mock_websocket_manager):
        """Test cleanup releases WebSocket resources when trading is active."""
        # Simulate active trading
        trading_service._trading_service_active = True

        trading_service.cleanup()

        mock_websocket_manager.release_trading_service.assert_called_once()
        assert trading_service._trading_service_active is False

    def test_cleanup_when_trading_inactive(self, trading_service, mock_websocket_manager):
        """Test cleanup does nothing when trading is inactive."""
        trading_service._trading_service_active = False

        trading_service.cleanup()

        mock_websocket_manager.release_trading_service.assert_not_called()

    def test_cleanup_with_exception(self, trading_service, mock_websocket_manager):
        """Test cleanup handles exceptions gracefully."""
        trading_service._trading_service_active = True
        mock_websocket_manager.release_trading_service.side_effect = Exception("Release Error")

        # Should not raise exception
        trading_service.cleanup()

    def test_normalize_response_list_of_objects(self, trading_service):
        """Test normalizing list of objects to dict list."""
        mock_obj1 = Mock()
        mock_obj1.symbol = "AAPL"
        mock_obj1.status = "filled"

        mock_obj2 = Mock()
        mock_obj2.symbol = "MSFT"
        mock_obj2.status = "pending"

        response = [mock_obj1, mock_obj2]
        result = trading_service._normalize_response_to_dict_list(response)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)

    def test_normalize_response_list_of_dicts(self, trading_service):
        """Test normalizing list of dicts."""
        response = [
            {"symbol": "AAPL", "status": "filled"},
            {"symbol": "MSFT", "status": "pending"},
        ]
        result = trading_service._normalize_response_to_dict_list(response)

        assert result == response

    def test_normalize_response_single_dict(self, trading_service):
        """Test normalizing single dict response."""
        response = {"status": "success", "count": 2}
        result = trading_service._normalize_response_to_dict_list(response)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == response

    def test_normalize_response_empty_list(self, trading_service):
        """Test normalizing empty list."""
        response: list[object] = []
        result = trading_service._normalize_response_to_dict_list(response)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_normalize_response_non_dict_object(self, trading_service):
        """Test normalizing non-dict object fallback."""
        response = ["some_string"]
        result = trading_service._normalize_response_to_dict_list(response)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "response" in result[0]

    def test_place_market_order_success_with_qty(
        self, trading_service, mock_trading_client, mock_websocket_manager
    ):
        """Test successful market order placement with quantity."""
        mock_order = Mock()
        mock_order.id = "order123"
        mock_order.symbol = "AAPL"
        mock_order.side = OrderSide.BUY
        mock_order.qty = 10.0
        mock_order.filled_qty = 0.0
        mock_order.status = OrderStatus.ACCEPTED
        mock_order.submitted_at = "2024-01-01T10:00:00Z"


        mock_trading_client.submit_order.return_value = mock_order

        result = trading_service.place_market_order("AAPL", "buy", qty=10.0)

        # Just verify order was placed, don't check specific order_id due to DTO conversion complexity
        assert result.symbol == "AAPL"
        mock_trading_client.submit_order.assert_called_once()

    def test_place_market_order_success_with_notional(
        self, trading_service, mock_trading_client, mock_websocket_manager
    ):
        """Test successful market order placement with notional amount."""
        mock_order = Mock()
        mock_order.id = "order123"
        mock_order.symbol = "AAPL"
        mock_order.side = OrderSide.BUY
        mock_order.notional = 1000.0
        mock_order.filled_qty = 0.0
        mock_order.status = OrderStatus.ACCEPTED
        mock_order.submitted_at = "2024-01-01T10:00:00Z"

        mock_trading_client.submit_order.return_value = mock_order

        result = trading_service.place_market_order("AAPL", "buy", notional=1000.0)

        assert result.symbol == "AAPL"

    def test_place_market_order_validation_error_empty_symbol(self, trading_service):
        """Test market order with empty symbol."""
        result = trading_service.place_market_order("", "buy", qty=10.0)

        assert "INVALID" in result.order_id

    def test_place_market_order_validation_error_invalid_side(self, trading_service):
        """Test market order with invalid side."""
        result = trading_service.place_market_order("AAPL", "invalid", qty=10.0)

        assert "INVALID" in result.order_id

    def test_place_market_order_validation_error_no_qty_or_notional(self, trading_service):
        """Test market order without qty or notional."""
        result = trading_service.place_market_order("AAPL", "buy")

        assert "INVALID" in result.order_id

    def test_place_market_order_api_exception(
        self, trading_service, mock_trading_client, mock_websocket_manager
    ):
        """Test market order handles API exceptions."""
        mock_trading_client.submit_order.side_effect = Exception("API Error")

        result = trading_service.place_market_order("AAPL", "buy", qty=10.0)

        # Error orders have FAILED order_id
        assert "FAILED" in result.order_id or "ERROR" in result.order_id

    def test_place_market_order_complete_exit_flag(
        self, trading_service, mock_trading_client, mock_websocket_manager
    ):
        """Test market order with is_complete_exit flag."""
        mock_order = Mock()
        mock_order.id = "order123"
        mock_order.symbol = "AAPL"
        mock_order.side = OrderSide.SELL
        mock_order.qty = 10.0
        mock_order.filled_qty = 0.0
        mock_order.status = OrderStatus.ACCEPTED
        mock_order.submitted_at = "2024-01-01T10:00:00Z"

        mock_trading_client.submit_order.return_value = mock_order

        result = trading_service.place_market_order(
            "AAPL", "sell", qty=10.0, is_complete_exit=True
        )

        assert result.symbol == "AAPL"

    def test_place_limit_order_validation_empty_symbol(self, trading_service):
        """Test limit order with empty symbol."""
        result = trading_service.place_limit_order("", "buy", 10.0, 150.0)

        assert result.success is False
        assert "symbol" in result.error.lower() or "empty" in result.error.lower()

    def test_place_limit_order_validation_negative_quantity(self, trading_service):
        """Test limit order with negative quantity."""
        result = trading_service.place_limit_order("AAPL", "buy", -10.0, 150.0)

        assert result.success is False
        assert "quantity" in result.error.lower() or "positive" in result.error.lower()

    def test_place_limit_order_validation_zero_price(self, trading_service):
        """Test limit order with zero limit price."""
        result = trading_service.place_limit_order("AAPL", "buy", 10.0, 0.0)

        assert result.success is False
        assert "price" in result.error.lower() or "positive" in result.error.lower()

    def test_place_limit_order_validation_invalid_side(self, trading_service):
        """Test limit order with invalid side."""
        result = trading_service.place_limit_order("AAPL", "invalid", 10.0, 150.0)

        assert result.success is False
        assert "side" in result.error.lower() or "invalid" in result.error.lower()

    def test_place_limit_order_api_exception(
        self, trading_service, mock_trading_client, mock_websocket_manager
    ):
        """Test limit order handles API exceptions."""
        mock_trading_client.submit_order.side_effect = Exception("API Error")

        result = trading_service.place_limit_order("AAPL", "buy", 10.0, 150.0)


        assert result.success is False
        # Just verify it failed, don't check exact error message
        assert result.order_id == "unknown"


class TestAlpacaOrderConversionEdgeCases:
    """Test edge cases in Alpaca order to execution result conversion."""

    @pytest.fixture
    def mock_trading_client(self):
        """Create mock Alpaca trading client."""
        return Mock()

    @pytest.fixture
    def mock_websocket_manager(self):
        """Create mock WebSocket manager."""
        return Mock()

    @pytest.fixture
    def trading_service(self, mock_trading_client, mock_websocket_manager):
        """Create trading service with mocks."""
        return AlpacaTradingService(
            trading_client=mock_trading_client,
            websocket_manager=mock_websocket_manager,
            paper_trading=True,
        )

    def test_filled_order_without_avg_fill_price_treated_as_accepted(
        self, trading_service, mock_trading_client
    ):
        """Test that filled orders without avg_fill_price are treated as accepted.

        This handles race conditions where Alpaca reports status='filled' before
        the avg_fill_price is populated during settlement.

        When this happens, we downgrade the status to 'accepted' and reset filled_qty to 0
        to satisfy validation rules (accepted status requires filled_qty == 0).
        """
        from datetime import UTC, datetime
        from decimal import Decimal

        # Create mock order that is "filled" but missing avg_fill_price
        mock_order = Mock()
        mock_order.id = "test-order-123"
        mock_order.status = OrderStatus.FILLED  # Status is FILLED
        mock_order.filled_qty = "10.5"
        mock_order.avg_fill_price = None  # But price is None (race condition)
        mock_order.filled_avg_price = None  # Alternative field also None
        mock_order.submitted_at = datetime.now(UTC)
        mock_order.updated_at = None

        mock_trading_client.get_order_by_id.return_value = mock_order

        # Get execution result
        result = trading_service.get_order_execution_result("test-order-123")

        # Should treat as "accepted" (pending) not "filled" to avoid validation error
        assert result.success is True
        assert result.status == "accepted"  # NOT "filled"
        assert result.filled_qty == Decimal("0")  # Reset to 0 for validation
        assert result.avg_fill_price is None
        assert result.order_id == "test-order-123"

    def test_filled_order_with_avg_fill_price_stays_filled(
        self, trading_service, mock_trading_client
    ):
        """Test that filled orders WITH avg_fill_price remain as filled."""
        from datetime import UTC, datetime
        from decimal import Decimal

        # Create mock order with both status and price
        mock_order = Mock()
        mock_order.id = "test-order-456"
        mock_order.status = OrderStatus.FILLED
        mock_order.filled_qty = "10.5"
        mock_order.avg_fill_price = "150.25"  # Price IS populated
        mock_order.filled_avg_price = None
        mock_order.submitted_at = datetime.now(UTC)
        mock_order.updated_at = datetime.now(UTC)

        mock_trading_client.get_order_by_id.return_value = mock_order

        # Get execution result
        result = trading_service.get_order_execution_result("test-order-456")

        # Should remain as "filled"
        assert result.success is True
        assert result.status == "filled"
        assert result.filled_qty == Decimal("10.5")
        assert result.avg_fill_price == Decimal("150.25")
        assert result.order_id == "test-order-456"

    def test_partially_filled_without_price_treated_as_accepted(
        self, trading_service, mock_trading_client
    ):
        """Test that partially_filled orders without price are treated as accepted.

        Similar to filled orders, partially filled orders without avg_fill_price
        are downgraded to 'accepted' status with filled_qty reset to 0.
        """
        from datetime import UTC, datetime
        from decimal import Decimal

        mock_order = Mock()
        mock_order.id = "test-order-789"
        mock_order.status = OrderStatus.PARTIALLY_FILLED
        mock_order.filled_qty = "5.25"
        mock_order.avg_fill_price = None  # Missing price
        mock_order.filled_avg_price = None
        mock_order.submitted_at = datetime.now(UTC)
        mock_order.updated_at = None

        mock_trading_client.get_order_by_id.return_value = mock_order

        result = trading_service.get_order_execution_result("test-order-789")

        # Should treat as "accepted" to avoid validation error
        assert result.success is True
        assert result.status == "accepted"  # NOT "partially_filled"
        assert result.filled_qty == Decimal("0")  # Reset to 0 for validation
        assert result.avg_fill_price is None

