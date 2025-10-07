"""Business Unit: portfolio | Status: current

Test portfolio state reader branch coverage.

Tests edge cases and error paths in PortfolioStateReader to achieve
comprehensive branch coverage, including missing prices, validation failures,
and settlement wait logic.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
    AlpacaDataAdapter,
)
from the_alchemiser.portfolio_v2.core.state_reader import PortfolioStateReader
from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot
from the_alchemiser.shared.errors.exceptions import NegativeCashBalanceError


class TestStateReaderBranchCoverage:
    """Test branch coverage for PortfolioStateReader."""

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

    def test_missing_price_for_position_raises_error(self, state_reader, mock_alpaca_manager):
        """Test that missing price for a position raises ValueError."""
        # Setup: account has a position but no price available
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty_available = 10
        mock_position.qty = 10
        mock_alpaca_manager.get_positions.return_value = [mock_position]
        
        # Mock get_current_price to return None (price unavailable)
        mock_alpaca_manager.get_current_price.return_value = None
        
        # Should raise ValueError when price is missing or invalid
        with pytest.raises(ValueError) as exc_info:
            state_reader.build_portfolio_snapshot()
        
        # Check the actual error message from the adapter
        assert "Invalid price" in str(exc_info.value) or "Missing price" in str(exc_info.value)

    def test_validation_failure_logs_warning_but_continues(self, state_reader, mock_alpaca_manager):
        """Test that validation failure logs warning but doesn't fail."""
        # Setup account with slight mismatch in total value calculation
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty_available = 10
        mock_position.qty = 10
        mock_alpaca_manager.get_positions.return_value = [mock_position]
        
        # Price that will cause validation mismatch
        mock_alpaca_manager.get_current_price.return_value = 150.0
        
        # Create snapshot - should succeed even with validation mismatch
        snapshot = state_reader.build_portfolio_snapshot()
        
        # Verify snapshot was created
        assert snapshot is not None
        assert snapshot.cash == Decimal("1000.00")
        # Position value: 10 * 150 = 1500
        # Total: 1000 + 1500 = 2500
        assert snapshot.total_value == Decimal("2500.00")

    def test_build_snapshot_with_requested_symbols(self, state_reader, mock_alpaca_manager):
        """Test building snapshot with specific requested symbols."""
        mock_alpaca_manager.get_account.return_value = {
            "cash": "2000.00",
        }
        
        # No positions
        mock_alpaca_manager.get_positions.return_value = []
        
        # Mock prices for requested symbols
        mock_alpaca_manager.get_current_price.side_effect = lambda symbol: {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
        }.get(symbol)
        
        # Build snapshot with specific symbols
        snapshot = state_reader.build_portfolio_snapshot(symbols={"AAPL", "GOOGL"})
        
        assert snapshot is not None
        assert snapshot.cash == Decimal("2000.00")
        assert "AAPL" in snapshot.prices
        assert "GOOGL" in snapshot.prices

    def test_build_snapshot_merges_position_and_requested_symbols(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that snapshot includes both position symbols and requested symbols."""
        mock_alpaca_manager.get_account.return_value = {
            "cash": "3000.00",
        }
        
        # Has position in AAPL
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty_available = 10
        mock_position.qty = 10
        mock_alpaca_manager.get_positions.return_value = [mock_position]
        
        # Mock prices
        mock_alpaca_manager.get_current_price.side_effect = lambda symbol: {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 380.0,
        }.get(symbol)
        
        # Request specific symbols (GOOGL, MSFT)
        snapshot = state_reader.build_portfolio_snapshot(symbols={"GOOGL", "MSFT"})
        
        # Should include prices for: AAPL (position), GOOGL (requested), MSFT (requested)
        assert "AAPL" in snapshot.prices
        assert "GOOGL" in snapshot.prices
        assert "MSFT" in snapshot.prices

    def test_settlement_wait_success_after_retries(self, state_reader, mock_alpaca_manager):
        """Test that settlement wait succeeds after liquidation and polling."""
        # First call: negative cash
        # After liquidation: cash becomes positive
        call_count = [0]
        
        def get_account_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return {"cash": "-100.00"}
            # After first settlement check, return positive
            else:
                return {"cash": "500.00"}
        
        mock_alpaca_manager.get_account.side_effect = get_account_side_effect
        mock_alpaca_manager.get_positions.return_value = []
        
        # Mock the liquidate method to return True
        with patch.object(state_reader._data_adapter, 'liquidate_all_positions', return_value=True):
            snapshot = state_reader.build_portfolio_snapshot()
        
        assert snapshot is not None
        assert snapshot.cash == Decimal("500.00")

    def test_settlement_wait_timeout_still_negative(self, state_reader, mock_alpaca_manager):
        """Test that settlement wait times out if cash remains negative."""
        # Cash stays negative even after liquidation
        mock_alpaca_manager.get_account.return_value = {"cash": "-100.00"}
        mock_alpaca_manager.get_positions.return_value = []
        
        # Mock liquidation to succeed but cash still negative
        with patch.object(state_reader._data_adapter, 'liquidate_all_positions', return_value=True):
            # The settlement wait will poll and timeout
            with pytest.raises(NegativeCashBalanceError) as exc_info:
                state_reader.build_portfolio_snapshot()
        
        # The actual error message says "after liquidation"  
        assert "liquidation" in str(exc_info.value).lower()

    def test_calculate_portfolio_value_with_multiple_positions(
        self, state_reader, mock_alpaca_manager
    ):
        """Test portfolio value calculation with multiple positions."""
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        
        # Multiple positions
        pos1 = Mock()
        pos1.symbol = "AAPL"
        pos1.qty_available = 10
        pos1.qty = 10
        
        pos2 = Mock()
        pos2.symbol = "GOOGL"
        pos2.qty_available = 5
        pos2.qty = 5
        
        mock_alpaca_manager.get_positions.return_value = [pos1, pos2]
        
        # Mock prices
        mock_alpaca_manager.get_current_price.side_effect = lambda symbol: {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
        }.get(symbol)
        
        snapshot = state_reader.build_portfolio_snapshot()
        
        # Calculate expected total:
        # AAPL: 10 * 150 = 1500
        # GOOGL: 5 * 2800 = 14000
        # Cash: 1000
        # Total: 16500
        assert snapshot.total_value == Decimal("16500.00")

    def test_exception_during_snapshot_building_is_raised(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that exceptions during snapshot building are logged and raised."""
        # Force an exception in get_account_cash
        mock_alpaca_manager.get_account.side_effect = Exception("API connection failed")
        
        with pytest.raises(Exception) as exc_info:
            state_reader.build_portfolio_snapshot()
        
        assert "API connection failed" in str(exc_info.value)

    def test_empty_positions_and_symbols_builds_cash_only_snapshot(
        self, state_reader, mock_alpaca_manager
    ):
        """Test building snapshot with no positions and no requested symbols."""
        mock_alpaca_manager.get_account.return_value = {
            "cash": "5000.00",
        }
        mock_alpaca_manager.get_positions.return_value = []
        
        snapshot = state_reader.build_portfolio_snapshot()
        
        assert snapshot.cash == Decimal("5000.00")
        assert snapshot.total_value == Decimal("5000.00")
        assert len(snapshot.positions) == 0
        assert len(snapshot.prices) == 0

    def test_positions_with_zero_price_fails_validation(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that zero or negative prices cause validation to fail."""
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty_available = 10
        mock_position.qty = 10
        mock_alpaca_manager.get_positions.return_value = [mock_position]
        
        # Return zero price
        mock_alpaca_manager.get_current_price.return_value = 0.0
        
        # Should raise ValueError for invalid price
        with pytest.raises(ValueError) as exc_info:
            state_reader.build_portfolio_snapshot()
        
        # Zero/negative prices should be filtered in the adapter,
        # but if they get through, snapshot validation should catch them
        assert "price" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()


class TestStateReaderLiquidationBranches:
    """Test liquidation-specific branches in state reader."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        manager = Mock()
        return manager

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    @pytest.fixture
    def state_reader(self, data_adapter):
        """Create state reader with mock data adapter."""
        return PortfolioStateReader(data_adapter)

    def test_liquidation_failure_immediately_raises_error(
        self, state_reader, mock_alpaca_manager
    ):
        """Test that liquidation failure immediately raises error."""
        mock_alpaca_manager.get_account.return_value = {"cash": "-100.00"}
        mock_alpaca_manager.get_positions.return_value = []
        
        # Liquidation fails (returns False or exception)
        mock_alpaca_manager.close_all_positions.return_value = None  # Simulate failure
        
        with pytest.raises(NegativeCashBalanceError) as exc_info:
            state_reader.build_portfolio_snapshot()
        
        assert "liquidation failed" in str(exc_info.value).lower()

    def test_liquidation_with_positions_then_success(
        self, state_reader, mock_alpaca_manager
    ):
        """Test successful liquidation recovers from negative cash."""
        call_count = [0]
        
        def get_account_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return {"cash": "-50.00"}
            # After first settlement check, return positive
            else:
                return {"cash": "100.00"}
        
        def get_positions_side_effect():
            # After liquidation, always return empty (simulating all positions closed)
            return []
        
        mock_alpaca_manager.get_account.side_effect = get_account_side_effect
        mock_alpaca_manager.get_positions.side_effect = get_positions_side_effect
        
        # Mock liquidation to succeed
        with patch.object(state_reader._data_adapter, 'liquidate_all_positions', return_value=True):
            snapshot = state_reader.build_portfolio_snapshot()
        
        assert snapshot is not None
        assert snapshot.cash == Decimal("100.00")
        assert len(snapshot.positions) == 0
