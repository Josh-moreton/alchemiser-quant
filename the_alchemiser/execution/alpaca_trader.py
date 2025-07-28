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
from the_alchemiser.execution.order_manager import OrderManager, is_market_open
from the_alchemiser.utils.trading_math import calculate_position_size as calc_position_size

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
        
        self.order_manager = OrderManager(
            trading_client=self.trading_client,
            data_provider=self.data_provider,
            ignore_market_hours=self.ignore_market_hours,
            config=config_dict
        )

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
        """
        Rebalance portfolio to match target allocations.
        
        Process:
        1. Calculate targets and current allocations based on portfolio value
        2. Calculate deltas (what needs buying/selling)
        3. Round down all values to ensure we stay within buying power
        4. Execute all sells first, wait for settlement, then execute all buys
        5. Re-check allocations and repeat if discrepancies remain
        
        Args:
            target_portfolio: Dict of {symbol: weight} where weights sum to ~1.0
            
        Returns:
            List of order dictionaries for executed trades
        """
        all_orders_executed = []
        max_rebalance_attempts = 2
        
        for attempt in range(max_rebalance_attempts):
            try:
                if attempt == 0:
                    print("🔄 Starting portfolio rebalancing...")
                    logging.info("🔄 Starting portfolio rebalancing...")
                else:
                    print(f"\n🔄 Second pass rebalancing (attempt {attempt + 1})...")
                    logging.info(f"🔄 Second pass rebalancing (attempt {attempt + 1})...")
                
                # Get account information
                account_info = self.get_account_info()
                if not account_info:
                    print("❌ Unable to get account information")
                    logging.error("❌ Unable to get account information")
                    return all_orders_executed
                
                portfolio_value = account_info.get('portfolio_value', 0.0)
                cash = account_info.get('cash', 0.0)
                
                print(f"📊 Portfolio Value: ${portfolio_value:,.2f} | Available Cash: ${cash:,.2f}")

                # Get current positions
                current_positions = self.get_positions()

                # STEP 1: Calculate target and current allocations and display them using rich
                from the_alchemiser.core.ui.cli_formatter import render_target_vs_current_allocations
                render_target_vs_current_allocations(target_portfolio, account_info, current_positions)
                
                # Calculate values for discrepancy check
                portfolio_value = account_info.get('portfolio_value', 0.0)
                target_values = {symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()}
                current_values = {symbol: pos.get('market_value', 0.0) for symbol, pos in current_positions.items()}
                
                # Check if rebalancing is needed
                if not self.check_allocation_discrepancies(target_values, current_values, tolerance=1.0):
                    if attempt == 0:
                        print("✅ Portfolio already aligned with targets, no rebalancing needed")
                        return all_orders_executed
                    else:
                        print("✅ Second pass complete - portfolio now aligned with targets")
                        break

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
                    # Calculate allocation percentages
                    target_percent = target_value / portfolio_value if portfolio_value > 0 else 0.0
                    current_percent = current_value / portfolio_value if portfolio_value > 0 else 0.0
                    percent_diff = abs(target_percent - current_percent) * 100

                    # If the target is zero (or very close), liquidate the entire position, even if tiny
                    if target_value <= 0.0 and pos['qty'] > 0:
                        current_price = self.get_current_price(symbol)
                        if current_price <= 0:
                            logging.error(f"Cannot get price for {symbol}, skipping")
                            continue
                        shares_to_sell = pos['qty']
                        estimated_proceeds = shares_to_sell * current_price
                        sell_orders_plan.append({
                            'symbol': symbol,
                            'qty': shares_to_sell,
                            'estimated_proceeds': estimated_proceeds,
                            'reason': 'entire position (target 0%)'
                        })
                        total_proceeds_expected += estimated_proceeds
                    # Only sell if allocation percentage point difference is at least 1.0
                    elif percent_diff >= 1.0 and current_percent > target_percent:
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
                                'reason': f'excess allocation ({percent_diff:.2f} pct pts)'
                            })
                            total_proceeds_expected += estimated_proceeds

                # Calculate buys (positions to increase or add)
                for symbol, target_value in target_values.items():
                    current_value = current_values.get(symbol, 0.0)
                    target_percent = target_value / portfolio_value if portfolio_value > 0 else 0.0
                    current_percent = current_value / portfolio_value if portfolio_value > 0 else 0.0
                    percent_diff = abs(target_percent - current_percent) * 100

                    # Only buy if allocation percentage point difference is at least 1.0
                    if percent_diff >= 1.0 and target_percent > current_percent:
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
                    # If cash shortfall is less than 1% or $1, scale down by 1% only
                    cash_shortfall = total_cash_needed - projected_cash
                    one_percent = total_cash_needed * 0.01
                    if cash_shortfall <= max(one_percent, 1.0):
                        scale_factor = 0.99
                        print(f"⚠️  Insufficient cash, but within 1% or $1. Scaling down buys by 1%.")
                    else:
                        scale_factor = projected_cash / total_cash_needed if total_cash_needed > 0 else 0
                        print(f"⚠️  Insufficient cash, scaling down buys to {scale_factor:.1%}")
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
                
                # Skip execution if no orders needed
                if not sell_orders_plan and not final_buy_orders:
                    if attempt == 0:
                        print("✅ No orders needed - portfolio already aligned")
                        return all_orders_executed
                    else:
                        print("✅ Second pass complete - no additional orders needed")
                        break
                
                # Display plan using rich
                from the_alchemiser.core.ui.cli_formatter import render_execution_plan
                render_execution_plan(sell_orders_plan, final_buy_orders)
                
                orders_executed = []
                
                # STEP 4: Execute all sells first
                print("📉 Executing Sell Orders:")
                if sell_orders_plan:
                    for sell_plan in sell_orders_plan:
                        symbol = sell_plan['symbol']
                        qty = sell_plan['qty']
                        print(f"   {symbol}: Selling {qty} shares ({sell_plan['reason']})")
                        
                        try:
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
                        except Exception as e:
                            print(f"   ❌ {symbol}: Exception during sell order: {e}")
                            logging.error(f"Exception during sell order for {symbol}: {e}", exc_info=True)
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
                            
                            try:
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
                            except Exception as e:
                                print(f"   ❌ {symbol}: Exception during buy order: {e}")
                                logging.error(f"Exception during buy order for {symbol}: {e}", exc_info=True)
                        else:
                            # Retry with available cash amount
                            current_price = self.get_current_price(symbol)
                            if current_price > 0 and available_cash > 1.0:  # Only retry if we have at least $1
                                adjusted_qty = int(available_cash / current_price * 1000000) / 1000000  # Round down to 6 decimals
                                adjusted_cost = adjusted_qty * current_price
                                
                                if adjusted_qty > 0:
                                    print(f"   🔄 {symbol}: Retrying with available cash (${available_cash:.2f} → {adjusted_qty} shares)")
                                    
                                    try:
                                        order_id = self.place_order(symbol, adjusted_qty, OrderSide.BUY)
                                        if order_id:
                                            orders_executed.append({
                                                'symbol': symbol,
                                                'side': OrderSide.BUY,
                                                'qty': adjusted_qty,
                                                'order_id': order_id,
                                                'estimated_value': adjusted_cost
                                            })
                                            available_cash -= adjusted_cost
                                            print(f"   ✅ {symbol}: Adjusted buy order placed (ID: {order_id})")
                                        else:
                                            print(f"   ❌ {symbol}: Failed to place adjusted buy order")
                                            logging.error(f"Failed to place adjusted buy order for {symbol}")
                                    except Exception as e:
                                        print(f"   ❌ {symbol}: Exception during adjusted buy order: {e}")
                                        logging.error(f"Exception during adjusted buy order for {symbol}: {e}", exc_info=True)
                                else:
                                    print(f"   ❌ {symbol}: Cannot buy with available cash (${available_cash:.2f})")
                            else:
                                print(f"   ❌ {symbol}: Insufficient cash (need ${estimated_cost:.2f}, have ${available_cash:.2f})")
                else:
                    print("   No buys needed")

                print(f"✅ Executed {len(orders_executed)} orders ({sum(1 for o in orders_executed if o['side'] == OrderSide.BUY)} buys, {sum(1 for o in orders_executed if o['side'] == OrderSide.SELL)} sells)")
                
                # Display trading summary using rich
                from the_alchemiser.core.ui.cli_formatter import render_trading_summary
                render_trading_summary(orders_executed)
                logging.info(f"✅ Rebalancing attempt {attempt + 1} complete. Orders executed: {len(orders_executed)}")
                
                if orders_executed:
                    logging.info(f"📋 Summary of executed orders (attempt {attempt + 1}):")
                    for order in orders_executed:
                        logging.info(f"   {order['side'].value.lower()} {order['qty']} {order['symbol']} (${order['estimated_value']:.2f})")
                
                # Add this attempt's orders to the total
                all_orders_executed.extend(orders_executed)
                
                # If this was the last attempt, break
                if attempt == max_rebalance_attempts - 1:
                    break
                    
                # Wait a moment before second attempt to allow orders to settle
                if orders_executed:
                    print("\n⏳ Waiting 3 seconds before second validation pass...")
                    import time
                    time.sleep(3)

            except Exception as e:
                print(f"❌ Error in rebalancing attempt {attempt + 1}: {e}")
                logging.error(f"❌ Error in rebalancing attempt {attempt + 1}: {e}")
                import traceback
                logging.error(f"Stack trace: {traceback.format_exc()}")
                if attempt == max_rebalance_attempts - 1:
                    return all_orders_executed
        
        print(f"\n✅ Portfolio rebalancing complete. Total orders executed: {len(all_orders_executed)}")
        
        # Display final portfolio state after all rebalancing attempts
        if all_orders_executed:
            print("\n🏁 FINAL PORTFOLIO STATE:")
            try:
                # Get updated account and position information
                final_account_info = self.get_account_info()
                final_positions = self.get_positions()
                
                if final_account_info and final_positions is not None:
                    self.display_target_vs_current_allocations(
                        target_portfolio, final_account_info, final_positions
                    )
                else:
                    print("   Unable to retrieve final portfolio state")
            except Exception as e:
                print(f"   Error displaying final portfolio state: {e}")
                logging.error(f"Error displaying final portfolio state: {e}")
        
        return all_orders_executed
    
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
