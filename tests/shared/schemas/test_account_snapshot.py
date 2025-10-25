"""Business Unit: shared | Status: current.

Tests for account snapshot schemas (DTOs).

This test module validates AccountSnapshot and related DTOs,
ensuring proper validation, checksum computation, and S3 key generation.
"""

# ruff: noqa: S101  # Allow asserts in tests
# ruff: noqa: DTZ001  # Allow naive datetime for testing timezone conversion

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.account_snapshot import (
    AccountSnapshot,
    AlpacaAccountData,
    AlpacaOrderData,
    AlpacaPositionData,
    InternalLedgerData,
    StrategyPerformance,
)


class TestAlpacaAccountData:
    """Test suite for AlpacaAccountData DTO."""

    def test_create_valid_account_data(self) -> None:
        """Test creating valid Alpaca account data."""
        data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        assert data.account_id == "test-account-123"
        assert data.buying_power == Decimal("100000.00")
        assert data.cash == Decimal("50000.00")

    def test_account_data_is_frozen(self) -> None:
        """Test that AlpacaAccountData is immutable."""
        data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime.now(UTC),
        )

        with pytest.raises(ValidationError):
            data.buying_power = Decimal("200000.00")  # type: ignore

    def test_negative_buying_power_rejected(self) -> None:
        """Test that negative buying power is rejected."""
        with pytest.raises(ValidationError):
            AlpacaAccountData(
                account_id="test-account-123",
                account_number="PA123456789",
                status="ACTIVE",
                currency="USD",
                buying_power=Decimal("-100.00"),  # Negative - invalid
                cash=Decimal("50000.00"),
                equity=Decimal("150000.00"),
                portfolio_value=Decimal("150000.00"),
                captured_at=datetime.now(UTC),
            )


class TestAlpacaPositionData:
    """Test suite for AlpacaPositionData DTO."""

    def test_create_valid_position(self) -> None:
        """Test creating valid position data."""
        pos = AlpacaPositionData(
            symbol="AAPL",
            qty=Decimal("100"),
            market_value=Decimal("15000.00"),
            avg_entry_price=Decimal("150.00"),
            current_price=Decimal("150.00"),
            unrealized_pl=Decimal("0.00"),
            unrealized_plpc=Decimal("0.00"),
            cost_basis=Decimal("15000.00"),
        )

        assert pos.symbol == "AAPL"
        assert pos.qty == Decimal("100")

    def test_symbol_normalized_to_uppercase(self) -> None:
        """Test symbol is normalized to uppercase."""
        pos = AlpacaPositionData(
            symbol="aapl",  # lowercase
            qty=Decimal("100"),
            market_value=Decimal("15000.00"),
            avg_entry_price=Decimal("150.00"),
            current_price=Decimal("150.00"),
            unrealized_pl=Decimal("0.00"),
            unrealized_plpc=Decimal("0.00"),
            cost_basis=Decimal("15000.00"),
        )

        assert pos.symbol == "AAPL"  # Should be uppercase


class TestAlpacaOrderData:
    """Test suite for AlpacaOrderData DTO."""

    def test_create_valid_order(self) -> None:
        """Test creating valid order data."""
        order = AlpacaOrderData(
            order_id="order-123",
            symbol="AAPL",
            side="buy",
            order_type="market",
            status="filled",
            qty=Decimal("10"),
            filled_qty=Decimal("10"),
            submitted_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            filled_at=datetime(2024, 1, 1, 10, 1, 0, tzinfo=UTC),
        )

        assert order.order_id == "order-123"
        assert order.side == "buy"
        assert order.filled_qty == Decimal("10")

    def test_side_must_be_buy_or_sell(self) -> None:
        """Test that order side must be 'buy' or 'sell'."""
        with pytest.raises(ValidationError):
            AlpacaOrderData(
                order_id="order-123",
                symbol="AAPL",
                side="hold",  # Invalid
                order_type="market",
                status="filled",
                qty=Decimal("10"),
                filled_qty=Decimal("10"),
                submitted_at=datetime.now(UTC),
            )


