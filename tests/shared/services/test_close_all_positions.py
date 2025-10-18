"""Business Unit: shared | Status: current

Test close_all_positions functionality in AlpacaTradingService and AlpacaManager.

Tests the liquidation API integration at the shared services layer.
"""

from unittest.mock import Mock

import pytest

from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService


class TestAlpacaTradingServiceCloseAllPositions:
    """Test close_all_positions in AlpacaTradingService."""

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

    def test_close_all_positions_with_list_response(self, trading_service, mock_trading_client):
        """Test close_all_positions with list response from Alpaca."""
        # Mock response objects
        mock_response_1 = Mock()
        mock_response_1.symbol = "AAPL"
        mock_response_1.status = "closed"

        mock_response_2 = Mock()
        mock_response_2.symbol = "MSFT"
        mock_response_2.status = "closed"

        mock_trading_client.close_all_positions.return_value = [
            mock_response_1,
            mock_response_2,
        ]

        result = trading_service.close_all_positions(cancel_orders=True)

        # Verify result is a list of dicts
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)

        # Verify the API was called correctly
        mock_trading_client.close_all_positions.assert_called_once_with(cancel_orders=True)

    def test_close_all_positions_with_dict_response(self, trading_service, mock_trading_client):
        """Test close_all_positions with dict response."""
        mock_trading_client.close_all_positions.return_value = {
            "status": "success",
            "count": 2,
        }

        result = trading_service.close_all_positions(cancel_orders=False)

        # Verify result is a list containing the dict
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == {"status": "success", "count": 2}

        # Verify the API was called correctly
        mock_trading_client.close_all_positions.assert_called_once_with(cancel_orders=False)

    def test_close_all_positions_empty_result(self, trading_service, mock_trading_client):
        """Test close_all_positions with no positions to close."""
        mock_trading_client.close_all_positions.return_value = []

        result = trading_service.close_all_positions(cancel_orders=True)

        # Verify empty result
        assert isinstance(result, list)
        assert len(result) == 0

    def test_close_all_positions_exception(self, trading_service, mock_trading_client):
        """Test close_all_positions handles exceptions gracefully."""
        mock_trading_client.close_all_positions.side_effect = Exception("API Error")

        result = trading_service.close_all_positions(cancel_orders=True)

        # Verify error handling returns empty list
        assert isinstance(result, list)
        assert len(result) == 0

    def test_close_all_positions_default_cancel_orders(self, trading_service, mock_trading_client):
        """Test that cancel_orders defaults to True."""
        mock_trading_client.close_all_positions.return_value = []

        trading_service.close_all_positions()

        # Verify default parameter
        mock_trading_client.close_all_positions.assert_called_once_with(cancel_orders=True)
