#!/usr/bin/env python3
"""Tests for StrategyOrderTracker DTO integration."""

from unittest.mock import Mock, patch

from tests.utils.float_checks import assert_close
from the_alchemiser.application.tracking.strategy_order_tracker import StrategyOrderTracker
from the_alchemiser.domain.strategies.strategy_manager import StrategyType


class TestStrategyOrderTracker:
    """Test StrategyOrderTracker DTO integration."""

    def setup_method(self) -> None:
        self.mock_s3_handler = Mock()
        self.mock_s3_handler.file_exists.return_value = False
        self.mock_s3_handler.read_json.return_value = None
        self.mock_s3_handler.write_json.return_value = True

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_record_order_sequence_events(self, mock_get_s3_handler: Mock) -> None:
        """Test recording sequence of events (submitted->accepted->filled)."""
        mock_get_s3_handler.return_value = self.mock_s3_handler
        tracker = StrategyOrderTracker(paper_trading=True)

        tracker.record_order(
            "order_123",
            StrategyType.NUCLEAR,
            "AAPL",
            "buy",
            100,
            150.25,
        )

        order = tracker._orders_cache[0]
        assert order.order_id == "order_123"
        assert order.strategy == StrategyType.NUCLEAR.value
        assert order.symbol == "AAPL"
        assert order.side == "BUY"
        assert_close(order.quantity, 100.0)
        assert_close(order.price, 150.25)

    @patch("the_alchemiser.application.tracking.strategy_order_tracker.get_s3_handler")
    def test_partial_fills_aggregation(self, mock_get_s3_handler: Mock) -> None:
        """Test partial fills aggregation."""
        mock_get_s3_handler.return_value = self.mock_s3_handler
        tracker = StrategyOrderTracker(paper_trading=True)

        tracker.record_order("order_1", StrategyType.TECL, "TSLA", "buy", 50, 200.0)
        tracker.record_order("order_2", StrategyType.TECL, "TSLA", "buy", 50, 205.0)

        position_key = (StrategyType.TECL.value, "TSLA")
        assert position_key in tracker._positions_cache
        position = tracker._positions_cache[position_key]
        assert_close(position.quantity, 100.0)
        assert_close(position.average_cost, 202.5)