class TestStrategyPerformance:
    """Test suite for StrategyPerformance DTO."""

    def test_create_valid_strategy_performance(self) -> None:
        """Test creating valid strategy performance metrics."""
        perf = StrategyPerformance(
            strategy_name="nuclear",
            total_trades=10,
            buy_trades=5,
            sell_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("27000.00"),
            realized_pnl=Decimal("2000.00"),
            gross_pnl=Decimal("2000.00"),
            symbols_traded=["AAPL", "GOOGL"],
            first_trade_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            last_trade_at=datetime(2024, 1, 15, 16, 0, 0, tzinfo=UTC),
        )

        assert perf.strategy_name == "nuclear"
        assert perf.total_trades == 10
        assert perf.realized_pnl == Decimal("2000.00")
        assert len(perf.symbols_traded) == 2

    def test_strategy_performance_is_frozen(self) -> None:
        """Test that StrategyPerformance is immutable."""
        perf = StrategyPerformance(
            strategy_name="nuclear",
            total_trades=10,
            buy_trades=5,
            sell_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("27000.00"),
        )

        with pytest.raises(ValidationError):
            perf.total_trades = 20  # type: ignore


class TestInternalLedgerData:
    """Test suite for InternalLedgerData DTO."""

    def test_create_valid_ledger_data(self) -> None:
        """Test creating valid internal ledger data."""
        ledger = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=10,
            total_buy_value=Decimal("50000.00"),
            total_sell_value=Decimal("30000.00"),
            strategies_active=["nuclear", "tecl"],
            strategy_allocations={"nuclear": Decimal("0.3"), "tecl": Decimal("0.7")},
        )

        assert ledger.total_trades == 10
        assert len(ledger.strategies_active) == 2

    def test_ledger_data_with_strategy_performance(self) -> None:
        """Test ledger data with per-strategy performance metrics."""
        nuclear_perf = StrategyPerformance(
            strategy_name="nuclear",
            total_trades=5,
            buy_trades=3,
            sell_trades=2,
            total_buy_value=Decimal("15000.00"),
            total_sell_value=Decimal("16000.00"),
            realized_pnl=Decimal("1000.00"),
            gross_pnl=Decimal("1000.00"),
            symbols_traded=["AAPL"],
        )

        tecl_perf = StrategyPerformance(
            strategy_name="tecl",
            total_trades=5,
            buy_trades=2,
            sell_trades=3,
            total_buy_value=Decimal("35000.00"),
            total_sell_value=Decimal("34000.00"),
            realized_pnl=Decimal("-1000.00"),
            gross_pnl=Decimal("-1000.00"),
            symbols_traded=["TECL"],
        )

        ledger = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=10,
            total_buy_value=Decimal("50000.00"),
            total_sell_value=Decimal("50000.00"),
            strategies_active=["nuclear", "tecl"],
            strategy_performance={
                "nuclear": nuclear_perf,
                "tecl": tecl_perf,
            },
        )

        assert len(ledger.strategy_performance) == 2
        assert ledger.strategy_performance["nuclear"].realized_pnl == Decimal("1000.00")
        assert ledger.strategy_performance["tecl"].realized_pnl == Decimal("-1000.00")


class TestInternalLedgerData_Legacy:
    """Test suite for InternalLedgerData DTO (legacy tests)."""

    def test_create_valid_ledger_data(self) -> None:
        """Test creating valid internal ledger data."""
        ledger = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=10,
            total_buy_value=Decimal("50000.00"),
            total_sell_value=Decimal("30000.00"),
            strategies_active=["nuclear", "tecl"],
            strategy_allocations={"nuclear": Decimal("0.3"), "tecl": Decimal("0.7")},
        )

        assert ledger.total_trades == 10
        assert len(ledger.strategies_active) == 2


