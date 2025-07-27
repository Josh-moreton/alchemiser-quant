#!/usr/bin/env python3
"""
Order Manager for Alpaca Trading
Handles order placement, dynamic limit pricing, and settlement waiting.
"""

import logging
import time
import re
from typing import Dict, List, Optional
from datetime import datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from the_alchemiser.core.data.data_provider import UnifiedDataProvider


def is_market_open(trading_client: TradingClient) -> bool:
    """Check if the market is currently open."""
    try:
        clock = trading_client.get_clock()
        return getattr(clock, 'is_open', False)
    except Exception:
        return False


class OrderManager:
    """
    Manages order placement, dynamic limit pricing, and settlement waiting.
    
    This class encapsulates the complex order flow logic including:
    - Dynamic limit price calculation with progressive market approach
    - Order status polling and settlement waiting
    - Fallback to market orders when limit orders fail
    - Handling of insufficient buying power with quantity reduction
    """

    def __init__(self, trading_client: TradingClient, data_provider: UnifiedDataProvider, 
                 ignore_market_hours: bool = False, config: Optional[Dict] = None):
        """
        Initialize OrderManager.
        
        Args:
            trading_client: Alpaca trading client for order operations
            data_provider: Unified data provider for market data
            ignore_market_hours: Whether to ignore market hours when placing orders
            config: Configuration dictionary with slippage settings
        """
        self.trading_client = trading_client
        self.data_provider = data_provider
        self.ignore_market_hours = ignore_market_hours
        self.config = config or {}

    def calculate_dynamic_limit_price(
        self,
        side: OrderSide,
        bid: float,
        ask: float,
        step: int = 0,
        tick_size: float = 0.01,
        max_steps: int = 5,
    ) -> float:
        """
        Calculate a limit price using a dynamic pegging strategy.
        
        The strategy starts near the bid/ask midpoint and progressively moves
        toward the market on each retry attempt.
        
        Args:
            side: OrderSide.BUY or OrderSide.SELL
            bid: Current bid price
            ask: Current ask price
            step: Current retry step (0 = first attempt)
            tick_size: Price increment for each step
            max_steps: Maximum number of steps before using market price
            
        Returns:
            Calculated limit price rounded to 2 decimal places
        """
        if bid > 0 and ask > 0:
            mid = (bid + ask) / 2
        else:
            mid = bid if side == OrderSide.BUY else ask

        if step > max_steps:
            return round(ask if side == OrderSide.BUY else bid, 2)

        if side == OrderSide.BUY:
            price = min(mid + step * tick_size, ask if ask > 0 else mid)
        else:
            price = max(mid - step * tick_size, bid if bid > 0 else mid)

        return round(price, 2)

    def place_limit_or_market(
        self, 
        symbol: str, 
        qty: float, 
        side: OrderSide, 
        max_retries: int = 3, 
        poll_timeout: int = 30, 
        poll_interval: float = 2.0, 
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Place a limit order using dynamic pegging strategy, falling back to market order.
        
        Orders start near the bid/ask midpoint and move toward the market on each retry.
        Falls back to a market order if all retries fail. When ignore_market_hours is set,
        a market order is used directly if the market is closed.
        
        Args:
            symbol: Stock symbol
            qty: Quantity of shares (float for fractional shares)
            side: OrderSide.BUY or OrderSide.SELL
            max_retries: Maximum number of retry attempts
            poll_timeout: Time to wait for limit order fill before canceling
            poll_interval: Time between status checks
            slippage_bps: Slippage buffer in basis points (default from config)
            
        Returns:
            Order ID if successful, None if failed
        """
        if qty <= 0:
            logging.warning(f"Invalid quantity for {symbol}: {qty}")
            return None

        # Use config slippage if not provided
        if slippage_bps is None:
            slippage_bps = float(self.config.get('alpaca', {}).get('slippage_bps', 5))
        else:
            slippage_bps = float(slippage_bps)

        # Check if market is open
        market_open = is_market_open(self.trading_client)
        
        # For closed market + ignore_market_hours, use market order directly
        if not market_open and self.ignore_market_hours:
            logging.info(f"Market closed but ignore_market_hours=True, using market order for {symbol}")
            return self._place_market_order(symbol, qty, side)
        
        # Don't place orders when market is closed (unless ignoring market hours)
        if not market_open and not self.ignore_market_hours:
            logging.warning(f"Market is closed. Order for {symbol} not placed.")
            return None

        # Standard limit order flow for open market using dynamic pegging
        return self._place_limit_order_with_retries(
            symbol, qty, side, max_retries, poll_timeout, poll_interval, slippage_bps
        )

    def _place_limit_order_with_retries(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        max_retries: int,
        poll_timeout: int,
        poll_interval: float,
        slippage_bps: float
    ) -> Optional[str]:
        """Place limit orders with progressive market approach and retries."""
        attempt = 0
        current_qty = qty
        
        while attempt <= max_retries:
            try:
                current_price = self.data_provider.get_current_price(symbol)
                if current_price <= 0:
                    logging.error(f"Invalid current price for {symbol}")
                    return None

                bid, ask = self.data_provider.get_latest_quote(symbol)
                tick_size = current_price * (slippage_bps / 10000)
                
                limit_price = self.calculate_dynamic_limit_price(
                    side,
                    bid,
                    ask,
                    step=attempt,
                    tick_size=tick_size,
                    max_steps=max_retries,
                )

                logging.info(
                    f"Placing LIMIT {side.value} order for {symbol}: qty={current_qty}, limit_price={limit_price}"
                )

                limit_order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=current_qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price,
                )
                
                # Place order
                order = self.trading_client.submit_order(limit_order_data)
                order_id = str(getattr(order, 'id', 'unknown'))

                # Poll for order status
                if self._poll_order_status(order_id, poll_timeout, poll_interval):
                    return order_id

                # If not filled, cancel and retry closer to market
                self.trading_client.cancel_order_by_id(order_id)
                logging.warning(
                    f"Limit order {order_id} not filled in time, increasing aggressiveness."
                )
                attempt += 1

            except Exception as e:
                # Handle insufficient buying power by reducing quantity
                if self._is_insufficient_buying_power_error(e) and attempt < max_retries:
                    old_qty = current_qty
                    current_qty = round(current_qty * 0.95, 6)
                    logging.warning(
                        f"Order failed for {symbol} due to insufficient buying power. "
                        f"Retrying with 5% lower qty: {old_qty} -> {current_qty}"
                    )
                    print(f"   ⚠️  {symbol}: Insufficient buying power, retrying with 5% lower qty ({old_qty} -> {current_qty})")
                    attempt += 1
                    continue
                else:
                    logging.error(f"Exception placing limit order for {symbol}: {e}", exc_info=True)
                    attempt += 1

        # If all limit order attempts failed, try a market order as final fallback
        logging.warning(f"All limit order attempts failed for {symbol}. Falling back to MARKET order.")
        return self._place_market_order_with_fallback(symbol, current_qty, side)

    def _poll_order_status(self, order_id: str, poll_timeout: int, poll_interval: float) -> bool:
        """Poll order status until filled, cancelled, or timeout."""
        poll_start = time.time()
        while time.time() - poll_start < poll_timeout:
            try:
                polled_order = self.trading_client.get_order_by_id(order_id)
                polled_status = getattr(polled_order, 'status', 'unknown')
                
                if polled_status == "filled":
                    logging.info(f"Limit order filled: {order_id}")
                    return True
                elif polled_status in ("canceled", "rejected"):
                    logging.warning(f"Limit order {order_id} was {polled_status}")
                    return False
                    
                time.sleep(poll_interval)
            except Exception as e:
                logging.warning(f"Error polling order {order_id}: {e}")
                break
                
        return False

    def _place_market_order(self, symbol: str, qty: float, side: OrderSide) -> Optional[str]:
        """Place a simple market order."""
        try:
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            order = self.trading_client.submit_order(market_order_data)
            order_id = str(getattr(order, 'id', 'unknown'))
            logging.info(f"Market order placed: {order_id}")
            return order_id
        except Exception as e:
            logging.error(f"Market order failed for {symbol}: {e}", exc_info=True)
            return None

    def _place_market_order_with_fallback(self, symbol: str, qty: float, side: OrderSide) -> Optional[str]:
        """Place market order with quantity reduction fallback for insufficient buying power."""
        try:
            return self._place_market_order(symbol, qty, side)
        except Exception as e:
            if self._is_insufficient_buying_power_error(e):
                # Reduce qty by 10% for final attempt
                reduced_qty = round(qty * 0.90, 6)
                logging.warning(
                    f"Market order failed for {symbol} due to insufficient buying power. "
                    f"Final attempt with 10% lower qty: {reduced_qty}"
                )
                print(f"   ⚠️  {symbol}: Market order insufficient buying power, final attempt with 10% lower qty ({reduced_qty})")
                
                try:
                    return self._place_market_order(symbol, reduced_qty, side)
                except Exception as e2:
                    logging.error(f"Final market order also failed for {symbol}: {e2}", exc_info=True)
                    return None
            else:
                logging.error(f"Market order fallback failed for {symbol}: {e}", exc_info=True)
                return None

    def _is_insufficient_buying_power_error(self, error: Exception) -> bool:
        """Check if error is due to insufficient buying power (Alpaca error code 40310000)."""
        error_str = str(error)
        match = re.search(r'"code":\s*40310000', error_str)
        return match is not None

    def wait_for_settlement(
        self, 
        sell_orders: List[Dict], 
        max_wait_time: int = 60, 
        poll_interval: float = 2.0
    ) -> bool:
        """
        Wait for sell orders to settle by polling their status.
        
        Args:
            sell_orders: List of order dictionaries with 'order_id' keys
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            True if all orders settled, False if timeout
        """
        if not sell_orders:
            return True
            
        order_ids = [order['order_id'] for order in sell_orders if 'order_id' in order]
        if not order_ids:
            return True
        
        # Skip waiting when market is closed and ignore_market_hours is True
        market_open = is_market_open(self.trading_client)
        if not market_open and self.ignore_market_hours:
            logging.info(f"Market closed with ignore_market_hours=True, assuming immediate settlement")
            return True
            
        logging.info(f"Waiting for settlement of {len(order_ids)} sell orders...")
        start_time = time.time()
        settled_orders = set()
        
        while time.time() - start_time < max_wait_time:
            # Check status of all pending orders
            for order_id in order_ids:
                if order_id in settled_orders:
                    continue
                    
                try:
                    order = self.trading_client.get_order_by_id(order_id)
                    status = getattr(order, 'status', 'unknown')
                    
                    if status in ['filled', 'canceled', 'rejected']:
                        settled_orders.add(order_id)
                        logging.info(f"Order {order_id} settled with status: {status}")
                        
                except Exception as e:
                    logging.warning(f"Error checking status of order {order_id}: {e}")
                    # Consider the order settled if we can't check its status
                    settled_orders.add(order_id)
            
            # All orders settled
            if len(settled_orders) == len(order_ids):
                elapsed = time.time() - start_time
                logging.info(f"All sell orders settled in {elapsed:.1f} seconds")
                return True
                
            # Wait before next poll
            time.sleep(poll_interval)
        
        # Timeout reached
        unsettled_count = len(order_ids) - len(settled_orders)
        logging.warning(f"Settlement timeout: {unsettled_count} orders still pending after {max_wait_time}s")
        return False
