#!/usr/bin/env python3
"""Portfolio rebalancing helper."""

import logging
from typing import Dict, List, Optional

from alpaca.trading.enums import OrderSide
from ..utils.trading_math import calculate_rebalance_amounts
from ..core.trading.strategy_manager import StrategyType
from ..tracking.strategy_order_tracker import get_strategy_tracker


class PortfolioRebalancer:
    """Encapsulate portfolio rebalancing workflow."""

    def __init__(self, bot):
        """Initialize with parent trading system."""
        self.bot = bot
        self.order_manager = bot.order_manager
    
    def _get_primary_strategy_for_symbol(self, symbol: str, strategy_attribution: Optional[Dict[str, List[StrategyType]]]) -> StrategyType:
        """
        Determine the primary strategy responsible for a symbol.
        
        Args:
            symbol: The symbol to lookup
            strategy_attribution: Mapping of symbols to contributing strategies
            
        Returns:
            StrategyType: The primary strategy (first if multiple, or default if unknown)
        """
        if strategy_attribution and symbol in strategy_attribution:
            strategies = strategy_attribution[symbol]
            if strategies:
                return strategies[0]  # Use first strategy as primary
        
        # Default fallback - try to infer from symbol
        if symbol in ['SMR', 'LEU', 'OKLO', 'NLR', 'BWXT', 'PSQ', 'SQQQ', 'UUP', 'UVXY', 'BTAL']:
            return StrategyType.NUCLEAR
        elif symbol in ['TECL', 'TQQQ', 'UPRO', 'BIL', 'QQQ']:
            return StrategyType.TECL
        else:
            # Default to first available strategy
            return StrategyType.NUCLEAR

    def rebalance_portfolio(self, target_portfolio: Dict[str, float], 
                          strategy_attribution: Optional[Dict[str, List[StrategyType]]] = None) -> List[Dict]:
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
            symbol: float(getattr(pos, 'market_value', 0.0)) for symbol, pos in current_positions.items()
        }

        # Use threshold-aware rebalancing logic
        rebalance_plan = calculate_rebalance_amounts(
            target_portfolio, current_values, portfolio_value
        )

        # --- Step 4: Build list of sells ---
        sell_plans: List[Dict] = []
        
        # Check ALL current positions for liquidation needs
        for symbol, pos in current_positions.items():
            plan_data = rebalance_plan.get(symbol, {})
            target_value = plan_data.get('target_value', 0.0)
            current_value = plan_data.get('current_value', 0.0)
            needs_rebalance = plan_data.get('needs_rebalance', False)
            
            # Force liquidation if symbol not in target portfolio (regardless of rebalance plan)
            if symbol not in target_portfolio:
                qty = float(getattr(pos, 'qty', 0))
                if abs(qty) > 0:  # Check for any position (positive or negative)
                    from rich.console import Console
                    Console().print(f"[yellow]Liquidating {symbol} (not in target portfolio)[/yellow]")
                    # Use Alpaca's liquidate_position API instead of manual calculation
                    order_id = self.order_manager.liquidate_position(symbol)
                    if order_id:
                        # Estimate value for tracking purposes
                        price = self.bot.get_current_price(symbol)
                        estimated_value = abs(qty) * price if price > 0 else 0
                        
                        # Track order with strategy
                        try:
                            strategy = self._get_primary_strategy_for_symbol(symbol, strategy_attribution)
                            tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                            tracker.record_order(order_id, strategy, symbol, 'SELL', abs(qty), price)
                        except Exception as e:
                            logging.warning(f"Failed to track liquidation order {order_id}: {e}")
                        
                        orders_executed.append({
                            "symbol": symbol,
                            "qty": abs(qty),
                            "side": OrderSide.SELL,
                            "order_id": order_id,
                            "estimated_value": estimated_value,
                        })
                    continue
            
            # Continue with normal rebalance plan logic
            if not needs_rebalance:
                continue
            
            if target_value <= 0 and float(getattr(pos, 'qty', 0)) > 0:
                # Target is 0, liquidate the entire position using Alpaca API
                from rich.console import Console
                Console().print(f"[yellow]Liquidating {symbol} (target allocation: 0%)[/yellow]")
                order_id = self.order_manager.liquidate_position(symbol)
                if order_id:
                    # Estimate value for tracking purposes
                    qty = float(getattr(pos, 'qty', 0))
                    price = self.bot.get_current_price(symbol)
                    estimated_value = abs(qty) * price if price > 0 else 0
                    
                    # Track order with strategy
                    try:
                        strategy = self._get_primary_strategy_for_symbol(symbol, strategy_attribution)
                        tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                        tracker.record_order(order_id, strategy, symbol, 'SELL', abs(qty), price)
                    except Exception as e:
                        logging.warning(f"Failed to track liquidation order {order_id}: {e}")
                    
                    orders_executed.append({
                        "symbol": symbol,
                        "qty": abs(qty),
                        "side": OrderSide.SELL,
                        "order_id": order_id,
                        "estimated_value": estimated_value,
                    })
            elif current_value > target_value:
                price = self.bot.get_current_price(symbol)
                diff_value = current_value - target_value
                if price > 0:
                    qty = min(int(diff_value / price * 1e6) / 1e6, float(getattr(pos, 'qty', 0)))
                    if qty > 0:
                        sell_plans.append({"symbol": symbol, "qty": qty, "est": qty * price})

        # Execute sell orders using better orders execution
        for plan in sell_plans:
            symbol = plan["symbol"]
            qty = plan["qty"]
            
            # Use professional Better Orders execution for all sell orders
            order_id = self.order_manager.place_order(
                symbol, 
                qty, 
                OrderSide.SELL
            )
            if order_id:
                # Track order with strategy
                try:
                    symbol = plan["symbol"]
                    qty = plan["qty"]
                    price = plan.get("price", self.bot.get_current_price(symbol))
                    strategy = self._get_primary_strategy_for_symbol(symbol, strategy_attribution)
                    tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                    tracker.record_order(order_id, strategy, symbol, 'SELL', qty, price)
                except Exception as e:
                    logging.warning(f"Failed to track sell order {order_id}: {e}")
                
                orders_executed.append({
                    "symbol": plan["symbol"],
                    "qty": plan["qty"],
                    "side": OrderSide.SELL,
                    "order_id": order_id,
                    "estimated_value": plan["est"],
                })

        # Wait for all sell orders (liquidations + partial sells) to settle
        sell_orders = [o for o in orders_executed if o["side"] == OrderSide.SELL]
        if sell_orders:
            self.bot.wait_for_settlement(sell_orders)
            account_info = self.bot.get_account_info()
        available_cash = account_info.get("buying_power", cash)

        # --- Step 6: Build list of buys using refreshed info ---
        current_positions = self.bot.get_positions()
        portfolio_value = account_info.get("portfolio_value", portfolio_value)
        
        # Recalculate current values after sells
        current_values = {
            symbol: float(getattr(pos, 'market_value', 0.0)) for symbol, pos in current_positions.items()
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

        # Execute buy orders SEQUENTIALLY with fresh buying power checks
        for plan in buy_plans:
            # Refresh account info and buying power before each order
            account_info = self.bot.get_account_info()
            available_cash = account_info.get("buying_power", 0.0)
            
            # Debug logging for buying power issues
            logging.info(f"Account info: cash=${account_info.get('cash', 0):.2f}, buying_power=${account_info.get('buying_power', 0):.2f}")
            
            if available_cash <= 1.0:  # Less than $1 left
                logging.warning(f"Insufficient buying power (${available_cash:.2f}) for {plan['symbol']}, skipping remaining orders")
                break
                
            symbol = plan["symbol"]
            target_qty = plan["qty"]
            price = self.bot.get_current_price(symbol)
            estimated_cost = target_qty * price
            
            # Always use notional orders for buy orders to avoid insufficient buying power issues
            # Use the minimum of: target dollar amount or available cash (with small buffer)
            logging.info(f"Order calculation for {symbol}: estimated_cost=${estimated_cost:.2f}, available_cash=${available_cash:.2f}")
            target_dollar_amount = min(estimated_cost, available_cash * 0.99)  # 99% to leave small buffer
            logging.info(f"Final target_dollar_amount for {symbol}: ${target_dollar_amount:.2f}")
            
            # Get bid/ask for display
            quote = self.bot.data_provider.get_latest_quote(symbol)
            bid = quote.bid_price if quote and hasattr(quote, 'bid_price') else 0
            ask = quote.ask_price if quote and hasattr(quote, 'ask_price') else 0
            
            from rich.console import Console
            if bid > 0 and ask > 0:
                Console().print(f"[green]Buying {symbol}: ${target_dollar_amount:.2f} (bid=${bid:.2f}, ask=${ask:.2f})[/green]")
            else:
                Console().print(f"[green]Buying {symbol}: ${target_dollar_amount:.2f}[/green]")
            
            # Use professional Better Orders execution with notional amount
            order_id = self.order_manager.place_order(
                symbol, 
                qty=target_qty if target_qty > 0 else 1.0,  # Use calculated qty or fallback
                side=OrderSide.BUY,
                notional=target_dollar_amount if target_qty <= 0 else None  # Use notional if no qty
            )
                
            if order_id:
                # Track order with strategy
                try:
                    strategy = self._get_primary_strategy_for_symbol(symbol, strategy_attribution)
                    tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                    # For notional orders, we estimate the quantity and use current price
                    tracker.record_order(order_id, strategy, symbol, 'BUY', target_qty, price)
                except Exception as e:
                    logging.warning(f"Failed to track buy order {order_id}: {e}")
                
                orders_executed.append({
                    "symbol": symbol,
                    "qty": target_qty,  # Estimated quantity for display
                    "side": OrderSide.BUY,
                    "order_id": order_id,
                    "estimated_value": target_dollar_amount,
                })
                
                # Wait for this individual order to settle before moving to the next
                self.bot.wait_for_settlement([{
                    "symbol": symbol,
                    "order_id": order_id,
                    "qty": target_qty,
                    "side": OrderSide.BUY
                }])
                
                # Refresh positions and account info to detect any fills
                try:
                    account_info = self.bot.get_account_info()
                    current_positions = self.bot.get_positions()
                    logging.info(f"Post-order account refresh: cash=${account_info.get('cash', 0):.2f}, buying_power=${account_info.get('buying_power', 0):.2f}")
                    
                    # Check if we now have the position we wanted
                    current_value = float(getattr(current_positions.get(symbol), 'market_value', 0.0))
                    if current_value > 0:
                        logging.info(f"Detected {symbol} position after order: ${current_value:.2f}")
                except Exception as e:
                    logging.warning(f"Failed to refresh account info after order: {e}")

        # Final summary
        final_positions = self.bot.get_positions()
        self.bot.display_target_vs_current_allocations(target_portfolio, account_info, final_positions)

        return orders_executed
