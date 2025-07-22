#!/usr/bin/env python3
"""
Improved rebalancing logic for Alpaca trading bot.
This fixes the key issues:
1. Uses buying power instead of portfolio value for allocation base
2. Properly handles complete portfolio switches
3. Minimizes trades and respects cash constraints
"""

from typing import Dict, List
import time
import logging
from alpaca.trading.enums import OrderSide


def improved_rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
    """
    Efficiently rebalance portfolio to match target allocations.
    Uses buying power as the base for allocation calculations to handle cash properly.
    
    Key improvements:
    1. Uses buying power (not portfolio value) as allocation base
    2. Sells unwanted positions completely before buying new ones
    3. Prioritizes high-weight target positions
    4. Handles complete portfolio composition changes efficiently
    
    Args:
        target_portfolio: Dict of {symbol: weight} where weights sum to ~1.0
        
    Returns:
        List of order dictionaries for executed trades
    """
    try:
        print("🔄 Starting improved portfolio rebalancing...")
        logging.info("🔄 Starting improved portfolio rebalancing...")
        
        # Get account information
        account_info = self.get_account_info()
        if not account_info:
            print("❌ Unable to get account information")
            logging.error("❌ Unable to get account information")
            return []
        
        # Use buying power as the base for calculations (includes cash + margin)
        total_buying_power = account_info.get('buying_power', 0.0)
        cash = account_info.get('cash', 0.0)
        portfolio_value = account_info.get('portfolio_value', 0.0)
        
        # Cash reserve (5% minimum)
        cash_reserve_pct = 0.05
        usable_buying_power = total_buying_power * (1 - cash_reserve_pct)
        
        print(f"📊 Account Info:")
        print(f"   Portfolio Value: ${portfolio_value:,.2f}")
        print(f"   Total Buying Power: ${total_buying_power:,.2f}")
        print(f"   Cash: ${cash:,.2f}")
        print(f"   Cash Reserve: {cash_reserve_pct:.1%}")
        print(f"   Usable Buying Power: ${usable_buying_power:,.2f}")
        
        logging.info(f"📊 Account Info:")
        logging.info(f"   Portfolio Value: ${portfolio_value:,.2f}")
        logging.info(f"   Total Buying Power: ${total_buying_power:,.2f}")
        logging.info(f"   Usable Buying Power: ${usable_buying_power:,.2f}")

        # Get current positions
        current_positions = self.get_positions()

        # Calculate target values based on usable buying power (not portfolio value!)
        target_values = {
            symbol: usable_buying_power * weight 
            for symbol, weight in target_portfolio.items()
        }
        
        # Calculate current values
        current_values = {
            symbol: pos.get('market_value', 0.0) 
            for symbol, pos in current_positions.items()
        }
        
        print(f"🎯 Target vs Current Allocations (based on ${usable_buying_power:,.2f} usable buying power):")
        logging.info(f"🎯 Target vs Current Allocations:")
        
        all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
        for symbol in sorted(all_symbols):
            target_weight = target_portfolio.get(symbol, 0.0)
            target_value = target_values.get(symbol, 0.0)
            current_value = current_values.get(symbol, 0.0)
            current_weight = current_value / usable_buying_power if usable_buying_power > 0 else 0.0
            
            print(f"   {symbol}: Target {target_weight:.1%} (${target_value:.2f}) | Current {current_weight:.1%} (${current_value:.2f})")
            logging.info(f"   {symbol}: Target {target_weight:.1%} (${target_value:.2f}) | Current {current_weight:.1%} (${current_value:.2f})")

        orders_executed = []
        
        # PHASE 1: Sell positions that are not in target or exceed target
        print("📉 PHASE 1: Selling excess/unwanted positions...")
        logging.info("📉 PHASE 1: Selling excess/unwanted positions...")
        
        sells_made = False
        for symbol, pos in current_positions.items():
            target_value = target_values.get(symbol, 0.0)
            current_value = current_values[symbol]
            
            # If not in target portfolio, sell entire position
            if target_value == 0.0:
                sell_qty = pos['qty']
                print(f"   {symbol}: Selling entire position ({sell_qty} shares) - not in target portfolio")
                logging.info(f"   {symbol}: Selling entire position ({sell_qty} shares) - not in target portfolio")
            # If current value exceeds target by more than $1, sell excess
            elif current_value > target_value + 1.0:
                excess_value = current_value - target_value
                current_price = self.get_current_price(symbol)
                sell_qty = min(round(excess_value / current_price, 6), pos['qty'])
                print(f"   {symbol}: Selling {sell_qty} shares (excess ${excess_value:.2f})")
                logging.info(f"   {symbol}: Selling {sell_qty} shares (excess ${excess_value:.2f})")
            else:
                print(f"   {symbol}: No sell needed")
                logging.info(f"   {symbol}: No sell needed")
                continue
            
            if sell_qty > 0:
                order_id = self.place_order(symbol, sell_qty, OrderSide.SELL)
                if order_id:
                    estimated_value = sell_qty * self.get_current_price(symbol)
                    orders_executed.append({
                        'symbol': symbol,
                        'side': OrderSide.SELL,
                        'qty': sell_qty,
                        'order_id': order_id,
                        'estimated_value': estimated_value
                    })
                    sells_made = True
                    print(f"   ✅ {symbol}: Sold {sell_qty} shares (Order ID: {order_id})")
                    logging.info(f"   ✅ {symbol}: Sold {sell_qty} shares (Order ID: {order_id})")
                else:
                    print(f"   ❌ {symbol}: Failed to place sell order")
                    logging.error(f"   ❌ {symbol}: Failed to place sell order")
        
        if not sells_made:
            print("   No sells needed")
            logging.info("   No sells needed")

        # Wait for settlement if we made sells
        if sells_made:
            print("⏳ Waiting for settlement after sells...")
            logging.info("⏳ Waiting for settlement after sells...")
            time.sleep(10)
            
            # Refresh account info and positions
            account_info = self.get_account_info()
            current_positions = self.get_positions()
            cash = account_info.get('cash', 0.0)
            
            print(f"   Updated Cash: ${cash:,.2f}")
            logging.info(f"   Updated Cash: ${cash:,.2f}")

        # PHASE 2: Buy positions to reach targets
        print("📈 PHASE 2: Buying to reach target allocations...")
        logging.info("📈 PHASE 2: Buying to reach target allocations...")
        
        available_cash = cash
        print(f"   Available cash for purchases: ${available_cash:.2f}")
        logging.info(f"   Available cash for purchases: ${available_cash:.2f}")
        
        # Sort by target weight (largest first) to prioritize important positions
        for symbol in sorted(target_portfolio.keys(), key=lambda x: target_portfolio[x], reverse=True):
            target_value = target_values[symbol]
            
            # Get updated current value
            current_value = 0.0
            if symbol in current_positions:
                current_value = current_positions[symbol].get('market_value', 0.0)
            
            value_to_buy = target_value - current_value
            
            if value_to_buy > 1.0 and available_cash > 1.0:
                current_price = self.get_current_price(symbol)
                actual_value_to_buy = min(value_to_buy, available_cash)
                
                # Calculate exact shares with proper rounding
                buy_qty = round(actual_value_to_buy / current_price, 6)
                required_cash = buy_qty * current_price
                
                print(f"   {symbol}: Need ${value_to_buy:.2f}, buying ${actual_value_to_buy:.2f} ({buy_qty} shares)")
                logging.info(f"   {symbol}: Need ${value_to_buy:.2f}, buying ${actual_value_to_buy:.2f} ({buy_qty} shares)")
                
                if buy_qty > 0 and required_cash <= available_cash:
                    order_id = self.place_order(symbol, buy_qty, OrderSide.BUY)
                    if order_id:
                        orders_executed.append({
                            'symbol': symbol,
                            'side': OrderSide.BUY,
                            'qty': buy_qty,
                            'order_id': order_id,
                            'estimated_value': required_cash
                        })
                        available_cash -= required_cash
                        print(f"   ✅ {symbol}: Bought {buy_qty} shares (Order ID: {order_id})")
                        logging.info(f"   ✅ {symbol}: Bought {buy_qty} shares (Order ID: {order_id})")
                    else:
                        print(f"   ❌ {symbol}: Failed to place buy order")
                        logging.error(f"   ❌ {symbol}: Failed to place buy order")
                else:
                    print(f"   {symbol}: Cannot buy - insufficient cash (need ${required_cash:.2f}, have ${available_cash:.2f})")
                    logging.info(f"   {symbol}: Cannot buy - insufficient cash")
            elif value_to_buy <= 1.0:
                print(f"   {symbol}: Already at target (difference: ${value_to_buy:.2f})")
                logging.info(f"   {symbol}: Already at target")
            else:
                print(f"   {symbol}: No cash remaining (${available_cash:.2f})")
                logging.info(f"   {symbol}: No cash remaining")

        print(f"✅ Rebalancing complete. Orders executed: {len(orders_executed)}")
        logging.info(f"✅ Rebalancing complete. Orders executed: {len(orders_executed)}")
        
        if orders_executed:
            print("📋 Summary of executed orders:")
            logging.info("📋 Summary of executed orders:")
            for order in orders_executed:
                print(f"   {order['side'].value.lower()} {order['qty']} {order['symbol']} (${order['estimated_value']:.2f})")
                logging.info(f"   {order['side'].value.lower()} {order['qty']} {order['symbol']} (${order['estimated_value']:.2f})")
        
        return orders_executed

    except Exception as e:
        print(f"❌ Error rebalancing portfolio: {e}")
        logging.error(f"❌ Error rebalancing portfolio: {e}")
        import traceback
        logging.error(f"Stack trace: {traceback.format_exc()}")
        return []


# This function should replace the existing rebalance_portfolio method in AlpacaTradingBot
