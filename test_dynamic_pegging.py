#!/usr/bin/env python3
"""
Test suite for dynamic limit order pegging functionality.

Tests various market conditions and rebalancing scenarios to ensure
the dynamic pegging strategy works correctly.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List, Tuple
import time

# Assuming these imports work with your project structure
from the_alchemiser.execution.alpaca_trader import AlpacaTradingBot
from alpaca.trading.enums import OrderSide, TimeInForce


@dataclass
class MockQuote:
    """Mock quote data for testing"""
    bid_price: float
    ask_price: float
    spread: float
    
    @property
    def mid(self) -> float:
        return (self.bid_price + self.ask_price) / 2


@dataclass
class TestScenario:
    """Test scenario for different market conditions"""
    name: str
    bid: float
    ask: float
    current_price: float
    side: OrderSide
    expected_behavior: str
    description: str


class TestDynamicLimitOrderPegging:
    """Test suite for dynamic limit order pegging"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_trader = Mock(spec=AlpacaTradingBot)
        self.mock_data_provider = Mock()
        self.mock_trading_client = Mock()
        
        # Set up the trader with mocked dependencies
        self.mock_trader.data_provider = self.mock_data_provider
        self.mock_trader.trading_client = self.mock_trading_client
        
        # Add the actual method we're testing
        self.mock_trader.calculate_dynamic_limit_price = AlpacaTradingBot.calculate_dynamic_limit_price.__get__(self.mock_trader)
    
    def test_dynamic_limit_price_calculation(self):
        """Test the core dynamic limit price calculation logic"""
        
        scenarios = [
            TestScenario(
                name="Normal Spread BUY",
                bid=100.0, ask=100.10, current_price=100.05,
                side=OrderSide.BUY,
                expected_behavior="Start at mid, move toward ask",
                description="Normal market with 10 cent spread"
            ),
            TestScenario(
                name="Normal Spread SELL", 
                bid=100.0, ask=100.10, current_price=100.05,
                side=OrderSide.SELL,
                expected_behavior="Start at mid, move toward bid",
                description="Normal market with 10 cent spread"
            ),
            TestScenario(
                name="Wide Spread BUY",
                bid=99.50, ask=100.50, current_price=100.0,
                side=OrderSide.BUY,
                expected_behavior="Start at mid, step toward ask",
                description="Wide spread market (1 dollar spread)"
            ),
            TestScenario(
                name="Tight Spread BUY",
                bid=100.00, ask=100.01, current_price=100.005,
                side=OrderSide.BUY,
                expected_behavior="Start at mid, minimal stepping",
                description="Very tight spread market (1 cent spread)"
            ),
            TestScenario(
                name="No Bid Available",
                bid=0.0, ask=100.10, current_price=100.05,
                side=OrderSide.SELL,
                expected_behavior="Use ask as fallback",
                description="Missing bid data"
            ),
            TestScenario(
                name="No Ask Available",
                bid=100.0, ask=0.0, current_price=100.05,
                side=OrderSide.BUY,
                expected_behavior="Use bid as fallback",
                description="Missing ask data"
            )
        ]
        
        for scenario in scenarios:
            print(f"\nTesting: {scenario.name}")
            print(f"Description: {scenario.description}")
            print(f"Market: Bid=${scenario.bid}, Ask=${scenario.ask}, Current=${scenario.current_price}")
            
            # Test progression through steps
            prices = []
            for step in range(6):  # 0 to 5 steps
                price = self.mock_trader.calculate_dynamic_limit_price(
                    side=scenario.side,
                    bid=scenario.bid,
                    ask=scenario.ask,
                    step=step,
                    tick_size=0.01,
                    max_steps=5
                )
                prices.append(price)
                print(f"  Step {step}: ${price:.2f}")
            
            # Validate the price progression
            self._validate_price_progression(scenario, prices)
    
    def _validate_price_progression(self, scenario: TestScenario, prices: List[float]):
        """Validate that price progression makes sense"""
        
        # Basic validations
        assert len(prices) == 6, "Should have 6 price points (steps 0-5)"
        assert all(price > 0 for price in prices), "All prices should be positive"
        
        if scenario.bid > 0 and scenario.ask > 0:
            mid = (scenario.bid + scenario.ask) / 2
            
            if scenario.side == OrderSide.BUY:
                # For BUY orders, prices should progress from mid toward ask
                assert prices[0] >= mid - 0.02, f"First price should be near mid: {prices[0]} vs {mid}"
                assert prices[-1] <= scenario.ask + 0.01, f"Final price should not exceed ask: {prices[-1]} vs {scenario.ask}"
                
                # Prices should generally increase (move toward ask)
                for i in range(1, len(prices)):
                    assert prices[i] >= prices[i-1] - 0.01, f"BUY prices should not decrease significantly: {prices[i]} vs {prices[i-1]}"
            
            else:  # SELL
                # For SELL orders, prices should progress from mid toward bid
                assert prices[0] <= mid + 0.02, f"First price should be near mid: {prices[0]} vs {mid}"
                assert prices[-1] >= scenario.bid - 0.01, f"Final price should not go below bid: {prices[-1]} vs {scenario.bid}"
                
                # Prices should generally decrease (move toward bid)
                for i in range(1, len(prices)):
                    assert prices[i] <= prices[i-1] + 0.01, f"SELL prices should not increase significantly: {prices[i]} vs {prices[i-1]}"
    
    @patch('time.time')
    @patch('time.sleep')
    def test_rebalancing_scenario_normal_market(self, mock_sleep, mock_time):
        """Test dynamic pegging in a normal rebalancing scenario"""
        
        # Mock time progression
        mock_time.side_effect = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30]  # Simulate timeouts
        
        # Setup mock responses
        self.mock_data_provider.get_current_price.return_value = 150.0
        self.mock_data_provider.get_latest_quote.return_value = (149.95, 150.05)  # 10 cent spread
        
        # Mock order creation and status
        mock_order = Mock()
        mock_order.id = "test_order_123"
        mock_order.status = "new"
        self.mock_trading_client.submit_order.return_value = mock_order
        
        # Mock order status progression: new -> partially_filled -> filled
        order_statuses = ["new", "new", "partially_filled", "filled"]
        mock_polled_orders = []
        for status in order_statuses:
            mock_polled_order = Mock()
            mock_polled_order.status = status
            mock_polled_orders.append(mock_polled_order)
        
        self.mock_trading_client.get_order_by_id.side_effect = mock_polled_orders
        
        # Create a real trader instance for this test
        trader = AlpacaTradingBot(paper_trading=True, ignore_market_hours=True)
        trader.data_provider = self.mock_data_provider
        trader.trading_client = self.mock_trading_client
        
        # Test BUY order
        order_id = trader.place_order(
            symbol="AAPL",
            qty=10,
            side=OrderSide.BUY,
            max_retries=3,
            poll_timeout=10,
            poll_interval=1.0,
            slippage_bps=10
        )
        
        # Verify order was placed successfully
        assert order_id == "test_order_123"
        self.mock_trading_client.submit_order.assert_called()
        
        # Verify the limit price was calculated with dynamic pegging
        call_args = self.mock_trading_client.submit_order.call_args
        limit_order_request = call_args[0][0]
        
        # Should start near midpoint (150.00)
        assert 149.98 <= limit_order_request.limit_price <= 150.02
    
    @patch('time.time')
    @patch('time.sleep')
    def test_rebalancing_scenario_volatile_market(self, mock_sleep, mock_time):
        """Test dynamic pegging in a volatile market with wide spreads"""
        
        mock_time.side_effect = list(range(100))  # Plenty of time values
        
        # Volatile market: wide spread
        self.mock_data_provider.get_current_price.return_value = 50.0
        self.mock_data_provider.get_latest_quote.return_value = (49.50, 50.50)  # $1 spread
        
        # All orders timeout and need retry
        mock_order = Mock()
        mock_order.id = "volatile_order_123"
        self.mock_trading_client.submit_order.return_value = mock_order
        
        # Mock orders that timeout then eventually fill
        timeout_order = Mock()
        timeout_order.status = "new"
        
        filled_order = Mock() 
        filled_order.status = "filled"
        
        # First 3 attempts timeout, 4th fills
        self.mock_trading_client.get_order_by_id.side_effect = [
            timeout_order, timeout_order, timeout_order,  # First attempt timeouts
            timeout_order, timeout_order, timeout_order,  # Second attempt timeouts  
            timeout_order, timeout_order, timeout_order,  # Third attempt timeouts
            filled_order  # Fourth attempt fills
        ]
        
        trader = AlpacaTradingBot(paper_trading=True, ignore_market_hours=True)
        trader.data_provider = self.mock_data_provider
        trader.trading_client = self.mock_trading_client
        
        # Test SELL order in volatile market
        order_id = trader.place_order(
            symbol="TSLA",
            qty=5,
            side=OrderSide.SELL,
            max_retries=3,
            poll_timeout=5,
            poll_interval=1.0,
            slippage_bps=20
        )
        
        # Should eventually succeed
        assert order_id == "volatile_order_123"
        
        # Should have made multiple attempts (4 total: initial + 3 retries)
        assert self.mock_trading_client.submit_order.call_count == 4
        
        # Verify limit prices became more aggressive
        limit_prices = []
        for call in self.mock_trading_client.submit_order.call_args_list:
            limit_order_request = call[0][0]
            limit_prices.append(limit_order_request.limit_price)
        
        print(f"Limit prices across attempts: {limit_prices}")
        
        # For SELL orders in volatile market, prices should move toward bid
        # First price should be near mid (50.00), last should be closer to bid (49.50)
        assert limit_prices[0] <= 50.10  # Start near mid
        assert limit_prices[-1] >= 49.40  # End closer to bid
        assert limit_prices[-1] < limit_prices[0]  # Should be more aggressive (lower for sell)
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        
        # Test with zero/negative tick size
        price = self.mock_trader.calculate_dynamic_limit_price(
            side=OrderSide.BUY,
            bid=100.0,
            ask=100.10,
            step=0,
            tick_size=0.0,
            max_steps=5
        )
        assert price == 100.05  # Should still return mid
        
        # Test with very large step
        price = self.mock_trader.calculate_dynamic_limit_price(
            side=OrderSide.BUY,
            bid=100.0,
            ask=100.10,
            step=100,  # Way beyond max_steps
            tick_size=0.01,
            max_steps=5
        )
        assert price == 100.10  # Should return ask for BUY when step > max_steps
        
        # Test with inverted bid/ask (should handle gracefully)
        price = self.mock_trader.calculate_dynamic_limit_price(
            side=OrderSide.BUY,
            bid=100.10,  # Bid higher than ask (bad data)
            ask=100.00,
            step=0,
            tick_size=0.01,
            max_steps=5
        )
        assert price > 0  # Should still return a valid price
    
    def test_market_impact_simulation(self):
        """Simulate the market impact of dynamic pegging vs static slippage"""
        
        scenarios = [
            ("Normal Market", 100.0, 100.10, 10),   # 10 cent spread, 10 bps slippage
            ("Tight Market", 100.0, 100.02, 5),    # 2 cent spread, 5 bps slippage  
            ("Wide Market", 100.0, 100.50, 25),    # 50 cent spread, 25 bps slippage
        ]
        
        for name, bid, ask, slippage_bps in scenarios:
            print(f"\n=== {name} ===")
            current_price = (bid + ask) / 2
            
            # Calculate static slippage approach
            static_buy_price = current_price * (1 + slippage_bps / 10000)
            static_sell_price = current_price * (1 - slippage_bps / 10000)
            
            # Calculate dynamic pegging approach (step 0)
            dynamic_buy_price = self.mock_trader.calculate_dynamic_limit_price(
                OrderSide.BUY, bid, ask, 0, current_price * (slippage_bps / 10000), 5
            )
            dynamic_sell_price = self.mock_trader.calculate_dynamic_limit_price(
                OrderSide.SELL, bid, ask, 0, current_price * (slippage_bps / 10000), 5  
            )
            
            print(f"Bid: ${bid:.2f}, Ask: ${ask:.2f}, Mid: ${current_price:.2f}")
            print(f"Static BUY:  ${static_buy_price:.2f} vs Dynamic: ${dynamic_buy_price:.2f}")
            print(f"Static SELL: ${static_sell_price:.2f} vs Dynamic: ${dynamic_sell_price:.2f}")
            
            # Dynamic should generally be more favorable (closer to mid)
            buy_improvement = static_buy_price - dynamic_buy_price
            sell_improvement = dynamic_sell_price - static_sell_price
            
            print(f"BUY improvement: ${buy_improvement:.3f} ({buy_improvement/current_price*10000:.1f} bps)")
            print(f"SELL improvement: ${sell_improvement:.3f} ({sell_improvement/current_price*10000:.1f} bps)")


def run_pegging_analysis():
    """Run a comprehensive analysis of the pegging strategy"""
    
    print("=" * 60)
    print("DYNAMIC LIMIT ORDER PEGGING ANALYSIS")
    print("=" * 60)
    
    test_suite = TestDynamicLimitOrderPegging()
    test_suite.setup_method()
    
    print("\n1. Testing Core Price Calculation Logic")
    print("-" * 40)
    test_suite.test_dynamic_limit_price_calculation()
    
    print("\n2. Testing Market Impact Comparison")
    print("-" * 40)
    test_suite.test_market_impact_simulation()
    
    print("\n3. Testing Edge Cases")
    print("-" * 40)
    test_suite.test_edge_cases()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_pegging_analysis()
