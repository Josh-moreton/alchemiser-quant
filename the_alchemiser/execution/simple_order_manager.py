#!/usr/bin/env python3
"""
Simple Order Manager for Alpaca Trading.

A straightforward, robust order placement system that uses Alpaca's APIs directly.
No complex retry logic or dynamic pegging - just simple, reliable order placement.

DESIGN PHILOSOPHY:
=================
This order manager prioritizes simplicity, reliability, and transparency over complexity.
It follows a "fail-fast, clear errors" approach rather than trying to be overly clever
with retries and dynamic adjustments that can mask underlying issues.

KEY PRINCIPLES:
==============
1. USE ALPACA'S APIS DIRECTLY
   - get_all_positions() for current holdings
   - close_position() for safe liquidation of entire positions
   - get_orders() for pending order status
   - cancel_orders() for cleanup before new trades
   - submit_order() for straightforward order placement

2. PREVENT OVERSELLING WITH POSITION VALIDATION
   - Always check actual positions before selling
   - Cap sell quantities to available shares
   - Use liquidation API for full position exits (99%+)
   - Never attempt to sell more than we own

3. CLEAN ORDER MANAGEMENT
   - Cancel existing orders before placing new ones
   - Wait briefly for cancellations to process
   - Use simple market orders for immediate execution
   - Use limit orders only when price control is needed

4. CLEAR ERROR HANDLING
   - Fail fast with clear error messages
   - No complex retry logic that can hide problems
   - Log all important actions and failures
   - Return None for failures, order_id for success

ORDER PLACEMENT LOGIC:
=====================

SELLING POSITIONS:
- For partial sales (< 99% of position): Use market order
- For full sales (≥ 99% of position): Use Alpaca's close_position() API
- Always validate position exists before attempting to sell
- Automatically cap sell quantity to available shares

BUYING POSITIONS:
- Use market orders for immediate execution
- Cancel any existing orders first to avoid conflicts
- Round quantities to avoid fractional share issues
- Validate positive quantities and prices

REBALANCING WORKFLOW:
1. Get current positions from Alpaca
2. Calculate what needs to be sold (target = 0%)
3. Execute all sell orders first (using liquidation API for full exits)
4. Wait for sells to process
5. Execute buy orders with remaining cash
6. Return order IDs for all trades

SAFETY FEATURES:
===============
- Position validation before every sell order
- Automatic quantity capping to prevent overselling
- Order cancellation before new orders to prevent conflicts
- Liquidation API usage for full position exits
- Decimal rounding to handle fractional shares properly
- Clear logging of all order attempts and results

ERROR SCENARIOS HANDLED:
=======================
- Attempting to sell non-existent positions → Returns None
- Attempting to sell more than owned → Automatically caps to available
- Invalid quantities (≤ 0) → Returns None with warning
- API failures → Returns None with error logging
- Missing market data → Returns None with error logging

This approach trades sophistication for reliability. It's designed to work
consistently in live trading environments where clarity and predictability
are more valuable than complex optimization.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_DOWN

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus

from the_alchemiser.core.data.data_provider import UnifiedDataProvider


class SimpleOrderManager:
    """
    Simple, robust order manager that:
    1. Gets current positions from Alpaca
    2. Cancels any pending orders before placing new ones
    3. Uses liquidation API for selling entire positions
    4. Places straightforward market or limit orders
    5. No complex retry logic - fail fast and clear
    """

    def __init__(self, trading_client: TradingClient, data_provider: UnifiedDataProvider):
        """
        Initialize SimpleOrderManager.
        
        Args:
            trading_client: Alpaca trading client
            data_provider: Data provider for quotes (optional for market orders)
        """
        self.trading_client = trading_client
        self.data_provider = data_provider

    def get_current_positions(self) -> Dict[str, float]:
        """
        Get all current positions from Alpaca.
        
        Returns:
            Dictionary mapping symbol -> quantity owned
        """
        try:
            positions = self.trading_client.get_all_positions()
            return {
                str(getattr(pos, 'symbol', '')): float(getattr(pos, 'qty', 0))
                for pos in positions
                if float(getattr(pos, 'qty', 0)) != 0
            }
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return {}

    def get_pending_orders(self) -> List[Dict]:
        """
        Get all pending orders from Alpaca.
        
        Returns:
            List of pending order information
        """
        try:
            # Get all orders (Alpaca defaults to open orders)
            orders = self.trading_client.get_orders()
            return [
                {
                    'id': str(getattr(order, 'id', '')),
                    'symbol': str(getattr(order, 'symbol', '')),
                    'side': str(getattr(order, 'side', '')),
                    'qty': float(getattr(order, 'qty', 0)),
                    'status': str(getattr(order, 'status', ''))
                }
                for order in orders
            ]
        except Exception as e:
            logging.error(f"Error getting pending orders: {e}")
            return []

    def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """
        Cancel all pending orders, optionally filtered by symbol.
        
        Args:
            symbol: If provided, only cancel orders for this symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if symbol:
                # Cancel orders for specific symbol
                orders = self.get_pending_orders()
                symbol_orders = [o for o in orders if o['symbol'] == symbol]
                
                for order in symbol_orders:
                    try:
                        self.trading_client.cancel_order_by_id(order['id'])
                        logging.info(f"Cancelled order {order['id']} for {symbol}")
                    except Exception as e:
                        logging.warning(f"Could not cancel order {order['id']}: {e}")
            else:
                # Cancel all orders
                self.trading_client.cancel_orders()
                logging.info("Cancelled all pending orders")
                
            return True
        except Exception as e:
            logging.error(f"Error cancelling orders: {e}")
            return False

    def liquidate_position(self, symbol: str) -> Optional[str]:
        """
        Liquidate entire position using Alpaca's close_position API.
        This is the safest way to sell an entire position.
        
        Args:
            symbol: Symbol to liquidate
            
        Returns:
            Order ID if successful, None if failed
        """
        try:
            # First check we actually have a position
            positions = self.get_current_positions()
            if symbol not in positions or positions[symbol] <= 0:
                logging.warning(f"No position to liquidate for {symbol}")
                return None
                
            logging.info(f"Liquidating entire position for {symbol} ({positions[symbol]} shares)")
            
            # Cancel any pending orders for this symbol first
            self.cancel_all_orders(symbol)
            time.sleep(0.5)  # Brief pause for cancellations to process
            
            # Use Alpaca's liquidation API
            response = self.trading_client.close_position(symbol)
            
            if response:
                order_id = str(getattr(response, 'id', 'unknown'))
                logging.info(f"Position liquidation order placed for {symbol}: {order_id}")
                return order_id
            else:
                logging.error(f"Failed to liquidate position for {symbol}: No response")
                return None
                
        except Exception as e:
            logging.error(f"Exception liquidating position for {symbol}: {e}")
            return None

    def place_market_order(
        self, 
        symbol: str, 
        qty: float, 
        side: OrderSide, 
        cancel_existing: bool = True
    ) -> Optional[str]:
        """
        Place a simple market order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: OrderSide.BUY or OrderSide.SELL
            cancel_existing: Whether to cancel existing orders for this symbol first
            
        Returns:
            Order ID if successful, None if failed
        """
        # Check for invalid types first (before float conversion)
        if isinstance(qty, bool) or qty is None or isinstance(qty, (list, dict)):
            logging.warning(f"Invalid quantity type for {symbol}: {qty}")
            return None
            
        # Convert qty to float if it's a string
        try:
            qty = float(qty)
        except (ValueError, TypeError):
            logging.warning(f"Invalid quantity type for {symbol}: {qty}")
            return None
        
        # Check for invalid numeric values
        import math
        if math.isnan(qty) or math.isinf(qty) or qty <= 0:
            logging.warning(f"Invalid quantity for {symbol}: {qty}")
            return None

        try:
            # Cancel existing orders if requested
            if cancel_existing:
                self.cancel_all_orders(symbol)
                time.sleep(0.5)  # Brief pause for cancellations to process

            # For sell orders, validate we have enough to sell
            if side == OrderSide.SELL:
                positions = self.get_current_positions()
                available = positions.get(symbol, 0)
                
                if available <= 0:
                    logging.warning(f"No position to sell for {symbol}")
                    return None
                    
                if qty > available:
                    logging.warning(f"Reducing sell quantity for {symbol}: {qty} -> {available}")
                    qty = available

            # Round quantity to avoid fractional share issues
            qty = float(Decimal(str(qty)).quantize(Decimal('0.000001'), rounding=ROUND_DOWN))
            
            if qty <= 0:
                logging.warning(f"Quantity rounded to zero for {symbol}")
                return None

            logging.info(f"Placing MARKET {side.value} order for {symbol}: qty={qty}")

            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(market_order_data)
            order_id = str(getattr(order, 'id', 'unknown'))
            
            logging.info(f"Market order placed for {symbol}: {order_id}")
            return order_id
            
        except Exception as e:
            logging.error(f"Market order failed for {symbol}: {e}")
            return None

    def place_limit_order(
        self, 
        symbol: str, 
        qty: float, 
        side: OrderSide, 
        limit_price: float,
        cancel_existing: bool = True
    ) -> Optional[str]:
        """
        Place a simple limit order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: OrderSide.BUY or OrderSide.SELL
            limit_price: Limit price for the order
            cancel_existing: Whether to cancel existing orders for this symbol first
            
        Returns:
            Order ID if successful, None if failed
        """
        if qty <= 0:
            logging.warning(f"Invalid quantity for {symbol}: {qty}")
            return None
            
        if limit_price <= 0:
            logging.warning(f"Invalid limit price for {symbol}: {limit_price}")
            return None

        try:
            # Cancel existing orders if requested
            if cancel_existing:
                self.cancel_all_orders(symbol)
                time.sleep(0.5)  # Brief pause for cancellations to process

            # For sell orders, validate we have enough to sell
            if side == OrderSide.SELL:
                positions = self.get_current_positions()
                available = positions.get(symbol, 0)
                
                if available <= 0:
                    logging.warning(f"No position to sell for {symbol}")
                    return None
                    
                if qty > available:
                    logging.warning(f"Reducing sell quantity for {symbol}: {qty} -> {available}")
                    qty = available

            # Round quantity and price
            qty = float(Decimal(str(qty)).quantize(Decimal('0.000001'), rounding=ROUND_DOWN))
            limit_price = round(limit_price, 2)
            
            if qty <= 0:
                logging.warning(f"Quantity rounded to zero for {symbol}")
                return None

            logging.info(f"Placing LIMIT {side.value} order for {symbol}: qty={qty}, price=${limit_price}")

            limit_order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
            
            order = self.trading_client.submit_order(limit_order_data)
            order_id = str(getattr(order, 'id', 'unknown'))
            
            logging.info(f"Limit order placed for {symbol}: {order_id}")
            return order_id
            
        except Exception as e:
            logging.error(f"Limit order failed for {symbol}: {e}")
            return None

    def place_smart_sell_order(self, symbol: str, qty: float) -> Optional[str]:
        """
        Smart sell order that uses liquidation API for full position sells.
        
        Args:
            symbol: Symbol to sell
            qty: Quantity to sell
            
        Returns:
            Order ID if successful, None if failed
        """
        positions = self.get_current_positions()
        available = positions.get(symbol, 0)
        
        if available <= 0:
            logging.warning(f"No position to sell for {symbol}")
            return None
            
        # If selling 99%+ of position, use liquidation API
        if qty >= available * 0.99:
            logging.info(f"Selling {qty}/{available} shares ({qty/available:.1%}) - using liquidation API")
            return self.liquidate_position(symbol)
        else:
            logging.info(f"Selling {qty}/{available} shares ({qty/available:.1%}) - using market order")
            return self.place_market_order(symbol, qty, OrderSide.SELL)

    def get_smart_limit_price(self, symbol: str, side: OrderSide, aggressiveness: float = 0.5) -> Optional[float]:
        """
        Get a smart limit price based on current bid/ask.
        
        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            aggressiveness: 0.0 = most conservative, 1.0 = most aggressive (market price)
            
        Returns:
            Calculated limit price, or None if data unavailable
        """
        try:
            bid, ask = self.data_provider.get_latest_quote(symbol)
            
            if bid <= 0 or ask <= 0 or bid >= ask:
                logging.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return None
                
            if side == OrderSide.BUY:
                # For buying: bid = conservative, ask = aggressive
                price = bid + (ask - bid) * aggressiveness
            else:
                # For selling: ask = conservative, bid = aggressive  
                price = ask - (ask - bid) * aggressiveness
                
            return round(price, 2)
            
        except Exception as e:
            logging.error(f"Error getting smart limit price for {symbol}: {e}")
            return None

    def execute_rebalance_plan(self, target_allocations: Dict[str, float], total_value: float) -> Dict[str, Optional[str]]:
        """
        Execute a complete rebalancing plan.
        
        Args:
            target_allocations: Dict of symbol -> target percentage (0.0 to 1.0)
            total_value: Total portfolio value to allocate
            
        Returns:
            Dict of symbol -> order_id (or None if failed)
        """
        logging.info(f"🔄 Executing rebalance plan with ${total_value:.2f} total value")
        
        # Get current positions
        current_positions = self.get_current_positions()
        
        # Calculate target quantities
        results = {}
        sells_first = []
        buys_second = []
        
        # Plan all trades
        for symbol, target_pct in target_allocations.items():
            target_value = total_value * target_pct
            current_qty = current_positions.get(symbol, 0)
            
            if target_pct == 0 and current_qty > 0:
                # Need to sell entire position
                sells_first.append(symbol)
            elif target_pct > 0:
                # Will need to buy after sells complete
                buys_second.append((symbol, target_value))
        
        # Execute sells first
        logging.info(f"📉 Executing {len(sells_first)} sell orders...")
        for symbol in sells_first:
            current_qty = current_positions.get(symbol, 0)
            if current_qty > 0:
                logging.info(f"Selling entire position: {symbol} ({current_qty} shares)")
                order_id = self.liquidate_position(symbol)
                results[symbol] = order_id
            else:
                logging.warning(f"No position to sell for {symbol}")
                results[symbol] = None
        
        # Wait a moment for sells to process
        if sells_first:
            logging.info("⏳ Waiting for sell orders to process...")
            time.sleep(3)
        
        # Execute buys second
        logging.info(f"📈 Executing {len(buys_second)} buy orders...")
        for symbol, target_value in buys_second:
            if target_value <= 1:  # Skip very small allocations
                logging.warning(f"Skipping {symbol}: target value too small (${target_value:.2f})")
                results[symbol] = None
                continue
                
            try:
                current_price = self.data_provider.get_current_price(symbol)
                if current_price <= 0:
                    logging.error(f"Invalid price for {symbol}")
                    results[symbol] = None
                    continue
                    
                target_qty = target_value / current_price
                logging.info(f"Buying {symbol}: ${target_value:.2f} ≈ {target_qty:.6f} shares @ ${current_price:.2f}")
                
                order_id = self.place_market_order(symbol, target_qty, OrderSide.BUY)
                results[symbol] = order_id
                
            except Exception as e:
                logging.error(f"Error calculating buy order for {symbol}: {e}")
                results[symbol] = None
        
        # Summary
        successful_orders = sum(1 for order_id in results.values() if order_id is not None)
        total_orders = len(results)
        
        logging.info(f"✅ Rebalance complete: {successful_orders}/{total_orders} orders successful")
        
        return results

    def wait_for_order_completion(
        self, 
        order_ids: List[str], 
        max_wait_seconds: int = 60
    ) -> Dict[str, str]:
        """
        Wait for orders to complete (filled, canceled, or rejected).
        
        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait
            
        Returns:
            Dict of order_id -> final_status
        """
        if not order_ids:
            return {}
            
        logging.info(f"⏳ Waiting for {len(order_ids)} orders to complete...")
        
        start_time = time.time()
        completed = {}
        
        while time.time() - start_time < max_wait_seconds and len(completed) < len(order_ids):
            for order_id in order_ids:
                if order_id in completed:
                    continue
                    
                try:
                    order = self.trading_client.get_order_by_id(order_id)
                    status = str(getattr(order, 'status', 'unknown'))
                    
                    if status in ['filled', 'canceled', 'rejected', 'expired']:
                        completed[order_id] = status
                        logging.info(f"Order {order_id}: {status}")
                        
                except Exception as e:
                    logging.warning(f"Error checking order {order_id}: {e}")
                    completed[order_id] = 'error'
            
            if len(completed) < len(order_ids):
                time.sleep(2)  # Wait 2 seconds before checking again
        
        # Handle any remaining orders
        for order_id in order_ids:
            if order_id not in completed:
                completed[order_id] = 'timeout'
                
        return completed
