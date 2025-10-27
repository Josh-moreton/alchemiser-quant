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

    def test_valid_snapshot_creation(self, sample_account, sample_position):
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
            checksum=checksum,
        )

        assert snapshot.snapshot_id == "snap-123"
        assert snapshot.account_id == "test-account"
        assert len(snapshot.alpaca_positions) == 1

    def test_checksum_verification(self, sample_account):
        """Test checksum calculation and verification."""
        # Use fixed timestamp to ensure consistency
        created_at = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)

        # Create snapshot first to get consistent serialization
        # Use a temporary checksum that will be replaced
        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account",
            period_start=period_start,
            period_end=period_end,
            correlation_id="corr-123",
            created_at=created_at,
            alpaca_account=sample_account,
            alpaca_positions=[],
            alpaca_orders=[],
            checksum="temp-checksum-to-be-replaced",  # Temporary value for serialization
        )

        # Calculate checksum from model_dump (excluding ttl_timestamp and checksum)
        snapshot_dict = snapshot.model_dump(exclude={"ttl_timestamp", "checksum"})
        checksum = AccountSnapshot.calculate_checksum(snapshot_dict)

        # Create final snapshot with correct checksum
        snapshot_final = AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account",
            period_start=period_start,
            period_end=period_end,
            correlation_id="corr-123",
            created_at=created_at,
            alpaca_account=sample_account,
            alpaca_positions=[],
            alpaca_orders=[],
            checksum=checksum,
        )

        assert snapshot_final.verify_checksum()

    def test_ttl_timestamp_calculation(self, sample_account):
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
            checksum=checksum,
        )

        # Verify TTL is 90 days from creation
        from datetime import timedelta

        expected_ttl = created_at + timedelta(days=90)
        assert snapshot.ttl_timestamp == int(expected_ttl.timestamp())

    def test_frozen_snapshot(self, sample_account):
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
            checksum=checksum,
        )

        # Attempt to modify should raise ValidationError
        with pytest.raises(Exception):  # Pydantic frozen models raise ValidationError
            snapshot.snapshot_id = "modified-id"  # type: ignore[misc]
