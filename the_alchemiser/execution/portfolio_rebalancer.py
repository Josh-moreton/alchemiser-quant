#!/usr/bin/env python3
"""Portfolio rebalancing helper."""

import logging
from typing import Dict, List

from alpaca.trading.enums import OrderSide
from ..utils.trading_math import calculate_rebalance_amounts


class PortfolioRebalancer:
    """Encapsulate portfolio rebalancing workflow."""

    def __init__(self, bot):
        """Initialize with parent trading bot."""
        self.bot = bot
        self.order_manager = bot.order_manager
        self.trading_client = bot.trading_client
        self.ignore_market_hours = getattr(bot, "ignore_market_hours", False)

    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
        """Rebalance portfolio following a sell-then-buy process.

        Steps:
        1. Calculate indicators (delegated to the parent bot if available)
        2. Calculate signals based on those indicators
        3. Determine target weights from signals
        4. Calculate sell orders and batch send
        5. Wait for settlement, refresh account info and buying power
        6. Calculate buy orders and batch send
        7. Wait for settlement again and refresh final account info
        """
        orders_executed: List[Dict] = []

        # Get current account info and positions
        account_info = self.bot.get_account_info()
        if not account_info:
            logging.error("Unable to retrieve account info for rebalancing")
            return orders_executed

        portfolio_value = account_info.get("portfolio_value", 0.0)
        cash = account_info.get("cash", 0.0)
        current_positions = self.bot.get_positions()

        target_values = {
            symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()
        }
        current_values = {
            symbol: pos.get("market_value", 0.0) for symbol, pos in current_positions.items()
        }

        # Use threshold-aware rebalancing logic
        rebalance_plan = calculate_rebalance_amounts(
            target_portfolio, current_values, portfolio_value
        )

        # --- Step 4: Build list of sells ---
        sell_plans: List[Dict] = []
        for symbol, pos in current_positions.items():
            plan_data = rebalance_plan.get(symbol, {})
            if not plan_data.get('needs_rebalance', False):
                continue
                
            target_value = plan_data.get('target_value', 0.0)
            current_value = plan_data.get('current_value', 0.0)
            
            if target_value <= 0 and pos.get("qty", 0) > 0:
                price = self.bot.get_current_price(symbol)
                qty = pos["qty"]
                if price > 0 and qty > 0:
                    sell_plans.append({"symbol": symbol, "qty": qty, "est": qty * price})
            elif current_value > target_value:
                price = self.bot.get_current_price(symbol)
                diff_value = current_value - target_value
                if price > 0:
                    qty = min(int(diff_value / price * 1e6) / 1e6, pos["qty"])
                    if qty > 0:
                        sell_plans.append({"symbol": symbol, "qty": qty, "est": qty * price})

        # Execute sell orders
        for plan in sell_plans:
            order_id = self.bot.place_order(plan["symbol"], plan["qty"], OrderSide.SELL)
            if order_id:
                orders_executed.append({
                    "symbol": plan["symbol"],
                    "qty": plan["qty"],
                    "side": OrderSide.SELL,
                    "order_id": order_id,
                    "estimated_value": plan["est"],
                })

        if sell_plans:
            sell_orders = [o for o in orders_executed if o["side"] == OrderSide.SELL]
            self.bot.wait_for_settlement(sell_orders)
            account_info = self.bot.get_account_info()
        available_cash = account_info.get("cash", cash)

        # --- Step 6: Build list of buys using refreshed info ---
        current_positions = self.bot.get_positions()
        portfolio_value = account_info.get("portfolio_value", portfolio_value)
        
        # Recalculate current values after sells
        current_values = {
            symbol: pos.get("market_value", 0.0) for symbol, pos in current_positions.items()
        }
        
        # Recalculate rebalance plan with updated portfolio state
        rebalance_plan = calculate_rebalance_amounts(
            target_portfolio, current_values, portfolio_value
        )

        buy_plans: List[Dict] = []
        for symbol, plan_data in rebalance_plan.items():
            if not plan_data.get('needs_rebalance', False):
                continue
                
            target_value = plan_data.get('target_value', 0.0)
            current_value = plan_data.get('current_value', 0.0)
            
            if target_value > current_value:
                price = self.bot.get_current_price(symbol)
                diff_value = target_value - current_value
                if price > 0:
                    qty = int(diff_value / price * 1e6) / 1e6
                    if qty > 0:
                        buy_plans.append({"symbol": symbol, "qty": qty, "est": qty * price})

        for plan in buy_plans:
            if available_cash <= 0:
                break
            price = self.bot.get_current_price(plan["symbol"])
            qty = plan["qty"]
            cost = qty * price
            if cost > available_cash:
                qty = int(available_cash / price * 1e6) / 1e6
                cost = qty * price
            if qty <= 0:
                continue
            order_id = self.bot.place_order(plan["symbol"], qty, OrderSide.BUY)
            if order_id:
                orders_executed.append({
                    "symbol": plan["symbol"],
                    "qty": qty,
                    "side": OrderSide.BUY,
                    "order_id": order_id,
                    "estimated_value": cost,
                })
                available_cash -= cost

        if buy_plans:
            buy_orders = [o for o in orders_executed if o["side"] == OrderSide.BUY]
            self.bot.wait_for_settlement(buy_orders)
            account_info = self.bot.get_account_info()

        # Final summary
        final_positions = self.bot.get_positions()
        self.bot.display_target_vs_current_allocations(target_portfolio, account_info, final_positions)

        logging.info(
            f"Rebalance complete with {len(orders_executed)} orders"
        )
        return orders_executed
