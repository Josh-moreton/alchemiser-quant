"""Tests for tracking mapping functions."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tests.utils.float_checks import assert_close
from the_alchemiser.application.mapping.tracking import (
    dict_to_strategy_execution_summary_dto,
    dict_to_strategy_order_event_dto,
    strategy_execution_summary_dto_to_dict,
    strategy_order_event_dto_to_dict,
)
from the_alchemiser.interfaces.schemas.tracking import (
    ExecutionStatus,
    OrderEventStatus,
    StrategyExecutionSummaryDTO,
    StrategyOrderEventDTO,
)


class TestStrategyOrderEventDTOToDict:
    """Test conversion from StrategyOrderEventDTO to dictionary."""

    def test_basic_event_conversion(self) -> None:
        """Test converting basic order event DTO to dictionary."""
        timestamp = datetime.now(UTC)
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.25"),
            ts=timestamp,
            error=None,
        )

        result = strategy_order_event_dto_to_dict(event)

        expected = {
            "event_id": "evt_123",
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100.0,  # Converted to float
            "status": "filled",
            "price": 150.25,  # Converted to float
            "timestamp": timestamp.isoformat(),
            "error": None,
            "event_type": "order_event",
            "source": "strategy_tracking",
        }

        assert result == expected

    def test_event_with_error(self) -> None:
        """Test converting event with error to dictionary."""
        event = StrategyOrderEventDTO(
            event_id="evt_456",
            strategy="TECL",
            symbol="TSLA",
            side="sell",
            quantity=Decimal("50"),
            status=OrderEventStatus.REJECTED,
            price=None,
            ts=datetime.now(UTC),
            error="Insufficient funds",
        )

        result = strategy_order_event_dto_to_dict(event)

        assert result["error"] == "Insufficient funds"
        assert result["status"] == "rejected"
        assert result["price"] is None

    def test_decimal_to_float_conversion(self) -> None:
        """Test that Decimal values are properly converted to float."""
        event = StrategyOrderEventDTO(
            event_id="evt_789",
            strategy="KLM",
            symbol="SPY",
            side="buy",
            quantity=Decimal("100.500000"),  # High precision Decimal
            status=OrderEventStatus.FILLED,
            price=Decimal("400.1234"),  # High precision price
            ts=datetime.now(UTC),
        )

        result = strategy_order_event_dto_to_dict(event)

        assert_close(result["quantity"], 100.5)
        assert_close(result["price"], 400.1234)
        assert isinstance(result["quantity"], float)
        assert isinstance(result["price"], float)


class TestStrategyExecutionSummaryDTOToDict:
    """Test conversion from StrategyExecutionSummaryDTO to dictionary."""

    def test_summary_with_events(self) -> None:
        """Test converting summary with event details to dictionary."""
        timestamp1 = datetime.now(UTC)
        timestamp2 = datetime.now(UTC)

        event1 = StrategyOrderEventDTO(
            event_id="evt_1",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.00"),
            ts=timestamp1,
        )

        event2 = StrategyOrderEventDTO(
            event_id="evt_2",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            price=Decimal("151.00"),
            ts=timestamp2,
        )

        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("100"),
            avg_price=Decimal("150.50"),
            pnl=Decimal("50.00"),
            status=ExecutionStatus.OK,
            details=[event1, event2],
        )

        result = strategy_execution_summary_dto_to_dict(summary)

        assert result["strategy"] == "NUCLEAR"
        assert result["symbol"] == "AAPL"
        assert_close(result["total_quantity"], 100.0)
        assert_close(result["average_price"], 150.5)
        assert_close(result["pnl"], 50.0)
        assert result["status"] == "ok"
        assert result["event_count"] == 2
        assert len(result["event_details"]) == 2
        assert result["summary_type"] == "execution_summary"
        assert result["source"] == "strategy_tracking"

    def test_summary_with_null_values(self) -> None:
        """Test converting summary with null values to dictionary."""
        summary = StrategyExecutionSummaryDTO(
            strategy="TECL",
            symbol="QQQ",
            total_qty=Decimal("0"),
            avg_price=None,
            pnl=None,
            status=ExecutionStatus.FAILED,
            details=[],
        )

        result = strategy_execution_summary_dto_to_dict(summary)

        assert_close(result["total_quantity"], 0.0)
        assert result["average_price"] is None
        assert result["pnl"] is None
        assert result["status"] == "failed"
        assert result["event_count"] == 0
        assert result["event_details"] == []


class TestDictToStrategyOrderEventDTO:
    """Test conversion from dictionary to StrategyOrderEventDTO."""

    def test_basic_dict_conversion(self) -> None:
        """Test converting basic dictionary to order event DTO."""
        timestamp = datetime.now(UTC)
        data = {
            "event_id": "evt_123",
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "status": "filled",
            "price": 150.25,
            "ts": timestamp,
            "error": None,
        }

        event = dict_to_strategy_order_event_dto(data)

        assert event.event_id == "evt_123"
        assert event.strategy == "NUCLEAR"
        assert event.symbol == "AAPL"
        assert event.side == "buy"
        assert event.quantity == Decimal("100")
        assert event.status == "filled"
        assert event.price == Decimal("150.25")
        assert event.ts == timestamp
        assert event.error is None

    def test_string_timestamp_conversion(self) -> None:
        """Test converting dictionary with string timestamp."""
        data = {
            "event_id": "evt_456",
            "strategy": "TECL",
            "symbol": "QQQ",
            "side": "sell",
            "quantity": 50,
            "status": "filled",  # Use "filled" instead of "rejected" to avoid error requirement
            "ts": "2024-01-15T10:30:00+00:00",
        }

        event = dict_to_strategy_order_event_dto(data)

        assert isinstance(event.ts, datetime)
        assert event.ts.tzinfo is not None

    def test_missing_required_field_raises_error(self) -> None:
        """Test that missing required field raises ValueError."""
        data = {
            "event_id": "evt_789",
            "strategy": "KLM",
            # Missing symbol
            "side": "buy",
            "quantity": 100,
            "status": "submitted",
            "ts": datetime.now(UTC),
        }

        with pytest.raises(ValueError, match="Missing required field: symbol"):
            dict_to_strategy_order_event_dto(data)

    def test_decimal_conversion_from_various_types(self) -> None:
        """Test that quantities and prices are properly converted to Decimal."""
        data = {
            "event_id": "evt_test",
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "100.500",  # String quantity
            "status": "filled",
            "price": 150,  # Integer price
            "ts": datetime.now(UTC),
        }

        event = dict_to_strategy_order_event_dto(data)

        assert event.quantity == Decimal("100.500")
        assert event.price == Decimal("150")
        assert isinstance(event.quantity, Decimal)
        assert isinstance(event.price, Decimal)


class TestDictToStrategyExecutionSummaryDTO:
    """Test conversion from dictionary to StrategyExecutionSummaryDTO."""

    def test_summary_dict_conversion(self) -> None:
        """Test converting dictionary to execution summary DTO."""
        event_data = {
            "event_id": "evt_1",
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "status": "filled",
            "price": 150.00,
            "ts": datetime.now(UTC),
        }

        data = {
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "total_qty": "100.00",
            "avg_price": 150.50,
            "pnl": "25.00",
            "status": "ok",
            "event_details": [event_data],
        }

        summary = dict_to_strategy_execution_summary_dto(data)

        assert summary.strategy == "NUCLEAR"
        assert summary.symbol == "AAPL"
        assert summary.total_qty == Decimal("100.00")
        assert summary.avg_price == Decimal("150.50")
        assert summary.pnl == Decimal("25.00")
        assert summary.status == "ok"
        assert len(summary.details) == 1
        assert summary.details[0].event_id == "evt_1"

    def test_summary_without_events(self) -> None:
        """Test converting summary dictionary without event details."""
        data = {
            "strategy": "TECL",
            "symbol": "QQQ",
            "total_qty": 0,
            "avg_price": None,
            "pnl": None,
            "status": "failed",
        }

        summary = dict_to_strategy_execution_summary_dto(data)

        assert summary.strategy == "TECL"
        assert summary.symbol == "QQQ"
        assert summary.total_qty == Decimal("0")
        assert summary.avg_price is None
        assert summary.pnl is None
        assert summary.status == "failed"
        assert summary.details == []

    def test_missing_required_field_in_summary_raises_error(self) -> None:
        """Test that missing required field raises ValueError."""
        data = {
            "strategy": "KLM",
            # Missing symbol
            "total_qty": 100,
            "status": "ok",
        }

        with pytest.raises(ValueError, match="Missing required field: symbol"):
            dict_to_strategy_execution_summary_dto(data)


class TestMappingPurityAndTypes:
    """Test that mappings maintain purity and proper types."""

    def test_no_side_effects_in_event_mapping(self) -> None:
        """Test that event mapping functions don't modify input."""
        original_event = StrategyOrderEventDTO(
            event_id="evt_test",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.25"),
            ts=datetime.now(UTC),
        )

        # Store original values
        original_quantity = original_event.quantity
        original_price = original_event.price

        # Perform mapping
        strategy_order_event_dto_to_dict(original_event)

        # Verify original is unchanged
        assert original_event.quantity == original_quantity
        assert original_event.price == original_price

    def test_no_side_effects_in_summary_mapping(self) -> None:
        """Test that summary mapping functions don't modify input."""
        event = StrategyOrderEventDTO(
            event_id="evt_test",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.25"),
            ts=datetime.now(UTC),
        )

        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("100"),
            avg_price=Decimal("150.25"),
            pnl=Decimal("25.00"),
            status=ExecutionStatus.OK,
            details=[event],
        )

        # Store original values
        original_total_qty = summary.total_qty
        original_details_length = len(summary.details)

        # Perform mapping
        strategy_execution_summary_dto_to_dict(summary)

        # Verify original is unchanged
        assert summary.total_qty == original_total_qty
        assert len(summary.details) == original_details_length

    def test_decimal_preservation_in_roundtrip(self) -> None:
        """Test that Decimal precision is preserved in roundtrip conversions."""
        # Create event with high precision Decimal
        original_quantity = Decimal("100.123456")
        original_price = Decimal("150.654321")

        event_dict = {
            "event_id": "evt_precision_test",
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": str(original_quantity),  # Use string to preserve precision
            "status": "filled",
            "price": str(original_price),
            "ts": datetime.now(UTC),
        }

        # Convert to DTO and back
        event_dto = dict_to_strategy_order_event_dto(event_dict)
        result_dict = strategy_order_event_dto_to_dict(event_dto)

        # Verify DTO preserves Decimal precision
        assert event_dto.quantity == original_quantity
        assert event_dto.price == original_price

        # Note: The float conversion in _to_dict is intentional for JSON serialization
        assert isinstance(result_dict["quantity"], float)
        assert isinstance(result_dict["price"], float)
