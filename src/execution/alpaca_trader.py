#!/usr/bin/env python3
"""
Alpaca Trading Bot
Executes trades based on nuclear trading signals using Alpaca paper trading account
"""

import os
import json
import logging
import sys
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
    level=logging.INFO,
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
        
        # Portfolio configuration  
        self.min_cash_reserve = 0.02   # Keep only 2% cash reserve for strategy execution
        
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
        """Get current price for a symbol - simplified version using yfinance as fallback"""
        try:
            # For now, use yfinance as a fallback for pricing
            # This will be replaced with proper Alpaca data once we figure out the API
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            else:
                logging.warning(f"No price data found for {symbol}")
                return 0.0
                
        except Exception as e:
            logging.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
    def calculate_position_size(self, symbol: str, portfolio_weight: float, account_value: float) -> int:
        """
        Calculate position size based on portfolio weight
        
        Args:
            symbol: Stock symbol
            portfolio_weight: Target weight (0.0 to 1.0)
            account_value: Total account value
            
        Returns:
            Number of shares to buy/sell
        """
        try:
            current_price = self.get_current_price(symbol)
            if current_price <= 0:
                return 0
            
            # Calculate target dollar amount based on strategy allocation
            target_value = account_value * portfolio_weight
            
            # Calculate shares
            shares = int(target_value / current_price)
            
            logging.info(f"Position calculation for {symbol}: "
                        f"Target weight: {portfolio_weight:.1%}, "
                        f"Target value: ${target_value:.2f}, "
                        f"Price: ${current_price:.2f}, "
                        f"Shares: {shares}")
            
            return shares
        
        except Exception as e:
            logging.error(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def place_order(self, symbol: str, qty: int, side: OrderSide) -> Optional[str]:
        """
        Place a market order
        
        Args:
            symbol: Stock symbol
            qty: Quantity of shares
            side: OrderSide.BUY or OrderSide.SELL
            
        Returns:
            Order ID if successful, None if failed
        """
        try:
            if qty <= 0:
                logging.warning(f"Invalid quantity for {symbol}: {qty}")
                return None
            
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
            logging.error(f"Error placing order for {symbol}: {e}")
            return None
    
    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> Dict[str, str]:
        """
        Rebalance portfolio to match target allocations
        
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
            
            # Get current positions
            current_positions = self.get_positions()
            
            # Calculate orders needed
            orders_executed = {}
            
            logging.info(f"🔄 Starting portfolio rebalance - Portfolio Value: ${portfolio_value:,.2f}, Current Cash: ${current_cash:,.2f}")
            
            # First, handle sells for positions we need to reduce or eliminate
            cash_from_sells = 0
            for symbol in list(current_positions.keys()):
                current_qty = current_positions[symbol]['qty']
                target_weight = target_portfolio.get(symbol, 0.0)
                target_qty = self.calculate_position_size(symbol, target_weight, portfolio_value)
                
                if current_qty > target_qty:
                    # Sell excess shares
                    sell_qty = int(current_qty - target_qty)
                    if sell_qty > 0:
                        current_price = self.get_current_price(symbol)
                        cash_from_sells += sell_qty * current_price
                        
                        order_id = self.place_order(symbol, sell_qty, OrderSide.SELL)
                        if order_id:
                            orders_executed[f"{symbol}_SELL"] = order_id
                            logging.info(f"💰 Selling {sell_qty} shares of {symbol} will add ${sell_qty * current_price:,.2f} cash")
            
            # Calculate total cash available after sells
            total_cash_available = current_cash + cash_from_sells
            logging.info(f"💸 Total cash available for buys: ${total_cash_available:,.2f} (current: ${current_cash:,.2f} + from sells: ${cash_from_sells:,.2f})")
            
            # Then handle buys for new positions or increases
            # Sort by priority (largest allocations first to ensure they get filled)
            buy_orders = []
            for symbol, target_weight in sorted(target_portfolio.items(), key=lambda x: x[1], reverse=True):
                if target_weight <= 0:
                    continue
                
                current_qty = current_positions.get(symbol, {}).get('qty', 0)
                target_qty = self.calculate_position_size(symbol, target_weight, portfolio_value)
                
                if target_qty > current_qty:
                    # Buy additional shares
                    buy_qty = int(target_qty - current_qty)
                    if buy_qty > 0:
                        current_price = self.get_current_price(symbol)
                        required_cash = buy_qty * current_price
                        buy_orders.append((symbol, buy_qty, required_cash))
            
            # Execute buy orders with available cash
            for symbol, buy_qty, required_cash in buy_orders:
                if required_cash <= total_cash_available:
                    order_id = self.place_order(symbol, buy_qty, OrderSide.BUY)
                    if order_id:
                        orders_executed[f"{symbol}_BUY"] = order_id
                        total_cash_available -= required_cash
                        logging.info(f"✅ Bought {buy_qty} shares of {symbol} for ${required_cash:,.2f}, remaining cash: ${total_cash_available:,.2f}")
                else:
                    logging.warning(f"❌ Insufficient cash for {symbol}: need ${required_cash:.2f}, have ${total_cash_available:.2f}")
            
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
                logging.info("No recent signals found")
                return False
            
            logging.info(f"Found {len(signals)} recent signals")
            
            # Parse target portfolio
            target_portfolio = self.parse_portfolio_from_signals(signals)
            if not target_portfolio:
                logging.info("No valid portfolio allocation found in signals")
                return False
            
            logging.info(f"Target Portfolio: {target_portfolio}")
            
            # Get account info
            account_info = self.get_account_info()
            logging.info(f"Account Value: ${account_info.get('portfolio_value', 0):,.2f}")
            
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
                logging.info("No trades needed - portfolio already aligned")
                return True
                
        except Exception as e:
            logging.error(f"Error executing nuclear strategy: {e}")
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
