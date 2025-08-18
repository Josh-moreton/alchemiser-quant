#!/usr/bin/env python3
"""
Unit tests for strategy tracking DTOs.

Tests comprehensive validation, field normalization, and business rules
for StrategyOrderEventDTO and StrategyExecutionSummaryDTO.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import ValidationError

from the_alchemiser.interfaces.schemas.tracking import (
    StrategyOrderEventDTO,
    StrategyExecutionSummaryDTO,
    OrderEventStatus,
    ExecutionStatus,
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
            ts=datetime.now(timezone.utc),
            error=None
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
            ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
            )
        
        # Check for Pydantic v2 error message format
        error_msg = str(exc_info.value)
        assert ("Input should be 'NUCLEAR', 'TECL' or 'KLM'" in error_msg or 
                "Strategy must be one of" in error_msg)
    
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc),
                error=None  # Missing required error
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
                ts=datetime.now(timezone.utc),
                error=None  # Missing required error
            )
        
        # Valid error with error status
        event = StrategyOrderEventDTO(
            event_id="evt_123",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.ERROR,
            ts=datetime.now(timezone.utc),
            error="Market closed"
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
            ts=datetime.now(timezone.utc),
            error="Informational warning"
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
            ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
                ts=datetime.now(timezone.utc)
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
            details=[]
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
            status=ExecutionStatus.OK
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
                status=ExecutionStatus.OK
            )
            assert summary.strategy == strategy
        
        # Invalid strategy
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="INVALID_STRATEGY",
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK
            )
        
        # Check for Pydantic v2 error message format
        error_msg = str(exc_info.value)
        assert ("Input should be 'NUCLEAR', 'TECL' or 'KLM'" in error_msg or 
                "Strategy must be one of" in error_msg)
    
    def test_total_qty_validation(self) -> None:
        """Test total quantity validation rules."""
        # Valid quantities including zero
        for qty in [Decimal("0"), Decimal("100"), Decimal("0.5")]:
            summary = StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=qty,
                status=ExecutionStatus.OK
            )
            assert summary.total_qty == qty
        
        # Invalid negative total quantity
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("-100"),
                status=ExecutionStatus.OK
            )
        
        # Check for Pydantic v2 error message format
        error_msg = str(exc_info.value)
        assert ("greater than or equal to 0" in error_msg or 
                "non-negative" in error_msg)
    
    def test_event_ordering_validation(self) -> None:
        """Test that events must be ordered by timestamp."""
        ts1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        ts3 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        event1 = StrategyOrderEventDTO(
            event_id="evt_1",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts1
        )
        
        event2 = StrategyOrderEventDTO(
            event_id="evt_2",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts2
        )
        
        event3 = StrategyOrderEventDTO(
            event_id="evt_3",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("25"),
            status=OrderEventStatus.FILLED,
            ts=ts3
        )
        
        # Valid: events in chronological order
        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("75"),
            status=ExecutionStatus.OK,
            details=[event1, event2, event3]
        )
        assert len(summary.details) == 3
        
        # Invalid: events out of order
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("75"),
                status=ExecutionStatus.OK,
                details=[event2, event1, event3]  # Out of order
            )
        
        assert "must be sorted by timestamp" in str(exc_info.value)
    
    def test_event_consistency_validation(self) -> None:
        """Test that all events must belong to the same strategy and symbol."""
        ts = datetime.now(timezone.utc)
        
        nuclear_event = StrategyOrderEventDTO(
            event_id="evt_1",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts
        )
        
        tecl_event = StrategyOrderEventDTO(
            event_id="evt_2",
            strategy="TECL",  # Different strategy
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts
        )
        
        msft_event = StrategyOrderEventDTO(
            event_id="evt_3",
            strategy="NUCLEAR",
            symbol="MSFT",  # Different symbol
            side="buy",
            quantity=Decimal("50"),
            status=OrderEventStatus.FILLED,
            ts=ts
        )
        
        # Invalid: different strategies
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK,
                details=[nuclear_event, tecl_event]
            )
        
        assert "doesn't match summary strategy" in str(exc_info.value)
        
        # Invalid: different symbols
        with pytest.raises(ValidationError) as exc_info:
            StrategyExecutionSummaryDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                total_qty=Decimal("100"),
                status=ExecutionStatus.OK,
                details=[nuclear_event, msft_event]
            )
        
        assert "doesn't match summary symbol" in str(exc_info.value)
    
    def test_immutability(self) -> None:
        """Test that DTOs are immutable."""
        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("100"),
            status=ExecutionStatus.OK
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
            details=[]
        )
        
        assert summary.avg_price is None
        assert summary.pnl is None
        assert summary.details == []
    
    def test_complex_scenario(self) -> None:
        """Test a complex scenario with multiple events."""
        ts1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        ts3 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        buy_event = StrategyOrderEventDTO(
            event_id="evt_buy",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            status=OrderEventStatus.FILLED,
            price=Decimal("150.00"),
            ts=ts1
        )
        
        partial_sell_event = StrategyOrderEventDTO(
            event_id="evt_sell_partial",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("30"),
            status=OrderEventStatus.FILLED,
            price=Decimal("155.00"),
            ts=ts2
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
            error="Insufficient shares"
        )
        
        summary = StrategyExecutionSummaryDTO(
            strategy="NUCLEAR",
            symbol="AAPL",
            total_qty=Decimal("70"),  # 100 - 30 = 70 remaining
            avg_price=Decimal("151.50"),
            pnl=Decimal("150.00"),  # 30 * (155 - 150)
            status=ExecutionStatus.PARTIAL,
            details=[buy_event, partial_sell_event, failed_sell_event]
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