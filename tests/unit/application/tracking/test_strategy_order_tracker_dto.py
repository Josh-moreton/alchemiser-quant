#!/usr/bin/env python3
"""
Unit tests for StrategyOrderTracker DTO integration.

Tests the new DTO-based methods added for Pydantic v2 migration:
- add_order() accepting StrategyOrderDTO  
- get_orders_for_strategy() returning List[StrategyOrderDTO]
- get_positions_summary() returning List[StrategyPositionDTO]
- get_pnl_summary() returning StrategyPnLDTO
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from the_alchemiser.application.tracking.strategy_order_tracker import (
    StrategyOrder,
    StrategyOrderTracker,
    StrategyPnL,
    StrategyPosition,
)
from the_alchemiser.interfaces.schemas.tracking import (
    StrategyOrderDTO,
    StrategyPnLDTO,
    StrategyPositionDTO,
)


class TestStrategyOrderTrackerDTO:
    """Test DTO integration in StrategyOrderTracker."""

    def setup_method(self):
        """Set up test fixture."""
        with patch('the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler'):
            with patch('the_alchemiser.application.tracking.strategy_order_tracker.load_settings'):
                self.tracker = StrategyOrderTracker()
                # Clear any S3 loading errors
                self.tracker._orders_cache = []
                self.tracker._positions_cache = {}
                self.tracker._realized_pnl_cache = {}

    def test_add_order_with_dto(self):
        """Test adding order using StrategyOrderDTO."""
        # Create test DTO
        order_dto = StrategyOrderDTO(
            order_id="test_001",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.25"),
            timestamp=datetime.now(UTC)
        )

        # Mock the persistence method to avoid S3 calls
        with patch.object(self.tracker, '_persist_order'):
            # Add order via DTO
            self.tracker.add_order(order_dto)

        # Verify order was added to cache
        assert len(self.tracker._orders_cache) == 1
        cached_order = self.tracker._orders_cache[0]
        assert cached_order.order_id == "test_001"
        assert cached_order.strategy == "NUCLEAR"
        assert cached_order.symbol == "AAPL"
        assert cached_order.side == "BUY"  # Should be uppercase in dataclass
        assert cached_order.quantity == 100.0  # Should be float in dataclass
        assert cached_order.price == 150.25

    def test_get_orders_for_strategy(self):
        """Test retrieving orders for a strategy as DTOs."""
        # Add some test orders to cache
        order1 = StrategyOrder(
            order_id="test_001",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="BUY",
            quantity=100.0,
            price=150.25,
            timestamp=datetime.now(UTC).isoformat()
        )
        order2 = StrategyOrder(
            order_id="test_002",
            strategy="TECL",
            symbol="MSFT",
            side="SELL",
            quantity=50.0,
            price=300.50,
            timestamp=datetime.now(UTC).isoformat()
        )
        self.tracker._orders_cache = [order1, order2]

        # Get orders for NUCLEAR strategy
        nuclear_orders = self.tracker.get_orders_for_strategy("NUCLEAR")

        # Verify results
        assert len(nuclear_orders) == 1
        assert isinstance(nuclear_orders[0], StrategyOrderDTO)
        assert nuclear_orders[0].order_id == "test_001"
        assert nuclear_orders[0].strategy == "NUCLEAR"
        assert nuclear_orders[0].side == "buy"  # Should be lowercase in DTO
        assert nuclear_orders[0].quantity == Decimal("100")  # Should be Decimal in DTO

    def test_get_positions_summary(self):
        """Test retrieving positions summary as DTOs."""
        # Add test positions to cache
        position1 = StrategyPosition(
            strategy="NUCLEAR",
            symbol="AAPL",
            quantity=100.0,
            average_cost=150.25,
            total_cost=15025.0,
            last_updated=datetime.now(UTC).isoformat()
        )
        position2 = StrategyPosition(
            strategy="TECL",
            symbol="MSFT",
            quantity=0.0,  # Closed position - should be filtered out
            average_cost=0.0,
            total_cost=0.0,
            last_updated=datetime.now(UTC).isoformat()
        )
        self.tracker._positions_cache = {
            ("NUCLEAR", "AAPL"): position1,
            ("TECL", "MSFT"): position2,
        }

        # Get positions summary
        positions = self.tracker.get_positions_summary()

        # Verify results (only active positions)
        assert len(positions) == 1
        assert isinstance(positions[0], StrategyPositionDTO)
        assert positions[0].strategy == "NUCLEAR"
        assert positions[0].symbol == "AAPL"
        assert positions[0].quantity == Decimal("100")
        assert positions[0].average_cost == Decimal("150.25")

    def test_get_pnl_summary(self):
        """Test retrieving P&L summary as DTO."""
        # Mock the get_strategy_pnl method to return test data
        test_pnl = StrategyPnL(
            strategy="NUCLEAR",
            realized_pnl=250.0,
            unrealized_pnl=150.0,
            total_pnl=400.0,
            positions={"AAPL": 100.0},
            allocation_value=15000.0
        )

        with patch.object(self.tracker, 'get_strategy_pnl', return_value=test_pnl):
            # Get P&L summary
            pnl_dto = self.tracker.get_pnl_summary("NUCLEAR")

        # Verify results
        assert isinstance(pnl_dto, StrategyPnLDTO)
        assert pnl_dto.strategy == "NUCLEAR"
        assert pnl_dto.realized_pnl == Decimal("250")
        assert pnl_dto.unrealized_pnl == Decimal("150")
        assert pnl_dto.total_pnl == Decimal("400")
        assert pnl_dto.positions["AAPL"] == Decimal("100")
        assert pnl_dto.allocation_value == Decimal("15000")

    def test_dto_to_storage_conversion(self):
        """Test DTO to storage format conversion."""
        order_dto = StrategyOrderDTO(
            order_id="test_001",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.25"),
            timestamp=datetime.now(UTC)
        )

        # Convert to storage format
        storage_data = self.tracker._dto_to_storage(order_dto)

        # Verify format
        assert isinstance(storage_data, dict)
        assert storage_data["order_id"] == "test_001"
        assert storage_data["strategy"] == "NUCLEAR"
        assert storage_data["side"] == "buy"
        # Decimal should be serialized as string in JSON mode
        assert isinstance(storage_data["quantity"], (str, int, float))
        assert isinstance(storage_data["price"], (str, int, float))

    def test_storage_to_dto_conversion(self):
        """Test storage format to DTO conversion."""
        storage_data = {
            "order_id": "test_001",
            "strategy": "NUCLEAR",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "100",
            "price": "150.25",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Convert from storage format
        order_dto = self.tracker._storage_to_dto(storage_data)

        # Verify DTO
        assert isinstance(order_dto, StrategyOrderDTO)
        assert order_dto.order_id == "test_001"
        assert order_dto.strategy == "NUCLEAR"
        assert order_dto.quantity == Decimal("100")
        assert order_dto.price == Decimal("150.25")

    def test_add_order_error_handling(self):
        """Test error handling in add_order method."""
        # Create invalid DTO (will be caught during conversion)
        order_dto = StrategyOrderDTO(
            order_id="test_001",
            strategy="NUCLEAR",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.25"),
            timestamp=datetime.now(UTC)
        )

        # Mock process_order to raise an exception
        with patch.object(self.tracker, '_process_order', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                self.tracker.add_order(order_dto)

    def test_get_pnl_summary_unknown_strategy(self):
        """Test P&L summary with unknown strategy."""
        # Get P&L for non-existent strategy
        pnl_dto = self.tracker.get_pnl_summary("UNKNOWN_STRATEGY")

        # Should return zero P&L DTO with default strategy
        assert isinstance(pnl_dto, StrategyPnLDTO)
        assert pnl_dto.strategy == "NUCLEAR"  # Should use default valid strategy
        assert pnl_dto.realized_pnl == Decimal("0")
        assert pnl_dto.unrealized_pnl == Decimal("0")
        assert pnl_dto.total_pnl == Decimal("0")
        assert pnl_dto.allocation_value == Decimal("0")
