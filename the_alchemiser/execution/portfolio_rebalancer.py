#!/usr/bin/env python3
"""Portfolio rebalancing helper."""

import logging
from typing import Any

from alpaca.trading.enums import OrderSide

from ..core.trading.strategy_manager import StrategyType
from ..core.types import OrderDetails
from ..tracking.strategy_order_tracker import get_strategy_tracker
from ..utils.trading_math import calculate_rebalance_amounts


class PortfolioRebalancer:
    """Encapsulate portfolio rebalancing workflow."""

    def __init__(self, bot) -> None:
        """Initialize with parent trading system."""
        self.bot = bot
        self.order_manager = bot.order_manager

    def _get_primary_strategy_for_symbol(
        self, symbol: str, strategy_attribution: dict[str, list[StrategyType]] | None
    ) -> StrategyType:
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
        if symbol in ["SMR", "LEU", "OKLO", "NLR", "BWXT", "PSQ", "SQQQ", "UUP", "UVXY", "BTAL"]:
            return StrategyType.NUCLEAR
        elif symbol in ["TECL", "TQQQ", "UPRO", "BIL", "QQQ"]:
            return StrategyType.TECL
        else:
            # Default to first available strategy
            return StrategyType.NUCLEAR

    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:  # Phase 18: Migrated from list[dict[str, Any]] to list[OrderDetails]
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
        orders_executed: list[OrderDetails] = []  # Phase 18: Migrated to list[OrderDetails]

        # Get current account info and positions
        account_info = self.bot.get_account_info()
        if not account_info:
            logging.error("Unable to retrieve account info for rebalancing")
            return orders_executed

        portfolio_value = account_info.get("portfolio_value", 0.0)
        cash = account_info.get("cash", 0.0)

        # Get positions as a dictionary keyed by symbol using the new method
        current_positions = self.bot.get_positions_dict()
        logging.debug(f"Position keys: {list(current_positions.keys())}")

        # Log each position's market value at debug level
        for symbol, pos in current_positions.items():
            if hasattr(pos, "market_value"):
                market_value = float(pos.market_value)
                logging.debug(f"Position {symbol} market_value: ${market_value:.2f}")
            elif isinstance(pos, dict) and "market_value" in pos:
                market_value = float(pos["market_value"])
                logging.debug(f"Position {symbol} market_value from dict: ${market_value:.2f}")
            else:
                logging.debug(f"Position {symbol} has no market_value attribute")

        _target_values = {  # Reserved for future use in value-based rebalancing
            symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()
        }
        # Now build current_values dictionary properly from the positions
        current_values = {}

        # Handle positions properly whether they're objects or dictionaries
        for symbol, pos in current_positions.items():
            # Extract market value depending on position structure
            if hasattr(pos, "market_value"):
                market_value = float(pos.market_value)
            elif isinstance(pos, dict) and "market_value" in pos:
                market_value = float(pos["market_value"])
            else:
                try:
                    market_value = float(getattr(pos, "market_value", 0.0))
                except (AttributeError, TypeError, ValueError):
                    market_value = 0.0

            current_values[symbol] = market_value
            logging.debug(f"Added to current_values: {symbol} = ${market_value:.2f}")

        # Use threshold-aware rebalancing logic
        rebalance_plan = calculate_rebalance_amounts(
            target_portfolio, current_values, portfolio_value
        )

        # --- Step 4: Build list of sells ---
        sell_plans: list[dict[str, Any]] = (
            []
        )  # TODO: Phase 5 - Will refactor to TradingPlan structure later

        # Check ALL current positions for liquidation needs
        for symbol, pos in current_positions.items():
            plan_data = rebalance_plan.get(symbol, {})
            target_value = plan_data.get("target_value", 0.0)
            current_value = plan_data.get("current_value", 0.0)
            needs_rebalance = plan_data.get("needs_rebalance", False)

            # Force liquidation if symbol not in target portfolio (regardless of rebalance plan)
            if symbol not in target_portfolio:
                # Handle both dict and object position formats for qty
                if isinstance(pos, dict):
                    qty = float(pos.get("qty", 0))
                else:
                    qty = float(getattr(pos, "qty", 0))
                if abs(qty) > 0:  # Check for any position (positive or negative)
                    from rich.console import Console

                    Console().print(
                        f"[yellow]Liquidating {symbol} (not in target portfolio)[/yellow]"
                    )
                    # Use Alpaca's liquidate_position API instead of manual calculation
                    order_id = self.order_manager.liquidate_position(symbol)
                    if order_id:
                        # Estimate value for tracking purposes
                        price = self.bot.get_current_price(symbol)
                        estimated_value = abs(qty) * price if price > 0 else 0

                        # Track order with strategy
                        try:
                            strategy = self._get_primary_strategy_for_symbol(
                                symbol, strategy_attribution
                            )
                            tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                            tracker.record_order(
                                order_id, strategy, symbol, "SELL", abs(qty), price
                            )
                        except Exception as e:
                            logging.warning(f"Failed to track liquidation order {order_id}: {e}")

                        order_details: OrderDetails = {
                            "id": order_id,
                            "symbol": symbol,
                            "qty": abs(qty),
                            "side": "sell",
                            "order_type": "market",
                            "time_in_force": "day",
                            "status": "new",
                            "filled_qty": 0.0,
                            "filled_avg_price": None,
                            "created_at": "",
                            "updated_at": "",
                        }
                        # Add estimated_value dynamically for display purposes
                        order_details["estimated_value"] = estimated_value  # type: ignore
                        orders_executed.append(order_details)
                    continue

            # Continue with normal rebalance plan logic
            if not needs_rebalance:
                continue

            # Handle both dict and object position formats for qty check
            if isinstance(pos, dict):
                position_qty = float(pos.get("qty", 0))
            else:
                position_qty = float(getattr(pos, "qty", 0))

            if target_value <= 0 and position_qty > 0:
                # Target is 0, liquidate the entire position using Alpaca API
                from rich.console import Console

                Console().print(f"[yellow]Liquidating {symbol} (target allocation: 0%)[/yellow]")
                order_id = self.order_manager.liquidate_position(symbol)
                if order_id:
                    # Estimate value for tracking purposes
                    qty = position_qty  # Use the already calculated position_qty
                    price = self.bot.get_current_price(symbol)
                    estimated_value = abs(qty) * price if price > 0 else 0

                    # Track order with strategy
                    try:
                        strategy = self._get_primary_strategy_for_symbol(
                            symbol, strategy_attribution
                        )
                        tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                        tracker.record_order(order_id, strategy, symbol, "SELL", abs(qty), price)
                    except Exception as e:
                        logging.warning(f"Failed to track liquidation order {order_id}: {e}")

                    order_details: OrderDetails = {
                        "id": order_id,
                        "symbol": symbol,
                        "qty": abs(qty),
                        "side": "sell",
                        "order_type": "market",
                        "time_in_force": "day",
                        "status": "new",
                        "filled_qty": 0.0,
                        "filled_avg_price": None,
                        "created_at": "",
                        "updated_at": "",
                    }
                    # Add estimated_value dynamically for display purposes
                    order_details["estimated_value"] = estimated_value  # type: ignore
                    orders_executed.append(order_details)
            elif current_value > target_value:
                price = self.bot.get_current_price(symbol)
                diff_value = current_value - target_value
                if price > 0:
                    # Handle both dict and object position formats for qty
                    if isinstance(pos, dict):
                        position_qty = float(pos.get("qty", 0))
                    else:
                        position_qty = float(getattr(pos, "qty", 0))

                    qty = min(int(diff_value / price * 1e6) / 1e6, position_qty)
                    if qty > 0:
                        sell_plans.append({"symbol": symbol, "qty": qty, "est": qty * price})

        # Execute sell orders using better orders execution
        for plan in sell_plans:
            symbol = plan["symbol"]
            qty = plan["qty"]

            # Use professional Better Orders execution for all sell orders
            order_id = self.order_manager.place_order(symbol, qty, OrderSide.SELL)
            if order_id:
                # Track order with strategy
                try:
                    symbol = plan["symbol"]
                    qty = plan["qty"]
                    price = plan.get("price", self.bot.get_current_price(symbol))
                    strategy = self._get_primary_strategy_for_symbol(symbol, strategy_attribution)
                    tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                    tracker.record_order(order_id, strategy, symbol, "SELL", qty, price)
                except Exception as e:
                    logging.warning(f"Failed to track sell order {order_id}: {e}")

                order_details: OrderDetails = {
                    "id": order_id,
                    "symbol": plan["symbol"],
                    "qty": plan["qty"],
                    "side": "sell",
                    "order_type": "market",
                    "time_in_force": "day",
                    "status": "new",
                    "filled_qty": 0.0,
                    "filled_avg_price": None,
                    "created_at": "",
                    "updated_at": "",
                }
                # Add estimated_value dynamically for display purposes
                order_details["estimated_value"] = plan.get("est", 0.0)  # type: ignore
                orders_executed.append(order_details)

        # Wait for all sell orders (liquidations + partial sells) to settle
        sell_orders = [o for o in orders_executed if o["side"] == "sell"]
        if sell_orders:
            self.bot.wait_for_settlement(sell_orders)
            account_info = self.bot.get_account_info()
        available_cash = account_info.get("buying_power", cash)

        # --- Step 6: Build list of buys using refreshed info ---
        # Get positions as a dictionary keyed by symbol
        current_positions = self.bot.get_positions_dict()
        logging.debug(f"After sells - got current_positions as dict: {current_positions}")

        portfolio_value = account_info.get("portfolio_value", portfolio_value)

        # Recalculate current values after sells
        current_values = {}
        logging.debug(f"Re-processing current positions after sells: {current_positions}")

        # Handle positions properly whether they're objects or dictionaries
        for symbol, pos in current_positions.items():
            # Extract market value depending on position structure
            if hasattr(pos, "market_value"):
                market_value = float(pos.market_value)
            elif isinstance(pos, dict) and "market_value" in pos:
                market_value = float(pos["market_value"])
            else:
                try:
                    market_value = float(getattr(pos, "market_value", 0.0))
                except (AttributeError, TypeError, ValueError):
                    market_value = 0.0

            current_values[symbol] = market_value
            logging.debug(f"Adding current value after sells: {symbol} = ${market_value:.2f}")

        logging.debug(f"Final current_values before rebalancing: {current_values}")

        # Recalculate rebalance plan with updated portfolio state
        rebalance_plan = calculate_rebalance_amounts(
            target_portfolio, current_values, portfolio_value
        )

        # Debug logging for the rebalance plan
        logging.debug(f"portfolio_value: ${portfolio_value:.2f}")
        logging.debug(f"available_cash: ${available_cash:.2f}")
        logging.debug(f"Full rebalance plan: {rebalance_plan}")

        buy_plans: list[dict[str, Any]] = []  # TODO: Phase 5 - Migrate to list[TradingPlan]
        for symbol, plan_data in rebalance_plan.items():
            if not plan_data.get("needs_rebalance", False):
                continue

            target_value = plan_data.get("target_value", 0.0)
            current_value = plan_data.get("current_value", 0.0)

            if target_value > current_value:
                price = self.bot.get_current_price(symbol)
                diff_value = target_value - current_value
                if price > 0:
                    qty = int(diff_value / price * 1e6) / 1e6
                    if qty > 0:
                        buy_plans.append(
                            {
                                "symbol": symbol,
                                "qty": qty,
                                "est": qty * price,
                                "target_value": target_value,
                            }
                        )
                        logging.warning(
                            f"DEBUG: Adding to buy_plans - symbol: {symbol}, qty: {qty}, est: ${qty * price:.2f}, target_value: ${target_value:.2f}"
                        )

        # Execute buy orders SEQUENTIALLY with fresh buying power checks
        for plan in buy_plans:
            # Refresh account info and buying power before each order
            account_info = self.bot.get_account_info()
            available_cash = account_info.get("buying_power", 0.0)

            # Debug logging for buying power issues
            logging.info(
                f"Account info: cash=${account_info.get('cash', 0):.2f}, buying_power=${account_info.get('buying_power', 0):.2f}"
            )

            if available_cash <= 1.0:  # Less than $1 left
                logging.warning(
                    f"Insufficient buying power (${available_cash:.2f}) for {plan['symbol']}, skipping remaining orders"
                )
                break

            symbol = plan["symbol"]
            target_qty = plan["qty"]
            target_value = plan.get("target_value", 0.0)  # Get the target value from the plan
            price = self.bot.get_current_price(symbol)
            estimated_cost = target_qty * price

            # Always use notional orders for buy orders to avoid insufficient buying power issues
            # Use the minimum of: target dollar amount or available cash (with small buffer)
            logging.info(
                f"Order calculation for {symbol}: estimated_cost=${estimated_cost:.2f}, available_cash=${available_cash:.2f}"
            )
            # Get the original target value from the rebalance plan
            plan_data = rebalance_plan.get(symbol, {})
            original_target_value = plan_data.get("target_value", 0.0)
            trade_amount = plan_data.get("trade_amount", 0.0)

            # Use debug logging to see all values
            logging.debug(f"{symbol} rebalance plan: {plan_data}")
            logging.debug(f"{symbol} target_value from plan: ${original_target_value:.2f}")
            logging.debug(f"{symbol} trade_amount from plan: ${trade_amount:.2f}")
            logging.debug(f"{symbol} target_value from buy plan: ${target_value:.2f}")
            logging.debug(f"{symbol} available_cash: ${available_cash:.2f}")

            # Use the target value from the rebalance plan, but limit to available cash
            target_dollar_amount = min(
                target_value, available_cash * 0.99
            )  # 99% to leave small buffer
            logging.warning(
                f"DEBUG: Final target_dollar_amount for {symbol}: ${target_dollar_amount:.2f}"
            )  # Get bid/ask for display
            quote = self.bot.data_provider.get_latest_quote(symbol)
            bid = quote.bid_price if quote and hasattr(quote, "bid_price") else 0
            ask = quote.ask_price if quote and hasattr(quote, "ask_price") else 0

            from rich.console import Console

            if bid > 0 and ask > 0:
                Console().print(
                    f"[green]Buying {symbol}: ${target_dollar_amount:.2f} (bid=${bid:.2f}, ask=${ask:.2f})[/green]"
                )
            else:
                Console().print(f"[green]Buying {symbol}: ${target_dollar_amount:.2f}[/green]")

            # Debug what we're actually sending to place_order
            logging.warning(
                f"DEBUG: Calling place_order with symbol={symbol}, qty=1.0, side=BUY, notional=${target_dollar_amount}"
            )

            # ALWAYS use notional amount for buy orders to ensure correct amounts
            order_id = self.order_manager.place_order(
                symbol,
                qty=1.0,  # Use placeholder quantity; notional amount will override this
                side=OrderSide.BUY,
                notional=target_dollar_amount,  # Always use notional for buy orders
            )

            if order_id:
                # Track order with strategy
                try:
                    strategy = self._get_primary_strategy_for_symbol(symbol, strategy_attribution)
                    tracker = get_strategy_tracker(paper_trading=self.bot.paper_trading)
                    # For notional orders, we estimate the quantity and use current price
                    tracker.record_order(order_id, strategy, symbol, "BUY", target_qty, price)
                except Exception as e:
                    logging.warning(f"Failed to track buy order {order_id}: {e}")

                order_details: OrderDetails = {
                    "id": order_id,
                    "symbol": symbol,
                    "qty": target_qty,  # Estimated quantity for display
                    "side": "buy",
                    "order_type": "market",
                    "time_in_force": "day",
                    "status": "new",
                    "filled_qty": 0.0,
                    "filled_avg_price": None,
                    "created_at": "",
                    "updated_at": "",
                }
                # Add estimated_value dynamically for display purposes
                order_details["estimated_value"] = target_dollar_amount  # type: ignore
                orders_executed.append(order_details)

                # Wait for this individual order to settle before moving to the next
                self.bot.wait_for_settlement([order_details])

                # Update order details with actual filled information
                try:
                    # Get the actual order from API to get filled data
                    actual_order = self.bot.get_order_by_id(order_id)
                    if actual_order:
                        order_details["filled_qty"] = float(getattr(actual_order, "filled_qty", 0))
                        filled_price = getattr(actual_order, "filled_avg_price", None)
                        order_details["filled_avg_price"] = (
                            float(filled_price) if filled_price else None
                        )
                        order_details["status"] = str(getattr(actual_order, "status", "unknown"))
                        logging.info(
                            f"Updated {symbol} order with filled data: qty={order_details['filled_qty']}, price={order_details['filled_avg_price']}"
                        )
                except Exception as e:
                    logging.warning(f"Could not fetch filled data for order {order_id}: {e}")

                # Refresh positions and account info to detect any fills
                try:
                    account_info = self.bot.get_account_info()

                    # Get positions in the proper format (dictionary)
                    current_positions = self.bot.get_positions_dict()

                    logging.info(
                        f"Post-order account refresh: cash=${account_info.get('cash', 0):.2f}, buying_power=${account_info.get('buying_power', 0):.2f}"
                    )

                    # Check if we now have the position we wanted
                    if symbol in current_positions:
                        pos = current_positions[symbol]
                        if hasattr(pos, "market_value"):
                            current_value = float(pos.market_value)
                        elif isinstance(pos, dict) and "market_value" in pos:
                            current_value = float(pos["market_value"])
                        else:
                            current_value = float(getattr(pos, "market_value", 0.0))

                        if current_value > 0:
                            logging.info(
                                f"Detected {symbol} position after order: ${current_value:.2f}"
                            )
                except Exception as e:
                    logging.warning(f"Failed to refresh account info after order: {e}")

        # Final summary
        final_positions = self.bot.get_positions()
        self.bot.display_target_vs_current_allocations(
            target_portfolio, account_info, final_positions
        )

        return orders_executed
