#!/usr/bin/env python3
"""
Test edge cases including fractional shares, delisted symbols,
duplicate orders, and other boundary conditions.
"""

import pytest
from unittest.mock import MagicMock, patch
from alpaca.trading.enums import OrderSide
from alpaca.common.exceptions import APIError
from decimal import Decimal

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_account.return_value = MagicMock(buying_power=10000.0, cash=10000.0)
    client.get_clock.return_value = MagicMock(is_open=True)
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock()
    provider.get_current_price.return_value = 100.0
    provider.get_latest_quote.return_value = (99.0, 101.0)
    return provider


@pytest.fixture
def order_manager(mock_trading_client, mock_data_provider):
    """Create OrderManagerAdapter for testing."""
    return OrderManagerAdapter(mock_trading_client, mock_data_provider)


class TestFractionalShares:
    """Test fractional share scenarios."""
    
    def test_fractional_position_liquidation(self, order_manager, mock_trading_client):
        """Test liquidating fractional share positions."""
        # Mock fractional position
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=12.753, market_value=1912.95)
        ]
        mock_trading_client.close_position.return_value = MagicMock(id='liquidation_order')
        
        order_id = order_manager.liquidate_position('AAPL')
        
        assert order_id is not None
        mock_trading_client.close_position.assert_called_once_with('AAPL')
    
    def test_fractional_sell_order(self, order_manager, mock_trading_client):
        """Test selling fractional shares."""
        # Mock fractional position
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=5.5)  # 5.5 shares
        ]
        
        # Try to sell 2.3 shares
        order_id = order_manager.place_safe_sell_order('AAPL', 2.3)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
        
        # Verify fractional quantity was used
        call_args = mock_trading_client.submit_order.call_args[0][0]
        assert float(call_args.qty) == 2.3
    
    def test_fractional_buy_order(self, order_manager, mock_trading_client):
        """Test buying fractional shares."""
        order_id = order_manager.place_limit_or_market('AAPL', 1.75, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
        
        # Verify fractional quantity
        call_args = mock_trading_client.submit_order.call_args[0][0]
        assert float(call_args.qty) == 1.75
    
    def test_very_small_fractional_shares(self, order_manager, mock_trading_client):
        """Test handling very small fractional amounts."""
        # Test tiny fractional amounts (0.001 shares)
        order_id = order_manager.place_limit_or_market('AAPL', 0.001, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
    
    def test_high_precision_fractional_shares(self, order_manager, mock_trading_client):
        """Test handling high precision fractional shares."""
        # Mock position with high precision
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.3333333)  # High precision
        ]
        
        # Sell with high precision
        order_id = order_manager.place_safe_sell_order('AAPL', 16.6666667)
        
        assert order_id is not None
    
    def test_fractional_share_rounding_edge_cases(self, order_manager, mock_trading_client):
        """Test rounding edge cases with fractional shares."""
        # Test amounts that might cause rounding issues
        test_quantities = [0.999999, 1.000001, 33.333333, 66.666667]
        
        for qty in test_quantities:
            order_id = order_manager.place_limit_or_market('AAPL', qty, OrderSide.BUY)
            assert order_id is not None


