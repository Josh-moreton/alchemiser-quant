#!/usr/bin/env python3
"""
Alpaca Trading Bot
Executes trades based on nuclear trading signals using Alpaca paper trading account
"""

import os
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Centralized logging setup
from core.logging_utils import setup_logging
from core.data_provider import UnifiedDataProvider
from core.config import Config

# Alpaca imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Initialize logging once
setup_logging()

def is_market_open(trading_client):
    clock = trading_client.get_clock()
    return clock.is_open

class AlpacaTradingBot:
    """Alpaca Trading Bot for Nuclear Strategy"""

    def __init__(self, paper_trading=None, ignore_market_hours=False):
        """
        Initialize Alpaca trading bot using UnifiedDataProvider for all data access.
        Uses config.yaml for trading mode and endpoints.
        
        Args:
            paper_trading (bool, optional): Override config setting for paper trading. 
                                          If None, uses config.yaml setting.
            ignore_market_hours (bool, optional): Whether to ignore market hours when placing orders.
                                               Default False.
        """
        from core.config import Config
        config = Config()
        alpaca_cfg = config['alpaca']
        
        # Use parameter if provided, otherwise default to paper trading for safety
        if paper_trading is not None:
            self.paper_trading = paper_trading
        else:
            self.paper_trading = True  # Default to paper trading for safety
            
        self.endpoint = alpaca_cfg.get('endpoint', 'https://api.alpaca.markets')
        self.paper_endpoint = alpaca_cfg.get('paper_endpoint', 'https://paper-api.alpaca.markets/v2')
        
        # Store the ignore_market_hours setting
        self.ignore_market_hours = ignore_market_hours

        # Log trading mode to file only
        logging.info(f"Trading Mode: {'PAPER' if self.paper_trading else 'LIVE'} (from CLI mode)")
        
        # Display trading mode cleanly to user
        print(f"🏦 Trading Mode: {'PAPER' if self.paper_trading else 'LIVE'} (from CLI mode)")

        # Use UnifiedDataProvider for all Alpaca data access
        self.data_provider = UnifiedDataProvider(
            paper_trading=self.paper_trading
        )
        self.trading_client = self.data_provider.trading_client  # For order placement
        
        # Log to file
        logging.info(f"Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}")
        # User-facing message
        print("Successfully retrieved Alpaca paper trading keys")
        print(f"Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}")
    
    def get_account_info(self) -> Dict:
        """Get account information via UnifiedDataProvider, returns dict for compatibility"""
        account = self.data_provider.get_account_info()
        if not account:
            return {}
        return {
            'account_number': getattr(account, 'account_number', 'N/A'),
            'portfolio_value': float(getattr(account, 'portfolio_value', 0) or 0),
            'buying_power': float(getattr(account, 'buying_power', 0) or 0),
            'cash': float(getattr(account, 'cash', 0) or 0),
            'day_trade_count': getattr(account, 'day_trade_count', 0),
            'status': getattr(account, 'status', 'unknown')
        }
    
    def get_positions(self) -> Dict:
        """Get current positions via UnifiedDataProvider, returns dict for compatibility"""
        positions = self.data_provider.get_positions()
        position_dict = {}
        if not positions:
            return position_dict
        for position in positions:
            position_dict[getattr(position, 'symbol', 'unknown')] = {
                'qty': float(getattr(position, 'qty', 0) or 0),
                'market_value': float(getattr(position, 'market_value', 0) or 0),
                'cost_basis': float(getattr(position, 'cost_basis', 0) or 0),
                'unrealized_pl': float(getattr(position, 'unrealized_pl', 0) or 0),
                'unrealized_plpc': float(getattr(position, 'unrealized_plpc', 0) or 0),
                'current_price': float(getattr(position, 'current_price', 0) or 0)
            }
        return position_dict
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol via UnifiedDataProvider"""
        return self.data_provider.get_current_price(symbol)
    
    def calculate_position_size(self, symbol: str, portfolio_weight: float, account_value: float) -> float:
        """
        Calculate position size based on portfolio weight (fractional shares supported)
        
        Args:
            symbol: Stock symbol
            portfolio_weight: Target weight (0.0 to 1.0)
            account_value: Total account value
        Returns:
            Number of shares to buy/sell (float for fractional shares)
        """
        try:
            current_price = self.get_current_price(symbol)
            if current_price <= 0:
                return 0.0
            # Calculate target dollar amount based on strategy allocation of full account value
            target_value = account_value * portfolio_weight
            # Calculate shares (fractional)
            shares = round(target_value / current_price, 6)  # 6 decimals is safe for Alpaca
            logging.info(f"Position calculation for {symbol}: "
                        f"Target weight: {portfolio_weight:.1%}, "
                        f"Target value: ${target_value:.2f}, "
                        f"Price: ${current_price:.2f}, "
                        f"Shares: {shares}")
            return shares
        except Exception as e:
            logging.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    def wait_for_settlement(self, sell_orders: List[Dict], max_wait_time: int = 60, poll_interval: float = 2.0) -> bool:
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

    def place_order(
        self, symbol: str, qty: float, side: OrderSide, 
        max_retries: int = 3, poll_timeout: int = 30, poll_interval: float = 2.0, 
        slippage_bps: float = 0.3
    ) -> Optional[str]:
        """
        Place a limit order with a small slippage buffer. Fallback to market order if not filled.
        If ignore_market_hours is set, will use a market order directly when market is closed.
        
        Args:
            symbol: Stock symbol
            qty: Quantity of shares (float for fractional shares)
            side: OrderSide.BUY or OrderSide.SELL
            max_retries: Maximum number of retry attempts
        Returns:
            Order ID if successful, None if failed
        """
        if qty <= 0:
            logging.warning(f"Invalid quantity for {symbol}: {qty}")
            return None

        # Check if market is open
        market_open = is_market_open(self.trading_client)
        
        # For closed market + ignore_market_hours, use market order directly
        if not market_open and self.ignore_market_hours:
            logging.info(f"Market closed but ignore_market_hours=True, using market order for {symbol}")
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
        
        # Don't place orders when market is closed (unless ignoring market hours)
        if not market_open and not self.ignore_market_hours:
            logging.warning(f"Market is closed. Order for {symbol} not placed.")
            return None

        # Standard limit order flow for open market
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                current_price = self.get_current_price(symbol)
                if current_price <= 0:
                    logging.error(f"Invalid current price for {symbol}")
                    return None

                # Calculate limit price with slippage buffer
                if side == OrderSide.BUY:
                    limit_price = round(current_price * (1 + slippage_bps / 100), 2)
                else:
                    limit_price = round(current_price * (1 - slippage_bps / 100), 2)

                logging.info(f"Placing LIMIT {side.value} order for {symbol}: qty={qty}, limit_price={limit_price}")

                limit_order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
                
                # Place order
                order = self.trading_client.submit_order(limit_order_data)
                order_id = str(getattr(order, 'id', 'unknown'))
                order_status = getattr(order, 'status', 'unknown')

                # Poll for order status
                poll_start = time.time()
                while time.time() - poll_start < poll_timeout:
                    polled_order = self.trading_client.get_order_by_id(order_id)
                    polled_status = getattr(polled_order, 'status', 'unknown')
                    if polled_status == "filled":
                        logging.info(f"Limit order filled: {order_id}")
                        return order_id
                    elif polled_status in ("canceled", "rejected"):
                        logging.warning(f"Limit order {order_id} was {polled_status}")
                        break
                    time.sleep(poll_interval)

                # If not filled, cancel and retry with wider slippage
                self.trading_client.cancel_order_by_id(order_id)
                logging.warning(f"Limit order {order_id} not filled in time, canceled. Retrying with wider slippage.")
                slippage_bps *= 2  # Double the slippage for next attempt

            except Exception as e:
                logging.error(f"Exception placing limit order for {symbol}: {e}", exc_info=True)
                if attempt == max_retries:
                    # As a last resort, fallback to market order
                    try:
                        logging.warning(f"Falling back to MARKET order for {symbol}")
                        market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=qty,
                            side=side,
                            time_in_force=TimeInForce.DAY
                        )
                        order = self.trading_client.submit_order(market_order_data)
                        return str(getattr(order, 'id', 'unknown'))
                    except Exception as e2:
                        logging.error(f"Market order also failed for {symbol}: {e2}", exc_info=True)
                        return None
        return None
    
    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
        """
        Rebalance portfolio to match target allocations.
        
        Process:
        1. Calculate targets and current allocations based on portfolio value
        2. Calculate deltas (what needs buying/selling)
        3. Round down all values to ensure we stay within buying power
        4. Execute all sells first, wait for settlement, then execute all buys
        
        Args:
            target_portfolio: Dict of {symbol: weight} where weights sum to ~1.0
            
        Returns:
            List of order dictionaries for executed trades
        """
        try:
            print("🔄 Starting portfolio rebalancing...")
            logging.info("🔄 Starting portfolio rebalancing...")
            
            # Get account information
            account_info = self.get_account_info()
            if not account_info:
                print("❌ Unable to get account information")
                logging.error("❌ Unable to get account information")
                return []
            
            portfolio_value = account_info.get('portfolio_value', 0.0)
            cash = account_info.get('cash', 0.0)
            
            print(f"📊 Portfolio Value: ${portfolio_value:,.2f} | Available Cash: ${cash:,.2f}")

            # Get current positions
            current_positions = self.get_positions()

            # STEP 1: Calculate target and current allocations based on portfolio value
            target_values = {
                symbol: portfolio_value * weight 
                for symbol, weight in target_portfolio.items()
            }
            
            current_values = {
                symbol: pos.get('market_value', 0.0) 
                for symbol, pos in current_positions.items()
            }
            
            # Display allocations
            print(f"🎯 Target vs Current Allocations:")
            all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
            for symbol in sorted(all_symbols):
                target_weight = target_portfolio.get(symbol, 0.0)
                target_value = target_values.get(symbol, 0.0)
                current_value = current_values.get(symbol, 0.0)
                current_weight = current_value / portfolio_value if portfolio_value > 0 else 0.0
                
                print(f"   {symbol:>4}: Target {target_weight:>5.1%} (${target_value:>8,.2f}) | Current {current_weight:>5.1%} (${current_value:>8,.2f})")
                logging.info(f"   {symbol}: Target {target_weight:.1%} (${target_value:.2f}) | Current {current_weight:.1%} (${current_value:.2f})")

            # STEP 2: Calculate deltas (what needs buying/selling)
            sell_orders_plan = []
            buy_orders_plan = []
            total_proceeds_expected = 0.0
            total_cash_needed = 0.0
            
            print(f"📊 Calculating order plan...")
            
            # Calculate sells (positions to reduce or eliminate)
            for symbol, pos in current_positions.items():
                target_value = target_values.get(symbol, 0.0)
                current_value = current_values[symbol]
                
                if current_value > target_value + 1.0:  # Need to sell (with $1 tolerance)
                    value_to_sell = current_value - target_value
                    current_price = self.get_current_price(symbol)
                    
                    if current_price <= 0:
                        logging.error(f"Cannot get price for {symbol}, skipping")
                        continue
                    
                    # Round DOWN shares to sell to be conservative
                    max_shares = pos['qty']
                    shares_to_sell = min(int(value_to_sell / current_price * 1000000) / 1000000, max_shares)  # Round down to 6 decimals
                    
                    if shares_to_sell > 0:
                        estimated_proceeds = shares_to_sell * current_price
                        sell_orders_plan.append({
                            'symbol': symbol,
                            'qty': shares_to_sell,
                            'estimated_proceeds': estimated_proceeds,
                            'reason': 'entire position' if target_value == 0 else f'excess ${value_to_sell:.2f}'
                        })
                        total_proceeds_expected += estimated_proceeds
            
            # Calculate buys (positions to increase or add)
            for symbol, target_value in target_values.items():
                current_value = current_values.get(symbol, 0.0)
                
                if target_value > current_value + 1.0:  # Need to buy (with $1 tolerance)
                    value_to_buy = target_value - current_value
                    current_price = self.get_current_price(symbol)
                    
                    if current_price <= 0:
                        logging.error(f"Cannot get price for {symbol}, skipping")
                        continue
                    
                    buy_orders_plan.append({
                        'symbol': symbol,
                        'value_needed': value_to_buy,
                        'price': current_price
                    })
                    total_cash_needed += value_to_buy
            
            # STEP 3: Adjust buy orders to fit available cash (round down)
            projected_cash = cash + total_proceeds_expected
            
            print(f"💰 Cash Analysis:")
            print(f"   Current cash: ${cash:.2f}")
            print(f"   Expected proceeds: ${total_proceeds_expected:.2f}")
            print(f"   Projected cash: ${projected_cash:.2f}")
            print(f"   Cash needed for targets: ${total_cash_needed:.2f}")
            
            if total_cash_needed > projected_cash:
                # Scale down buy orders proportionally
                scale_factor = projected_cash / total_cash_needed if total_cash_needed > 0 else 0
                print(f"⚠️  Insufficient cash, scaling down buys by {scale_factor:.1%}")
                
                for buy_plan in buy_orders_plan:
                    buy_plan['value_needed'] *= scale_factor
            
            # Convert buy plans to actual quantities (round DOWN)
            final_buy_orders = []
            for buy_plan in buy_orders_plan:
                shares_to_buy = int(buy_plan['value_needed'] / buy_plan['price'] * 1000000) / 1000000  # Round down to 6 decimals
                if shares_to_buy > 0:
                    final_buy_orders.append({
                        'symbol': buy_plan['symbol'],
                        'qty': shares_to_buy,
                        'estimated_cost': shares_to_buy * buy_plan['price']
                    })
            
            # Display plan
            print(f"📋 Execution Plan:")
            print(f"   Sells: {len(sell_orders_plan)} orders, ${total_proceeds_expected:.2f} proceeds")
            print(f"   Buys: {len(final_buy_orders)} orders, ${sum(o['estimated_cost'] for o in final_buy_orders):.2f} cost")
            
            orders_executed = []
            
            # STEP 4: Execute all sells first
            print("📉 Executing Sell Orders:")
            if sell_orders_plan:
                for sell_plan in sell_orders_plan:
                    symbol = sell_plan['symbol']
                    qty = sell_plan['qty']
                    print(f"   {symbol}: Selling {qty} shares ({sell_plan['reason']})")
                    
                    order_id = self.place_order(symbol, qty, OrderSide.SELL)
                    if order_id:
                        orders_executed.append({
                            'symbol': symbol,
                            'side': OrderSide.SELL,
                            'qty': qty,
                            'order_id': order_id,
                            'estimated_value': sell_plan['estimated_proceeds']
                        })
                        print(f"   ✅ {symbol}: Sell order placed (ID: {order_id})")
                    else:
                        print(f"   ❌ {symbol}: Failed to place sell order")
                        logging.error(f"Failed to place sell order for {symbol}")
            else:
                print("   No sells needed")
            
            # Wait for settlement
            if sell_orders_plan:
                # Skip waiting when market is closed and ignore_market_hours is True
                market_open = is_market_open(self.trading_client)
                if not market_open and self.ignore_market_hours:
                    print("📝 Market closed with ignore_market_hours=True, skipping settlement wait")
                    logging.info("Market closed with ignore_market_hours=True, skipping settlement wait")
                    
                    # When market is closed, Alpaca doesn't update cash balance for pending orders
                    # So we use projected cash (current cash + expected proceeds) instead of querying account
                    sell_proceeds = sum(o.get('estimated_value', 0) for o in orders_executed if o.get('side') == OrderSide.SELL)
                    # Refresh account info to get the most current cash, but add our sell proceeds to it
                    account_info = self.get_account_info()
                    current_cash = account_info.get('cash', 0.0)
                    available_cash = current_cash + sell_proceeds
                    print(f"💰 Cash after orders: ${current_cash:.2f} (actual) + ${sell_proceeds:.2f} (pending sells) = ${available_cash:.2f}")
                else:
                    print("⏳ Waiting for sell order settlement...")
                    sell_orders = [o for o in orders_executed if o['side'] == OrderSide.SELL]
                    settlement_success = self.wait_for_settlement(sell_orders, max_wait_time=60, poll_interval=2.0)
                    
                    if not settlement_success:
                        logging.warning("Some sell orders may not have settled completely")
                    
                    # Refresh account info
                    account_info = self.get_account_info()
                    available_cash = account_info.get('cash', 0.0)
                    print(f"💰 Cash after settlement: ${available_cash:.2f}")
            else:
                available_cash = cash
            
            # STEP 5: Execute all buys
            print("📈 Executing Buy Orders:")
            if final_buy_orders:
                for buy_plan in final_buy_orders:
                    symbol = buy_plan['symbol']
                    qty = buy_plan['qty']
                    estimated_cost = buy_plan['estimated_cost']
                    
                    if estimated_cost <= available_cash:
                        print(f"   {symbol}: Buying {qty} shares (${estimated_cost:.2f})")
                        
                        order_id = self.place_order(symbol, qty, OrderSide.BUY)
                        if order_id:
                            orders_executed.append({
                                'symbol': symbol,
                                'side': OrderSide.BUY,
                                'qty': qty,
                                'order_id': order_id,
                                'estimated_value': estimated_cost
                            })
                            available_cash -= estimated_cost
                            print(f"   ✅ {symbol}: Buy order placed (ID: {order_id})")
                        else:
                            print(f"   ❌ {symbol}: Failed to place buy order")
                            logging.error(f"Failed to place buy order for {symbol}")
                    else:
                        print(f"   ❌ {symbol}: Insufficient cash (need ${estimated_cost:.2f}, have ${available_cash:.2f})")
            else:
                print("   No buys needed")

            print(f"✅ Executed {len(orders_executed)} orders ({sum(1 for o in orders_executed if o['side'] == OrderSide.BUY)} buys, {sum(1 for o in orders_executed if o['side'] == OrderSide.SELL)} sells)")
            logging.info(f"✅ Rebalancing complete. Orders executed: {len(orders_executed)}")
            
            if orders_executed:
                logging.info("📋 Summary of executed orders:")
                for order in orders_executed:
                    logging.info(f"   {order['side'].value.lower()} {order['qty']} {order['symbol']} (${order['estimated_value']:.2f})")
            
            return orders_executed

        except Exception as e:
            print(f"❌ Error rebalancing portfolio: {e}")
            logging.error(f"❌ Error rebalancing portfolio: {e}")
            import traceback
            logging.error(f"Stack trace: {traceback.format_exc()}")
            return []
    
    def read_nuclear_signals(self) -> List[Dict]:
        """Read the latest nuclear trading signals from the alerts file"""
        try:
            signals = []
            config = Config()
            alerts_file = config['logging']['nuclear_alerts_json']
            
            from core.s3_utils import get_s3_handler
            s3_handler = get_s3_handler()
            
            if alerts_file.startswith('s3://'):
                # Read from S3
                content = s3_handler.read_text(alerts_file)
                if not content:
                    logging.warning(f"Alerts file not found or empty: {alerts_file}")
                    return signals
                lines = content.strip().split('\n')
            else:
                # Read from local file
                if not os.path.exists(alerts_file):
                    logging.warning(f"Alerts file not found: {alerts_file}")
                    return signals
                
                with open(alerts_file, 'r') as f:
                    lines = f.readlines()
            
            # Get signals from the last 5 minutes to group portfolio signals
            cutoff_time = datetime.now() - timedelta(minutes=5)
            
            for line in lines:
                try:
                    signal = json.loads(line.strip())
                    signal_time = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
                    
                    if signal_time >= cutoff_time:
                        signals.append(signal)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logging.warning(f"Error parsing signal line: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logging.error(f"Error reading nuclear signals: {e}")
            return []
    
    def parse_portfolio_from_signals(self, signals: List[Dict]) -> Dict[str, float]:
        """
        Parse portfolio allocation from nuclear signals
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            Dict of {symbol: weight} for target portfolio
        """
        portfolio = {}
        single_buy_signals = []
        
        for signal in signals:
            if signal.get('action') != 'BUY':
                continue
            
            symbol = signal.get('symbol')
            reason = signal.get('reason', '')
            
            # Extract allocation percentage from reason
            import re
            allocation_match = re.search(r'(\d+\.?\d*)%', reason)
            
            if allocation_match and symbol:
                allocation_pct = float(allocation_match.group(1))
                weight = allocation_pct / 100.0
                portfolio[symbol] = weight
                logging.info(f"Parsed signal: {symbol} -> {weight:.1%}")
            elif symbol:
                # This is a single BUY signal without percentage - save for potential 100% allocation
                single_buy_signals.append((symbol, reason))
                logging.info(f"Found single BUY signal: {symbol} - {reason}")
        
        # If no portfolio allocations were found but we have single BUY signals,
        # treat the first (most recent) single BUY as 100% allocation
        if not portfolio and single_buy_signals:
            symbol, reason = single_buy_signals[0]  # Use the first/most recent signal
            portfolio[symbol] = 1.0  # 100% allocation
            logging.info(f"✅ Single signal handling: {symbol} -> 100% allocation (reason: {reason})")
        
        return portfolio
    
    def execute_nuclear_strategy(self) -> Tuple[bool, List[Dict]]:
        """
        Execute trades based on the latest nuclear strategy signals
        
        Returns:
            Tuple where the first element indicates success and the second
            element is the list of executed order dictionaries.
        """
        try:
            logging.info("🚀 Executing Nuclear Strategy with Alpaca")
            
            # Read latest signals
            signals = self.read_nuclear_signals()
            if not signals:
                logging.warning("⚠️ No recent signals found - unable to execute strategy")
                return False, []
            
            logging.info(f"Found {len(signals)} recent signals")
            
            # Parse target portfolio
            target_portfolio = self.parse_portfolio_from_signals(signals)
            if not target_portfolio:
                logging.warning("⚠️ No valid portfolio allocation found in signals - unable to execute")
                return False, []
            
            logging.info(f"Target Portfolio: {target_portfolio}")
            
            # Validate target portfolio
            total_allocation = sum(target_portfolio.values())
            if abs(total_allocation - 1.0) > 0.05:  # Allow 5% tolerance
                logging.warning(f"⚠️ Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")
            
            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                logging.error("❌ Failed to get account information - aborting strategy execution")
                return False, []
                
            # Validate we have sufficient data for pricing
            missing_prices = []
            for symbol in target_portfolio.keys():
                price = self.get_current_price(symbol)
                if price <= 0:
                    missing_prices.append(symbol)
            
            if missing_prices:
                logging.error(f"❌ Unable to get prices for symbols: {missing_prices} - aborting execution")
                return False, []
            
            # Execute rebalancing
            orders = self.rebalance_portfolio(target_portfolio)

            if orders:
                logging.info(f"✅ Portfolio rebalanced - {len(orders)} orders executed")
                for order in orders:
                    logging.info(f"   {order['side'].value} {order['qty']} {order['symbol']} (Order ID: {order['order_id']}, Value: ${order['estimated_value']:.2f})")
                # Log trade execution
                self.log_trade_execution(target_portfolio, orders, account_info)
                return True, orders
            else:
                logging.info("ℹ️ No trades needed - portfolio already aligned with strategy")
                return True, []
                
        except Exception as e:
            logging.error(f"💥 Critical error executing nuclear strategy: {e}")
            import traceback
            logging.error(f"Stack trace: {traceback.format_exc()}")
            return False, []
    
    def log_trade_execution(self, target_portfolio: Dict[str, float], orders: List[Dict], account_info: Dict):
        """Log trade execution details"""
        try:
            # Convert OrderSide enum to string for JSON serialization
            serializable_orders = []
            for order in orders:
                serializable_orders.append({
                    'symbol': order['symbol'],
                    'side': order['side'].value if hasattr(order['side'], 'value') else str(order['side']),
                    'qty': order['qty'],
                    'order_id': order['order_id'],
                    'estimated_value': order['estimated_value']
                })
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'account_value': account_info.get('portfolio_value', 0),
                'target_portfolio': target_portfolio,
                'orders_executed': serializable_orders,
                'paper_trading': self.paper_trading
            }
            config = Config()
            log_file = config['logging']['alpaca_trades_json']
            
            from core.s3_utils import get_s3_handler
            s3_handler = get_s3_handler()
            
            if log_file.startswith('s3://'):
                # Write to S3
                s3_handler.append_text(log_file, json.dumps(trade_log) + '\n')
            else:
                # Write to local file
                with open(log_file, 'a') as f:
                    f.write(json.dumps(trade_log) + '\n')
        except Exception as e:
            logging.error(f"Error logging trade execution: {e}")
    
def main():
    """Main function for testing"""
    try:
        # Initialize bot - will read ALPACA_PAPER_TRADING from environment
        bot = AlpacaTradingBot()
        
        # Execute nuclear strategy
        success = bot.execute_nuclear_strategy()
        
        if success:
            print("\n✅ Nuclear strategy execution completed successfully!")
        else:
            print("\n❌ Nuclear strategy execution failed!")
        
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        print(f"❌ Error: {e}")
