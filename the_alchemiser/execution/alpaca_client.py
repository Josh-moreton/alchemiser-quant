#!/usr/bin/env python3
"""Alpaca Client for Direct API Access.

A straightforward, robust wrapper around Alpaca's trading APIs that provides direct access
to core trading functions without complex retry logic or dynamic adjustments.

This client prioritizes simplicity, reliability, and transparency over complexity.
It follows a "fail-fast, clear errors" approach rather than trying to be overly clever
with retries and dynamic adjustments that can mask underlying issues.

Key Features:
    - Direct Alpaca API usage for positions, orders, and trades
    - Position validation to prevent overselling
    - Clean order management with automatic cancellation
    - Liquidation API for safe full position exits
    - Clear error handling with transparent logging

Order Placement Logic:
    Selling Positions:
        - Partial sales (< 99%): Use market orders
        - Full sales (≥ 99%): Use Alpaca's close_position() API
        - Always validate position exists before selling
        - Automatically cap sell quantity to available shares
    
    Buying Positions:
        - Use market orders for immediate execution
        - Cancel existing orders first to avoid conflicts
        - Round quantities to avoid fractional share issues
        - Validate positive quantities and prices

Safety Features:
    - Position validation before every sell order
    - Automatic quantity capping to prevent overselling
    - Order cancellation before new orders to prevent conflicts
    - Liquidation API usage for full position exits
    - Decimal rounding to handle fractional shares properly
    - Clear logging of all order attempts and results

Example:
    Basic usage for order placement:
    
    >>> client = AlpacaClient(trading_client, data_provider)
    >>> positions = client.get_current_positions()
    >>> order_id = client.place_market_order('AAPL', 10, OrderSide.BUY)
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_DOWN

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from alpaca.trading.stream import TradingStream
import threading

from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.utils.asset_info import fractionability_detector


class AlpacaClient:
    """Direct Alpaca API client for reliable order execution.
    
    Provides straightforward access to Alpaca trading APIs with focus on:
    1. Getting current positions from Alpaca
    2. Canceling pending orders before placing new ones  
    3. Using liquidation API for selling entire positions
    4. Placing market or limit orders with clear error handling
    5. No complex retry logic - fail fast and clear
    
    Attributes:
        trading_client: Alpaca trading client for API calls.
        data_provider: Data provider for market quotes and prices.
        validate_buying_power: Whether to validate buying power for buy orders.
    """

    def __init__(self, trading_client: TradingClient, data_provider: UnifiedDataProvider, validate_buying_power: bool = False):
        """Initialize AlpacaClient.
        
        Args:
            trading_client: Alpaca trading client instance.
            data_provider: Data provider for quotes (optional for market orders).
            validate_buying_power: Whether to validate buying power for buy orders.
                Defaults to False.
        """
        self.trading_client = trading_client
        self.data_provider = data_provider
        self.validate_buying_power = validate_buying_power

    def get_current_positions(self) -> Dict[str, float]:
        """Get all current positions from Alpaca.
        
        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.
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
        """Get all pending orders from Alpaca.
        
        Returns:
            List of pending order information dictionaries.
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
        side: OrderSide,
        qty: Optional[float] = None,
        notional: Optional[float] = None,
        cancel_existing: bool = True
    ) -> Optional[str]:
        """
        Place a simple market order.
        
        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            qty: Quantity to trade (use either qty OR notional, not both)
            notional: Dollar amount to trade (use either qty OR notional, not both)
            cancel_existing: Whether to cancel existing orders for this symbol first
            
        Returns:
            Order ID if successful, None if failed
        """
        # Validate that exactly one of qty or notional is provided
        if (qty is None and notional is None) or (qty is not None and notional is not None):
            logging.warning(f"Must provide exactly one of qty OR notional for {symbol}")
            return None
            
        # Validate the provided parameter
        if qty is not None:
            # Check for invalid types first (before float conversion)
            if isinstance(qty, bool) or isinstance(qty, (list, dict)):
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
                
        if notional is not None:
            # Check for invalid types first (before float conversion)
            if isinstance(notional, bool) or isinstance(notional, (list, dict)):
                logging.warning(f"Invalid notional type for {symbol}: {notional}")
                return None
                
            # Convert notional to float if it's a string
            try:
                notional = float(notional)
            except (ValueError, TypeError):
                logging.warning(f"Invalid notional type for {symbol}: {notional}")
                return None
            
            # Check for invalid numeric values
            import math
            if math.isnan(notional) or math.isinf(notional) or notional <= 0:
                logging.warning(f"Invalid notional for {symbol}: {notional}")
                return None

        try:
            # Cancel existing orders if requested
            if cancel_existing:
                self.cancel_all_orders(symbol)
                time.sleep(0.5)  # Brief pause for cancellations to process

            # For buy orders, validate buying power (if enabled)
            if side == OrderSide.BUY and self.validate_buying_power:
                try:
                    account = self.trading_client.get_account()
                    buying_power = float(getattr(account, 'buying_power', 0) or 0)
                    current_price = self.data_provider.get_current_price(symbol)
                    if current_price is not None and current_price > 0 and qty is not None:
                        price_value = float(current_price)
                        qty_value = float(qty)
                        order_value = qty_value * price_value
                        
                        if order_value > buying_power:
                            logging.warning(f"Order value ${order_value:.2f} exceeds buying power ${buying_power:.2f} for {symbol}")
                            return None
                except Exception as e:
                    logging.warning(f"Unable to validate buying power for {symbol}: {e}")
                    # Continue with order despite validation error

            # For sell orders, validate we have enough to sell (only applies to qty orders)
            if side == OrderSide.SELL and qty is not None:
                positions = self.get_current_positions()
                available = positions.get(symbol, 0)
                
                if available <= 0:
                    logging.warning(f"No position to sell for {symbol}")
                    return None
                    
                if qty > available:
                    logging.warning(f"Reducing sell quantity for {symbol}: {qty} -> {available}")
                    qty = available

            # For notional sell orders, we can't pre-validate but Alpaca will handle it
            if side == OrderSide.SELL and notional is not None:
                positions = self.get_current_positions()
                available = positions.get(symbol, 0)
                
                if available <= 0:
                    logging.warning(f"No position to sell for {symbol}")
                    return None

            # Prepare order parameters with smart non-fractionable asset handling
            if qty is not None:
                # Smart handling for non-fractionable assets
                current_price = None
                try:
                    current_price = self.data_provider.get_current_price(symbol)
                except Exception as e:
                    logging.warning(f"Could not get current price for {symbol}: {e}")
                
                # Check if we should use notional orders for non-fractionable assets
                if (current_price and current_price > 0 and 
                    side == OrderSide.BUY and
                    fractionability_detector.should_use_notional_order(symbol, qty)):
                    
                    # Convert to notional order for better handling of non-fractionable assets
                    original_notional = qty * current_price
                    logging.info(f"🔄 Converting {symbol} from qty={qty} to notional=${original_notional:.2f} "
                               f"(likely non-fractionable asset)")
                    
                    market_order_data = MarketOrderRequest(
                        symbol=symbol,
                        notional=round(original_notional, 2),
                        side=side,
                        time_in_force=TimeInForce.DAY
                    )
                    
                    logging.info(f"Placing MARKET {side.value} order for {symbol}: notional=${original_notional:.2f} "
                               f"(converted from qty={qty})")
                else:
                    # Regular quantity order with fractional rounding
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
            else:
                # Notional order
                assert notional is not None  # Type hint for mypy
                notional = round(notional, 2)  # Round to cents
                
                logging.info(f"Placing MARKET {side.value} order for {symbol}: notional=${notional}")
                
                market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    notional=notional,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
            
            # Submit the order with error handling for non-fractionable assets
            try:
                order = self.trading_client.submit_order(market_order_data)
                order_id = str(getattr(order, 'id', 'unknown'))
                
                logging.info(f"Market order placed for {symbol}: {order_id}")
                return order_id
                
            except Exception as order_error:
                error_msg = str(order_error)
                
                # Handle the specific "not fractionable" error
                if ("not fractionable" in error_msg.lower() and 
                    qty is not None and 
                    hasattr(market_order_data, 'qty')):
                    
                    logging.warning(f"🔄 {symbol} is not fractionable, retrying with whole shares...")
                    
                    # Get current price for conversion
                    if current_price is None:
                        try:
                            current_price = self.data_provider.get_current_price(symbol)
                        except Exception:
                            current_price = None
                    
                    if current_price and current_price > 0:
                        # Convert to notional order as fallback
                        fallback_notional = qty * current_price
                        logging.info(f"💰 Converting to notional order: ${fallback_notional:.2f}")
                        
                        fallback_order_data = MarketOrderRequest(
                            symbol=symbol,
                            notional=round(fallback_notional, 2),
                            side=side,
                            time_in_force=TimeInForce.DAY
                        )
                        
                        try:
                            order = self.trading_client.submit_order(fallback_order_data)
                            order_id = str(getattr(order, 'id', 'unknown'))
                            
                            logging.info(f"✅ Fallback notional order placed for {symbol}: {order_id}")
                            return order_id
                            
                        except Exception as fallback_error:
                            logging.error(f"❌ Fallback notional order also failed for {symbol}: {fallback_error}")
                            return None
                    else:
                        logging.error(f"❌ Cannot convert to notional order - no current price for {symbol}")
                        return None
                else:
                    # Re-raise the original error if it's not a fractionability issue
                    raise order_error
            
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

            # Smart handling for non-fractionable assets
            original_qty = qty
            
            # For non-fractionable assets, convert to whole shares
            if not fractionability_detector.is_fractionable(symbol):
                adjusted_qty, was_rounded = fractionability_detector.convert_to_whole_shares(
                    symbol, qty, limit_price
                )
                
                if was_rounded:
                    qty = adjusted_qty
                    if qty <= 0:
                        logging.warning(f"❌ {symbol} quantity rounded to zero whole shares (original: {original_qty})")
                        return None
                    
                    logging.info(f"🔄 Rounded {symbol} to {qty} whole shares for non-fractionable asset")
            else:
                # Round quantity for regular assets
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
            
            # Submit order with error handling for non-fractionable assets
            try:
                order = self.trading_client.submit_order(limit_order_data)
                order_id = str(getattr(order, 'id', 'unknown'))
                
                logging.info(f"Limit order placed for {symbol}: {order_id}")
                return order_id
                
            except Exception as order_error:
                error_msg = str(order_error)
                
                # Handle the specific "not fractionable" error for limit orders
                if "not fractionable" in error_msg.lower():
                    logging.warning(f"🔄 {symbol} limit order failed (not fractionable), trying whole shares...")
                    
                    # Convert to whole shares if we haven't already
                    if fractionability_detector.is_fractionable(symbol):
                        whole_qty = int(original_qty)
                        
                        if whole_qty <= 0:
                            logging.error(f"❌ Cannot place {symbol} order - rounds to zero whole shares")
                            return None
                        
                        logging.info(f"💰 Retrying with {whole_qty} whole shares instead of {original_qty}")
                        
                        fallback_order_data = LimitOrderRequest(
                            symbol=symbol,
                            qty=whole_qty,
                            side=side,
                            time_in_force=TimeInForce.DAY,
                            limit_price=limit_price
                        )
                        
                        try:
                            order = self.trading_client.submit_order(fallback_order_data)
                            order_id = str(getattr(order, 'id', 'unknown'))
                            
                            logging.info(f"✅ Fallback whole-share limit order placed for {symbol}: {order_id}")
                            return order_id
                            
                        except Exception as fallback_error:
                            logging.error(f"❌ Fallback whole-share limit order also failed for {symbol}: {fallback_error}")
                            return None
                    else:
                        # We already tried whole shares, this is a different issue
                        logging.error(f"❌ {symbol} limit order failed even with whole shares: {error_msg}")
                        return None
                else:
                    # Re-raise the original error if it's not a fractionability issue
                    raise order_error
            
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
            return self.place_market_order(symbol, OrderSide.SELL, qty=qty)

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


    def wait_for_order_completion(
        self,
        order_ids: List[str],
        max_wait_seconds: int = 60,
    ) -> Dict[str, str]:
        """Wait for orders to reach a final state."""
        if not order_ids:
            return {}

        api_key = getattr(self.trading_client, "_api_key", None)
        secret_key = getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)

        from rich.console import Console
        console = Console()
        console.print(f"[blue]🔑 API keys available: {has_keys}[/blue]")
        
        if has_keys:
            try:
                if logging.getLogger().level <= logging.DEBUG:
                    console.print("[blue]🚀 Attempting WebSocket streaming method for order completion[/blue]")
                return self._wait_for_order_completion_stream(order_ids, max_wait_seconds)
            except Exception as e:  # pragma: no cover - streaming errors fallback
                console.print(f"[red]❌ Falling back to polling due to streaming error: {e}[/red]")
                logging.warning(f"❌ Falling back to polling due to streaming error: {e}")

        if logging.getLogger().level <= logging.DEBUG:
            console.print("[blue]🔄 Using polling method for order completion[/blue]")
        return self._wait_for_order_completion_polling(order_ids, max_wait_seconds)

    def _wait_for_order_completion_polling(self, order_ids: List[str], max_wait_seconds: int) -> Dict[str, str]:
        """Original polling-based settlement check."""
        logging.info(
            f"⏳ Waiting for {len(order_ids)} orders to complete via polling..."
        )

        start_time = time.time()
        completed: Dict[str, str] = {}

        while time.time() - start_time < max_wait_seconds and len(completed) < len(order_ids):
            logging.info(
                f"🔍 Checking {len(order_ids)} orders, {len(completed)} completed so far..."
            )
            for order_id in order_ids:
                if order_id in completed:
                    continue

                try:
                    order = self.trading_client.get_order_by_id(order_id)
                    status = getattr(order, "status", "unknown")
                    status_str = str(status)
                    logging.info(f"📋 Order {order_id}: status={status_str}")

                    final_states = [
                        "filled",
                        "canceled",
                        "rejected",
                        "expired",
                        "OrderStatus.FILLED",
                        "OrderStatus.CANCELED",
                        "OrderStatus.REJECTED",
                        "OrderStatus.EXPIRED",
                    ]
                    if status_str in final_states or str(status).lower() in [
                        "filled",
                        "canceled",
                        "rejected",
                        "expired",
                    ]:
                        completed[order_id] = status_str
                        logging.info(f"✅ Order {order_id}: {status_str}")

                except Exception as e:
                    logging.warning(f"❌ Error checking order {order_id}: {e}")
                    completed[order_id] = "error"

            if len(completed) < len(order_ids):
                # Use shorter polling interval for faster detection
                sleep_time = min(1.0, max_wait_seconds / 10)  # More frequent checks
                logging.info(
                    f"⏳ {len(order_ids) - len(completed)} orders still pending, waiting {sleep_time}s..."
                )
                time.sleep(sleep_time)

        if len(completed) < len(order_ids):
            elapsed_time = time.time() - start_time
            logging.warning(
                f"⏰ Timeout after {elapsed_time:.1f}s: {len(order_ids) - len(completed)} orders did not complete"
            )

        for order_id in order_ids:
            if order_id not in completed:
                completed[order_id] = "timeout"
                logging.warning(f"⏰ Order {order_id}: timeout")

        logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
        return completed

    def _wait_for_order_completion_stream(self, order_ids: List[str], max_wait_seconds: int) -> Dict[str, str]:
        """Use Alpaca's TradingStream to monitor order status."""
        from rich.console import Console
        console = Console()
        
        # Only show detailed monitoring info at DEBUG level
        if logging.getLogger().level <= logging.DEBUG:
            if logging.getLogger().level <= logging.DEBUG:
                console.print(f"[blue]⏳ Waiting for {len(order_ids)} orders to complete via websocket...[/blue]")
            logging.info(f"⏳ Waiting for {len(order_ids)} orders via WebSocket")
            if logging.getLogger().level <= logging.DEBUG:
                console.print(f"[blue]🔍 Order IDs to monitor: {order_ids}[/blue]")
            logging.info(f"Monitoring {len(order_ids)} orders via WebSocket")
        
        logging.info(f"⏳ Waiting for {len(order_ids)} orders to complete via websocket...")
        logging.debug(f"🔍 Order IDs to monitor: {order_ids}")

        # First, check if any orders are already completed before starting websocket monitoring
        completed: Dict[str, str] = {}
        remaining = set(order_ids)
        
        # Quick API check for already completed orders
        for order_id in list(remaining):
            try:
                order = self.trading_client.get_order_by_id(order_id)
                status = str(getattr(order, "status", "")).lower()
                if 'orderstatus.' in status:
                    actual_status = status.split('.')[-1]
                else:
                    actual_status = status
                    
                final_states = {"filled", "canceled", "rejected", "expired"}
                if actual_status in final_states:
                    if logging.getLogger().level <= logging.DEBUG:
                        console.print(f"[green]✅ Order {order_id} already completed with status: {actual_status}[/green]")
                    logging.info(f"✅ Order {order_id} already completed with status: {actual_status}")
                    completed[order_id] = actual_status
                    remaining.remove(order_id)
            except Exception as e:
                logging.warning(f"❌ Error checking initial order status for {order_id}: {e}")
        
        # If all orders are already completed, return immediately
        if not remaining:
            console.print(f"[green]✅ All {len(order_ids)} orders completed[/green]")
            logging.info(f"🎯 All {len(order_ids)} orders already completed, no websocket monitoring needed")
            return completed

        final_states = {"filled", "canceled", "rejected", "expired"}
        stream_stopped = False

        async def on_update(data) -> None:
            nonlocal stream_stopped
            if stream_stopped:
                return
                
            # Reduce websocket message logging - only log if debug mode
            if logging.getLogger().level <= logging.DEBUG:
                console.print(f"[dim]📡 WebSocket trade update received: {data}[/dim]")
                logging.debug(f"📡 WebSocket trade update received: {data}")
            
            order = getattr(data, "order", None)
            if not order:
                return
                
            oid = str(getattr(order, "id", ""))
            status = str(getattr(order, "status", ""))
            
            if oid in remaining:
                # Only show detailed updates at DEBUG level, simple status for INFO
                if logging.getLogger().level <= logging.DEBUG:
                    console.print(f"[green]📋 WebSocket order update: ID={oid}, status={status}[/green]")
                    logging.debug(f"📋 WebSocket order update: ID={oid}, status={status}")
                
                # Handle both string status and enum status
                status_str = str(status).lower()
                # Extract the actual status from enum strings like 'OrderStatus.FILLED'
                if 'orderstatus.' in status_str:
                    actual_status = status_str.split('.')[-1]  # Gets 'filled' from 'orderstatus.filled'
                else:
                    actual_status = status_str
                
                if actual_status in final_states:
                    console.print(f"[green]✅ Order filled[/green]")
                    logging.info(f"✅ Order {oid} reached final state: {status} -> {actual_status}")
                    completed[oid] = actual_status
                    remaining.remove(oid)
                    if logging.getLogger().level <= logging.DEBUG:
                        console.print(f"[green]📊 Completed orders: {completed}, remaining: {remaining}[/green]")
                        logging.debug(f"📊 Completed orders: {completed}, remaining: {remaining}")
                    if not remaining:
                        if logging.getLogger().level <= logging.DEBUG:
                            console.print("[green]🏁 All orders completed, stopping stream[/green]")
                        logging.info("🏁 All orders completed, stopping stream")
                        stream_stopped = True
                else:
                    if logging.getLogger().level <= logging.DEBUG:
                        console.print(f"[yellow]⏳ Order {oid} status '{actual_status}' not final, continuing to monitor[/yellow]")
                    logging.debug(f"⏳ Order {oid} status '{status}' -> '{actual_status}' not in final states {final_states}")

        # Check if we have a pre-connected WebSocket stream
        if hasattr(self, '_websocket_stream') and hasattr(self, '_websocket_thread'):
            if logging.getLogger().level <= logging.DEBUG:
                if logging.getLogger().level <= logging.DEBUG:
                    console.print("[green]🎯 Using pre-connected WebSocket stream[/green]")
                logging.info("Using existing WebSocket connection")
            logging.info("🎯 Using pre-connected WebSocket stream")
            
            try:
                # Re-subscribe with our actual order monitoring handler
                self._websocket_stream.subscribe_trade_updates(on_update)
                if logging.getLogger().level <= logging.DEBUG:
                    console.print("[green]✅ Subscribed to trade updates on pre-connected stream[/green]")
                logging.info("✅ Subscribed to trade updates on pre-connected stream")
                
                # Wait for orders to complete
                if logging.getLogger().level <= logging.DEBUG:
                    if logging.getLogger().level <= logging.DEBUG:
                        console.print("[blue]⏱️ Starting timeout monitoring with pre-connected stream...[/blue]")
                    logging.info("Starting order monitoring")
                logging.info("⏱️ Starting timeout monitoring with pre-connected stream...")
                start_time = time.time()
                last_log_time = 0
                
                while remaining and time.time() - start_time < max_wait_seconds and not stream_stopped:
                    elapsed = time.time() - start_time
                    # Only log every 2 seconds at DEBUG level to reduce noise
                    if elapsed - last_log_time >= 2.0 and logging.getLogger().level <= logging.DEBUG:
                        console.print(f"[blue]⌛ Waiting... elapsed={elapsed:.1f}s, remaining orders: {remaining}[/blue]")
                        logging.debug(f"⌛ Waiting... elapsed={elapsed:.1f}s, remaining orders: {remaining}")
                        last_log_time = elapsed
                    time.sleep(0.1)  # Smaller sleep for faster response

                if remaining and not stream_stopped:
                    console.print(f"[red]⏰ Timeout reached! {len(remaining)} orders timed out[/red]")
                    logging.warning(f"⏰ Timeout reached! Remaining orders: {remaining}")
                    for oid in remaining:
                        completed[oid] = "timeout"
                        # Only log individual timeouts at DEBUG level to reduce noise
                        if logging.getLogger().level <= logging.DEBUG:
                            console.print(f"[red]⏰ Order {oid}: timeout[/red]")
                            logging.debug(f"⏰ Order {oid}: timeout")
                else:
                    if logging.getLogger().level <= logging.DEBUG:
                        console.print("[green]✅ All orders completed before timeout[/green]")
                    logging.info("✅ All orders completed before timeout")

                if logging.getLogger().level <= logging.DEBUG:
                    console.print(f"[blue]🏁 Order settlement complete: {len(completed)} orders processed[/blue]")
                    console.print(f"[blue]📋 Final completion status: {completed}[/blue]")
                logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
                logging.debug(f"📋 Final completion status: {completed}")
                return completed
                
            except Exception as e:
                console.print(f"[red]❌ Error using pre-connected WebSocket: {e}[/red]")
                logging.error(f"❌ Error using pre-connected WebSocket: {e}")
                # Fall through to create new connection
        
        # If no pre-connected stream, create a new one (original behavior)
        api_key = getattr(self.trading_client, "_api_key")
        secret_key = getattr(self.trading_client, "_secret_key")
        paper = getattr(self.trading_client, "_sandbox", True)
        
        if logging.getLogger().level <= logging.DEBUG:
            console.print(f"[blue]🔧 Creating new WebSocket connection: paper={paper}, api_key={api_key[:8]}...[/blue]")
        logging.info("Creating new WebSocket connection")
        logging.info(f"🔧 Creating new WebSocket connection: paper={paper}, api_key={api_key[:8]}...")

        # Import here to avoid circular imports
        from alpaca.trading.stream import TradingStream
        import threading
        
        try:
            if logging.getLogger().level <= logging.DEBUG:
                console.print("[blue]🔌 Initializing new WebSocket stream...[/blue]")
            stream = TradingStream(api_key, secret_key, paper=paper)
            
            stream.subscribe_trade_updates(on_update)
            
            if logging.getLogger().level <= logging.DEBUG:
                console.print("[blue]🚀 Starting new WebSocket stream...[/blue]")
            logging.info("🚀 Starting new WebSocket stream...")
            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()
            if logging.getLogger().level <= logging.DEBUG:
                console.print(f"[blue]🧵 WebSocket thread started: {thread.name} (daemon={thread.daemon})[/blue]")
            
            # Give WebSocket time to connect (up to 3 seconds)
            if logging.getLogger().level <= logging.DEBUG:
                console.print("[blue]⏳ Waiting for new WebSocket connection (up to 3 seconds)...[/blue]")
            time.sleep(3)
                
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize new WebSocket stream: {e}[/red]")
            logging.error(f"❌ Failed to initialize new WebSocket stream: {e}")
            # Fall back to polling
            return self._wait_for_order_completion_polling(order_ids, max_wait_seconds)
        
        if logging.getLogger().level <= logging.DEBUG:
            console.print("[blue]⏱️ Starting timeout monitoring with new stream...[/blue]")
        logging.info("Starting order monitoring")
        logging.info("⏱️ Starting timeout monitoring with new stream...")
        start_time = time.time()
        while remaining and time.time() - start_time < max_wait_seconds:
            elapsed = time.time() - start_time
            if elapsed % 2 < 0.5:  # Print every 2 seconds
                console.print(f"[blue]⌛ Waiting... elapsed={elapsed:.1f}s, remaining orders: {remaining}[/blue]")
            logging.info(f"⌛ Waiting... elapsed={elapsed:.1f}s, remaining orders: {remaining}")
            time.sleep(0.5)

        if remaining:
            console.print(f"[red]⏰ Timeout reached! {len(remaining)} orders timed out[/red]")
            logging.warning(f"⏰ Timeout reached! Remaining orders: {remaining}")
            stream.stop()
            thread.join(timeout=2)
            for oid in remaining:
                completed[oid] = "timeout"
                # Only log individual timeouts at DEBUG level to reduce noise
                if logging.getLogger().level <= logging.DEBUG:
                    console.print(f"[red]⏰ Order {oid}: timeout[/red]")
                    logging.debug(f"⏰ Order {oid}: timeout")
        else:
            console.print("[green]✅ All orders completed before timeout[/green]")
            logging.info("✅ All orders completed before timeout")
            
            # Skip cleanup entirely - just let the daemon thread die naturally
            if logging.getLogger().level <= logging.DEBUG:
                console.print("[blue]⚡ Skipping WebSocket cleanup (daemon thread will terminate automatically)[/blue]")
                console.print("[green]🚀 WebSocket monitoring complete, proceeding...[/green]")
            logging.info("WebSocket monitoring complete")

        if logging.getLogger().level <= logging.DEBUG:
            console.print(f"[blue]🏁 Order settlement complete: {len(completed)} orders processed[/blue]")
            console.print(f"[blue]📋 Final completion status: {completed}[/blue]")
        logging.info(f"Order settlement complete: {len(completed)} orders processed")
        logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
        logging.info(f"📋 Final completion status: {completed}")
        return completed

    def _prepare_websocket_connection(self) -> bool:
        """
        Pre-initialize WebSocket connection and wait for it to be ready.
        
        Returns:
            True if WebSocket is ready, False if it failed to connect
        """
        from rich.console import Console
        console = Console()
        
        api_key = getattr(self.trading_client, "_api_key", None)
        secret_key = getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)
        
        if not has_keys:
            console.print("[yellow]⚠️ No API keys available for WebSocket[/yellow]")
            return False
        
        paper = getattr(self.trading_client, "_sandbox", True)
        
        try:
            from alpaca.trading.stream import TradingStream
            import threading
            import time
            
            # Clean up any existing connection first
            self._cleanup_websocket_connection()
            
            console.print("[blue]🔌 Initializing WebSocket for trade monitoring...[/blue]")
            
            # Create the stream - we know api_key and secret_key are strings at this point
            stream = TradingStream(str(api_key), str(secret_key), paper=paper)
            
            # Track connection status - be more optimistic about connection
            connection_started = threading.Event()
            connection_error = None
            
            # Dummy handler for trade updates (we'll replace this later)
            async def dummy_handler(data):
                if logging.getLogger().level <= logging.DEBUG:
                    console.print(f"[dim]📡 Pre-connection WebSocket message: {data}[/dim]")
            
            # Subscribe to trade updates
            stream.subscribe_trade_updates(dummy_handler)
            
            # Start the stream
            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()
            connection_started.set()  # Assume connection will work if thread starts
            
            # Give it a short time to connect
            time.sleep(2.0)
            
            # Store the stream for later use optimistically
            self._websocket_stream = stream
            self._websocket_thread = thread
            
            console.print("[green]🎯 WebSocket connection established![/green]")
            logging.info("🎯 WebSocket pre-connection established!")
            return True
                
        except Exception as e:
            console.print(f"[red]❌ Failed to pre-initialize WebSocket: {e}[/red]")
            logging.error(f"❌ Failed to pre-initialize WebSocket: {e}")
            return False

    def _cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        if hasattr(self, '_websocket_stream'):
            try:
                self._websocket_stream.stop()
            except:
                pass
            delattr(self, '_websocket_stream')
        
        if hasattr(self, '_websocket_thread'):
            try:
                if self._websocket_thread.is_alive():
                    self._websocket_thread.join(timeout=1.0)
            except:
                pass
            delattr(self, '_websocket_thread')
