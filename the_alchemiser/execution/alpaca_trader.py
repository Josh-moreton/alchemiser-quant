#!/usr/bin/env python3
"""
Alpaca Trading Bot Execution Module.

Implements the main trading bot logic for executing trades based on nuclear and TECL strategy signals
using Alpaca's paper trading or live trading API. Handles orchestration, portfolio rebalancing,
signal parsing, and trade logging.
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
from the_alchemiser.core.logging.logging_utils import setup_logging
from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.core.config import Config

# Alpaca imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Import new order management components
from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter, is_market_open
from the_alchemiser.utils.trading_math import calculate_position_size as calc_position_size

from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer
# Initialize logging once
setup_logging()


class AlpacaTradingBot:
    """Alpaca Trading Bot for Nuclear Strategy"""

    def __init__(self, paper_trading=None, ignore_market_hours=False, config=None):
        """
        Initialize Alpaca trading bot using UnifiedDataProvider for all data access.
        Uses config.yaml for trading mode and endpoints.
        
        Args:
            paper_trading (bool, optional): Override config setting for paper trading. 
                                          If None, uses config.yaml setting.
            ignore_market_hours (bool, optional): Whether to ignore market hours when placing orders.
                                               Default False.
            config (Config, optional): Configuration object. If None, will load from global config.
        """
        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import get_config
            config = get_config()
        
        alpaca_cfg = config['alpaca']
        logging_cfg = config['logging']
        self.config = config

        # Use parameter if provided, otherwise default to paper trading for safety
        if paper_trading is not None:
            self.paper_trading = paper_trading
        else:
            self.paper_trading = True  # Default to paper trading for safety

        # Set environment variable for alert service to use correct JSON file
        import os
        os.environ['ALPACA_PAPER_TRADING'] = 'true' if self.paper_trading else 'false'

        self.endpoint = alpaca_cfg.get('endpoint', 'https://api.alpaca.markets')
        self.paper_endpoint = alpaca_cfg.get('paper_endpoint', 'https://paper-api.alpaca.markets/v2')

        # Store the ignore_market_hours setting
        self.ignore_market_hours = ignore_market_hours

        # Removed alpaca_log reference; logging now handled by Cloudwatch/S3 trades/signals JSON

        # Log trading mode to file only
        logging.info(f"Trading Mode: {'PAPER' if self.paper_trading else 'LIVE'} (from CLI mode)")

        # Display trading mode cleanly to user using rich
        from the_alchemiser.core.ui.cli_formatter import render_header
        mode_str = "PAPER" if self.paper_trading else "LIVE"
        render_header(f"🏦 Trading Mode: {mode_str}", "Alpaca Trading Bot Initialized")

        # Use UnifiedDataProvider for all Alpaca data access
        self.data_provider = UnifiedDataProvider(
            paper_trading=self.paper_trading,
            config=config
        )
        self.trading_client = self.data_provider.trading_client  # For order placement

        # Initialize OrderManager for order placement and settlement
        # Convert config to dict for OrderManager compatibility
        config_dict = {}
        if self.config and hasattr(self.config, 'get'):
            try:
                config_dict = {
                    'alpaca': self.config.get('alpaca', {}),
                    'logging': self.config.get('logging', {})
                }
            except Exception:
                config_dict = {}
        
        self.order_manager = OrderManagerAdapter(
            trading_client=self.trading_client,
            data_provider=self.data_provider,
            ignore_market_hours=self.ignore_market_hours,
            config=config_dict
        )
        self.portfolio_rebalancer = PortfolioRebalancer(self)

        # Log to file
        logging.info(f"Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}")
        # User-facing message with rich
        from rich.console import Console
        console = Console()
        if self.paper_trading:
            console.print("[green]Successfully retrieved Alpaca paper trading keys[/green]")
            console.print(f"[bold blue]Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}[/bold blue]")
        else:
            console.print("[green]Successfully retrieved Alpaca live trading keys[/green]")
            console.print(f"[bold blue]Alpaca Trading Bot initialized - Paper Trading: {self.paper_trading}[/bold blue]")
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information including P&L data"""
        # Get basic account info
        account = self.data_provider.get_account_info()
        if not account:
            return {}
        
        # Get portfolio history for P&L data
        portfolio_history = self.data_provider.get_portfolio_history()
        
        # Get open positions for current P&L
        open_positions = self.data_provider.get_open_positions()
        
        return {
            'account_number': getattr(account, 'account_number', 'N/A'),
            'portfolio_value': float(getattr(account, 'portfolio_value', 0) or 0),
            'equity': float(getattr(account, 'equity', 0) or 0),
            'buying_power': float(getattr(account, 'buying_power', 0) or 0),
            'cash': float(getattr(account, 'cash', 0) or 0),
            'day_trade_count': getattr(account, 'day_trade_count', 0),
            'status': getattr(account, 'status', 'unknown'),
            'portfolio_history': portfolio_history,
            'open_positions': open_positions
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
                
            # Use the pure function from trading_math module
            shares = calc_position_size(current_price, portfolio_weight, account_value)
            
            logging.info(f"Position calculation for {symbol}: "
                        f"Target weight: {portfolio_weight:.1%}, "
                        f"Target value: ${account_value * portfolio_weight:.2f}, "
                        f"Price: ${current_price:.2f}, "
                        f"Shares: {shares}")
            return shares
        except Exception as e:
            logging.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    def wait_for_settlement(self, sell_orders: List[Dict], max_wait_time: int = 60, poll_interval: float = 2.0) -> bool:
        """
        Wait for sell orders to settle by polling their status.
        Delegates to OrderManager.
        """
        return self.order_manager.wait_for_settlement(sell_orders, max_wait_time, poll_interval)

    def place_order(
        self, symbol: str, qty: float, side: OrderSide, 
        max_retries: int = 3, poll_timeout: int = 30, poll_interval: float = 2.0, 
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Place a limit order using a dynamic pegging strategy.
        Delegates to OrderManager.
        """
        return self.order_manager.place_limit_or_market(
            symbol, qty, side, max_retries, poll_timeout, poll_interval, slippage_bps
        )
    
    def display_target_vs_current_allocations(self, target_portfolio: Dict[str, float], account_info: Dict, current_positions: Dict) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Display target vs current allocations and return the calculated values.
        
        Returns:
            Tuple of (target_values, current_values) dictionaries
        """
        portfolio_value = account_info.get('portfolio_value', 0.0)
        
        # Calculate target and current allocations based on portfolio value
        target_values = {
            symbol: portfolio_value * weight 
            for symbol, weight in target_portfolio.items()
        }
        
        current_values = {
            symbol: pos.get('market_value', 0.0) 
            for symbol, pos in current_positions.items()
        }
        
        print(f"🎯 Target vs Current Allocations (trades only if % difference > 1.0):")
        all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
        for symbol in sorted(all_symbols):
            target_weight = target_portfolio.get(symbol, 0.0)
            target_value = target_values.get(symbol, 0.0)
            current_value = current_values.get(symbol, 0.0)
            current_weight = current_value / portfolio_value if portfolio_value > 0 else 0.0
            percent_diff = abs(target_weight - current_weight) * 100
            print(f"   {symbol:>4}: Target {target_weight:>5.1%} | Current {current_weight:>5.1%} | Δ = {percent_diff:>4.2f} pct pts")
            logging.info(f"   {symbol}: Target {target_weight:.1%} | Current {current_weight:.1%} | Δ = {percent_diff:.2f} pct pts")
        return target_values, current_values

    def check_allocation_discrepancies(self, target_values: Dict[str, float], current_values: Dict[str, float], tolerance: float = 1.0) -> bool:
        """
        Check if there are significant discrepancies between target and current allocations.
        Uses percentage point difference only (absolute percent difference > 1.0%).
        Args:
            target_values: Target dollar values by symbol
            current_values: Current dollar values by symbol
            tolerance: Tolerance in percentage points (default 1.0)
        Returns:
            True if there are discrepancies that need rebalancing, False otherwise
        """
        all_symbols = set(target_values.keys()) | set(current_values.keys())
        total_portfolio_value = sum(target_values.values()) + sum(current_values.values())
        # Use the larger of the two for denominator to avoid division by zero
        portfolio_value = max(sum(target_values.values()), sum(current_values.values()), 1.0)

        for symbol in all_symbols:
            target_value = target_values.get(symbol, 0.0)
            current_value = current_values.get(symbol, 0.0)
            target_pct = target_value / portfolio_value if portfolio_value > 0 else 0.0
            current_pct = current_value / portfolio_value if portfolio_value > 0 else 0.0
            percent_diff = abs(target_pct - current_pct) * 100
            # Only check percentage point difference
            if percent_diff > tolerance:
                return True
            # Special check: if target is 0 but we still have a position
            if target_value == 0.0 and current_value > 0.0:
                return True
        return False

    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
        """Delegate to PortfolioRebalancer for actual workflow."""
        return self.portfolio_rebalancer.rebalance_portfolio(target_portfolio)

    
    def read_nuclear_signals(self) -> List[Dict]:
        """Read the latest nuclear trading signals from the alerts file"""
        try:
            signals = []
            # Signal logging files removed - signals now only tracked through dashboard data
            
            # Define default alerts file path based on trading mode
            alerts_file = f"s3://the-alchemiser-s3/dashboard/{'paper_' if self.paper_trading else ''}signals.json"
            
            from the_alchemiser.core.utils.s3_utils import get_s3_handler
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
            from the_alchemiser.core.config import get_config
            config = get_config()
            
            # Trade logging simplified - trades now tracked through dashboard data only
            log_file = f"s3://the-alchemiser-s3/dashboard/{'paper_' if self.paper_trading else ''}trades.json"
            
            from the_alchemiser.core.utils.s3_utils import get_s3_handler
            s3_handler = get_s3_handler()
            s3_handler.append_text(log_file, json.dumps(trade_log) + '\n')
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
