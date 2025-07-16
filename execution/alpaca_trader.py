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
from dotenv import load_dotenv

# Alpaca imports

# Alpaca order enums
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Import AlpacaDataProvider
from core.data_provider import AlpacaDataProvider

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/alpaca_trader.log'),
        logging.StreamHandler()
    ]
)
class AlpacaTradingBot:
    """Alpaca Trading Bot for Nuclear Strategy"""

    def __init__(self, paper_trading=None):
        """
        Initialize Alpaca trading bot using AlpacaDataProvider for all data access.
        Args:
            paper_trading (bool, optional): Use paper trading account if True. If None, reads from ALPACA_PAPER_TRADING env variable
        """
        # Determine paper trading mode
        if paper_trading is None:
            env_paper_trading = os.getenv('ALPACA_PAPER_TRADING', 'true').lower()
            self.paper_trading = env_paper_trading in ('true', '1', 'yes', 'on')
        else:
            self.paper_trading = paper_trading

        logging.info(f"\U0001F3E6 Trading Mode: {'PAPER' if self.paper_trading else 'LIVE'} (from {'env variable' if paper_trading is None else 'parameter'})")

        # Use AlpacaDataProvider for all Alpaca data access
        self.data_provider = AlpacaDataProvider(paper_trading=self.paper_trading)
        self.trading_client = self.data_provider.trading_client  # For order placement
        logging.info(f"Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}")
        
        # Portfolio configuration - no cash reserves, invest everything based on strategy
        
        logging.info(f"Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}")
    
    def get_account_info(self) -> Dict:
        """Get account information via AlpacaDataProvider, returns dict for compatibility"""
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
        """Get current positions via AlpacaDataProvider, returns dict for compatibility"""
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
        """Get current price for a symbol via AlpacaDataProvider"""
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
    
    def place_order(self, symbol: str, qty: float, side: OrderSide, max_retries: int = 3, poll_timeout: int = 30, poll_interval: float = 2.0) -> Optional[str]:
        """
        Place a market order (supports fractional shares) with retry logic and detailed Alpaca API response logging.
        
        Args:
            symbol: Stock symbol
            qty: Quantity of shares (float for fractional shares)
            side: OrderSide.BUY or OrderSide.SELL
            max_retries: Maximum number of retry attempts
        Returns:
            Order ID if successful, None if failed
        """
        if os.environ.get("FAST_TEST") == "1":
            poll_timeout = 0
            poll_interval = 0

        if qty <= 0:
            logging.warning(f"Invalid quantity for {symbol}: {qty}")
            return None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
                order = self.trading_client.submit_order(market_order_data)
                # Log the full order response for debugging
                try:
                    order_json = order.__dict__ if hasattr(order, '__dict__') else str(order)
                    logging.debug(f"Alpaca API order response for {symbol}: {order_json}")
                except Exception as log_exc:
                    logging.warning(f"Could not serialize Alpaca order response for {symbol}: {log_exc}")
                order_id = str(getattr(order, 'id', 'unknown'))
                order_status = getattr(order, 'status', 'unknown')
                filled_qty = getattr(order, 'filled_qty', None)
                filled_avg_price = getattr(order, 'filled_avg_price', None)
                submitted_at = getattr(order, 'submitted_at', None)
                logging.info(f"Order placed: {side.value} {qty} shares of {symbol} - Order ID: {order_id}, Status: {order_status}")
                logging.info(f"Order details: filled_qty={filled_qty}, filled_avg_price={filled_avg_price}, submitted_at={submitted_at}")
                # Poll for order status until filled, canceled, or rejected, or timeout
                poll_start = time.time()
                final_status = order_status
                final_filled_qty = filled_qty
                final_filled_avg_price = filled_avg_price
                if order_id != 'unknown' and order_status not in ("filled", "canceled", "rejected"):
                    while time.time() - poll_start < poll_timeout:
                        try:
                            polled_order = self.trading_client.get_order_by_id(order_id)
                            polled_status = getattr(polled_order, 'status', 'unknown')
                            polled_filled_qty = getattr(polled_order, 'filled_qty', None)
                            polled_filled_avg_price = getattr(polled_order, 'filled_avg_price', None)
                            logging.debug(f"Polled order status for {symbol}: {polled_status}, filled_qty={polled_filled_qty}, filled_avg_price={polled_filled_avg_price}")
                            if polled_status in ("filled", "canceled", "rejected"):
                                final_status = polled_status
                                final_filled_qty = polled_filled_qty
                                final_filled_avg_price = polled_filled_avg_price
                                break
                        except Exception as poll_exc:
                            logging.warning(f"Error polling order status for {symbol} (Order ID: {order_id}): {poll_exc}")
                        time.sleep(poll_interval)
                # Log final status
                logging.info(f"Final order status for {symbol}: {final_status}, filled_qty={final_filled_qty}, filled_avg_price={final_filled_avg_price}")
                if final_status == "filled":
                    return order_id
                else:
                    logging.warning(f"Order for {symbol} ({side.value}) was not filled. Final status: {final_status}. Not counting as executed.")
                    return None
            except Exception as e:
                # Log the full exception and any Alpaca API error details
                logging.error(f"Alpaca API Exception placing order for {symbol}: {e}", exc_info=True)
                api_response = getattr(e, 'response', None)
                if api_response is not None:
                    try:
                        logging.error(f"Alpaca API error response: {getattr(api_response, 'text', str(api_response))}")
                    except Exception:
                        pass
                if attempt < max_retries:
                    # Calculate delay: 5 seconds for first retry, then increase
                    delay = 5 + (attempt * 5)  # 5, 10, 15 seconds
                    logging.warning(f"Order failed for {symbol} (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logging.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    # Refresh account info before retry (buying power might have changed)
                    if side == OrderSide.BUY:
                        account_info = self.get_account_info()
                        current_buying_power = account_info.get('buying_power', 0)
                        logging.debug(f"Current buying power before retry: ${current_buying_power:,.2f}")
                else:
                    logging.error(f"Order failed for {symbol} after {max_retries + 1} attempts: {e}")
                    return None
        return None
    
    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
        """
        Rebalance portfolio to match target allocations with minimal trading
        
        Args:
            target_portfolio: Dict of {symbol: weight} where weight is 0.0 to 1.0
            
        Returns:
            List of order dicts for executed orders
        """
        try:
            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                logging.error("Could not get account information")
                return []
            
            portfolio_value = account_info['portfolio_value']
            current_cash = account_info['cash']
            buying_power = account_info.get('buying_power', current_cash)  # Fallback to cash if missing
            
            # Get current positions
            current_positions = self.get_positions()
            
            # Calculate orders needed
            orders_executed = []
            
            logging.info(f"🔄 Starting portfolio rebalance - Portfolio Value: ${portfolio_value:,.2f}, Cash: ${current_cash:,.2f}, Buying Power: ${buying_power:,.2f}")
            
            # Calculate current and target allocations
            current_allocations = {}
            target_allocations = {}
            
            # Calculate current allocations based on market value
            for symbol, position in current_positions.items():
                current_allocations[symbol] = position['market_value'] / portfolio_value
                logging.info(f"Current allocation {symbol}: {current_allocations[symbol]:.1%} (${position['market_value']:,.2f})")
            
            # Calculate target allocations
            for symbol, target_weight in target_portfolio.items():
                target_allocations[symbol] = target_weight
                target_value = portfolio_value * target_weight
                logging.info(f"Target allocation {symbol}: {target_weight:.1%} (${target_value:,.2f})")
            
            # PHASE 1: Sell positions that need to be reduced or eliminated
            cash_from_sells = 0
            successful_sells = 0
            
            for symbol in list(current_positions.keys()):
                current_weight = current_allocations.get(symbol, 0.0)
                target_weight = target_allocations.get(symbol, 0.0)
                
                if current_weight > target_weight:
                    # Need to reduce this position
                    current_qty = current_positions[symbol]['qty']
                    current_value = current_positions[symbol]['market_value']
                    target_value = portfolio_value * target_weight
                    
                    # Calculate how much to sell
                    value_to_sell = current_value - target_value
                    current_price = self.get_current_price(symbol)
                    
                    if current_price > 0 and value_to_sell > 1.0:  # Only sell if more than $1
                        sell_qty = round(value_to_sell / current_price, 6)
                        sell_qty = min(sell_qty, current_qty)  # Don't sell more than we have
                        
                        if sell_qty > 0:
                            order_id = self.place_order(symbol, sell_qty, OrderSide.SELL)
                            if order_id:
                                orders_executed.append({
                                    'symbol': symbol,
                                    'side': OrderSide.SELL,
                                    'qty': sell_qty,
                                    'order_id': order_id,
                                    'estimated_value': sell_qty * current_price
                                })
                                estimated_proceeds = sell_qty * current_price
                                cash_from_sells += estimated_proceeds
                                successful_sells += 1
                                logging.info(f"💰 Selling {sell_qty} shares of {symbol} to rebalance (${estimated_proceeds:,.2f})")
                            else:
                                logging.error(f"❌ Failed to place sell order for {symbol}")
            
            if successful_sells > 0:
                logging.info(f"📉 Rebalancing sells: {successful_sells} successful")
                
                # Wait for buying power to update after sells
                logging.info("⏳ Waiting for buying power to update after sells...")
                time.sleep(10)  # Wait 10 seconds for settlement
                
                # Refresh account info to get updated buying power
                updated_account_info = self.get_account_info()
                if updated_account_info:
                    updated_buying_power = updated_account_info.get('buying_power', buying_power)
                    logging.info(f"� Updated buying power after sells: ${updated_buying_power:,.2f} (was ${buying_power:,.2f})")
                    buying_power = updated_buying_power  # Use the updated value
            
            # Calculate total buying power available after sells
            # Use actual buying power instead of estimated
            total_buying_power_available = buying_power
            logging.info(f"💸 Total buying power available: ${total_buying_power_available:,.2f}")
            
            # PHASE 2: Buy positions that need to be increased or added
            successful_buys = 0
            remaining_buying_power = total_buying_power_available
            
            # Sort by priority (largest allocations first)
            for symbol, target_weight in sorted(target_portfolio.items(), key=lambda x: x[1], reverse=True):
                if target_weight <= 0:
                    continue
                
                current_weight = current_allocations.get(symbol, 0.0)
                
                if target_weight > current_weight:
                    # Need to increase this position
                    current_value = current_positions.get(symbol, {}).get('market_value', 0.0)
                    target_value = portfolio_value * target_weight
                    value_to_buy = target_value - current_value
                    
                    if value_to_buy > 1.0 and remaining_buying_power > 1.0:  # Only buy if more than $1
                        current_price = self.get_current_price(symbol)
                        
                        if current_price > 0:
                            # Limit purchase to available buying power
                            actual_value_to_buy = min(value_to_buy, remaining_buying_power)
                            buy_qty = round(actual_value_to_buy / current_price, 6)
                            required_cash = buy_qty * current_price
                            
                            if buy_qty > 0 and required_cash <= remaining_buying_power:
                                order_id = self.place_order(symbol, buy_qty, OrderSide.BUY)
                                if order_id:
                                    orders_executed.append({
                                        'symbol': symbol,
                                        'side': OrderSide.BUY,
                                        'qty': buy_qty,
                                        'order_id': order_id,
                                        'estimated_value': required_cash
                                    })
                                    remaining_buying_power -= required_cash
                                    successful_buys += 1
                                    logging.info(f"✅ Bought {buy_qty} shares of {symbol} for ${required_cash:,.2f}")
                                else:
                                    logging.error(f"❌ Failed to place buy order for {symbol}")
            
            if successful_buys > 0:
                logging.info(f"📈 Rebalancing buys: {successful_buys} successful")
            
            logging.info(f"💰 Buying power remaining after rebalancing: ${remaining_buying_power:,.2f}")
            
            return orders_executed
            
        except Exception as e:
            logging.error(f"Error rebalancing portfolio: {e}")
            return []
    
    def read_nuclear_signals(self) -> List[Dict]:
        """Read the latest nuclear trading signals from the alerts file"""
        try:
            signals = []
            alerts_file = 'data/logs/nuclear_alerts.json'
            
            if not os.path.exists(alerts_file):
                logging.warning(f"Alerts file not found: {alerts_file}")
                return signals
            
            # Read the last few lines (recent signals)
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
    
    def execute_nuclear_strategy(self) -> bool:
        """
        Execute trades based on the latest nuclear strategy signals
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info("🚀 Executing Nuclear Strategy with Alpaca")
            
            # Read latest signals
            signals = self.read_nuclear_signals()
            if not signals:
                logging.warning("⚠️ No recent signals found - unable to execute strategy")
                return False
            
            logging.info(f"Found {len(signals)} recent signals")
            
            # Parse target portfolio
            target_portfolio = self.parse_portfolio_from_signals(signals)
            if not target_portfolio:
                logging.warning("⚠️ No valid portfolio allocation found in signals - unable to execute")
                return False
            
            logging.info(f"Target Portfolio: {target_portfolio}")
            
            # Validate target portfolio
            total_allocation = sum(target_portfolio.values())
            if abs(total_allocation - 1.0) > 0.05:  # Allow 5% tolerance
                logging.warning(f"⚠️ Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")
            
            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                logging.error("❌ Failed to get account information - aborting strategy execution")
                return False
                
            logging.info(f"Account Value: ${account_info.get('portfolio_value', 0):,.2f}")
            
            # Validate we have sufficient data for pricing
            missing_prices = []
            for symbol in target_portfolio.keys():
                price = self.get_current_price(symbol)
                if price <= 0:
                    missing_prices.append(symbol)
            
            if missing_prices:
                logging.error(f"❌ Unable to get prices for symbols: {missing_prices} - aborting execution")
                return False
            
            # Execute rebalancing
            orders = self.rebalance_portfolio(target_portfolio)
            
            if orders:
                logging.info(f"✅ Portfolio rebalanced - {len(orders)} orders executed")
                for order in orders:
                    logging.info(f"   {order['side'].value} {order['qty']} {order['symbol']} (Order ID: {order['order_id']}, Value: ${order['estimated_value']:.2f})")
                # Log trade execution
                self.log_trade_execution(target_portfolio, orders, account_info)
                return True
            else:
                logging.info("ℹ️ No trades needed - portfolio already aligned with strategy")
                return True
                
        except Exception as e:
            logging.error(f"💥 Critical error executing nuclear strategy: {e}")
            import traceback
            logging.error(f"Stack trace: {traceback.format_exc()}")
            return False
    
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
            log_file = 'data/logs/alpaca_trades.json'
            with open(log_file, 'a') as f:
                f.write(json.dumps(trade_log) + '\n')
        except Exception as e:
            logging.error(f"Error logging trade execution: {e}")
    
    def display_account_summary(self):
        """Display account summary"""
        try:
            print("\n" + "="*60)
            print("🏦 ALPACA ACCOUNT SUMMARY")
            print("="*60)
            
            account_info = self.get_account_info()
            if account_info:
                print(f"Account Number: {account_info.get('account_number', 'N/A')}")
                print(f"Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
                print(f"Buying Power: ${account_info.get('buying_power', 0):,.2f}")
                print(f"Cash: ${account_info.get('cash', 0):,.2f}")
                print(f"Status: {account_info.get('status', 'N/A')}")
                print(f"Paper Trading: {self.paper_trading}")
            
            print("\n📊 CURRENT POSITIONS:")
            positions = self.get_positions()
            if positions:
                for symbol, pos in positions.items():
                    pnl_pct = pos['unrealized_plpc'] * 100
                    pnl_color = "🟢" if pnl_pct >= 0 else "🔴"
                    print(f"   {pnl_color} {symbol}: {pos['qty']} shares @ ${pos['current_price']:.2f} "
                          f"(P&L: {pnl_pct:+.1f}%)")
            else:
                print("   No positions")
            
            print("="*60)
            
        except Exception as e:
            logging.error(f"Error displaying account summary: {e}")


def main():
    """Main function for testing"""
    try:
        # Initialize bot - will read ALPACA_PAPER_TRADING from environment
        bot = AlpacaTradingBot()
        
        # Display account summary
        bot.display_account_summary()
        
        # Execute nuclear strategy
        success = bot.execute_nuclear_strategy()
        
        if success:
            print("\n✅ Nuclear strategy execution completed successfully!")
        else:
            print("\n❌ Nuclear strategy execution failed!")
        
        # Display updated account summary
        bot.display_account_summary()
        
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