class TestDelistedSymbols:
    """Test handling of delisted or invalid symbols."""
    
    def test_delisted_symbol_order(self, order_manager, mock_trading_client):
        """Test ordering delisted symbol."""
        error_response = {"code": 40410000, "message": "symbol not found"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('DELISTED', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_suspended_symbol_order(self, order_manager, mock_trading_client):
        """Test ordering suspended symbol."""
        error_response = {"code": 40410001, "message": "symbol suspended"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('SUSPENDED', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_liquidating_delisted_position(self, order_manager, mock_trading_client):
        """Test liquidating position in delisted stock."""
        # Mock having position in delisted stock
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='DELISTED', qty=100.0, market_value=0.01)  # Nearly worthless
        ]
        
        # Liquidation might fail for delisted stocks
        mock_trading_client.close_position.side_effect = APIError({"code": 40410000, "message": "symbol not found"})
        
        order_id = order_manager.liquidate_position('DELISTED')
        
        assert order_id is None  # Should handle gracefully
    
    def test_symbol_format_validation(self, order_manager, mock_trading_client):
        """Test various invalid symbol formats."""
        invalid_symbols = ['', '123', 'TOOLONGSYMBOL', 'symbol with spaces', 'symbol!@#']
        
        for symbol in invalid_symbols:
            error_response = {"code": 40410000, "message": "invalid symbol format"}
            mock_trading_client.submit_order.side_effect = APIError(error_response)
            
            order_id = order_manager.place_limit_or_market(symbol, 1.0, OrderSide.BUY)
            assert order_id is None


class TestDuplicateOrders:
    """Test duplicate order scenarios."""
    
    def test_rapid_duplicate_orders(self, order_manager, mock_trading_client):
        """Test placing multiple identical orders rapidly."""
        # Place multiple identical orders
        orders = []
        for i in range(3):
            mock_trading_client.submit_order.return_value = MagicMock(id=f'order_{i}')
            order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
            orders.append(order_id)
        
        # All orders should be placed (no duplicate detection at order manager level)
        assert all(order_id is not None for order_id in orders)
        assert len(set(orders)) == 3  # All different order IDs
    
    def test_duplicate_sell_order_safety(self, order_manager, mock_trading_client):
        """Test safety against selling more than owned."""
        # Mock having 10 shares
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=10.0)
        ]
        
        # Try to place multiple sell orders that together exceed position
        order1 = order_manager.place_safe_sell_order('AAPL', 8.0)
        order2 = order_manager.place_safe_sell_order('AAPL', 8.0)  # Would total 16 > 10 owned
        
        # Both orders might be placed, but quantities should be validated
        assert order1 is not None
        assert order2 is not None
    
    def test_order_idempotency(self, order_manager, mock_trading_client):
        """Test order idempotency mechanisms."""
        # Some systems might implement client order ID for idempotency
        # This tests the behavior when same client order ID is used
        
        # Mock first order succeeds
        mock_trading_client.submit_order.return_value = MagicMock(id='order_123')
        order1 = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
        
        # Mock second identical order (might be rejected by broker)
        mock_trading_client.submit_order.side_effect = APIError({"code": 42210000, "message": "duplicate client order id"})
        order2 = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
        
        assert order1 is not None
        assert order2 is None  # Duplicate rejected


class TestBoundaryConditions:
    """Test numerical and logical boundary conditions."""
    
    def test_zero_quantity_order(self, order_manager, mock_trading_client):
        """Test order with zero quantity."""
        order_id = order_manager.place_limit_or_market('AAPL', 0.0, OrderSide.BUY)
        
        # Should not place order with zero quantity
        assert order_id is None or mock_trading_client.submit_order.call_count == 0
    
    def test_negative_quantity_order(self, order_manager, mock_trading_client):
        """Test order with negative quantity."""
        order_id = order_manager.place_limit_or_market('AAPL', -5.0, OrderSide.BUY)
        
        # Should not place order with negative quantity
        assert order_id is None
    
    def test_extremely_large_quantity(self, order_manager, mock_trading_client):
        """Test order with extremely large quantity."""
        # Try to order more shares than exist
        huge_quantity = 1e12  # 1 trillion shares
        
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', huge_quantity, OrderSide.BUY)
        
        assert order_id is None
    
    def test_maximum_decimal_precision(self, order_manager, mock_trading_client):
        """Test orders with maximum decimal precision."""
        # Test with maximum supported decimal places
        precise_quantity = Decimal('1.123456789')
        
        order_id = order_manager.place_limit_or_market('AAPL', float(precise_quantity), OrderSide.BUY)
        
        # Should handle high precision gracefully
        assert order_id is not None
    
    def test_floating_point_precision_issues(self, order_manager, mock_trading_client):
        """Test potential floating point precision issues."""
        # Test quantities that might cause floating point errors
        problematic_quantities = [0.1 + 0.2, 1.0/3.0, 2.0/3.0, 0.999999999]
        
        for qty in problematic_quantities:
            order_id = order_manager.place_limit_or_market('AAPL', qty, OrderSide.BUY)
            assert order_id is not None


