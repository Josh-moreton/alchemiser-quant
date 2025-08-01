#!/usr/bin/env python3
"""
Test for Strategy Order Tracker

Simple test to validate the basic functionality of the strategy order tracker.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_alchemiser.tracking.strategy_order_tracker import (
    StrategyOrderTracker, StrategyOrder, StrategyPosition, StrategyPnL, get_strategy_tracker
)
from the_alchemiser.core.trading.strategy_manager import StrategyType


class TestStrategyOrderTracker(unittest.TestCase):
    """Test Strategy Order Tracker functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock S3 handler to avoid actual S3 calls
        self.mock_s3_handler = Mock()
        self.mock_s3_handler.file_exists.return_value = False
        self.mock_s3_handler.read_json.return_value = None
        self.mock_s3_handler.write_json.return_value = True
        
        # Mock config
        self.mock_config = {
            'tracking': {
                's3_bucket': 'test-bucket',
                'strategy_orders_path': 'test_orders/',
                'strategy_positions_path': 'test_positions/',
                'strategy_pnl_history_path': 'test_pnl/',
                'order_history_limit': 100
            }
        }
    
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_s3_handler')
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_config')
    def test_tracker_initialization(self, mock_get_config, mock_get_s3_handler):
        """Test tracker initializes correctly."""
        mock_get_config.return_value = self.mock_config
        mock_get_s3_handler.return_value = self.mock_s3_handler
        
        tracker = StrategyOrderTracker()
        
        self.assertEqual(tracker.order_history_limit, 100)
        self.assertIn('test-bucket', tracker.orders_s3_path)
        self.assertIn('test_orders/', tracker.orders_s3_path)
    
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_s3_handler')
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_config')
    def test_record_order(self, mock_get_config, mock_get_s3_handler):
        """Test recording an order."""
        mock_get_config.return_value = self.mock_config
        mock_get_s3_handler.return_value = self.mock_s3_handler
        
        tracker = StrategyOrderTracker()
        
        # Record a buy order
        tracker.record_order(
            order_id="test_order_123",
            strategy=StrategyType.NUCLEAR,
            symbol="SMR",
            side="BUY",
            quantity=100.0,
            price=50.0
        )
        
        # Check order was recorded
        self.assertEqual(len(tracker._orders_cache), 1)
        order = tracker._orders_cache[0]
        self.assertEqual(order.order_id, "test_order_123")
        self.assertEqual(order.strategy, "NUCLEAR")
        self.assertEqual(order.symbol, "SMR")
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.quantity, 100.0)
        self.assertEqual(order.price, 50.0)
        
        # Check position was created
        key = ("NUCLEAR", "SMR")
        self.assertIn(key, tracker._positions_cache)
        position = tracker._positions_cache[key]
        self.assertEqual(position.quantity, 100.0)
        self.assertEqual(position.average_cost, 50.0)
    
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_s3_handler')
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_config')
    def test_position_updates(self, mock_get_config, mock_get_s3_handler):
        """Test position updates with multiple orders."""
        mock_get_config.return_value = self.mock_config
        mock_get_s3_handler.return_value = self.mock_s3_handler
        
        tracker = StrategyOrderTracker()
        
        # First buy
        tracker.record_order("order_1", StrategyType.NUCLEAR, "SMR", "BUY", 100.0, 50.0)
        
        # Second buy at different price
        tracker.record_order("order_2", StrategyType.NUCLEAR, "SMR", "BUY", 50.0, 60.0)
        
        # Check position updates
        key = ("NUCLEAR", "SMR")
        position = tracker._positions_cache[key]
        self.assertEqual(position.quantity, 150.0)  # 100 + 50
        expected_avg_cost = (100*50 + 50*60) / 150  # 53.33333...
        self.assertAlmostEqual(position.average_cost, expected_avg_cost, places=4)
        
        # Partial sell
        tracker.record_order("order_3", StrategyType.NUCLEAR, "SMR", "SELL", 50.0, 70.0)
        
        # Check position after sell
        self.assertEqual(position.quantity, 100.0)  # 150 - 50
        self.assertAlmostEqual(position.average_cost, expected_avg_cost, places=4)  # Average cost unchanged
        
        # Check realized P&L was calculated
        self.assertIn("NUCLEAR", tracker._realized_pnl_cache)
        realized_pnl = tracker._realized_pnl_cache["NUCLEAR"]
        expected_pnl = 50.0 * (70.0 - expected_avg_cost)  # Use actual average cost
        self.assertAlmostEqual(realized_pnl, expected_pnl, places=2)
    
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_s3_handler')
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_config')
    def test_strategy_pnl_calculation(self, mock_get_config, mock_get_s3_handler):
        """Test P&L calculation for a strategy."""
        mock_get_config.return_value = self.mock_config
        mock_get_s3_handler.return_value = self.mock_s3_handler
        
        tracker = StrategyOrderTracker()
        
        # Record some orders
        tracker.record_order("order_1", StrategyType.NUCLEAR, "SMR", "BUY", 100.0, 50.0)
        tracker.record_order("order_2", StrategyType.NUCLEAR, "LEU", "BUY", 50.0, 200.0)
        tracker.record_order("order_3", StrategyType.NUCLEAR, "SMR", "SELL", 25.0, 60.0)
        
        # Current market prices
        current_prices = {
            "SMR": 55.0,  # Up from 50 average cost
            "LEU": 190.0  # Down from 200 cost
        }
        
        # Get P&L
        pnl = tracker.get_strategy_pnl(StrategyType.NUCLEAR, current_prices)
        
        # Check positions
        self.assertEqual(pnl.positions["SMR"], 75.0)  # 100 - 25 sold
        self.assertEqual(pnl.positions["LEU"], 50.0)
        
        # Check realized P&L (from SMR sale)
        expected_realized = 25.0 * (60.0 - 50.0)  # 25 shares * $10 profit
        self.assertAlmostEqual(pnl.realized_pnl, expected_realized, places=2)
        
        # Check unrealized P&L
        smr_unrealized = 75.0 * (55.0 - 50.0)  # 75 shares * $5 profit
        leu_unrealized = 50.0 * (190.0 - 200.0)  # 50 shares * $10 loss
        expected_unrealized = smr_unrealized + leu_unrealized
        self.assertAlmostEqual(pnl.unrealized_pnl, expected_unrealized, places=2)
        
        # Check total P&L
        self.assertAlmostEqual(pnl.total_pnl, expected_realized + expected_unrealized, places=2)
    
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_s3_handler')
    @patch('the_alchemiser.tracking.strategy_order_tracker.get_config')
    def test_email_summary(self, mock_get_config, mock_get_s3_handler):
        """Test email summary generation."""
        mock_get_config.return_value = self.mock_config
        mock_get_s3_handler.return_value = self.mock_s3_handler
        
        tracker = StrategyOrderTracker()
        
        # Record orders for multiple strategies
        tracker.record_order("order_1", StrategyType.NUCLEAR, "SMR", "BUY", 100.0, 50.0)
        tracker.record_order("order_2", StrategyType.TECL, "TECL", "BUY", 50.0, 60.0)
        
        current_prices = {"SMR": 55.0, "TECL": 65.0}
        
        summary = tracker.get_summary_for_email(current_prices)
        
        # Check summary structure
        self.assertIn('total_portfolio_pnl', summary)
        self.assertIn('strategies', summary)
        self.assertIn('NUCLEAR', summary['strategies'])
        self.assertIn('TECL', summary['strategies'])
        
        # Check strategy details
        nuclear_data = summary['strategies']['NUCLEAR']
        self.assertIn('total_pnl', nuclear_data)
        self.assertIn('total_return_pct', nuclear_data)
        self.assertIn('position_count', nuclear_data)


