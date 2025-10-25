"""Business Unit: shared | Status: current.

Tests for account snapshot schemas.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.shared.schemas.account_snapshot import (
    AccountSnapshot,
    AlpacaAccountData,
    AlpacaOrderData,
    AlpacaPositionData,
    InternalLedgerSummary,
    StrategyPerformanceData,
)


class TestAlpacaAccountData:
    """Test suite for AlpacaAccountData DTO."""

    def test_valid_account_data(self):
        """Test creation with valid data."""
        account = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            equity=Decimal("15000.00"),
            portfolio_value=Decimal("15000.00"),
        )

        assert account.account_id == "test-account-123"
        assert account.buying_power == Decimal("10000.00")
        assert account.currency == "USD"

    def test_negative_buying_power_fails(self):
        """Test that negative buying power is rejected."""
        with pytest.raises(ValueError):
            AlpacaAccountData(
                account_id="test-account",
                status="ACTIVE",
                buying_power=Decimal("-100.00"),
                cash=Decimal("5000.00"),
                equity=Decimal("15000.00"),
                portfolio_value=Decimal("15000.00"),
            )


class TestAlpacaPositionData:
    """Test suite for AlpacaPositionData DTO."""

    def test_valid_position_data(self):
        """Test creation with valid position data."""
        position = AlpacaPositionData(
            symbol="AAPL",
            qty=Decimal("10"),
            qty_available=Decimal("10"),
            avg_entry_price=Decimal("150.25"),
            current_price=Decimal("155.50"),
            market_value=Decimal("1555.00"),
            cost_basis=Decimal("1502.50"),
            unrealized_pl=Decimal("52.50"),
            unrealized_plpc=Decimal("0.035"),
            side="long",
        )

        assert position.symbol == "AAPL"
        assert position.qty == Decimal("10")
        assert position.unrealized_pl == Decimal("52.50")

    def test_zero_price_fails(self):
        """Test that zero price is rejected."""
        with pytest.raises(ValueError):
            AlpacaPositionData(
                symbol="AAPL",
                qty=Decimal("10"),
                avg_entry_price=Decimal("0"),  # Invalid
                current_price=Decimal("155.50"),
                market_value=Decimal("1555.00"),
                cost_basis=Decimal("1502.50"),
                unrealized_pl=Decimal("52.50"),
                unrealized_plpc=Decimal("0.035"),
                side="long",
            )


class TestAlpacaOrderData:
    """Test suite for AlpacaOrderData DTO."""

    def test_valid_order_data(self):
        """Test creation with valid order data."""
        order = AlpacaOrderData(
            order_id="order-123",
            symbol="AAPL",
            side="buy",
            order_type="market",
            qty=Decimal("10"),
            filled_qty=Decimal("10"),
            filled_avg_price=Decimal("150.25"),
            status="filled",
            time_in_force="day",
            submitted_at=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            filled_at=datetime(2025, 1, 15, 14, 30, 5, tzinfo=UTC),
        )

        assert order.order_id == "order-123"
        assert order.symbol == "AAPL"
        assert order.filled_qty == Decimal("10")


class TestStrategyPerformanceData:
    """Test suite for StrategyPerformanceData DTO."""

    def test_valid_strategy_performance(self):
        """Test creation with valid strategy performance data."""
        perf = StrategyPerformanceData(
            strategy_name="nuclear",
            total_trades=10,
            buy_trades=5,
            sell_trades=5,
            total_buy_value=Decimal("5000.00"),
            total_sell_value=Decimal("5200.00"),
            gross_pnl=Decimal("200.00"),
            realized_pnl=Decimal("180.00"),
            symbols_traded=["AAPL", "GOOGL"],
            first_trade_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
            last_trade_at=datetime(2025, 1, 15, 16, 0, 0, tzinfo=UTC),
        )

        assert perf.strategy_name == "nuclear"
        assert perf.total_trades == 10
        assert perf.gross_pnl == Decimal("200.00")
        assert len(perf.symbols_traded) == 2


class TestInternalLedgerSummary:
    """Test suite for InternalLedgerSummary DTO."""

    def test_valid_ledger_summary(self):
        """Test creation with valid ledger summary."""
        perf = StrategyPerformanceData(
            strategy_name="nuclear",
            total_trades=5,
            buy_trades=3,
            sell_trades=2,
            total_buy_value=Decimal("3000.00"),
            total_sell_value=Decimal("3100.00"),
            gross_pnl=Decimal("100.00"),
            realized_pnl=Decimal("90.00"),
            symbols_traded=["AAPL"],
        )

        summary = InternalLedgerSummary(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("3000.00"),
            total_sell_value=Decimal("3100.00"),
            strategies_active=["nuclear"],
            strategy_performance={"nuclear": perf},
        )

        assert summary.ledger_id == "ledger-123"
        assert summary.total_trades == 5
        assert len(summary.strategies_active) == 1
        assert "nuclear" in summary.strategy_performance


class TestAccountSnapshot:
    """Test suite for AccountSnapshot DTO."""

    @pytest.fixture
    def sample_account(self):
        """Create sample account data."""
        return AlpacaAccountData(
            account_id="test-account",
            status="ACTIVE",
            buying_power=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            equity=Decimal("15000.00"),
            portfolio_value=Decimal("15000.00"),
        )

    @pytest.fixture
    def sample_position(self):
        """Create sample position data."""
        return AlpacaPositionData(
            symbol="AAPL",
            qty=Decimal("10"),
            avg_entry_price=Decimal("150.25"),
            current_price=Decimal("155.50"),
            market_value=Decimal("1555.00"),
            cost_basis=Decimal("1502.50"),
            unrealized_pl=Decimal("52.50"),
            unrealized_plpc=Decimal("0.035"),
            side="long",
        )

    @pytest.fixture
    def sample_ledger_summary(self):
        """Create sample ledger summary."""
        return InternalLedgerSummary(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("3000.00"),
            total_sell_value=Decimal("3100.00"),
            strategies_active=["nuclear"],
            strategy_performance={},
        )

    def test_valid_snapshot_creation(self, sample_account, sample_position, sample_ledger_summary):
        """Test creation of valid snapshot."""
        snapshot_data = {
            "snapshot_id": "snap-123",
            "snapshot_version": "1.0",
            "account_id": "test-account",
            "period_start": datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC).isoformat(),
            "period_end": datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC).isoformat(),
            "correlation_id": "corr-123",
            "created_at": datetime.now(UTC).isoformat(),
            "alpaca_account": sample_account.model_dump(),
            "alpaca_positions": [sample_position.model_dump()],
            "alpaca_orders": [],
            "internal_ledger": sample_ledger_summary.model_dump(),
        }

        checksum = AccountSnapshot.calculate_checksum(snapshot_data)

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account",
            period_start=datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC),
            correlation_id="corr-123",
            created_at=datetime.now(UTC),
            alpaca_account=sample_account,
            alpaca_positions=[sample_position],
            alpaca_orders=[],
            internal_ledger=sample_ledger_summary,
            checksum=checksum,
        )

        assert snapshot.snapshot_id == "snap-123"
        assert snapshot.account_id == "test-account"
        assert len(snapshot.alpaca_positions) == 1

    def test_checksum_verification(self, sample_account, sample_ledger_summary):
        """Test checksum calculation and verification."""
        snapshot_data = {
            "snapshot_id": "snap-123",
            "snapshot_version": "1.0",
            "account_id": "test-account",
            "period_start": datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC).isoformat(),
            "period_end": datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC).isoformat(),
            "correlation_id": "corr-123",
            "created_at": datetime.now(UTC).isoformat(),
            "alpaca_account": sample_account.model_dump(),
            "alpaca_positions": [],
            "alpaca_orders": [],
            "internal_ledger": sample_ledger_summary.model_dump(),
        }

        checksum = AccountSnapshot.calculate_checksum(snapshot_data)

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account",
            period_start=datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC),
            correlation_id="corr-123",
            created_at=datetime.now(UTC),
            alpaca_account=sample_account,
            alpaca_positions=[],
            alpaca_orders=[],
            internal_ledger=sample_ledger_summary,
            checksum=checksum,
        )

        assert snapshot.verify_checksum()

    def test_ttl_timestamp_calculation(self, sample_account, sample_ledger_summary):
        """Test TTL timestamp calculation (90 days from creation)."""
        created_at = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        snapshot_data = {
            "snapshot_id": "snap-123",
            "snapshot_version": "1.0",
            "account_id": "test-account",
            "period_start": created_at.isoformat(),
            "period_end": created_at.isoformat(),
            "correlation_id": "corr-123",
            "created_at": created_at.isoformat(),
            "alpaca_account": sample_account.model_dump(),
            "alpaca_positions": [],
            "alpaca_orders": [],
            "internal_ledger": sample_ledger_summary.model_dump(),
        }

        checksum = AccountSnapshot.calculate_checksum(snapshot_data)

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account",
            period_start=created_at,
            period_end=created_at,
            correlation_id="corr-123",
            created_at=created_at,
            alpaca_account=sample_account,
            alpaca_positions=[],
            alpaca_orders=[],
            internal_ledger=sample_ledger_summary,
            checksum=checksum,
        )

        # Verify TTL is 90 days from creation
        from datetime import timedelta

        expected_ttl = created_at + timedelta(days=90)
        assert snapshot.ttl_timestamp == int(expected_ttl.timestamp())

    def test_frozen_snapshot(self, sample_account, sample_ledger_summary):
        """Test that snapshot is immutable (frozen)."""
        snapshot_data = {
            "snapshot_id": "snap-123",
            "snapshot_version": "1.0",
            "account_id": "test-account",
            "period_start": datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC).isoformat(),
            "period_end": datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC).isoformat(),
            "correlation_id": "corr-123",
            "created_at": datetime.now(UTC).isoformat(),
            "alpaca_account": sample_account.model_dump(),
            "alpaca_positions": [],
            "alpaca_orders": [],
            "internal_ledger": sample_ledger_summary.model_dump(),
        }

        checksum = AccountSnapshot.calculate_checksum(snapshot_data)

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account",
            period_start=datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC),
            correlation_id="corr-123",
            created_at=datetime.now(UTC),
            alpaca_account=sample_account,
            alpaca_positions=[],
            alpaca_orders=[],
            internal_ledger=sample_ledger_summary,
            checksum=checksum,
        )

        # Attempt to modify should raise ValidationError
        with pytest.raises(Exception):  # Pydantic frozen models raise ValidationError
            snapshot.snapshot_id = "modified-id"  # type: ignore[misc]
