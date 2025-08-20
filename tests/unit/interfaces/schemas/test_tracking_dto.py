#!/usr/bin/env python3
"""
Unit tests for strategy tracking DTOs.

Tests comprehensive validation, field normalization, and business rules
for StrategyOrderEventDTO and StrategyExecutionSummaryDTO.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.interfaces.schemas.tracking import (
    ExecutionStatus,
    OrderEventStatus,
    StrategyExecutionSummaryDTO,
    StrategyOrderDTO,
    StrategyOrderEventDTO,
    StrategyPnLDTO,
    StrategyPositionDTO,
)


class TestStrategyOrderEventDTO:
    """Test StrategyOrderEventDTO validation and behavior."""

    def test_valid_order_event_creation(self) -> None:
        """Test creating valid order events."""
        # Test basic valid event
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.25"),
            ts=datetime.now(UTC),
            error=None,
        )

        assert event.event_id == "evt_123"
        assert event.strategy == "NUCLEAR"
        assert event.symbol == "AAPL"
        assert event.side == "buy"
        assert event.quantity == Decimal("100")
        assert event.status == OrderEventStatus.FILLED
        assert event.price == Decimal("150.25")
        assert event.error is None

    def test_symbol_normalization(self) -> None:
        """Test symbol is normalized to uppercase."""
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="TECL",
            symbol="  aapl  ",  # Mixed case with whitespace
            side="sell",
            quantity=Decimal("50"),
            status=OrderEventStatus.SUBMITTED,
            price=None,
            ts=datetime.now(UTC),
        )

        assert event.symbol == "AAPL"

    def test_strategy_validation(self) -> None:
        """Test strategy validation against registered strategies."""
        # Valid strategies
        for strategy in ["NUCLEAR", "TECL", "KLM"]:
            event = StrategyOrderEventDTO(
                event_id="evt_123",
                strategy=strategy,
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )
            assert event.strategy == strategy

        # Invalid strategy
        with pytest.raises(ValidationError) as exc_info:
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="INVALID_STRATEGY",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )

        # Check for Pydantic v2 error message format
        error_msg = str(exc_info.value)
        assert (
            "Input should be 'NUCLEAR', 'TECL' or 'KLM'" in error_msg
            or "Strategy must be one of" in error_msg
        )

    def test_quantity_validation(self) -> None:
        """Test quantity validation rules."""
        # Valid positive quantities
        for qty in [Decimal("1"), Decimal("100.5"), Decimal("0.000001")]:
            event = StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=qty,
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )
            assert event.quantity == qty

        # Invalid negative quantity
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("-100"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )

        # Invalid zero quantity
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("0"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )

        # Invalid precision (too many decimal places)
        with pytest.raises(ValidationError) as exc_info:
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100.1234567"),  # 7 decimal places
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )

        assert "precision too high" in str(exc_info.value)

    def test_price_validation(self) -> None:
        """Test price validation rules."""
        # Valid prices
        for price in [None, Decimal("0"), Decimal("150.25"), Decimal("1000000")]:
            event = StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                price=price,
                ts=datetime.now(UTC),
            )
            assert event.price == price

        # Invalid negative price
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                price=Decimal("-150.25"),
                ts=datetime.now(UTC),
            )

    def test_error_status_consistency(self) -> None:
        """Test error message validation based on status."""
        # Error status requires error message
        with pytest.raises(ValidationError) as exc_info:
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.ERROR,
                ts=datetime.now(UTC),
                error=None,  # Missing required error
            )

        assert "Error message required" in str(exc_info.value)

        # Rejected status requires error message
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.REJECTED,
                ts=datetime.now(UTC),
                error=None,  # Missing required error
            )

        # Valid error with error status
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.ERROR,
            ts=datetime.now(UTC),
            error="Market closed",
        )
        assert event.error == "Market closed"

        # Error message allowed even on success (for informational purposes)
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            ts=datetime.now(UTC),
            error="Informational warning",
        )
        assert event.error == "Informational warning"

    def test_immutability(self) -> None:
        """Test that DTOs are immutable."""
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            ts=datetime.now(UTC),
        )

        # Should not be able to modify fields
        with pytest.raises(ValidationError):
            event.strategy = "TECL"

    def test_symbol_validation_edge_cases(self) -> None:
        """Test symbol validation edge cases."""
        # Empty symbol
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )

        # Symbol too long
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="VERYLONGSYMBOL",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )

        # Symbol with numbers (invalid)
        with pytest.raises(ValidationError):
            StrategyOrderEventDTO(
                event_id="evt_123",
                strategy="NUCLEAR",
                symbol="AAPL123",
                side="buy",
                quantity=Decimal("100"),
                status=OrderEventStatus.FILLED,
                ts=datetime.now(UTC),
            )


class TestStrategyExecutionSummaryDTO:
    """Test StrategyExecutionSummaryDTO validation and behavior."""

    def test_valid_execution_summary_creation(self) -> None:
        """Test creating valid execution summaries."""
        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("100"),
            avg_price=Decimal("150.25"),
            pnl=Decimal("250.50"),
            status=ExecutionStatus.OK,
            details=[],
        )

        assert summary.strategy == "NUCLEAR"
        assert summary.symbol == "AAPL"
        assert summary.total_qty == Decimal("100")
        assert summary.avg_price == Decimal("150.25")
        assert summary.pnl == Decimal("250.50")
        assert summary.status == ExecutionStatus.OK
        assert summary.details == []

    def test_symbol_normalization(self) -> None:
        """Test symbol is normalized to uppercase."""
        summary = StrategyExecutionSummaryDTO(
            strategy="TECL",
            symbol="  msft  ",  # Mixed case with whitespace
            total_qty=Decimal("50"),
            status=ExecutionStatus.OK,
        )

        assert summary.symbol == "MSFT"

    def test_strategy_validation(self) -> None:
        """Test strategy validation against registered strategies."""
        # Valid strategies
        for strategy in ["NUCLEAR", "TECL", "KLM"]:
            summary = StrategyExecutionSummaryDTO(
                strategy=strategy,
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK,
            )
            assert summary.strategy == strategy

        # Invalid strategy
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="INVALID_STRATEGY",
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK,
            )

        # Check for Pydantic v2 error message format
        error_msg = str(exc_info.value)
        assert (
            "Input should be 'NUCLEAR', 'TECL' or 'KLM'" in error_msg
            or "Strategy must be one of" in error_msg
        )

    def test_total_qty_validation(self) -> None:
        """Test total quantity validation rules."""
        # Valid quantities including zero
        for qty in [Decimal("0"), Decimal("100"), Decimal("0.5")]:
            summary = StrategyExecutionSummaryDTO(
                strategy="NUCLEAR", symbol="AAPL", total_qty=qty, status=ExecutionStatus.OK
            )
            assert summary.total_qty == qty

        # Invalid negative total quantity
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("-100"),
                status=ExecutionStatus.OK,
            )

        # Check for Pydantic v2 error message format
        error_msg = str(exc_info.value)
        assert "greater than or equal to 0" in error_msg or "non-negative" in error_msg

    def test_event_ordering_validation(self) -> None:
        """Test that events must be ordered by timestamp."""
        ts1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        ts2 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)
        ts3 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        event1 = StrategyOrderEventDTO(
            event_id="evt_1",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts1,
        )

        event2 = StrategyOrderEventDTO(
            event_id="evt_2",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts2,
        )

        event3 = StrategyOrderEventDTO(
            event_id="evt_3",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("25"),
            status=OrderEventStatus.FILLED,
            ts=ts3,
        )

        # Valid: events in chronological order
        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("75"),
            status=ExecutionStatus.OK,
            details=[event1, event2, event3],
        )
        assert len(summary.details) == 3

        # Invalid: events out of order
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("75"),
                status=ExecutionStatus.OK,
                details=[event2, event1, event3],  # Out of order
            )

        assert "must be sorted by timestamp" in str(exc_info.value)

    def test_event_consistency_validation(self) -> None:
        """Test that all events must belong to the same strategy and symbol."""
        ts = datetime.now(UTC)

        nuclear_event = StrategyOrderEventDTO(
            event_id="evt_1",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts,
        )

        tecl_event = StrategyOrderEventDTO(
            event_id="evt_2",
            strategy="TECL",  # Different strategy
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts,
        )

        msft_event = StrategyOrderEventDTO(
            event_id="evt_3",
            strategy="NUCLEAR",
            symbol="MSFT",  # Different symbol
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts,
        )

        # Invalid: different strategies
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK,
                details=[nuclear_event, tecl_event],
            )

        assert "doesn't match summary strategy" in str(exc_info.value)

        # Invalid: different symbols
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK,
                details=[nuclear_event, msft_event],
            )

        assert "doesn't match summary symbol" in str(exc_info.value)

    def test_immutability(self) -> None:
        """Test that DTOs are immutable."""
        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR", symbol="AAPL", total_qty=Decimal("100"), status=ExecutionStatus.OK
        )

        # Should not be able to modify fields
        with pytest.raises(ValidationError):
            summary.strategy = "TECL"

    def test_optional_fields(self) -> None:
        """Test handling of optional fields."""
        # All optional fields as None
        summary = StrategyExecutionSummaryDTO(
            strategy="KLM",
            symbol="GOOGL",
            total_qty=Decimal("0"),
            avg_price=None,
            pnl=None,
            status=ExecutionStatus.FAILED,
            details=[],
        )

        assert summary.avg_price is None
        assert summary.pnl is None
        assert summary.details == []

    def test_complex_scenario(self) -> None:
        """Test a complex scenario with multiple events."""
        ts1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        ts2 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)
        ts3 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        buy_event = StrategyOrderEventDTO(
            event_id="evt_buy",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.00"),
            ts=ts1,
        )

        partial_sell_event = StrategyOrderEventDTO(
            event_id="evt_sell_partial",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("30"),
            status=OrderEventStatus.FILLED,
            price=Decimal("155.00"),
            ts=ts2,
        )

        failed_sell_event = StrategyOrderEventDTO(
            event_id="evt_sell_failed",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("20"),
            status=OrderEventStatus.REJECTED,
            price=None,
            ts=ts3,
            error="Insufficient shares",
        )

        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("70"),  # 100 - 30 = 70 remaining
            avg_price=Decimal("151.50"),
            pnl=Decimal("150.00"),  # 30 * (155 - 150)
            status=ExecutionStatus.PARTIAL,
            details=[buy_event, partial_sell_event, failed_sell_event],
        )

        assert summary.total_qty == Decimal("70")
        assert summary.avg_price == Decimal("151.50")
        assert summary.pnl == Decimal("150.00")
        assert summary.status == ExecutionStatus.PARTIAL
        assert len(summary.details) == 3

        # Verify all events are properly ordered and consistent
        assert summary.details[0].event_id == "evt_buy"
        assert summary.details[1].event_id == "evt_sell_partial"
        assert summary.details[2].event_id == "evt_sell_failed"


class TestStrategyOrderDTO:
    """Test StrategyOrderDTO validation and behavior."""

    def test_valid_order_creation(self) -> None:
        """Test creating valid strategy orders."""
        order = StrategyOrderDTO(
            order_id="order_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.25"),
            timestamp=datetime.now(UTC),
        )

        assert order.order_id == "order_123"
        assert order.strategy == "NUCLEAR"
        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.quantity == Decimal("100")
        assert order.price == Decimal("150.25")

    def test_factory_method(self) -> None:
        """Test factory method for creating from raw data."""
        order = StrategyOrderDTO.from_strategy_order_data(
            order_id="order_123",
            strategy="NUCLEAR",
            symbol="aapl",  # Should be normalized
            side="BUY",  # Should be normalized
            quantity=100.5,
            price=150.25,
        )

        assert order.order_id == "order_123"
        assert order.strategy == "NUCLEAR"
        assert order.symbol == "AAPL"  # Normalized to uppercase
        assert order.side == "buy"  # Normalized to lowercase
        assert order.quantity == Decimal("100.5")
        assert order.price == Decimal("150.25")

    def test_side_normalization(self) -> None:
        """Test side is normalized to lowercase."""
        order = StrategyOrderDTO(
            order_id="order_123",
            strategy="TECL",
            symbol="AAPL",
            side="SELL",  # Uppercase input
            quantity=Decimal("50"),
            price=Decimal("150.00"),
            timestamp=datetime.now(UTC),
        )

        assert order.side == "sell"

    def test_validation_errors(self) -> None:
        """Test validation errors for invalid data."""
        # Invalid strategy
        with pytest.raises(ValidationError):
            StrategyOrderDTO(
                order_id="order_123",
                strategy="INVALID",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                price=Decimal("150.25"),
                timestamp=datetime.now(UTC),
            )

        # Invalid side
        with pytest.raises(ValidationError):
            StrategyOrderDTO(
                order_id="order_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="invalid_side",
                quantity=Decimal("100"),
                price=Decimal("150.25"),
                timestamp=datetime.now(UTC),
            )

        # Zero quantity
        with pytest.raises(ValidationError):
            StrategyOrderDTO(
                order_id="order_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("0"),
                price=Decimal("150.25"),
                timestamp=datetime.now(UTC),
            )

        # Negative price
        with pytest.raises(ValidationError):
            StrategyOrderDTO(
                order_id="order_123",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                price=Decimal("-150.25"),
                timestamp=datetime.now(UTC),
            )


class TestStrategyPositionDTO:
    """Test StrategyPositionDTO validation and behavior."""

    def test_valid_position_creation(self) -> None:
        """Test creating valid strategy positions."""
        position = StrategyPositionDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            quantity=Decimal("100"),
            average_cost=Decimal("150.00"),
            total_cost=Decimal("15000.00"),
            last_updated=datetime.now(UTC),
        )

        assert position.strategy == "NUCLEAR"
        assert position.symbol == "AAPL"
        assert position.quantity == Decimal("100")
        assert position.average_cost == Decimal("150.00")
        assert position.total_cost == Decimal("15000.00")

    def test_factory_method(self) -> None:
        """Test factory method for creating from raw data."""
        position = StrategyPositionDTO.from_position_data(
            strategy="NUCLEAR",
            symbol="aapl",  # Should be normalized
            quantity=100.0,
            average_cost=150.0,
            total_cost=15000.0,
        )

        assert position.strategy == "NUCLEAR"
        assert position.symbol == "AAPL"  # Normalized to uppercase
        assert position.quantity == Decimal("100.0")
        assert position.average_cost == Decimal("150.0")
        assert position.total_cost == Decimal("15000.0")

    def test_closed_position_validation(self) -> None:
        """Test validation for closed positions."""
        # Valid closed position
        position = StrategyPositionDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            quantity=Decimal("0"),
            average_cost=Decimal("0"),
            total_cost=Decimal("0"),
            last_updated=datetime.now(UTC),
        )

        assert position.quantity == Decimal("0")

        # Invalid closed position with non-zero costs
        with pytest.raises(ValidationError) as exc_info:
            StrategyPositionDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                quantity=Decimal("0"),
                average_cost=Decimal("150.00"),  # Should be 0 for closed position
                total_cost=Decimal("0"),
                last_updated=datetime.now(UTC),
            )

        assert "Closed position" in str(exc_info.value)

    def test_open_position_validation(self) -> None:
        """Test validation for open positions."""
        # Valid open position
        position = StrategyPositionDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            quantity=Decimal("100"),
            average_cost=Decimal("150.00"),
            total_cost=Decimal("15000.00"),
            last_updated=datetime.now(UTC),
        )

        assert position.quantity == Decimal("100")

        # Invalid open position with zero average cost
        with pytest.raises(ValidationError) as exc_info:
            StrategyPositionDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                quantity=Decimal("100"),
                average_cost=Decimal("0"),  # Should be positive for open position
                total_cost=Decimal("15000.00"),
                last_updated=datetime.now(UTC),
            )

        assert "positive average cost" in str(exc_info.value)

    def test_cost_consistency_validation(self) -> None:
        """Test validation for cost consistency."""
        # Valid consistent costs
        position = StrategyPositionDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            quantity=Decimal("100"),
            average_cost=Decimal("150.00"),
            total_cost=Decimal("15000.00"),  # 100 * 150
            last_updated=datetime.now(UTC),
        )

        assert position.total_cost == Decimal("15000.00")

        # Invalid inconsistent costs (difference > 0.01)
        with pytest.raises(ValidationError) as exc_info:
            StrategyPositionDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                quantity=Decimal("100"),
                average_cost=Decimal("150.00"),
                total_cost=Decimal("14000.00"),  # Should be 15000
                last_updated=datetime.now(UTC),
            )

        assert "inconsistent" in str(exc_info.value)


class TestStrategyPnLDTO:
    """Test StrategyPnLDTO validation and behavior."""

    def test_valid_pnl_creation(self) -> None:
        """Test creating valid strategy P&L."""
        pnl = StrategyPnLDTO(
            strategy="NUCLEAR",
            realized_pnl=Decimal("250.50"),
            unrealized_pnl=Decimal("100.25"),
            total_pnl=Decimal("350.75"),
            positions={"AAPL": Decimal("100"), "GOOGL": Decimal("50")},
            allocation_value=Decimal("25000.00"),
        )

        assert pnl.strategy == "NUCLEAR"
        assert pnl.realized_pnl == Decimal("250.50")
        assert pnl.unrealized_pnl == Decimal("100.25")
        assert pnl.total_pnl == Decimal("350.75")
        assert pnl.allocation_value == Decimal("25000.00")

    def test_factory_method(self) -> None:
        """Test factory method for creating from raw data."""
        pnl = StrategyPnLDTO.from_pnl_data(
            strategy="NUCLEAR",
            realized_pnl=250.50,
            unrealized_pnl=100.25,
            total_pnl=350.75,
            positions={"aapl": 100.0, "googl": 50.0},  # Should normalize symbols
            allocation_value=25000.0,
        )

        assert pnl.strategy == "NUCLEAR"
        assert pnl.total_pnl == Decimal("350.75")
        assert "AAPL" in pnl.positions  # Normalized to uppercase
        assert "GOOGL" in pnl.positions

    def test_computed_properties(self) -> None:
        """Test computed properties."""
        pnl = StrategyPnLDTO(
            strategy="NUCLEAR",
            realized_pnl=Decimal("250.50"),
            unrealized_pnl=Decimal("100.25"),
            total_pnl=Decimal("350.75"),
            positions={"AAPL": Decimal("100"), "GOOGL": Decimal("0")},  # One zero position
            allocation_value=Decimal("25000.00"),
        )

        # Total return percentage
        expected_return_pct = (Decimal("350.75") / Decimal("25000.00")) * Decimal("100")
        assert pnl.total_return_pct == expected_return_pct

        # Position count (non-zero positions only)
        assert pnl.position_count == 1  # Only AAPL has non-zero quantity

    def test_pnl_consistency_validation(self) -> None:
        """Test validation for P&L consistency."""
        # Valid consistent P&L
        pnl = StrategyPnLDTO(
            strategy="NUCLEAR",
            realized_pnl=Decimal("250.50"),
            unrealized_pnl=Decimal("100.25"),
            total_pnl=Decimal("350.75"),  # 250.50 + 100.25
            positions={},
            allocation_value=Decimal("25000.00"),
        )

        assert pnl.total_pnl == Decimal("350.75")

        # Invalid inconsistent P&L (difference > 0.01)
        with pytest.raises(ValidationError) as exc_info:
            StrategyPnLDTO(
                strategy="NUCLEAR",
                realized_pnl=Decimal("250.50"),
                unrealized_pnl=Decimal("100.25"),
                total_pnl=Decimal("300.00"),  # Should be 350.75
                positions={},
                allocation_value=Decimal("25000.00"),
            )

        assert "inconsistent" in str(exc_info.value)

    def test_positions_validation(self) -> None:
        """Test positions validation and normalization."""
        # Valid positions with normalization
        pnl = StrategyPnLDTO(
            strategy="NUCLEAR",
            realized_pnl=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            total_pnl=Decimal("0"),
            positions={"  aapl  ": Decimal("100")},  # Should normalize symbol
            allocation_value=Decimal("25000.00"),
        )

        assert "AAPL" in pnl.positions
        assert "  aapl  " not in pnl.positions

        # Invalid symbol format
        with pytest.raises(ValidationError):
            StrategyPnLDTO(
                strategy="NUCLEAR",
                realized_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                total_pnl=Decimal("0"),
                positions={"AAPL123": Decimal("100")},  # Invalid symbol
                allocation_value=Decimal("25000.00"),
            )

        # Invalid negative quantity
        with pytest.raises(ValidationError):
            StrategyPnLDTO(
                strategy="NUCLEAR",
                realized_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                total_pnl=Decimal("0"),
                positions={"AAPL": Decimal("-100")},  # Negative quantity
                allocation_value=Decimal("25000.00"),
            )
