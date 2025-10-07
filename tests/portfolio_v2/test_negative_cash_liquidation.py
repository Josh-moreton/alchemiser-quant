"""Business Unit: portfolio | Status: current.

Test negative cash balance liquidation in portfolio state reader.

Tests that the system automatically liquidates positions when detecting
negative or zero cash balances, then re-checks before raising exceptions.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
    AlpacaDataAdapter,
)
from the_alchemiser.portfolio_v2.core.state_reader import PortfolioStateReader
from the_alchemiser.shared.errors.exceptions import NegativeCashBalanceError


class TestNegativeCashLiquidation:
    """Test automatic liquidation on negative cash balance."""

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

    def test_negative_cash_triggers_liquidation_and_continues(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that negative cash balance triggers automatic liquidation and continues trading."""
        # Setup mock to return negative cash initially
        mock_alpaca_manager.get_account.return_value = {"cash": "-100.50"}
        mock_alpaca_manager.close_all_positions.return_value = [
            {"symbol": "AAPL", "status": "closed"},
            {"symbol": "MSFT", "status": "closed"},
        ]

        with patch.object(
            state_reader,
            "_wait_for_settlement",
            return_value=(Decimal("500.00"), {}),
        ):
            # Should succeed and return snapshot since liquidation recovers cash
            snapshot = state_reader.build_portfolio_snapshot()

        # Verify that close_all_positions was called
        mock_alpaca_manager.close_all_positions.assert_called_once_with(
            cancel_orders=True
        )

        # Verify snapshot was created successfully
        assert snapshot is not None
        assert snapshot.cash == Decimal("500.00")

    def test_negative_cash_liquidation_still_negative_raises(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that exception is raised when cash remains negative after liquidation."""
        # Setup mock to return negative cash
        mock_alpaca_manager.get_account.return_value = {"cash": "-100.50"}
        mock_alpaca_manager.close_all_positions.return_value = [
            {"symbol": "AAPL", "status": "closed"},
        ]

        with patch.object(
            state_reader,
            "_wait_for_settlement",
            return_value=(Decimal("-50.00"), {}),
        ):
            # Should raise exception because cash is still negative
            with pytest.raises(NegativeCashBalanceError) as exc_info:
                state_reader.build_portfolio_snapshot()

        # Verify liquidation was attempted
        mock_alpaca_manager.close_all_positions.assert_called_once_with(
            cancel_orders=True
        )

        # Exception should contain the final cash balance
        assert "-50.00" in str(exc_info.value.cash_balance)

    def test_zero_cash_triggers_liquidation_and_continues(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that zero cash balance triggers liquidation and continues if recovery succeeds."""
        # Setup mock to return zero cash initially
        mock_alpaca_manager.get_account.return_value = {"cash": "0.00"}
        mock_alpaca_manager.close_all_positions.return_value = [
            {"symbol": "TSLA", "status": "closed"},
        ]

        with patch.object(
            state_reader,
            "_wait_for_settlement",
            return_value=(Decimal("100.00"), {}),
        ):
            # Should succeed and return snapshot
            snapshot = state_reader.build_portfolio_snapshot()

        # Verify that close_all_positions was called
        mock_alpaca_manager.close_all_positions.assert_called_once()

        # Verify snapshot was created
        assert snapshot is not None
        assert snapshot.cash == Decimal("100.00")

    def test_liquidation_api_failure_handled(self, state_reader, mock_alpaca_manager):
        """Test that liquidation API failures are handled gracefully."""
        # Setup mock to return negative cash
        mock_alpaca_manager.get_account.return_value = {"cash": "-100.50"}
        mock_alpaca_manager.get_positions.return_value = []
        # Simulate API failure
        mock_alpaca_manager.close_all_positions.side_effect = Exception("API Error")

        # Should raise NegativeCashBalanceError (not the API error)
        with pytest.raises(NegativeCashBalanceError):
            state_reader.build_portfolio_snapshot()

        # Verify liquidation was attempted
        mock_alpaca_manager.close_all_positions.assert_called_once()

    def test_no_positions_to_liquidate(self, state_reader, mock_alpaca_manager):
        """Test behavior when there are no positions to liquidate."""
        # Setup mock to return negative cash with no positions
        mock_alpaca_manager.get_account.return_value = {"cash": "-50.00"}
        mock_alpaca_manager.get_positions.return_value = []
        # Empty result when no positions to close
        mock_alpaca_manager.close_all_positions.return_value = []

        # Should raise exception
        with pytest.raises(NegativeCashBalanceError):
            state_reader.build_portfolio_snapshot()

        # Verify liquidation was attempted even with no positions
        mock_alpaca_manager.close_all_positions.assert_called_once()

    def test_positive_cash_skips_liquidation(self, state_reader, mock_alpaca_manager):
        """Test that positive cash balance does not trigger liquidation."""
        # Setup mock to return positive cash
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        mock_alpaca_manager.get_positions.return_value = []

        # Should succeed without calling liquidation
        snapshot = state_reader.build_portfolio_snapshot()

        # Verify that close_all_positions was NOT called
        mock_alpaca_manager.close_all_positions.assert_not_called()

        # Verify snapshot was created successfully
        assert snapshot is not None
        assert snapshot.cash == Decimal("1000.00")


class TestAlpacaDataAdapterLiquidation:
    """Test AlpacaDataAdapter liquidation method."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        return Mock()

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    def test_liquidate_all_positions_success(self, data_adapter, mock_alpaca_manager):
        """Test successful liquidation returns True."""
        mock_alpaca_manager.close_all_positions.return_value = [
            {"symbol": "AAPL", "status": "closed"},
            {"symbol": "MSFT", "status": "closed"},
        ]

        result = data_adapter.liquidate_all_positions()

        assert result is True
        mock_alpaca_manager.close_all_positions.assert_called_once_with(
            cancel_orders=True
        )

    def test_liquidate_all_positions_empty_result(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that empty result returns False."""
        mock_alpaca_manager.close_all_positions.return_value = []

        result = data_adapter.liquidate_all_positions()

        assert result is False
        mock_alpaca_manager.close_all_positions.assert_called_once()

    def test_liquidate_all_positions_exception(self, data_adapter, mock_alpaca_manager):
        """Test that exceptions are caught and return False."""
        mock_alpaca_manager.close_all_positions.side_effect = Exception("API Error")

        result = data_adapter.liquidate_all_positions()

        assert result is False
        mock_alpaca_manager.close_all_positions.assert_called_once()
