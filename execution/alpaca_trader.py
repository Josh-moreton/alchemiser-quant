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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Centralized logging setup
from core.logging_utils import setup_logging
setup_logging()
# Alpaca imports
from alpaca.trading.client import TradingClient

# Alpaca order enums
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Import UnifiedDataProvider
from core.data_provider import UnifiedDataProvider
from core.config import Config

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables

# Load configuration
config = Config()
logging_config = config['logging']

# Configure logging
from core.s3_utils import S3FileHandler
from typing import List
import logging

handlers: List[logging.Handler] = [logging.StreamHandler()]

# Add S3 handler for logs
if logging_config['alpaca_log'].startswith('s3://'):
    s3_handler = S3FileHandler(logging_config['alpaca_log'])
    s3_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    handlers.append(s3_handler)
else:
    handlers.append(logging.FileHandler(logging_config['alpaca_log']))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)

def is_market_open(trading_client):
    clock = trading_client.get_clock()
    return clock.is_open

class AlpacaTradingBot:
    """Alpaca Trading Bot for Nuclear Strategy"""

    def __init__(self, paper_trading=None):
        """
        Initialize Alpaca trading bot using UnifiedDataProvider for all data access.
        Uses config.yaml for trading mode and endpoints.
        
        Args:
            paper_trading (bool, optional): Override config setting for paper trading. 
                                          If None, uses config.yaml setting.
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

        logging.info(f"\U0001F3E6 Trading Mode: {'PAPER' if self.paper_trading else 'LIVE'} (from CLI mode)")

                # Use UnifiedDataProvider for all Alpaca data access
        self.data_provider = UnifiedDataProvider(
            paper_trading=self.paper_trading
        )
        self.trading_client = self.data_provider.trading_client  # For order placement
        logging.info(f"Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}")
    
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
    
    def place_order(
        self, symbol: str, qty: float, side: OrderSide, 
        max_retries: int = 3, poll_timeout: int = 30, poll_interval: float = 2.0, 
        slippage_bps: float = 0.3
    ) -> Optional[str]:
        """
        Place a limit order with a small slippage buffer. Fallback to market order if not filled.
        
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
                
                # Place order directly (market hours check is handled in main.py)
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
        Rebalance portfolio to match target allocations with minimal trading.
        Sells all reductions first, waits for settlement, then buys.
        """
        try:
            # Get initial account info and positions
            account_info = self.get_account_info()
            if not account_info:
                logging.error("Could not get account information")
                return []
            
            portfolio_value = account_info['portfolio_value']
            buying_power = account_info.get('buying_power', account_info['cash'])
            
            # Use only (1-cash_reserve_pct) of buying power for allocations
            from core.config import Config
            config = Config()
            cash_reserve_pct = config['alpaca'].get('cash_reserve_pct', 0.05)
            usable_buying_power = buying_power * (1 - cash_reserve_pct)
            
            current_positions = self.get_positions()

            # Calculate current allocations
            current_allocations = {
                symbol: pos['market_value'] / portfolio_value
                for symbol, pos in current_positions.items()
            }
            
            # Calculate target values based on PORTFOLIO VALUE (not buying power!)
            # Allocations are percentages of total portfolio value
            target_values = {
                symbol: portfolio_value * weight 
                for symbol, weight in target_portfolio.items()
            }
            
            all_symbols = set(target_portfolio.keys()) | set(current_allocations.keys())
            trades_needed = []
            for symbol in sorted(all_symbols):
                target_weight = target_portfolio.get(symbol, 0.0)
                current_weight = current_allocations.get(symbol, 0.0)
                allocation_diff = abs(current_weight - target_weight) * 100
                
                # Only show positions that need significant changes
                if allocation_diff > 1.0 or target_weight == 0.0 or current_weight == 0.0:
                    change_direction = "→" if abs(allocation_diff) < 0.1 else ("↗️" if target_weight > current_weight else "↘️")
                    print(f"   {symbol}: {current_weight:.1%} {change_direction} {target_weight:.1%} (Δ{allocation_diff:.1f}pp)")
                    trades_needed.append(symbol)
                
            if not trades_needed:
                print("   ✅ All positions within tolerance")
                
            # --- PRE-CHECK: If all positions are within allocation tolerance, skip trading ---
            all_within_tolerance = True
            for symbol in sorted(target_portfolio.keys()):
                target_weight = target_portfolio.get(symbol, 0.0) * 100.0  # percent
                current_weight = current_allocations.get(symbol, 0.0) * 100.0  # percent
                allocation_diff = abs(current_weight - target_weight)
                if allocation_diff > 1.0:
                    all_within_tolerance = False
                    break
            if all_within_tolerance:
                print("✅ No trades needed - portfolio already balanced")
                return []
            
            # --- PHASE 1: Sells ---
            orders_executed = []
            sells_needed = False
            sells_summary = []
            
            for symbol, pos in current_positions.items():
                sell_qty = 0  # Initialize sell_qty for each position
                target_value = target_values.get(symbol, 0.0)
                current_value = pos['market_value']
                # If not in target portfolio, sell entire position
                if target_value == 0.0:
                    sells_needed = True
                    sell_qty = pos['qty']
                    sells_summary.append(f"{symbol}: Selling entire position ({sell_qty} shares)")
                else:
                    # Calculate percentage weights for both current and target
                    current_weight = (current_value / portfolio_value) * 100
                    target_weight = (target_value / portfolio_value) * 100
                    allocation_diff = abs(current_weight - target_weight)
                    
                    # Only sell excess if allocation difference is greater than 1.0 percentage point
                    # AND we actually have excess (current > target)
                    if allocation_diff > 1.0:
                        excess_value = current_value - target_value
                        # Only sell if we have excess (positive excess_value)
                        if excess_value > 0:
                            sells_needed = True
                            current_price = self.get_current_price(symbol)
                            sell_qty = min(round(excess_value / current_price, 6), pos['qty'])
                            sells_summary.append(f"{symbol}: Selling {sell_qty} shares (${excess_value:.0f} excess)")
                
                if sell_qty > 0:
                    current_price = self.get_current_price(symbol)
                    order_id = self.place_order(symbol, sell_qty, OrderSide.SELL)
                    if order_id:
                        orders_executed.append({
                            'symbol': symbol,
                            'side': OrderSide.SELL,
                            'qty': sell_qty,
                            'order_id': order_id,
                            'estimated_value': sell_qty * current_price
                        })
                    else:
                        logging.error(f"❌ {symbol}: Failed to place sell order")
            
            # Display sell summary
            if sells_summary:
                print("📉 Sell Orders:")
                for summary in sells_summary:
                    print(f"   {summary}")
            else:
                print("📉 No sells needed")

            # Wait for settlement and refresh account info
            if sells_needed and orders_executed:
                print("⏳ Waiting for settlement...")
                time.sleep(10)
                account_info = self.get_account_info()
                portfolio_value = account_info['portfolio_value']
                buying_power = account_info.get('buying_power', account_info['cash'])
                current_positions = self.get_positions()

            # --- PHASE 2: Buys ---
            # Check if any buys are actually needed (allocation difference > 1.0 percentage point)
            buys_needed = False
            for symbol in target_portfolio.keys():
                target_value = target_values[symbol]
                current_value = current_positions.get(symbol, {}).get('market_value', 0.0)
                current_weight = (current_value / portfolio_value) * 100
                target_weight = (target_value / portfolio_value) * 100
                allocation_diff = abs(current_weight - target_weight)
                if target_value - current_value > 1.0 and allocation_diff > 1.0:
                    buys_needed = True
                    break
            
            # If no buys needed, skip buy phase
            if not buys_needed:
                print("📈 No buys needed")
            else:
                # Use actual cash available after sells, but respect cash reserve
                account_info_after_sells = self.get_account_info()
                total_cash_available = account_info_after_sells.get('cash', 0.0)
                # Apply cash reserve to available cash
                available_cash = total_cash_available * (1 - cash_reserve_pct)
                current_positions_after_sells = self.get_positions()
                
                # STEP 1: Collect all buy orders needed
                buy_orders_planned = []
                buy_summary = []
                total_cash_needed = 0.0

                MIN_ORDER_COST = 1.0  # Alpaca minimum order cost

                # Sort by target weight (largest first) to prioritize important positions
                for symbol in sorted(target_portfolio.keys(), key=lambda x: target_portfolio[x], reverse=True):
                    target_value = target_values[symbol]
                    current_value = 0.0
                    if symbol in current_positions_after_sells:
                        current_value = current_positions_after_sells[symbol].get('market_value', 0.0)
                    value_to_buy = target_value - current_value

                    # Calculate allocation difference in percentage points
                    current_weight = (current_value / portfolio_value) * 100
                    target_weight = (target_value / portfolio_value) * 100
                    allocation_diff = abs(current_weight - target_weight)

                    if value_to_buy > 1.0 and allocation_diff > 1.0:
                        current_price = self.get_current_price(symbol)
                        remaining_cash = available_cash - total_cash_needed

                        # Calculate how much we can actually buy with remaining cash
                        actual_value_to_buy = min(value_to_buy, remaining_cash)
                        buy_qty = round(actual_value_to_buy / current_price, 6)
                        required_cash = buy_qty * current_price

                        # Minimum order cost check
                        if required_cash < MIN_ORDER_COST:
                            continue

                        # Simple check: can we afford this order with available cash?
                        # Use small tolerance (1 cent) to handle floating point precision issues
                        total_after_order = total_cash_needed + required_cash
                        can_afford = total_after_order <= (available_cash + 0.01)

                        if buy_qty > 0 and can_afford:
                            buy_orders_planned.append({
                                'symbol': symbol,
                                'qty': buy_qty,
                                'value_needed': value_to_buy,
                                'value_to_buy': actual_value_to_buy,
                                'required_cash': required_cash,
                                'allocation_diff': allocation_diff
                            })
                            total_cash_needed += required_cash
                            buy_summary.append(f"{symbol}: Buying {buy_qty} shares (${actual_value_to_buy:.0f})")
                    elif value_to_buy <= 1.0 or allocation_diff <= 1.0:
                        pass  # Already at target
                
                # Display buy summary and execute
                if buy_summary:
                    print("📈 Buy Orders:")
                    for summary in buy_summary:
                        print(f"   {summary}")
                
                # STEP 2: Submit all buy orders at once
                if buy_orders_planned:
                    for order_plan in buy_orders_planned:
                        symbol = order_plan['symbol']
                        buy_qty = order_plan['qty']
                        required_cash = order_plan['required_cash']
                        
                        order_id = self.place_order(symbol, buy_qty, OrderSide.BUY)
                        if order_id:
                            orders_executed.append({
                                'symbol': symbol,
                                'side': OrderSide.BUY,
                                'qty': buy_qty,
                                'order_id': order_id,
                                'estimated_value': required_cash
                            })

            # Simple summary
            if orders_executed:
                sell_count = sum(1 for o in orders_executed if (hasattr(o['side'], 'value') and o['side'].value == 'sell') or str(o['side']).upper() == 'SELL')
                buy_count = len(orders_executed) - sell_count
                print(f"✅ Executed {len(orders_executed)} orders ({buy_count} buys, {sell_count} sells)")
            else:
                print("✅ No trades needed - portfolio already balanced")
                
            return orders_executed

        except Exception as e:
            print(f"❌ Error rebalancing portfolio: {e}")
            logging.error(f"Error rebalancing portfolio: {e}")
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