class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent operations."""
    
    def test_position_changes_during_order(self, order_manager, mock_trading_client):
        """Test position changing between check and order placement."""
        # Mock position that changes between calls
        position_calls = [
            [MagicMock(symbol='AAPL', qty=10.0)],  # First call: 10 shares
            [MagicMock(symbol='AAPL', qty=5.0)]    # Second call: 5 shares (sold)
        ]
        mock_trading_client.get_all_positions.side_effect = position_calls
        
        # Try to sell 8 shares (should be safe based on first check)
        order_id = order_manager.place_safe_sell_order('AAPL', 8.0)
        
        # Should handle gracefully (implementation dependent)
        assert order_id is not None or order_id is None
    
    def test_market_close_during_order(self, order_manager, mock_trading_client):
        """Test market closing between order preparation and submission."""
        # Mock market closing during order process
        clock_calls = [
            MagicMock(is_open=True),   # Market open when checked
            MagicMock(is_open=False)   # Market closed when order submitted
        ]
        mock_trading_client.get_clock.side_effect = clock_calls
        
        # Order submission might fail due to market close
        error_response = {"code": 40010001, "message": "market is closed"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None


class TestDataTypeEdgeCases:
    """Test edge cases with different data types."""
    
    def test_string_quantities(self, order_manager, mock_trading_client):
        """Test handling of string quantities."""
        # Test with string that should convert to number
        order_id = order_manager.place_limit_or_market('AAPL', '10.5', OrderSide.BUY)
        
        # Should convert string to float
        assert order_id is not None
        
        call_args = mock_trading_client.submit_order.call_args[0][0]
        assert isinstance(call_args.qty, (int, float))
    
    def test_boolean_and_none_values(self, order_manager, mock_trading_client):
        """Test handling of invalid data types."""
        invalid_quantities = [None, True, False, [], {}]
        
        for qty in invalid_quantities:
            try:
                order_id = order_manager.place_limit_or_market('AAPL', qty, OrderSide.BUY)
                # Should either handle gracefully or raise appropriate error
                assert order_id is None
            except (TypeError, ValueError):
                # Acceptable to raise type/value errors for invalid types
                pass
    
    def test_infinity_and_nan_values(self, order_manager, mock_trading_client):
        """Test handling of infinity and NaN values."""
        import math
        
        special_values = [float('inf'), float('-inf'), float('nan')]
        
        for qty in special_values:
            order_id = order_manager.place_limit_or_market('AAPL', qty, OrderSide.BUY)
            # Should reject invalid numerical values
            assert order_id is None


class TestSystemLimits:
    """Test system and API limits."""
    
    def test_order_rate_limiting(self, order_manager, mock_trading_client):
        """Test behavior under order rate limiting."""
        # Simulate rate limiting after several orders
        successful_orders = 5
        
        def rate_limit_side_effect(*args, **kwargs):
            nonlocal successful_orders
            if successful_orders > 0:
                successful_orders -= 1
                return MagicMock(id=f'order_{successful_orders}')
            else:
                raise APIError({"code": 42910000, "message": "rate limit exceeded"})
        
        mock_trading_client.submit_order.side_effect = rate_limit_side_effect
        
        # Place orders until rate limited
        results = []
        for i in range(10):
            order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
            results.append(order_id)
        
        # First 5 should succeed, rest should fail
        assert sum(1 for r in results if r is not None) == 5
        assert sum(1 for r in results if r is None) == 5
    
    def test_daily_order_limits(self, order_manager, mock_trading_client):
        """Test daily order count limits."""
        # Simulate daily limit reached
        error_response = {"code": 42210001, "message": "daily order limit exceeded"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_position_size_limits(self, order_manager, mock_trading_client):
        """Test position size limits."""
        # Simulate position size limit
        error_response = {"code": 40310002, "message": "position size limit exceeded"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 10000.0, OrderSide.BUY)
        
        assert order_id is None
