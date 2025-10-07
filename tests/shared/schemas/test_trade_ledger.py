"""Business Unit: shared | Status: current.

Tests for trade ledger schemas (DTOs).

This test module validates TradeLedgerEntry and TradeLedger DTOs directly,
ensuring proper validation, immutability, and numerical correctness.
"""

# ruff: noqa: S101  # Allow asserts in tests
# ruff: noqa: DTZ001  # Allow naive datetime for testing timezone conversion

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.trade_ledger import TradeLedger, TradeLedgerEntry


class TestTradeLedgerEntry:
    """Test suite for TradeLedgerEntry DTO."""

    def test_create_valid_entry(self) -> None:
        """Test creating a valid trade ledger entry."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10.5"),
            fill_price=Decimal("150.25"),
            fill_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            order_type="MARKET",
        )

        assert entry.order_id == "order-123"
        assert entry.symbol == "AAPL"
        assert entry.filled_qty == Decimal("10.5")
        assert entry.fill_price == Decimal("150.25")

    def test_entry_is_frozen(self) -> None:
        """Test that TradeLedgerEntry is immutable."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        with pytest.raises(ValidationError):
            entry.symbol = "TSLA"  # type: ignore

    def test_symbol_normalized_to_uppercase(self) -> None:
        """Test symbol is normalized to uppercase."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="aapl",  # lowercase
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        assert entry.symbol == "AAPL"  # Should be uppercase

    def test_symbol_whitespace_stripped(self) -> None:
        """Test symbol whitespace is stripped during normalization."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="  AAPL  ",  # with whitespace
            direction="SELL",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="LIMIT",
        )

        assert entry.symbol == "AAPL"  # Whitespace stripped

    def test_invalid_direction_rejected(self) -> None:
        """Test invalid direction values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="HOLD",  # type: ignore[arg-type]  # Invalid direction
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

        assert "direction" in str(exc_info.value).lower()

    def test_invalid_order_type_rejected(self) -> None:
        """Test invalid order types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="TRAILING_STOP",  # type: ignore[arg-type]  # Invalid type
            )

        assert "order_type" in str(exc_info.value).lower()

    def test_negative_filled_qty_rejected(self) -> None:
        """Test negative filled quantity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("-10"),  # Negative
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

        assert "filled_qty" in str(exc_info.value).lower()

    def test_zero_filled_qty_rejected(self) -> None:
        """Test zero filled quantity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("0"),  # Zero
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

        assert "filled_qty" in str(exc_info.value).lower()

    def test_negative_fill_price_rejected(self) -> None:
        """Test negative fill price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("-150"),  # Negative
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

        assert "fill_price" in str(exc_info.value).lower()

    def test_zero_fill_price_rejected(self) -> None:
        """Test zero fill price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("0"),  # Zero
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

        assert "fill_price" in str(exc_info.value).lower()

    def test_timezone_naive_timestamp_converted(self) -> None:
        """Test naive timestamp is converted to timezone-aware."""
        naive_timestamp = datetime(2024, 1, 1, 12, 0, 0)  # No timezone

        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=naive_timestamp,
            order_type="MARKET",
        )

        assert entry.fill_timestamp.tzinfo is not None
        assert entry.fill_timestamp.tzinfo == UTC

    def test_optional_bid_ask_fields(self) -> None:
        """Test optional bid/ask fields can be None."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
            bid_at_fill=None,  # Optional
            ask_at_fill=None,  # Optional
        )

        assert entry.bid_at_fill is None
        assert entry.ask_at_fill is None

    def test_optional_bid_ask_fields_with_values(self) -> None:
        """Test optional bid/ask fields with valid values."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150.00"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
            bid_at_fill=Decimal("149.50"),
            ask_at_fill=Decimal("150.50"),
        )

        assert entry.bid_at_fill == Decimal("149.50")
        assert entry.ask_at_fill == Decimal("150.50")

    def test_negative_bid_rejected(self) -> None:
        """Test negative bid price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
                bid_at_fill=Decimal("-149.50"),  # Negative
                ask_at_fill=Decimal("150.50"),
            )

        assert "bid_at_fill" in str(exc_info.value).lower()

    def test_negative_ask_rejected(self) -> None:
        """Test negative ask price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
                bid_at_fill=Decimal("149.50"),
                ask_at_fill=Decimal("-150.50"),  # Negative
            )

        assert "ask_at_fill" in str(exc_info.value).lower()

    def test_strategy_weights_valid_sum(self) -> None:
        """Test strategy weights with valid sum (~1.0)."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
            strategy_names=["strategy_a", "strategy_b"],
            strategy_weights={
                "strategy_a": Decimal("0.6"),
                "strategy_b": Decimal("0.4"),
            },
        )

        assert entry.strategy_weights is not None
        assert entry.strategy_weights["strategy_a"] == Decimal("0.6")
        assert entry.strategy_weights["strategy_b"] == Decimal("0.4")

    def test_strategy_weights_exactly_one(self) -> None:
        """Test strategy weights summing to exactly 1.0."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
            strategy_weights={"strategy_a": Decimal("1.0")},
        )

        assert entry.strategy_weights is not None
        assert sum(entry.strategy_weights.values()) == Decimal("1.0")

    def test_strategy_weights_at_lower_tolerance(self) -> None:
        """Test strategy weights at lower tolerance boundary (0.99)."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
            strategy_weights={"strategy_a": Decimal("0.99")},
        )

        assert entry.strategy_weights is not None
        assert entry.strategy_weights["strategy_a"] == Decimal("0.99")

    def test_strategy_weights_at_upper_tolerance(self) -> None:
        """Test strategy weights at upper tolerance boundary (1.01)."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
            strategy_weights={"strategy_a": Decimal("1.01")},
        )

        assert entry.strategy_weights is not None
        assert entry.strategy_weights["strategy_a"] == Decimal("1.01")

    def test_strategy_weights_below_tolerance_rejected(self) -> None:
        """Test strategy weights below tolerance are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
                strategy_weights={"strategy_a": Decimal("0.5")},  # Too low
            )

        assert "must sum to ~1.0" in str(exc_info.value)

    def test_strategy_weights_above_tolerance_rejected(self) -> None:
        """Test strategy weights above tolerance are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
                strategy_weights={"strategy_a": Decimal("1.5")},  # Too high
            )

        assert "must sum to ~1.0" in str(exc_info.value)

    def test_empty_strategy_weights_rejected(self) -> None:
        """Test empty strategy weights dict is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
                strategy_weights={},  # Empty dict
            )

        assert "cannot be empty" in str(exc_info.value)

    def test_empty_string_fields_rejected(self) -> None:
        """Test empty string fields are rejected."""
        with pytest.raises(ValidationError):
            TradeLedgerEntry(
                order_id="",  # Empty
                correlation_id="corr-123",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

    def test_symbol_max_length_enforced(self) -> None:
        """Test symbol max length constraint is enforced."""
        with pytest.raises(ValidationError) as exc_info:
            TradeLedgerEntry(
                order_id="order-123",
                correlation_id="corr-123",
                symbol="VERYLONGSYMBOL",  # > 10 chars
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )

        assert "symbol" in str(exc_info.value).lower()


class TestTradeLedger:
    """Test suite for TradeLedger DTO."""

    def test_create_empty_ledger(self) -> None:
        """Test creating an empty trade ledger."""
        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
        )

        assert ledger.ledger_id == "ledger-123"
        assert ledger.total_entries == 0
        assert len(ledger.entries) == 0

    def test_ledger_is_frozen(self) -> None:
        """Test that TradeLedger is immutable."""
        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
        )

        with pytest.raises(ValidationError):
            ledger.ledger_id = "new-id"  # type: ignore

    def test_create_ledger_with_entries(self) -> None:
        """Test creating a ledger with entries."""
        entry1 = TradeLedgerEntry(
            order_id="order-1",
            correlation_id="corr-1",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        entry2 = TradeLedgerEntry(
            order_id="order-2",
            correlation_id="corr-2",
            symbol="TSLA",
            direction="SELL",
            filled_qty=Decimal("5"),
            fill_price=Decimal("200"),
            fill_timestamp=datetime.now(UTC),
            order_type="LIMIT",
        )

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=[entry1, entry2],
        )

        assert ledger.total_entries == 2
        assert len(ledger.entries) == 2

    def test_total_entries_property(self) -> None:
        """Test total_entries property returns correct count."""
        entries = [
            TradeLedgerEntry(
                order_id=f"order-{i}",
                correlation_id=f"corr-{i}",
                symbol="AAPL",
                direction="BUY",
                filled_qty=Decimal("10"),
                fill_price=Decimal("150"),
                fill_timestamp=datetime.now(UTC),
                order_type="MARKET",
            )
            for i in range(5)
        ]

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=entries,
        )

        assert ledger.total_entries == 5

    def test_total_buy_value_empty_ledger(self) -> None:
        """Test total_buy_value returns zero for empty ledger."""
        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
        )

        assert ledger.total_buy_value == Decimal("0")

    def test_total_buy_value_calculation(self) -> None:
        """Test total_buy_value calculates correctly."""
        entry1 = TradeLedgerEntry(
            order_id="order-1",
            correlation_id="corr-1",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),  # 10 * 150 = 1500
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        entry2 = TradeLedgerEntry(
            order_id="order-2",
            correlation_id="corr-2",
            symbol="TSLA",
            direction="BUY",
            filled_qty=Decimal("5"),
            fill_price=Decimal("200"),  # 5 * 200 = 1000
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        entry3 = TradeLedgerEntry(
            order_id="order-3",
            correlation_id="corr-3",
            symbol="NVDA",
            direction="SELL",  # Not a BUY
            filled_qty=Decimal("20"),
            fill_price=Decimal("500"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=[entry1, entry2, entry3],
        )

        # Should only sum BUY entries: 1500 + 1000 = 2500
        assert ledger.total_buy_value == Decimal("2500")

    def test_total_sell_value_empty_ledger(self) -> None:
        """Test total_sell_value returns zero for empty ledger."""
        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
        )

        assert ledger.total_sell_value == Decimal("0")

    def test_total_sell_value_calculation(self) -> None:
        """Test total_sell_value calculates correctly."""
        entry1 = TradeLedgerEntry(
            order_id="order-1",
            correlation_id="corr-1",
            symbol="AAPL",
            direction="SELL",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),  # 10 * 150 = 1500
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        entry2 = TradeLedgerEntry(
            order_id="order-2",
            correlation_id="corr-2",
            symbol="TSLA",
            direction="SELL",
            filled_qty=Decimal("5"),
            fill_price=Decimal("200"),  # 5 * 200 = 1000
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        entry3 = TradeLedgerEntry(
            order_id="order-3",
            correlation_id="corr-3",
            symbol="NVDA",
            direction="BUY",  # Not a SELL
            filled_qty=Decimal("20"),
            fill_price=Decimal("500"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=[entry1, entry2, entry3],
        )

        # Should only sum SELL entries: 1500 + 1000 = 2500
        assert ledger.total_sell_value == Decimal("2500")

    def test_decimal_precision_maintained(self) -> None:
        """Test Decimal precision is maintained in aggregations."""
        entry = TradeLedgerEntry(
            order_id="order-1",
            correlation_id="corr-1",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10.123456"),
            fill_price=Decimal("150.789012"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=[entry],
        )

        # Precise calculation: 10.123456 * 150.789012
        expected = Decimal("10.123456") * Decimal("150.789012")
        assert ledger.total_buy_value == expected

    def test_created_at_timezone_aware(self) -> None:
        """Test created_at timestamp is timezone-aware."""
        naive_timestamp = datetime(2024, 1, 1, 12, 0, 0)  # No timezone

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=naive_timestamp,
        )

        assert ledger.created_at.tzinfo is not None
        assert ledger.created_at.tzinfo == UTC

    def test_empty_ledger_id_rejected(self) -> None:
        """Test empty ledger_id is rejected."""
        with pytest.raises(ValidationError):
            TradeLedger(
                ledger_id="",  # Empty
                created_at=datetime.now(UTC),
            )

    def test_model_dump_serialization(self) -> None:
        """Test DTO can be serialized to dict."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=[entry],
        )

        data = ledger.model_dump()
        assert isinstance(data, dict)
        assert data["ledger_id"] == "ledger-123"
        assert len(data["entries"]) == 1

    def test_model_dump_json_serialization(self) -> None:
        """Test DTO can be serialized to JSON."""
        entry = TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-123",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        ledger = TradeLedger(
            ledger_id="ledger-123",
            created_at=datetime.now(UTC),
            entries=[entry],
        )

        json_str = ledger.model_dump_json()
        assert isinstance(json_str, str)
        assert "ledger-123" in json_str
        assert "order-123" in json_str
