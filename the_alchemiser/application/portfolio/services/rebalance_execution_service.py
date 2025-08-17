"""Rebalance execution service - handles trade execution for rebalancing."""

from decimal import Decimal
from typing import Any

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.smart_execution import SmartExecution
from the_alchemiser.application.trading.alpaca_client import AlpacaClient
from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import RebalancePlan
from the_alchemiser.services.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.services.errors.exceptions import StrategyExecutionError
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


class RebalanceExecutionService:
    """
    Service for executing rebalancing trades.

    Handles the actual execution of buy/sell orders required for portfolio rebalancing,
    with smart execution and comprehensive error handling.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        smart_execution: SmartExecution | None = None,
        error_handler: TradingSystemErrorHandler | None = None,
    ):
        """
        Initialize the rebalance execution service.

        Args:
            trading_manager: Service for trading operations
            smart_execution: Smart execution engine (optional)
            error_handler: Error handler for trading errors (optional)
        """
        self.trading_manager = trading_manager
        # Build a single AlpacaClient using the authenticated AlpacaManager and use it for execution
        if smart_execution is not None:
            self.smart_execution = smart_execution
        else:
            # Use AlpacaManager as the price/quote provider; it implements the minimal methods
            price_quote_provider = trading_manager.alpaca_manager
            alpaca_client = AlpacaClient(trading_manager.alpaca_manager, price_quote_provider)
            self.smart_execution = SmartExecution(
                order_executor=alpaca_client,
                data_provider=price_quote_provider,
            )
        self.error_handler = error_handler or TradingSystemErrorHandler()

    def execute_rebalancing_plan(
        self, rebalance_plan: dict[str, RebalancePlan], dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Execute a complete rebalancing plan.

        Args:
            rebalance_plan: Complete rebalancing plan to execute
            dry_run: If True, only simulate execution without placing real orders

        Returns:
            Execution results with order details and status
        """
        try:
            # Filter plans that need rebalancing
            plans_to_execute = {
                symbol: plan for symbol, plan in rebalance_plan.items() if plan.needs_rebalance
            }

            if not plans_to_execute:
                return {
                    "status": "success",
                    "message": "No rebalancing required",
                    "orders_placed": {},
                    "execution_summary": {
                        "total_orders": 0,
                        "successful_orders": 0,
                        "failed_orders": 0,
                    },
                }

            # Execute sells first to free up capital
            sell_results = self._execute_sell_orders(plans_to_execute, dry_run)

            # Execute buys with freed capital
            buy_results = self._execute_buy_orders(plans_to_execute, dry_run)

            # Combine results
            all_orders = {**sell_results, **buy_results}

            return {
                "status": "success",
                "message": f"Executed {len(all_orders)} rebalancing orders",
                "orders_placed": all_orders,
                "execution_summary": self._create_execution_summary(all_orders),
                "sell_orders": sell_results,
                "buy_orders": buy_results,
            }

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                component="RebalanceExecutionService.execute_rebalancing_plan",
                context="rebalancing_execution",
                additional_data={"plan_symbols": list(rebalance_plan.keys()), "dry_run": dry_run},
            )
            raise StrategyExecutionError(f"Rebalancing execution failed: {e}") from e

    def execute_single_rebalance(
        self, symbol: str, plan: RebalancePlan, dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Execute rebalancing for a single symbol.

        Args:
            symbol: Symbol to rebalance
            plan: Rebalancing plan for the symbol
            dry_run: If True, only simulate execution

        Returns:
            Execution result for the single symbol
        """
        try:
            if not plan.needs_rebalance:
                return {
                    "symbol": symbol,
                    "status": "skipped",
                    "message": "No rebalancing required",
                    "order_id": None,
                }

            # Determine order side and quantity
            if plan.trade_amount > 0:
                # Buy order
                return self._place_buy_order(symbol, abs(plan.trade_amount), dry_run)
            else:
                # Sell order
                return self._place_sell_order(symbol, abs(plan.trade_amount), dry_run)

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                component="RebalanceExecutionService.execute_single_rebalance",
                context="single_rebalance_execution",
                additional_data={"symbol": symbol, "trade_amount": str(plan.trade_amount)},
            )
            return {
                "symbol": symbol,
                "status": "failed",
                "message": f"Execution failed: {e}",
                "order_id": None,
                "error": str(e),
            }

    def validate_rebalancing_plan(self, rebalance_plan: dict[str, RebalancePlan]) -> dict[str, Any]:
        """
        Validate a rebalancing plan before execution.

        Args:
            rebalance_plan: Plan to validate

        Returns:
            Validation results with any issues found
        """
        import logging

        validation_results: dict[str, Any] = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "total_trade_value": Decimal("0"),
            "symbols_to_trade": [],
        }

        try:
            # Check for symbols needing rebalancing
            symbols_to_trade = [
                symbol for symbol, plan in rebalance_plan.items() if plan.needs_rebalance
            ]
            validation_results["symbols_to_trade"] = symbols_to_trade

            if not symbols_to_trade:
                validation_results["warnings"].append("No symbols require rebalancing")
                return validation_results

            # Calculate total trade value
            total_trade_value = sum(
                abs(plan.trade_amount) for plan in rebalance_plan.values() if plan.needs_rebalance
            )
            validation_results["total_trade_value"] = total_trade_value

            logging.debug(
                "Rebalance validation - symbols_to_trade=%s total_trade_value=%s",
                symbols_to_trade,
                str(total_trade_value),
            )

            # Validate account balance for buy orders
            buy_amount = sum(
                plan.trade_amount
                for plan in rebalance_plan.values()
                if plan.needs_rebalance and plan.trade_amount > 0
            )
            sell_proceeds = sum(
                abs(plan.trade_amount)
                for plan in rebalance_plan.values()
                if plan.needs_rebalance and plan.trade_amount < 0
            )

            if buy_amount > 0:
                account_summary = self.trading_manager.account.get_account_summary()
                buying_power = account_summary["buying_power"]
                # Consider sell proceeds as additional available funds within the workflow
                effective_buying_power = Decimal(str(buying_power)) + Decimal(str(sell_proceeds))
                logging.debug(
                    "Rebalance validation - buy_amount=%s sell_proceeds=%s buying_power=%s effective=%s",
                    str(buy_amount),
                    str(sell_proceeds),
                    str(buying_power),
                    str(effective_buying_power),
                )
                if buy_amount > effective_buying_power:
                    validation_results["is_valid"] = False
                    validation_results["issues"].append(
                        f"Insufficient buying power: need ${buy_amount}, have ${buying_power}, "
                        f"sell proceeds considered ${sell_proceeds}"
                    )

            # Validate positions for sell orders
            positions = self.trading_manager.get_all_positions()
            position_dict = {
                getattr(pos, "symbol", getattr(pos, "symbol", "")): pos for pos in positions
            }

            logging.debug(
                "Rebalance validation - positions available: %s",
                [getattr(p, "symbol", "?") for p in positions],
            )

            for symbol, plan in rebalance_plan.items():
                if plan.needs_rebalance and plan.trade_amount < 0:
                    position = position_dict.get(symbol)
                    # Extract quantity robustly (handles str, float, Decimal, or dict)
                    qty_raw = None
                    if position is None:
                        qty = Decimal("0")
                    else:
                        if isinstance(position, dict):
                            qty_raw = position.get("qty")
                        else:
                            qty_raw = getattr(position, "qty", None)
                        try:
                            qty = Decimal(str(qty_raw or 0))
                        except Exception:
                            qty = Decimal("0")

                    if position is None or qty <= Decimal("0"):
                        validation_results["is_valid"] = False
                        validation_results["issues"].append(
                            f"Cannot sell {symbol}: no position found"
                        )

            return validation_results

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                component="RebalanceExecutionService.validate_rebalancing_plan",
                context="plan_validation",
                additional_data={"plan_symbols": list(rebalance_plan.keys())},
            )
            validation_results["is_valid"] = False
            validation_results["issues"].append(f"Validation error: {e}")
            return validation_results

    def _execute_sell_orders(
        self, rebalance_plan: dict[str, RebalancePlan], dry_run: bool
    ) -> dict[str, Any]:
        """Execute all sell orders from the rebalancing plan."""
        sell_orders = {}

        for symbol, plan in rebalance_plan.items():
            if plan.needs_rebalance and plan.trade_amount < 0:
                sell_amount = abs(plan.trade_amount)
                result = self._place_sell_order(symbol, sell_amount, dry_run)
                sell_orders[symbol] = result

        return sell_orders

    def _execute_buy_orders(
        self, rebalance_plan: dict[str, RebalancePlan], dry_run: bool
    ) -> dict[str, Any]:
        """Execute all buy orders from the rebalancing plan."""
        buy_orders = {}

        for symbol, plan in rebalance_plan.items():
            if plan.needs_rebalance and plan.trade_amount > 0:
                buy_amount = plan.trade_amount
                result = self._place_buy_order(symbol, buy_amount, dry_run)
                buy_orders[symbol] = result

        return buy_orders

    def _place_sell_order(self, symbol: str, amount: Decimal, dry_run: bool) -> dict[str, Any]:
        """Place a sell order for the specified amount."""
        try:
            if dry_run:
                return {
                    "symbol": symbol,
                    "side": "sell",
                    "amount": amount,
                    "status": "simulated",
                    "order_id": f"DRY_SELL_{symbol}",
                    "message": f"Would sell ${amount} of {symbol}",
                }

                # Use smart execution for sell order
            price_val = self.trading_manager.alpaca_manager.get_current_price(symbol)
            try:
                price = Decimal(str(price_val))
            except Exception:
                price = Decimal("0")

            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}: {price_val}")

            shares_to_sell = amount / price

            order_result = self.smart_execution.place_order(
                symbol=symbol, qty=float(shares_to_sell), side=OrderSide.SELL
            )

            return {
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "shares": shares_to_sell,
                "status": "placed",
                "order_id": order_result,
                "message": f"Placed sell order for {shares_to_sell} shares of {symbol}",
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "status": "failed",
                "order_id": None,
                "error": str(e),
                "message": f"Failed to place sell order: {e}",
            }

    def _place_buy_order(self, symbol: str, amount: Decimal, dry_run: bool) -> dict[str, Any]:
        """Place a buy order for the specified amount."""
        try:
            if dry_run:
                return {
                    "symbol": symbol,
                    "side": "buy",
                    "amount": amount,
                    "status": "simulated",
                    "order_id": f"DRY_BUY_{symbol}",
                    "message": f"Would buy ${amount} of {symbol}",
                }

                # Use smart execution for buy order
            price_val = self.trading_manager.alpaca_manager.get_current_price(symbol)
            try:
                price = Decimal(str(price_val))
            except Exception:
                price = Decimal("0")

            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}: {price_val}")

            shares_to_buy = amount / price

            order_result = self.smart_execution.place_order(
                symbol=symbol, qty=float(shares_to_buy), side=OrderSide.BUY
            )

            return {
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "shares": shares_to_buy,
                "status": "placed",
                "order_id": order_result,
                "message": f"Placed buy order for {shares_to_buy} shares of {symbol}",
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "status": "failed",
                "order_id": None,
                "error": str(e),
                "message": f"Failed to place buy order: {e}",
            }

    def _create_execution_summary(self, orders: dict[str, Any]) -> dict[str, Any]:
        """Create summary of execution results."""
        total_orders = len(orders)
        successful_orders = sum(
            1 for order in orders.values() if order.get("status") in ["placed", "simulated"]
        )
        failed_orders = total_orders - successful_orders

        return {
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "failed_orders": failed_orders,
            "success_rate": successful_orders / total_orders if total_orders > 0 else 0,
        }