class TestAccountSnapshot:
    """Test suite for AccountSnapshot DTO."""

    def test_create_valid_snapshot(self) -> None:
        """Test creating a valid account snapshot."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        ledger_data = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("15000.00"),
        )

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            account_id="test-account-123",
            period_start=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 1, 16, 0, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 1, 16, 5, 0, tzinfo=UTC),
            correlation_id="corr-123",
            alpaca_account=account_data,
            internal_ledger=ledger_data,
        )

        assert snapshot.snapshot_id == "snap-123"
        assert snapshot.account_id == "test-account-123"
        assert snapshot.snapshot_version == "1.0"

    def test_snapshot_is_frozen(self) -> None:
        """Test that AccountSnapshot is immutable."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime.now(UTC),
        )

        ledger_data = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("15000.00"),
        )

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            account_id="test-account-123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            created_at=datetime.now(UTC),
            correlation_id="corr-123",
            alpaca_account=account_data,
            internal_ledger=ledger_data,
        )

        with pytest.raises(ValidationError):
            snapshot.account_id = "different-account"  # type: ignore

    def test_compute_checksum(self) -> None:
        """Test checksum computation is deterministic."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        ledger_data = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("15000.00"),
        )

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            account_id="test-account-123",
            period_start=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 1, 16, 0, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 1, 16, 5, 0, tzinfo=UTC),
            correlation_id="corr-123",
            alpaca_account=account_data,
            internal_ledger=ledger_data,
        )

        checksum1 = snapshot.compute_checksum()
        checksum2 = snapshot.compute_checksum()

        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex digest length

    def test_verify_checksum(self) -> None:
        """Test checksum verification."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        ledger_data = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("15000.00"),
        )

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            account_id="test-account-123",
            period_start=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 1, 16, 0, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 1, 16, 5, 0, tzinfo=UTC),
            correlation_id="corr-123",
            alpaca_account=account_data,
            internal_ledger=ledger_data,
            checksum=None,
        )

        # Without checksum, verification should fail
        assert not snapshot.verify_checksum()

        # With correct checksum, verification should pass
        checksum = snapshot.compute_checksum()
        snapshot_with_checksum = AccountSnapshot(
            **snapshot.model_dump(exclude={"checksum"}),
            checksum=checksum,
        )
        assert snapshot_with_checksum.verify_checksum()

    def test_s3_key_generation(self) -> None:
        """Test deterministic S3 key generation."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC),
        )

        ledger_data = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("15000.00"),
        )

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            account_id="test-account-123",
            period_start=datetime(2024, 1, 15, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 15, 14, 35, 0, tzinfo=UTC),
            correlation_id="corr-123",
            alpaca_account=account_data,
            internal_ledger=ledger_data,
        )

        expected_key = "snapshots/test-account-123/2024/01/15/1430_snapshot.json"
        assert snapshot.s3_key == expected_key

    def test_snapshot_with_positions_and_orders(self) -> None:
        """Test snapshot with positions and orders."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            account_number="PA123456789",
            status="ACTIVE",
            currency="USD",
            buying_power=Decimal("100000.00"),
            cash=Decimal("50000.00"),
            equity=Decimal("150000.00"),
            portfolio_value=Decimal("150000.00"),
            captured_at=datetime.now(UTC),
        )

        position = AlpacaPositionData(
            symbol="AAPL",
            qty=Decimal("100"),
            market_value=Decimal("15000.00"),
            avg_entry_price=Decimal("150.00"),
            current_price=Decimal("150.00"),
            unrealized_pl=Decimal("0.00"),
            unrealized_plpc=Decimal("0.00"),
            cost_basis=Decimal("15000.00"),
        )

        order = AlpacaOrderData(
            order_id="order-123",
            symbol="AAPL",
            side="buy",
            order_type="market",
            status="filled",
            qty=Decimal("10"),
            filled_qty=Decimal("10"),
            submitted_at=datetime.now(UTC),
        )

        ledger_data = InternalLedgerData(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("25000.00"),
            total_sell_value=Decimal("15000.00"),
        )

        snapshot = AccountSnapshot(
            snapshot_id="snap-123",
            account_id="test-account-123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            created_at=datetime.now(UTC),
            correlation_id="corr-123",
            alpaca_account=account_data,
            alpaca_positions=[position],
            alpaca_orders=[order],
            internal_ledger=ledger_data,
        )

        assert len(snapshot.alpaca_positions) == 1
        assert len(snapshot.alpaca_orders) == 1
        assert snapshot.alpaca_positions[0].symbol == "AAPL"
