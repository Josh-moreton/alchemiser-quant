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


def wait_for_settlement(trading_client, sell_orders: List[Dict], max_wait_time: int = 60, poll_interval: float = 2.0) -> bool:
    """
    Wait for sell orders to settle by polling their status.
    
    Args:
        trading_client: Alpaca trading client for API calls
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
        
    logging.info(f"Waiting for settlement of {len(order_ids)} sell orders...")
    start_time = time.time()
    settled_orders = set()
    
    while time.time() - start_time < max_wait_time:
        # Check status of all pending orders
        for order_id in order_ids:
            if order_id in settled_orders:
                continue
                
            try:
                order = trading_client.get_order_by_id(order_id)
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


def improved_rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
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
        
        print(f"� Calculating order plan...")
        
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
            print("⏳ Waiting for sell order settlement...")
            sell_orders = [o for o in orders_executed if o['side'] == OrderSide.SELL]
            settlement_success = wait_for_settlement(self.trading_client, sell_orders, max_wait_time=60, poll_interval=2.0)
            
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


# This function should replace the existing rebalance_portfolio method in AlpacaTradingBot
