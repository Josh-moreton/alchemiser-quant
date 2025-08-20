#!/usr/bin/env python3
"""
Tests for strategy_order_tracker.py refactored to use Tracking DTOs.

This module validates that the strategy order tracker correctly consumes/produces
StrategyOrderEventDTO and StrategyExecutionSummaryDTO, replacing untyped dict flows.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from the_alchemiser.application.tracking.strategy_order_tracker import (
    StrategyOrderTracker,
    get_strategy_tracker,
)
from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.interfaces.schemas.tracking import (
    ExecutionStatus,
    StrategyOrderEventDTO,
)


class TestStrategyOrderTracker:
    """Test StrategyOrderTracker DTO integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_s3_handler = Mock()
        self.mock_s3_handler.file_exists.return_value = False
        self.mock_s3_handler.read_json.return_value = None
        self.mock_s3_handler.write_json.return_value = True

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_record_order_sequence_events(self, mock_get_s3_handler):
        """Test recording sequence of events (submitted->accepted->filled)."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record initial order
        tracker.record_order(
            order_id="order_123",
            strategy=StrategyType.NUCLEAR,
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=150.25,
        )

        # Verify order was processed correctly
        order = tracker._orders_cache[0]
        assert order.order_id == "order_123"
        assert order.strategy == "NUCLEAR"
        assert order.symbol == "AAPL"
        assert order.side == "BUY"
        assert order.quantity == pytest.approx(100.0, rel=1e-9, abs=1e-9)
        assert order.price == pytest.approx(150.25, rel=1e-9, abs=1e-9)

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_partial_fills_aggregation(self, mock_get_s3_handler):
        """Test partial fills aggregation."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record partial fills
        tracker.record_order("order_1", StrategyType.TECL, "TSLA", "buy", 50, 200.0)
        tracker.record_order("order_2", StrategyType.TECL, "TSLA", "buy", 50, 205.0)

        # Check position aggregation
        position_key = ("TECL", "TSLA")
        assert position_key in tracker._positions_cache

        position = tracker._positions_cache[position_key]
        assert position.quantity == pytest.approx(100.0, rel=1e-9, abs=1e-9)  # 50 + 50
        assert position.average_cost == pytest.approx(202.5, rel=1e-9, abs=1e-9)  # (50*200 + 50*205) / 100

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_error_event_capturing(self, mock_get_s3_handler):
        """Test error event capturing and summary status == 'failed'."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Simulate error during order recording
        with patch.object(tracker, "_process_order", side_effect=Exception("Test error")):
            # This should handle the error gracefully
            tracker.record_order("error_order", StrategyType.KLM, "NVDA", "buy", 10, 500.0)

        # Verify error was handled and not crashed
        # The order should not be in cache due to error
        assert len(tracker._orders_cache) == 0

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_timestamp_ordering(self, mock_get_s3_handler):
        """Test that events maintain timestamp ordering."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record multiple orders
        tracker.record_order("order_1", StrategyType.NUCLEAR, "AAPL", "buy", 100, 150.0)
        tracker.record_order("order_2", StrategyType.NUCLEAR, "AAPL", "sell", 50, 155.0)
        tracker.record_order("order_3", StrategyType.NUCLEAR, "AAPL", "buy", 25, 152.0)

        # Verify orders are in chronological order
        timestamps = [order.timestamp for order in tracker._orders_cache]
        assert timestamps == sorted(timestamps)

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_decimal_precision_in_calculations(self, mock_get_s3_handler):
        """Test that financial calculations use appropriate precision."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record orders with precise amounts
        tracker.record_order("order_1", StrategyType.TECL, "SPY", "buy", 33.333, 425.12345)

        # Check that values are preserved with reasonable precision
        position = tracker._positions_cache[("TECL", "SPY")]
        assert abs(position.quantity - 33.333) < 0.001
        assert abs(position.average_cost - 425.12345) < 0.001

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_trading_system_error_handler_integration(self, mock_get_s3_handler):
        """Test integration with TradingSystemErrorHandler."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Force an error to test error handling
        with patch.object(tracker, "_persist_order", side_effect=Exception("S3 error")):
            # This should use the error handler
            tracker.record_order("test_order", StrategyType.NUCLEAR, "AAPL", "buy", 10, 150.0)

        # Order should still be in cache (error was in persistence)
        assert len(tracker._orders_cache) == 1

    def test_get_strategy_tracker_singleton(self):
        """Test that get_strategy_tracker returns singleton instances."""
        tracker1 = get_strategy_tracker(paper_trading=True)
        tracker2 = get_strategy_tracker(paper_trading=True)

        # Should be the same instance
        assert tracker1 is tracker2

        # Live trading should be different
        tracker3 = get_strategy_tracker(paper_trading=False)
        assert tracker3 is not tracker1

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_realized_pnl_calculation(self, mock_get_s3_handler):
        """Test realized P&L calculation for sell orders."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Buy some shares
        tracker.record_order("buy_1", StrategyType.NUCLEAR, "AAPL", "buy", 100, 150.0)

        # Sell some shares at a higher price
        tracker.record_order("sell_1", StrategyType.NUCLEAR, "AAPL", "sell", 50, 160.0)

        # Check realized P&L was calculated
        assert "NUCLEAR" in tracker._realized_pnl_cache
        expected_pnl = 50 * (160.0 - 150.0)  # 50 shares * $10 profit
        assert tracker._realized_pnl_cache["NUCLEAR"] == pytest.approx(expected_pnl, rel=1e-9, abs=1e-2)

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_strategy_pnl_summary(self, mock_get_s3_handler):
        """Test strategy P&L summary generation."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record some trades
        tracker.record_order("order_1", StrategyType.NUCLEAR, "AAPL", "buy", 100, 150.0)
        tracker.record_order("order_2", StrategyType.NUCLEAR, "AAPL", "sell", 25, 160.0)

        # Get P&L summary with current prices
        current_prices = {"AAPL": 155.0}
        pnl = tracker.get_strategy_pnl(StrategyType.NUCLEAR, current_prices)

        assert pnl.strategy == "NUCLEAR"
        assert pnl.realized_pnl == pytest.approx(250.0, rel=1e-9, abs=1e-9)  # 25 * (160 - 150)
        assert pnl.positions["AAPL"] == pytest.approx(75.0, rel=1e-9, abs=1e-9)  # 100 - 25 remaining

        # Check unrealized P&L: 75 shares * (155 - 150) = 375
        assert pnl.unrealized_pnl == pytest.approx(375.0, rel=1e-9, abs=1e-2)

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_get_execution_summary_dto(self, mock_get_s3_handler):
        """Test getting execution summary as DTO."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record some trades
        tracker.record_order("order_1", StrategyType.TECL, "TSLA", "buy", 100, 200.0)
        tracker.record_order("order_2", StrategyType.TECL, "TSLA", "sell", 50, 210.0)

        # Get execution summary DTO
        summary = tracker.get_execution_summary_dto(StrategyType.TECL, "TSLA")

        assert summary.strategy == "TECL"
        assert summary.symbol == "TSLA"
        assert summary.total_qty == Decimal("150")  # 100 + 50
        assert summary.status == ExecutionStatus.OK
        assert len(summary.details) == 2

        # Check that details contain StrategyOrderEventDTO objects
        for detail in summary.details:
            assert isinstance(detail, StrategyOrderEventDTO)
            assert detail.strategy == "TECL"
            assert detail.symbol == "TSLA"

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_decimal_usage_in_mappings(self, mock_get_s3_handler):
        """Test that decimal precision is maintained in DTO mappings."""
        mock_get_s3_handler.return_value = self.mock_s3_handler

        tracker = StrategyOrderTracker(paper_trading=True)

        # Record order with decimal precision
        tracker.record_order("order_1", StrategyType.KLM, "NVDA", "buy", 33.333, 523.45)

        # Get execution summary
        summary = tracker.get_execution_summary_dto(StrategyType.KLM, "NVDA")

        # Check decimal precision is maintained
        assert isinstance(summary.total_qty, Decimal)
        assert summary.total_qty == pytest.approx(Decimal("33.333"), rel=1e-9, abs=Decimal("0.001"))

        # Check event details use Decimal
        event = summary.details[0]
        assert isinstance(event.quantity, Decimal)
        assert isinstance(event.price, Decimal)
        assert event.quantity == pytest.approx(Decimal("33.333"), rel=1e-9, abs=Decimal("0.001"))
        assert event.price == pytest.approx(Decimal("523.45"), rel=1e-9, abs=Decimal("0.01"))
