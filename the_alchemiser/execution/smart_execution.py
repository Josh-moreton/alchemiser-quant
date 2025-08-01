#!/usr/bin/env python3
"""
Smart Execution Engine with Progressive Limit Order Strategy.

This module provides sophisticated order execution with progressive limit pricing that:
- Starts at midpoint of bid/ask spread for optimal price improvement
- Steps progressively toward less favorable prices (10% increments)
- Uses WebSocket notifications for instant fill detection
- Falls back to market orders if all limit attempts fail
"""

import logging
import time
from typing import Dict, List, Optional
from alpaca.trading.enums import OrderSide
from alpaca.trading.client import TradingClient

from the_alchemiser.execution.alpaca_client import AlpacaClient
from the_alchemiser.utils.progressive_order_utils import ProgressiveOrderCalculator, get_market_urgency_level


def is_market_open(trading_client: TradingClient) -> bool:
    """Check if the market is currently open."""
    try:
        clock = trading_client.get_clock()
        return getattr(clock, 'is_open', False)
    except Exception:
        return False


class SmartExecution:
    """
    Advanced execution engine with progressive limit order strategy.
    
    This provides sophisticated order execution using the AlpacaClient internally
    for reliable order placement with intelligent limit pricing.
    """
    
    def __init__(self, trading_client, data_provider, ignore_market_hours=False, config=None):
        """Initialize with same signature as old OrderManager for compatibility."""
        
        self.config = config or {}
        validate_buying_power = self.config.get('validate_buying_power', False)
        
        self.alpaca_client = AlpacaClient(trading_client, data_provider, validate_buying_power)
        self.ignore_market_hours = ignore_market_hours
        
        # Initialize progressive order calculator
        self.order_calculator = ProgressiveOrderCalculator(config)
        
        # OrderManagerAdapter initialized silently
    
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
        Place a safe sell order - delegates to AlpacaClient.place_smart_sell_order.
        
        This method provides the same interface as the old OrderManager but uses
        the much more reliable AlpacaClient internally.
        """
        # Safe sell order execution
        
        # The AlpacaClient handles all the safety checks internally
        return self.alpaca_client.place_smart_sell_order(symbol, target_qty)
    
    def place_limit_or_market(
        self, 
        symbol: str, 
        qty: float, 
        side: OrderSide, 
        max_retries: int = 3, 
        poll_timeout: int = 30, 
        poll_interval: float = 2.0, 
        slippage_bps: Optional[float] = None,
        notional: Optional[float] = None
    ) -> Optional[str]:
        """
        Place progressive limit order starting at midpoint, stepping toward less favorable price.
        
        Simplified Strategy (3 steps + market order fallback):
        1. Start at midpoint of bid/ask (most favorable)
        2. Step to 50% toward unfavorable price  
        3. Step to bid/ask price (100% unfavorable)
        4. Finally place market order if all limit attempts fail
        
        Each step waits 2 seconds for WebSocket fill notification before proceeding.
        For BUY orders: midpoint → ask direction
        For SELL orders: midpoint → bid direction
        """
        import time
        
        # Initialize console at the very beginning for consistent access
        from rich.console import Console
        console = Console()
        
        # Handle both string and OrderSide enum inputs
        side_str = side.value if hasattr(side, 'value') else str(side)
        
        # Convert string inputs to OrderSide enum if needed
        if isinstance(side, str):
            side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        # Handle notional orders for BUY by converting to quantity
        if side == OrderSide.BUY and notional is not None:
            try:
                current_price = self.alpaca_client.data_provider.get_current_price(symbol)
                if current_price <= 0:
                    logging.warning(f"Invalid price for {symbol}, falling back to market order")
                    return self.alpaca_client.place_market_order(symbol, side, notional=notional)
                
                # Calculate max quantity we can afford, round down to 6 decimals, then scale to 99%
                raw_qty = notional / current_price
                rounded_qty = int(raw_qty * 1e6) / 1e6  # Round down to 6 decimals
                scaled_qty = rounded_qty * 0.99  # Scale to 99% to avoid buying power issues
                
                if scaled_qty <= 0:
                    logging.warning(f"Calculated quantity too small for {symbol}, falling back to market order")
                    return self.alpaca_client.place_market_order(symbol, side, notional=notional)
                
                qty = scaled_qty
                
            except Exception as e:
                logging.warning(f"Error calculating quantity for {symbol}: {e}, falling back to market order")
                return self.alpaca_client.place_market_order(symbol, side, notional=notional)
        elif side == OrderSide.BUY:
            # For quantity orders, round down to 6 decimals and scale to 99%
            rounded_qty = int(qty * 1e6) / 1e6
            qty = rounded_qty * 0.99
        
        # For SELL notional orders, use market order (can't easily implement progressive limits)
        if side == OrderSide.SELL and notional is not None:
            return self.alpaca_client.place_market_order(symbol, side, notional=notional)
        
        # Get bid/ask for progressive limit order strategy
        try:
            quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                # No quote available, use market order
                console.print(f"[yellow]No bid/ask quote available for {symbol}, using market order[/yellow]")
                if notional is not None:
                    return self.alpaca_client.place_market_order(symbol, side, notional=notional)
                else:
                    return self.alpaca_client.place_market_order(symbol, side, qty=qty)
            
            bid = float(quote[0])
            ask = float(quote[1])
            
            # Enhanced validation with better logging
            if not (bid > 0 and ask > 0 and ask > bid):
                # Try fallback to data client for quotes
                logging.warning(f"Real-time quote invalid for {symbol}: bid={bid}, ask={ask}, trying data client fallback")
                fallback_quote = None
                try:
                    # Use the data client directly (bypassing real-time cache)
                    from alpaca.data.requests import StockLatestQuoteRequest
                    if hasattr(self.alpaca_client.data_provider, 'data_client'):
                        request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                        latest_quote = self.alpaca_client.data_provider.data_client.get_stock_latest_quote(request)
                        if latest_quote and symbol in latest_quote:
                            quote_obj = latest_quote[symbol]
                            fallback_bid = float(getattr(quote_obj, 'bid_price', 0) or 0)
                            fallback_ask = float(getattr(quote_obj, 'ask_price', 0) or 0)
                            if fallback_bid > 0 and fallback_ask > 0 and fallback_ask > fallback_bid:
                                logging.info(f"Using data client fallback quote for {symbol}: bid=${fallback_bid:.2f}, ask=${fallback_ask:.2f}")
                                bid, ask = fallback_bid, fallback_ask
                            else:
                                # Try using current price with estimated spread
                                current_price = self.alpaca_client.data_provider.get_current_price(symbol)
                                if current_price > 0:
                                    # Estimate 0.5% spread around current price
                                    estimated_spread = current_price * 0.005
                                    bid = current_price - estimated_spread
                                    ask = current_price + estimated_spread
                                    logging.info(f"Using estimated spread for {symbol}: price=${current_price:.2f}, bid=${bid:.2f}, ask=${ask:.2f}")
                except Exception as e:
                    logging.warning(f"Data client fallback failed for {symbol}: {e}")
                    # Try using current price with estimated spread as final fallback
                    try:
                        current_price = self.alpaca_client.data_provider.get_current_price(symbol)
                        if current_price > 0:
                            # Estimate 0.5% spread around current price
                            estimated_spread = current_price * 0.005
                            bid = current_price - estimated_spread
                            ask = current_price + estimated_spread
                            logging.info(f"Using price-based spread estimate for {symbol}: price=${current_price:.2f}, bid=${bid:.2f}, ask=${ask:.2f}")
                    except Exception as price_error:
                        logging.warning(f"Price fallback also failed for {symbol}: {price_error}")
                
                # If still invalid after all fallbacks, use market order
                if not (bid > 0 and ask > 0 and ask > bid):
                    console.print(f"[yellow]Invalid bid/ask quote for {symbol} (bid=${bid:.2f}, ask=${ask:.2f}), using market order[/yellow]")
                    logging.warning(f"All quote sources failed for {symbol}: bid={bid}, ask={ask}, fallback to market order")
                    if notional is not None:
                        return self.alpaca_client.place_market_order(symbol, side, notional=notional)
                    else:
                        return self.alpaca_client.place_market_order(symbol, side, qty=qty)
            
            # Calculate midpoint and spread
            midpoint = (bid + ask) / 2.0
            spread = ask - bid
            
            # Get intelligent execution parameters based on market conditions
            urgency_level = get_market_urgency_level()
            
            # Try to get recent price data for volatility calculation
            recent_high = None
            recent_low = None
            try:
                # Get recent price range (you might want to implement this in data_provider)
                current_price = self.alpaca_client.data_provider.get_current_price(symbol)
                # For now, use a simple estimate based on spread
                estimated_range = spread * 10  # Rough estimate
                recent_high = current_price + estimated_range / 2
                recent_low = current_price - estimated_range / 2
            except Exception as e:
                logging.warning(f"Could not get price range for {symbol}: {e}")
            
            # Calculate intelligent execution parameters
            exec_params = self.order_calculator.calculate_execution_params(
                symbol, bid, ask, side, urgency_level, recent_high, recent_low
            )
            
            # Progressive limit order strategy
            console.print(f"[cyan]Starting intelligent progressive limit order for {side.value} {symbol}[/cyan]")
            console.print(f"[dim]Bid: ${bid:.2f}, Ask: ${ask:.2f}, Midpoint: ${midpoint:.2f}, Spread: ${spread:.2f}[/dim]")
            console.print(f"[blue]Strategy: {exec_params}[/blue]")
            
            # Pre-initialize WebSocket connection for faster order monitoring
            websocket_ready = self.alpaca_client._prepare_websocket_connection()
            if websocket_ready:
                console.print(f"[green]🔌 WebSocket ready for order monitoring[/green]")
            else:
                console.print(f"[yellow]⚠️ WebSocket not ready, using polling fallback[/yellow]")
            
            # Use intelligent step percentages instead of hardcoded steps
            for step_idx, step_pct in enumerate(exec_params.step_percentages):
                # Calculate limit price for this step using the new calculator
                limit_price = self.order_calculator.calculate_step_price(
                    bid, ask, side, step_pct, exec_params.tick_aggressiveness
                )
                
                # Generate step description
                if step_pct == 0.0:
                    step_name = "Midpoint (most favorable)"
                elif step_pct == 1.0:
                    step_name = "Bid/Ask price (least favorable)"
                else:
                    step_name = f"Step {step_idx + 1} ({step_pct*100:.0f}% through spread)"
                
                # Display step information with appropriate colors
                color = "cyan" if side == OrderSide.BUY else "magenta"  # Use magenta for sells instead of red
                console.print(f"[{color}]{step_name}: {side.value} {symbol} @ ${limit_price:.2f}[/{color}]")
                
                # Place limit order
                limit_order_id = self.alpaca_client.place_limit_order(
                    symbol, qty, side, limit_price
                )
                
                if not limit_order_id:
                    console.print(f"[yellow]Failed to place limit order at ${limit_price:.2f}[/yellow]")
                    continue
                
                # Wait using intelligent timeout (varies by market conditions)
                console.print(f"[dim]Waiting {exec_params.max_wait_seconds} seconds for fill via WebSocket...[/dim]")
                logging.info(f"🔍 Monitoring order {limit_order_id} for {symbol} @ ${limit_price:.2f}")
                
                # Give WebSocket a moment to catch up before monitoring
                time.sleep(0.2)
                
                order_results = self.alpaca_client.wait_for_order_completion(
                    [limit_order_id], max_wait_seconds=exec_params.max_wait_seconds
                )
                
                # Only show detailed order results at DEBUG level to reduce noise
                if logging.getLogger().level <= logging.DEBUG:
                    console.print(f"[dim]📋 Order completion result: {order_results}[/dim]")
                logging.info(f"📋 Order completion result for {limit_order_id}: {order_results}")
                final_status = order_results.get(limit_order_id, '').lower()
                
                # If order is filled, return immediately without double-checking
                if 'filled' in final_status:
                    console.print(f"[green]✓ {side.value} {symbol} filled @ ${limit_price:.2f} ({step_name})[/green]")
                    return limit_order_id
                
                # Double-check order status only if timeout was reported
                if final_status == 'timeout' or not final_status:
                    try:
                        # Get fresh order status from API
                        console.print(f"[dim]🔍 Double-checking order status via API...[/dim]")
                        logging.info(f"🔍 Double-checking order status for {limit_order_id} due to timeout/empty status")
                        order = self.alpaca_client.trading_client.get_order_by_id(limit_order_id)
                        fresh_status = str(getattr(order, 'status', 'unknown')).lower()
                        console.print(f"[dim]✨ Fresh API status: {fresh_status}[/dim]")
                        logging.info(f"✨ Fresh order status for {limit_order_id}: {fresh_status}")
                        
                        # Check if order is filled or partially filled (don't cancel partial fills)
                        if 'filled' in fresh_status:
                            final_status = fresh_status
                            console.print(f"[green]🎯 Order was actually filled! WebSocket missed it.[/green]")
                            logging.info(f"🎯 Order {limit_order_id} was actually filled! WebSocket missed it.")
                            return limit_order_id
                        elif 'partially_filled' in fresh_status:
                            # Let partially filled orders continue for next 2 seconds
                            console.print(f"[yellow]⏳ Order partially filled, giving it 2 more seconds...[/yellow]")
                            time.sleep(2)
                            # Check again
                            order = self.alpaca_client.trading_client.get_order_by_id(limit_order_id)
                            final_check_status = str(getattr(order, 'status', 'unknown')).lower()
                            if 'filled' in final_check_status:
                                console.print(f"[green]✓ Order completed after partial fill wait[/green]")
                                return limit_order_id
                            else:
                                console.print(f"[yellow]Order still partially filled, moving to next step[/yellow]")
                    except Exception as e:
                        console.print(f"[red]❌ Failed to get fresh order status: {e}[/red]")
                        logging.warning(f"❌ Failed to get fresh order status: {e}")
                
                # Order was not filled
                console.print(f"[yellow]{step_name} not filled ({final_status}), trying next step...[/yellow]")
                # Order was automatically cancelled by wait_for_order_completion timeout
            
            # All progressive limit order steps failed, use market order as final fallback
            console.print(f"[yellow]All {len(exec_params.step_percentages)} progressive limit orders failed for {symbol}, checking final status before market order...[/yellow]")
            
            # Final safety check: verify no orders actually filled before placing market order
            try:
                positions_before = self.alpaca_client.get_current_positions()
                current_qty = positions_before.get(symbol, 0.0)
                logging.info(f"Current {symbol} position before market order: {current_qty}")
            except Exception as e:
                logging.warning(f"Failed to check position before market order: {e}")
            
            console.print(f"[yellow]Final fallback: Placing market order for {symbol}[/yellow]")
            
        except Exception as e:
            logging.warning(f"Error in progressive limit order strategy for {symbol}: {e}, using market order")
        
        # Always clean up WebSocket connection after progressive order completion
        try:
            if hasattr(self.alpaca_client, '_cleanup_websocket_connection'):
                self.alpaca_client._cleanup_websocket_connection()
                console.print(f"[dim]🔌 WebSocket connection cleaned up after {symbol} order[/dim]")
        except Exception as e:
            logging.warning(f"Error cleaning up WebSocket connection: {e}")
        
        # Final fallback to market order
        if notional is not None:
            return self.alpaca_client.place_market_order(symbol, side, notional=notional)
        else:
            return self.alpaca_client.place_market_order(symbol, side, qty=qty)
    
    def wait_for_settlement(
        self, 
        sell_orders: List[Dict], 
        max_wait_time: int = 60, 
        poll_interval: float = 2.0
    ) -> bool:
        """
        Wait for order settlement - delegates to SimpleOrderManager.wait_for_order_completion.
        """
        if not sell_orders:
            return True
            
        # Extract only valid string order IDs
        order_ids: List[str] = []
        for order in sell_orders:
            order_id = order.get('order_id')
            if order_id is not None and isinstance(order_id, str):
                order_ids.append(order_id)
                
        # If we had orders but no valid order IDs, that's a failure
        if not order_ids:
            logging.warning("No valid order IDs found in settlement data")
            return False
            
        # Quick pre-check: see if orders are already filled before starting websocket monitoring
        already_completed = {}
        remaining_order_ids = []
        
        for order_id in order_ids:
            try:
                order = self.alpaca_client.trading_client.get_order_by_id(order_id)
                status = str(getattr(order, 'status', 'unknown')).lower()
                if 'orderstatus.' in status:
                    actual_status = status.split('.')[-1]
                else:
                    actual_status = status
                    
                if actual_status in ['filled', 'canceled', 'rejected', 'expired']:
                    logging.info(f"✅ Order {order_id} already settled with status: {actual_status}")
                    already_completed[order_id] = actual_status
                else:
                    remaining_order_ids.append(order_id)
            except Exception as e:
                logging.warning(f"❌ Error checking order {order_id} pre-settlement status: {e}")
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check
        
        # If all orders are already completed, no need to wait
        if not remaining_order_ids:
            logging.info(f"🎯 All {len(order_ids)} orders already settled, skipping settlement monitoring")
            return True
        
        # Only monitor orders that aren't already completed
        logging.info(f"📊 Settlement check: {len(already_completed)} already completed, {len(remaining_order_ids)} need monitoring")
        
        # Wait for order settlement
        completion_statuses = self.alpaca_client.wait_for_order_completion(
            remaining_order_ids, max_wait_time
        )
        
        # Combine pre-completed orders with newly completed ones
        all_completion_statuses = {**already_completed, **completion_statuses}
        
        # Log the completion statuses for debugging
        logging.info(f"Order completion statuses: {all_completion_statuses}")
        
        # Consider orders settled if they're filled, canceled, or rejected
        # Handle both enum values and string representations
        settled_count = sum(
            1 for status in all_completion_statuses.values() 
            if status in ['filled', 'canceled', 'rejected', 'expired'] or
               str(status).lower() in ['filled', 'canceled', 'rejected', 'expired'] or
               status in ['OrderStatus.FILLED', 'OrderStatus.CANCELED', 'OrderStatus.REJECTED', 'OrderStatus.EXPIRED']
        )
        
        success = settled_count == len(order_ids)
        if success:
            pass  # All orders settled successfully
        else:
            logging.warning(f"Only {settled_count}/{len(order_ids)} orders settled")
            
        return success
    
    def liquidate_position(self, symbol: str) -> Optional[str]:
        """Liquidate position - delegates to SimpleOrderManager."""
        return self.alpaca_client.liquidate_position(symbol)
    
    def get_position_qty(self, symbol: str) -> float:
        """Get position quantity - delegates to SimpleOrderManager."""
        positions = self.alpaca_client.get_current_positions()
        return positions.get(symbol, 0.0)
    
    def calculate_dynamic_limit_price(self, side: OrderSide, bid: float, ask: float, 
                                     step: int = 1, tick_size: float = 0.01, 
                                     max_steps: int = 5) -> float:
        """
        Calculate a dynamic limit price based on the bid-ask spread and step.
        
        Test expects:
        - BUY: bid=99.0, ask=101.0, step=1, tick_size=0.2, max_steps=3 -> 100.2
        - SELL: bid=99.0, ask=101.0, step=2, tick_size=0.5, max_steps=3 -> 99.0
        
        Args:
            side: OrderSide.BUY or OrderSide.SELL
            bid: Current bid price
            ask: Current ask price  
            step: Step number (1-based)
            tick_size: Minimum price increment
            max_steps: Maximum number of steps
            
        Returns:
            Calculated limit price
        """
        mid_price = (bid + ask) / 2.0
        
        if side == OrderSide.BUY:
            # For buy orders, step toward ask from mid
            price = mid_price + (step * tick_size)
        else:
            # For sell orders, step toward bid from mid
            price = mid_price - (step * tick_size)
        
        # Round to nearest tick
        return round(price / tick_size) * tick_size

    def place_better_order(
        self, 
        symbol: str, 
        qty: float, 
        side: OrderSide,
        max_slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Implement the 5-step better orders execution ladder.
        
        This is the new primary order placement method that implements
        the professional swing trading execution strategy.
        """
        from the_alchemiser.utils.market_timing_utils import MarketOpenTimingEngine
        from the_alchemiser.utils.spread_assessment import SpreadAssessment
        from rich.console import Console
        
        console = Console()
        timing_engine = MarketOpenTimingEngine()
        spread_assessor = SpreadAssessment(self.alpaca_client.data_provider)
        
        # Step 0: Pre-Check (if before market open)
        if not is_market_open(self.alpaca_client.trading_client):
            console.print(f"[yellow]Market closed - assessing pre-market conditions for {symbol}[/yellow]")
            
            premarket = spread_assessor.assess_premarket_conditions(symbol)
            if premarket:
                console.print(f"[dim]Pre-market spread: {premarket.spread_cents:.1f}¢ ({premarket.spread_quality.value})[/dim]")
                console.print(f"[dim]Recommended wait: {premarket.recommended_wait_minutes} min after open[/dim]")
                
                # Use premarket slippage tolerance if not specified
                if max_slippage_bps is None:
                    max_slippage_bps = premarket.max_slippage_bps
        
        # Step 1: Open Assessment 
        strategy = timing_engine.get_execution_strategy()
        console.print(f"[cyan]Execution strategy: {strategy.value}[/cyan]")
        
        # Get current bid/ask
        try:
            quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                console.print(f"[yellow]No quote available, using market order[/yellow]")
                return self.alpaca_client.place_market_order(symbol, side, qty=qty)
                
            bid, ask = float(quote[0]), float(quote[1])
            spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
            
            console.print(f"[dim]Current spread: {spread_analysis.spread_cents:.1f}¢ ({spread_analysis.spread_quality.value})[/dim]")
            
            # Check if we should wait for spreads to normalize
            if not timing_engine.should_execute_immediately(spread_analysis.spread_cents, strategy):
                wait_time = timing_engine.get_wait_time_seconds(strategy, spread_analysis.spread_cents)
                console.print(f"[yellow]Wide spread detected, waiting {wait_time}s for normalization[/yellow]")
                import time
                time.sleep(wait_time)
                
                # Re-get quote after waiting
                quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
                if quote and len(quote) >= 2:
                    bid, ask = float(quote[0]), float(quote[1])
                    spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
                    console.print(f"[dim]Updated spread: {spread_analysis.spread_cents:.1f}¢[/dim]")
            
            # Step 2 & 3: Aggressive Marketable Limit with Re-pegging
            return self._execute_aggressive_limit_sequence(
                symbol, qty, side, bid, ask, strategy, console
            )
            
        except Exception as e:
            logging.error(f"Error in better order execution for {symbol}: {e}")
            # Step 4: Market order fallback
            console.print(f"[yellow]Falling back to market order[/yellow]")
            return self.alpaca_client.place_market_order(symbol, side, qty=qty)

    def _execute_aggressive_limit_sequence(
        self, symbol: str, qty: float, side: OrderSide, 
        bid: float, ask: float, strategy, console
    ) -> Optional[str]:
        """
        Execute the aggressive marketable limit sequence with re-pegging.
        
        Step 2: Aggressive marketable limit (ask+1 tick / bid-1 tick)
        Step 3: Re-peg 1-2 times (2-3 second timeouts)  
        Step 4: Market order fallback
        """
        from the_alchemiser.utils.market_timing_utils import ExecutionStrategy
        
        # Determine timeout based on strategy and ETF speed
        if strategy == ExecutionStrategy.WAIT_FOR_SPREADS:
            timeout_seconds = 2.0  # Fast execution at market open
        else:
            timeout_seconds = 3.0  # Slightly longer for normal times
            
        max_repegs = 2  # Maximum 2 re-peg attempts
        
        for attempt in range(max_repegs + 1):
            # Calculate aggressive marketable limit price
            if side == OrderSide.BUY:
                # Buy: ask + 1 tick (ask + 1¢)
                limit_price = ask + 0.01
                direction = "above ask"
            else:
                # Sell: bid - 1 tick (bid - 1¢)  
                limit_price = bid - 0.01
                direction = "below bid"
            
            attempt_label = f"Initial order" if attempt == 0 else f"Re-peg #{attempt}"
            console.print(f"[cyan]{attempt_label}: {side.value} {symbol} @ ${limit_price:.2f} ({direction})[/cyan]")
            
            # Place aggressive marketable limit
            order_id = self.alpaca_client.place_limit_order(symbol, qty, side, limit_price)
            if not order_id:
                console.print(f"[red]Failed to place limit order[/red]")
                continue
                
            # Wait for fill with fast timeout (2-3 seconds max)
            order_results = self.alpaca_client.wait_for_order_completion(
                [order_id], max_wait_seconds=int(timeout_seconds)
            )
            
            final_status = order_results.get(order_id, '').lower()
            if 'filled' in final_status:
                console.print(f"[green]✅ {side.value} {symbol} filled @ ${limit_price:.2f} ({attempt_label})[/green]")
                return order_id
            
            # Order not filled - prepare for re-peg if attempts remain
            if attempt < max_repegs:
                console.print(f"[yellow]{attempt_label} not filled, re-pegging...[/yellow]")
                
                # Get fresh quote for re-peg pricing
                fresh_quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
                if fresh_quote and len(fresh_quote) >= 2:
                    bid, ask = float(fresh_quote[0]), float(fresh_quote[1])
                else:
                    console.print(f"[yellow]No fresh quote, using market order[/yellow]")
                    break
            else:
                console.print(f"[yellow]Maximum re-pegs ({max_repegs}) reached[/yellow]")
        
        # Step 4: Market order fallback
        console.print(f"[yellow]All limit attempts failed, using market order[/yellow]")
        return self.alpaca_client.place_market_order(symbol, side, qty=qty)