def test_strategy_order_creation():
    """Test StrategyOrder creation."""
    order = StrategyOrder.from_order_data(
        order_id="test_123",
        strategy=StrategyType.NUCLEAR,
        symbol="SMR",
        side="buy",  # Should be normalized to uppercase
        quantity=100,
        price=50.5
    )
    
    assert order.order_id == "test_123"
    assert order.strategy == "NUCLEAR"
    assert order.symbol == "SMR"
    assert order.side == "BUY"
    assert order.quantity == 100.0
    assert order.price == 50.5
    assert order.timestamp  # Should be set


def test_strategy_position_updates():
    """Test StrategyPosition updates."""
    position = StrategyPosition(
        strategy="NUCLEAR",
        symbol="SMR",
        quantity=0.0,
        average_cost=0.0,
        total_cost=0.0,
        last_updated=""
    )
    
    # First buy
    buy_order = StrategyOrder(
        order_id="order_1",
        strategy="NUCLEAR",
        symbol="SMR",
        side="BUY",
        quantity=100.0,
        price=50.0,
        timestamp="2025-01-01T00:00:00Z"
    )
    
    position.update_with_order(buy_order)
    assert position.quantity == 100.0
    assert position.average_cost == 50.0
    assert position.total_cost == 5000.0
    
    # Second buy at different price
    buy_order2 = StrategyOrder(
        order_id="order_2",
        strategy="NUCLEAR",
        symbol="SMR",
        side="BUY",
        quantity=50.0,
        price=60.0,
        timestamp="2025-01-01T01:00:00Z"
    )
    
    position.update_with_order(buy_order2)
    assert position.quantity == 150.0
    assert abs(position.average_cost - 53.33) < 0.01  # (5000 + 3000) / 150
    
    # Partial sell
    sell_order = StrategyOrder(
        order_id="order_3",
        strategy="NUCLEAR",
        symbol="SMR",
        side="SELL",
        quantity=50.0,
        price=70.0,
        timestamp="2025-01-01T02:00:00Z"
    )
    
    position.update_with_order(sell_order)
    assert position.quantity == 100.0
    assert abs(position.average_cost - 53.33) < 0.01  # Average cost unchanged


if __name__ == "__main__":
    # Run simple tests
    print("🧪 Testing Strategy Order Tracker")
    print("=" * 50)
    
    try:
        test_strategy_order_creation()
        print("✅ StrategyOrder creation test passed")
        
        test_strategy_position_updates()
        print("✅ StrategyPosition updates test passed")
        
        # Run unit tests
        unittest.main(verbosity=2, exit=False)
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
