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
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

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
    
    def __init__(self, paper_trading=True):
        """
        Initialize Alpaca trading client
        
        Args:
            paper_trading (bool): Use paper trading account if True
        """
        self.paper_trading = paper_trading
        
        # Get credentials from environment
        if paper_trading:
            self.api_key = os.getenv('ALPACA_PAPER_KEY')
            self.secret_key = os.getenv('ALPACA_PAPER_SECRET')
            self.base_url = os.getenv('ALPACA_PAPER_ENDPOINT', 'https://paper-api.alpaca.markets')
        else:
            self.api_key = os.getenv('ALPACA_KEY')
            self.secret_key = os.getenv('ALPACA_SECRET')
            self.base_url = os.getenv('ALPACA_ENDPOINT', 'https://api.alpaca.markets')
        
        # Debug: Check if credentials are loaded
        logging.info(f"API Key loaded: {'Yes' if self.api_key else 'No'}")
        logging.info(f"Secret Key loaded: {'Yes' if self.secret_key else 'No'}")
        logging.info(f"Base URL: {self.base_url}")
        
        if not self.api_key or not self.secret_key:
            raise ValueError(f"Alpaca API credentials not found in environment variables. "
                           f"API Key: {'Found' if self.api_key else 'Missing'}, "
                           f"Secret: {'Found' if self.secret_key else 'Missing'}")
        
        # Initialize trading client
        try:
            self.trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=paper_trading
            )
            logging.info("TradingClient initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize TradingClient: {e}")
            raise
        
        # Initialize data client (API keys needed for stock data)
        try:
            self.data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
            logging.info("StockHistoricalDataClient initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize StockHistoricalDataClient: {e}")
            raise
        
        # Portfolio configuration - no cash reserves, invest everything based on strategy
        
        logging.info(f"Alpaca Trading Bot initialized - Paper Trading: {paper_trading}")
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {
                'account_number': getattr(account, 'account_number', 'N/A'),
                'portfolio_value': float(getattr(account, 'portfolio_value', 0) or 0),
                'buying_power': float(getattr(account, 'buying_power', 0) or 0),
                'cash': float(getattr(account, 'cash', 0) or 0),
                'day_trade_count': getattr(account, 'day_trade_count', 0),
                'status': getattr(account, 'status', 'unknown')
            }
        except Exception as e:
            logging.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            position_dict = {}
            
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
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return {}
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol using Alpaca data API only. Returns 0.0 if unavailable. Adds detailed debug logging for troubleshooting."""
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            logging.debug(f"Requesting latest quote for symbol: {symbol}")
            latest_quote = self.data_client.get_stock_latest_quote(request_params)
            logging.debug(f"Raw latest_quote response for {symbol}: {latest_quote}")
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                bid_price = float(getattr(quote, 'bid_price', 0) or 0)
                ask_price = float(getattr(quote, 'ask_price', 0) or 0)
                logging.debug(f"Parsed quote for {symbol}: bid_price={bid_price}, ask_price={ask_price}, full_quote={quote}")
                
                # Handle cases where only bid or ask is available
                if bid_price > 0 and ask_price > 0:
                    midpoint_price = (bid_price + ask_price) / 2
                    logging.info(f"Alpaca price for {symbol}: ${midpoint_price:.2f} (bid: ${bid_price:.2f}, ask: ${ask_price:.2f})")
                    return midpoint_price
                elif bid_price > 0:
                    logging.warning(f"Using bid price for {symbol} (ask=0): ${bid_price:.2f}")
                    return bid_price
                elif ask_price > 0:
                    logging.warning(f"Using ask price for {symbol} (bid=0): ${ask_price:.2f}")
                    return ask_price
                else:
                    logging.warning(f"Quote for {symbol} has non-positive bid/ask: bid={bid_price}, ask={ask_price}")
            else:
                logging.warning(f"No valid Alpaca quote for {symbol}. latest_quote={latest_quote}")
            return 0.0
        except Exception as e:
            logging.error(f"Alpaca pricing failed for {symbol}: {e}", exc_info=True)
            return 0.0
    
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
    
    def place_order(self, symbol: str, qty: float, side: OrderSide, max_retries: int = 3) -> Optional[str]:
        """
        Place a market order (supports fractional shares) with retry logic
        
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
                market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
                order = self.trading_client.submit_order(market_order_data)
                order_id = str(getattr(order, 'id', 'unknown'))
                logging.info(f"Order placed: {side.value} {qty} shares of {symbol} - Order ID: {order_id}")
                return order_id
                
            except Exception as e:
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
    
    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> Dict[str, str]:
        """
        Rebalance portfolio to match target allocations with minimal trading
        
        Args:
            target_portfolio: Dict of {symbol: weight} where weight is 0.0 to 1.0
            
        Returns:
            Dict of {symbol: order_id} for executed orders
        """
        try:
            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                logging.error("Could not get account information")
                return {}
            
            portfolio_value = account_info['portfolio_value']
            current_cash = account_info['cash']
            buying_power = account_info['buying_power']  # Add buying power for purchase calculations
            
            # Get current positions
            current_positions = self.get_positions()
            
            # Calculate orders needed
            orders_executed = {}
            
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
                                orders_executed[f"{symbol}_SELL"] = order_id
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
                    updated_buying_power = updated_account_info['buying_power']
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
                                    orders_executed[f"{symbol}_BUY"] = order_id
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
            return {}
    
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
                for trade_desc, order_id in orders.items():
                    logging.info(f"   {trade_desc}: Order {order_id}")
                
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
    
    def log_trade_execution(self, target_portfolio: Dict[str, float], orders: Dict[str, str], account_info: Dict):
        """Log trade execution details"""
        try:
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'account_value': account_info.get('portfolio_value', 0),
                'target_portfolio': target_portfolio,
                'orders_executed': orders,
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
        # Initialize bot with paper trading
        bot = AlpacaTradingBot(paper_trading=True)
        
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
