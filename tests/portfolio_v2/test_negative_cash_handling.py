"""Business Unit: portfolio | Status: current

Test negative cash balance handling in portfolio state reader.

Tests that the system gracefully handles accounts with negative or zero
cash balances by raising appropriate exceptions during snapshot creation.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
    AlpacaDataAdapter,
)
from the_alchemiser.portfolio_v2.core.state_reader import PortfolioStateReader
from the_alchemiser.shared.errors.exceptions import NegativeCashBalanceError


class TestNegativeCashHandling:
    """Test negative cash balance handling."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        manager = Mock()
        manager.close_all_positions.return_value = []
        return manager

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    @pytest.fixture
    def state_reader(self, data_adapter):
        """Create state reader with mock data adapter."""
        return PortfolioStateReader(data_adapter)

    def test_negative_cash_raises_exception(self, state_reader, mock_alpaca_manager):
        """Test that negative cash balance raises NegativeCashBalanceError."""
        # Setup mock to return negative cash
        mock_alpaca_manager.get_account.return_value = {
            "cash": "-100.50",
        }
        mock_alpaca_manager.get_positions.return_value = []

        # Attempting to build snapshot should raise exception
        with pytest.raises(NegativeCashBalanceError) as exc_info:
            state_reader.build_portfolio_snapshot()

        # Verify exception details
        assert "cash balance is $-100.50" in str(exc_info.value).lower()
        assert exc_info.value.cash_balance == "-100.50"
        assert exc_info.value.module == "portfolio_v2.core.state_reader"

    def test_zero_cash_raises_exception(self, state_reader, mock_alpaca_manager):
        """Test that zero cash balance raises NegativeCashBalanceError."""
        # Setup mock to return zero cash
        mock_alpaca_manager.get_account.return_value = {
            "cash": "0.00",
        }
        mock_alpaca_manager.get_positions.return_value = []

        # Attempting to build snapshot should raise exception
        with pytest.raises(NegativeCashBalanceError) as exc_info:
            state_reader.build_portfolio_snapshot()

        # Verify exception details
        assert "cash balance is $0.00" in str(exc_info.value).lower()
        assert exc_info.value.cash_balance == "0.00"

    def test_positive_cash_succeeds(self, state_reader, mock_alpaca_manager):
        """Test that positive cash balance allows snapshot creation."""
        # Setup mock to return positive cash and empty positions
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        mock_alpaca_manager.get_positions.return_value = []

        # Should succeed without raising exception
        snapshot = state_reader.build_portfolio_snapshot()

        # Verify snapshot was created successfully
        assert snapshot is not None
        assert snapshot.cash == Decimal("1000.00")
        assert snapshot.total_value == Decimal("1000.00")

    def test_negative_cash_with_positions_still_raises(self, state_reader, mock_alpaca_manager):
        """Test that negative cash raises exception even with positions."""
        # Setup mock position with correct attributes
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty_available = 10  # Available quantity
        mock_position.qty = 10  # Total quantity

        mock_alpaca_manager.get_account.return_value = {
            "cash": "-50.00",
        }
        mock_alpaca_manager.get_positions.return_value = [mock_position]
        # Mock get_current_price to return a valid price
        mock_alpaca_manager.get_current_price.return_value = 150.00

        # Should raise exception during snapshot creation when cash is checked
        with pytest.raises(NegativeCashBalanceError) as exc_info:
            state_reader.build_portfolio_snapshot()

        # Verify the exception has correct details
        assert exc_info.value.cash_balance == "-50.00"
        assert "trading cannot proceed" in str(exc_info.value).lower()

    def test_very_small_positive_cash_succeeds(self, state_reader, mock_alpaca_manager):
        """Test that very small positive cash (e.g., $0.01) succeeds."""
        # Setup mock to return minimal positive cash
        mock_alpaca_manager.get_account.return_value = {
            "cash": "0.01",
        }
        mock_alpaca_manager.get_positions.return_value = []

        # Should succeed as cash is positive
        snapshot = state_reader.build_portfolio_snapshot()

        assert snapshot is not None
        assert snapshot.cash == Decimal("0.01")
        assert snapshot.total_value == Decimal("0.01")

    def test_exception_message_clarity(self, state_reader, mock_alpaca_manager):
        """Test that exception message is clear and actionable."""
        # Setup mock to return negative cash
        mock_alpaca_manager.get_account.return_value = {
            "cash": "-250.75",
        }
        mock_alpaca_manager.get_positions.return_value = []

        # Check exception message
        with pytest.raises(NegativeCashBalanceError) as exc_info:
            state_reader.build_portfolio_snapshot()

        error_message = str(exc_info.value)
        # Message should mention the specific amount and liquidation failure
        assert "-250.75" in error_message
        assert "liquidation failed" in error_message.lower()
