"""Business Unit: shared | Status: current.

Tests for AccountSnapshotService.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from the_alchemiser.shared.services.account_snapshot_service import AccountSnapshotService


class TestAccountSnapshotService:
    """Test suite for AccountSnapshotService."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create a mock AlpacaManager."""
        manager = MagicMock()

        # Mock account
        mock_account = MagicMock()
        mock_account.id = "test-account-123"
        mock_account.account_number = "PA123456"
        mock_account.status = "ACTIVE"
        mock_account.currency = "USD"
        mock_account.buying_power = 10000.00
        mock_account.cash = 5000.00
        mock_account.equity = 15000.00
        mock_account.portfolio_value = 15000.00
        mock_account.last_equity = None
        mock_account.long_market_value = None
        mock_account.short_market_value = None
        mock_account.initial_margin = None
        mock_account.maintenance_margin = None

        manager.get_account_object.return_value = mock_account

        # Mock positions (empty list)
        manager.get_positions.return_value = []

        # Mock orders (empty list)
        manager.get_orders.return_value = []

        return manager

    @pytest.fixture
    def mock_snapshot_repository(self):
        """Create a mock AccountSnapshotRepository."""
        repo = MagicMock()
        repo.put_snapshot = MagicMock()
        return repo

    @pytest.fixture
    def mock_ledger_repository(self):
        """Create a mock DynamoDBTradeLedgerRepository."""
        repo = MagicMock()

        # Mock query_trades_by_correlation to return empty list
        repo.query_trades_by_correlation.return_value = []

        # Mock compute_strategy_performance
        repo.compute_strategy_performance.return_value = {
            "strategy_name": "nuclear",
            "total_trades": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "total_buy_value": Decimal("0"),
            "total_sell_value": Decimal("0"),
            "gross_pnl": Decimal("0"),
            "realized_pnl": Decimal("0"),
            "symbols_traded": [],
            "first_trade_at": None,
            "last_trade_at": None,
        }

        return repo

    @pytest.fixture
    def service(self, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository):
        """Create AccountSnapshotService with mocked dependencies."""
        return AccountSnapshotService(
            mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
        )

    def test_generate_snapshot_creates_valid_snapshot(
        self,
        service,
        mock_alpaca_manager,
        mock_snapshot_repository,
        mock_ledger_repository,
    ):
        """Test that generate_snapshot creates a valid snapshot."""
        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        snapshot = service.generate_snapshot(
            account_id, correlation_id, period_start, period_end, ledger_id
        )

        # Verify snapshot properties
        assert snapshot.account_id == account_id
        assert snapshot.correlation_id == correlation_id
        assert snapshot.period_start == period_start
        assert snapshot.period_end == period_end

        # Verify Alpaca data was fetched
        assert mock_alpaca_manager.get_account_object.called
        assert mock_alpaca_manager.get_positions.called
        assert mock_alpaca_manager.get_orders.called

        # Verify ledger data was fetched
        assert mock_ledger_repository.query_trades_by_correlation.called

        # Verify snapshot was stored
        assert mock_snapshot_repository.put_snapshot.called

    def test_generate_snapshot_calculates_checksum(
        self, service, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
    ):
        """Test that generate_snapshot calculates and verifies checksum."""
        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        snapshot = service.generate_snapshot(
            account_id, correlation_id, period_start, period_end, ledger_id
        )

        # Verify checksum is set
        assert snapshot.checksum is not None
        assert len(snapshot.checksum) > 0

        # Verify checksum is valid
        assert snapshot.verify_checksum()

    def test_generate_snapshot_handles_trades(
        self, service, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
    ):
        """Test that generate_snapshot handles trades from ledger."""
        # Mock trades data
        mock_ledger_repository.query_trades_by_correlation.return_value = [
            {
                "order_id": "order-1",
                "direction": "BUY",
                "filled_qty": "10",
                "fill_price": "150.25",
                "strategy_names": ["nuclear"],
            },
            {
                "order_id": "order-2",
                "direction": "SELL",
                "filled_qty": "10",
                "fill_price": "155.50",
                "strategy_names": ["nuclear"],
            },
        ]

        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        snapshot = service.generate_snapshot(
            account_id, correlation_id, period_start, period_end, ledger_id
        )

        # Verify trades were processed
        assert snapshot.internal_ledger.total_trades == 2
        assert snapshot.internal_ledger.total_buy_value > Decimal("0")
        assert snapshot.internal_ledger.total_sell_value > Decimal("0")

    def test_generate_snapshot_handles_multiple_strategies(
        self, service, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
    ):
        """Test that generate_snapshot handles multiple strategies."""
        # Mock trades with multiple strategies
        mock_ledger_repository.query_trades_by_correlation.return_value = [
            {
                "order_id": "order-1",
                "direction": "BUY",
                "filled_qty": "10",
                "fill_price": "150.25",
                "strategy_names": ["nuclear", "tecl"],
            }
        ]

        # Mock performance for both strategies
        def mock_compute_performance(strategy_name: str):
            return {
                "strategy_name": strategy_name,
                "total_trades": 1,
                "buy_trades": 1,
                "sell_trades": 0,
                "total_buy_value": Decimal("1502.50"),
                "total_sell_value": Decimal("0"),
                "gross_pnl": Decimal("0"),
                "realized_pnl": Decimal("0"),
                "symbols_traded": ["AAPL"],
                "first_trade_at": "2025-01-15T10:00:00+00:00",
                "last_trade_at": "2025-01-15T10:00:00+00:00",
            }

        mock_ledger_repository.compute_strategy_performance.side_effect = mock_compute_performance

        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        snapshot = service.generate_snapshot(
            account_id, correlation_id, period_start, period_end, ledger_id
        )

        # Verify both strategies are captured
        assert len(snapshot.internal_ledger.strategies_active) == 2
        assert "nuclear" in snapshot.internal_ledger.strategies_active
        assert "tecl" in snapshot.internal_ledger.strategies_active

    def test_generate_snapshot_fails_without_account(
        self, service, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
    ):
        """Test that generate_snapshot raises error when account cannot be fetched."""
        # Mock account fetch failure
        mock_alpaca_manager.get_account_object.return_value = None

        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        with pytest.raises(ValueError, match="Failed to fetch Alpaca account data"):
            service.generate_snapshot(account_id, correlation_id, period_start, period_end, ledger_id)

    def test_generate_snapshot_handles_positions(
        self, service, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
    ):
        """Test that generate_snapshot handles positions correctly."""
        # Mock position data
        mock_position = MagicMock()
        mock_position.symbol = "AAPL"
        mock_position.qty = 10
        mock_position.qty_available = 10
        mock_position.avg_entry_price = 150.25
        mock_position.current_price = 155.50
        mock_position.market_value = 1555.00
        mock_position.cost_basis = 1502.50
        mock_position.unrealized_pl = 52.50
        mock_position.unrealized_plpc = 0.035
        mock_position.unrealized_intraday_pl = None
        mock_position.unrealized_intraday_plpc = None
        mock_position.side = "long"
        mock_position.asset_class = "us_equity"

        mock_alpaca_manager.get_positions.return_value = [mock_position]

        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        snapshot = service.generate_snapshot(
            account_id, correlation_id, period_start, period_end, ledger_id
        )

        # Verify positions were captured
        assert len(snapshot.alpaca_positions) == 1
        assert snapshot.alpaca_positions[0].symbol == "AAPL"
        assert snapshot.alpaca_positions[0].qty == Decimal("10")

    def test_generate_snapshot_handles_orders(
        self, service, mock_alpaca_manager, mock_snapshot_repository, mock_ledger_repository
    ):
        """Test that generate_snapshot handles orders correctly."""
        # Mock order data
        mock_order = MagicMock()
        mock_order.id = "order-123"
        mock_order.symbol = "AAPL"
        mock_order.side = "buy"
        mock_order.order_type = "market"
        mock_order.qty = 10
        mock_order.notional = None
        mock_order.filled_qty = 10
        mock_order.filled_avg_price = 150.25
        mock_order.status = "filled"
        mock_order.time_in_force = "day"
        mock_order.limit_price = None
        mock_order.stop_price = None
        mock_order.submitted_at = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
        mock_order.filled_at = datetime(2025, 1, 15, 10, 0, 5, tzinfo=UTC)
        mock_order.expired_at = None
        mock_order.canceled_at = None

        mock_alpaca_manager.get_orders.return_value = [mock_order]

        account_id = "test-account-123"
        correlation_id = "corr-456"
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        ledger_id = "ledger-123"

        snapshot = service.generate_snapshot(
            account_id, correlation_id, period_start, period_end, ledger_id
        )

        # Verify orders were captured
        assert len(snapshot.alpaca_orders) == 1
        assert snapshot.alpaca_orders[0].order_id == "order-123"
        assert snapshot.alpaca_orders[0].symbol == "AAPL"
