#!/usr/bin/env python3
"""
Order Manager for Alpaca Trading.

Encapsulates order placement, dynamic limit price calculation, and settlement
waiting.
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
    - Safe position liquidation using Alpaca's liquidation API
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
        
        The strategy starts conservative and progressively becomes more aggressive:
        - Step 0: Start at bid (sell) or ask (buy) for immediate fill potential
        - Step 1: Move slightly toward market
        - Step 2+: Move progressively closer to market price
        - Final step: Use market price (bid for sell, ask for buy)
        
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
        # Validate inputs
        if bid <= 0 or ask <= 0 or bid >= ask:
            logging.warning(f"Invalid bid/ask: bid={bid}, ask={ask}")
            # Use the available price if one is invalid
            if side == OrderSide.BUY:
                return round(ask if ask > 0 else bid, 2)
            else:
                return round(bid if bid > 0 else ask, 2)

        spread = ask - bid
        mid = (bid + ask) / 2

        # If final step, use market price for immediate execution
        if step >= max_steps:
            return round(ask if side == OrderSide.BUY else bid, 2)

        if side == OrderSide.BUY:
            # Start at ask and work toward mid, then toward ask again
            if step == 0:
                # First attempt: slightly below ask for better price
                price = ask - min(tick_size, spread * 0.1)
            else:
                # Progressive steps toward ask (market price)
                progress = step / max_steps
                price = mid + (ask - mid) * progress
        else:  # SELL
            # Start at bid and work toward mid, then toward bid again  
            if step == 0:
                # First attempt: slightly above bid for better price
                price = bid + min(tick_size, spread * 0.1)
            else:
                # Progressive steps toward bid (market price)
                progress = step / max_steps
                price = mid - (mid - bid) * progress

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

    def liquidate_position(self, symbol: str) -> Optional[str]:
        """
        Liquidate an entire position using Alpaca's position liquidation API.
        This is safer than manual sell orders as it prevents overselling.
        
        Args:
            symbol: Symbol to liquidate
            
        Returns:
            Order ID if successful, None if failed
        """
        try:
            logging.info(f"Liquidating entire position for {symbol}")
            
            # Use Alpaca's liquidation endpoint - this creates a market order
            # to close the entire position safely
            response = self.trading_client.close_position(symbol)
            
            if response:
                order_id = str(getattr(response, 'id', 'unknown'))
                logging.info(f"Position liquidation order placed for {symbol}: {order_id}")
                return order_id
            else:
                logging.error(f"Failed to liquidate position for {symbol}: No response")
                return None
                
        except Exception as e:
            logging.error(f"Exception liquidating position for {symbol}: {e}", exc_info=True)
            return None

    def get_position_qty(self, symbol: str) -> float:
        """
        Get the actual quantity of shares we own for a symbol.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Quantity of shares owned (float, can be fractional)
        """
        try:
            positions = self.trading_client.get_all_positions()
            for position in positions:
                if getattr(position, 'symbol', '') == symbol:
                    return float(getattr(position, 'qty', 0))
            return 0.0
        except Exception as e:
            logging.error(f"Error getting position quantity for {symbol}: {e}")
            return 0.0

    def place_safe_sell_order(
        self,
        symbol: str,
        target_qty: float,
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Place a sell order with safety checks to prevent overselling.
        
        Args:
            symbol: Symbol to sell
            target_qty: Desired quantity to sell
            max_retries: Maximum retry attempts
            poll_timeout: Order polling timeout
            poll_interval: Polling interval
            slippage_bps: Slippage buffer in basis points
            
        Returns:
            Order ID if successful, None if failed
        """
        # Get actual position size to prevent overselling
        actual_qty = self.get_position_qty(symbol)
        
        if actual_qty <= 0:
            logging.warning(f"No position found for {symbol}, cannot sell")
            return None
            
        # Cap sell quantity to actual position size to prevent overselling
        safe_qty = min(target_qty, actual_qty)
        
        if safe_qty != target_qty:
            logging.warning(f"Adjusting sell quantity for {symbol}: {target_qty} -> {safe_qty} (actual position)")
        
        # If we're selling the entire position (within 0.1% tolerance), use liquidation API
        tolerance = 0.001  # 0.1% tolerance for rounding
        if actual_qty > 0 and abs(safe_qty - actual_qty) / actual_qty < tolerance:
            logging.info(f"Selling entire position for {symbol}, using liquidation API")
            return self.liquidate_position(symbol)
        
        # For very small positions or if safe_qty equals actual_qty exactly, also use liquidation
        if safe_qty >= actual_qty * 0.999:  # 99.9% or more of position
            logging.info(f"Selling {safe_qty}/{actual_qty} shares ({safe_qty/actual_qty:.1%}) for {symbol}, using liquidation API")
            return self.liquidate_position(symbol)
        
        # Otherwise use regular sell order
        return self.place_limit_or_market(
            symbol, safe_qty, OrderSide.SELL, max_retries, poll_timeout, poll_interval, slippage_bps
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
        
        # For sell orders, validate we don't try to sell more than we own
        if side == OrderSide.SELL:
            actual_qty = self.get_position_qty(symbol)
            if actual_qty <= 0:
                logging.warning(f"No position found for {symbol}, cannot sell")
                return None
            current_qty = min(current_qty, actual_qty)
            if current_qty != qty:
                logging.warning(f"Reduced sell quantity for {symbol}: {qty} -> {current_qty} (max position)")
        
        while attempt <= max_retries:
            try:
                current_price = self.data_provider.get_current_price(symbol)
                if current_price <= 0:
                    logging.error(f"Invalid current price for {symbol}")
                    return None

                bid, ask = self.data_provider.get_latest_quote(symbol)
                tick_size = max(current_price * (slippage_bps / 10000), 0.01)  # Minimum 1 cent
                
                limit_price = self.calculate_dynamic_limit_price(
                    side,
                    bid,
                    ask,
                    step=attempt,
                    tick_size=tick_size,
                    max_steps=max_retries,
                )

                logging.info(
                    f"Placing LIMIT {side.value} order for {symbol}: qty={current_qty}, limit_price={limit_price:.2f} (attempt {attempt + 1}/{max_retries + 1})"
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

                # Poll for order status with shorter timeout for aggressive attempts
                poll_time = max(poll_timeout - (attempt * 5), 10)  # Reduce timeout with each attempt
                if self._poll_order_status(order_id, poll_time, poll_interval):
                    return order_id

                # If not filled, cancel and retry closer to market
                try:
                    self.trading_client.cancel_order_by_id(order_id)
                    logging.warning(f"Limit order {order_id} not filled in {poll_time}s, retrying with more aggressive pricing")
                except Exception as cancel_e:
                    logging.warning(f"Could not cancel order {order_id}: {cancel_e}")
                
                attempt += 1

            except Exception as e:
                error_code = self._extract_error_code(e)
                error_msg = str(e).lower()
                
                # Handle insufficient buying power by reducing quantity
                if error_code == "40310000":
                    # Check if this is actually a "not allowed to short" error
                    if "not allowed to short" in error_msg:
                        logging.error(f"Account not allowed to short {symbol}. Sell quantity might exceed position.")
                        # For sell orders, this likely means we're trying to sell more than we own
                        if side == OrderSide.SELL:
                            # Re-check actual position and ensure we don't exceed it
                            actual_qty = self.get_position_qty(symbol)
                            if actual_qty <= 0:
                                logging.error(f"No position found for {symbol}, cannot sell")
                                break
                            # Use 95% of actual position to be safe
                            current_qty = round(actual_qty * 0.95, 6)
                            if current_qty <= 0:
                                logging.error(f"Position too small for {symbol}, cannot sell")
                                break
                            logging.warning(f"Reducing sell quantity for {symbol} to avoid short: {qty} -> {current_qty}")
                        else:
                            logging.error(f"Unexpected 'not allowed to short' error for BUY order: {symbol}")
                            break
                    else:
                        # Regular insufficient buying power
                        old_qty = current_qty
                        
                        if side == OrderSide.SELL:
                            # For sell orders, re-check actual position and use 90% of it
                            actual_qty = self.get_position_qty(symbol)
                            current_qty = round(actual_qty * 0.9, 6)
                        else:
                            # For buy orders, reduce by 10%
                            current_qty = round(current_qty * 0.9, 6)
                        
                        if current_qty <= 0:
                            logging.error(f"Quantity reduced to zero for {symbol}, cannot continue")
                            break
                            
                        logging.warning(
                            f"Order failed for {symbol} due to insufficient buying power (code {error_code}). "
                            f"Retrying with reduced qty: {old_qty} -> {current_qty}"
                        )
                        print(f"   ⚠️  {symbol}: Insufficient buying power, retrying with reduced qty ({old_qty} -> {current_qty})")
                    
                    # Don't increment attempt for quantity adjustments
                    continue
                else:
                    logging.error(f"Exception placing limit order for {symbol}: {e}", exc_info=True)
                    attempt += 1

        # If all limit order attempts failed, try a market order as final fallback
        logging.warning(f"All limit order attempts failed for {symbol}. Falling back to MARKET order.")
        return self._place_market_order_with_fallback(symbol, current_qty, side)

    def _extract_error_code(self, error: Exception) -> Optional[str]:
        """Extract Alpaca error code from exception."""
        # Try to get code from APIError directly if available
        if hasattr(error, 'code'):
            return str(getattr(error, 'code'))
        
        # Try to get from error args if it's a dict
        if hasattr(error, 'args') and error.args:
            arg = error.args[0]
            if isinstance(arg, dict) and 'code' in arg:
                return str(arg['code'])
        
        # Fallback to string parsing
        error_str = str(error)
        match = re.search(r'"code":\s*(\d+)', error_str)
        return match.group(1) if match else None

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
            error_code = self._extract_error_code(e)
            error_msg = str(e).lower()
            
            if error_code == "40310000":
                if "not allowed to short" in error_msg and side == OrderSide.SELL:
                    # This is definitely a shorting issue, not buying power
                    logging.error(f"Cannot short {symbol}. Sell quantity exceeds position.")
                    actual_qty = self.get_position_qty(symbol)
                    if actual_qty <= 0:
                        logging.error(f"No position to sell for {symbol}")
                        return None
                    
                    # Use liquidation API instead
                    logging.info(f"Falling back to liquidation API for {symbol}")
                    return self.liquidate_position(symbol)
                    
                else:
                    # Regular buying power issue
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
        return self._extract_error_code(error) == "40310000"

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
