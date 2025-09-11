"""Business Unit: portfolio assessment & management; Status: current.

Rebalance execution service - handles trade execution for rebalancing.
Updated to use shared broker abstractions for reduced coupling.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.core.trading_services_facade import (
    TradingServicesFacade as TradingServiceManager,
)
from the_alchemiser.execution.strategies.smart_execution import SmartExecution
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.types.broker_enums import BrokerOrderSide
from the_alchemiser.strategy.errors.strategy_errors import StrategyExecutionError

from .rebalance_plan import RebalancePlan

# Module logger for consistent logging
logger = logging.getLogger(__name__)


class RebalanceExecutionService:
    """Service for executing rebalancing trades.

    Handles the actual execution of buy/sell orders required for portfolio rebalancing,
    with smart execution and comprehensive error handling.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        smart_execution: SmartExecution | None = None,
        error_handler: TradingSystemErrorHandler | None = None,
    ) -> None:
        """Initialize the rebalance execution service.

        Args:
            trading_manager: Service for trading operations
            smart_execution: Smart execution engine (optional)
            error_handler: Error handler for trading errors (optional)

        """
        self.trading_manager = trading_manager
        # Use AlpacaManager directly instead of AlpacaClient wrapper (Phase 3: consolidation completed)
        if smart_execution is not None:
            self.smart_execution = smart_execution
        else:
            # Use AlpacaManager as both the order executor and data provider
            alpaca_manager = trading_manager.alpaca_manager
            self.smart_execution = SmartExecution(
                order_executor=alpaca_manager,
                data_provider=alpaca_manager,
            )
        self.error_handler = error_handler or TradingSystemErrorHandler()

    def execute_rebalancing_plan(
        self, rebalance_plan: dict[str, RebalancePlan], dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute a complete rebalancing plan.

        Args:
            rebalance_plan: Complete rebalancing plan to execute
            dry_run: If True, only simulate execution without placing real orders

        Returns:
            Execution results with order details and status

        """
        try:
            # === ENHANCED LOGGING: EXECUTION SERVICE ENTRY ===
            logger.info("=== REBALANCE EXECUTION SERVICE: EXECUTE_REBALANCING_PLAN ===")
            logger.info(f"EXECUTION_SERVICE_TYPE: {type(self).__name__}")
            logger.info(f"RECEIVED_REBALANCE_PLAN_TYPE: {type(rebalance_plan)}")
            logger.info(f"RECEIVED_PLAN_COUNT: {len(rebalance_plan) if rebalance_plan else 0}")
            logger.info(f"DRY_RUN_MODE: {dry_run}")

            if not rebalance_plan:
                logger.error("❌ EXECUTION_SERVICE: Empty rebalance plan received")
                logger.error("❌ This indicates portfolio facade failed to generate plans")
                return {
                    "status": "error",
                    "message": "Empty rebalance plan received",
                    "orders_placed": {},
                    "execution_summary": {
                        "total_orders": 0,
                        "successful_orders": 0,
                        "failed_orders": 0,
                    },
                }

            # Enhanced plan analysis logging
            logger.info("=== REBALANCE PLAN ANALYSIS ===")
            for symbol, plan in rebalance_plan.items():
                logger.info(f"PLAN_{symbol}: needs_rebalance={plan.needs_rebalance}")
                if plan.needs_rebalance:
                    action = "SELL" if plan.trade_amount < 0 else "BUY"
                    logger.info(f"  ACTION: {action} ${abs(plan.trade_amount):.2f}")
                    logger.info(
                        f"  DETAILS: weight_diff={plan.weight_diff:.4f}, trade_amount={plan.trade_amount:.2f}"
                    )

            # Filter plans that need rebalancing
            plans_to_execute = {
                symbol: plan for symbol, plan in rebalance_plan.items() if plan.needs_rebalance
            }

            # Enhanced filtering results logging
            needs_rebalance_count = len(plans_to_execute)
            logger.info(
                f"FILTERING_RESULTS: {len(rebalance_plan)} total plans → {needs_rebalance_count} need execution"
            )

            # === DETAILED PLAN ANALYSIS ===
            logger.info("=== DETAILED EXECUTION SERVICE PLAN ANALYSIS ===")
            for symbol, plan in rebalance_plan.items():
                logger.info(f"PLAN_ANALYSIS_{symbol}:")
                logger.info(
                    f"  needs_rebalance: {plan.needs_rebalance} (type: {type(plan.needs_rebalance)})"
                )
                logger.info(
                    f"  trade_amount: {plan.trade_amount} (type: {type(plan.trade_amount)})"
                )
                logger.info(f"  symbol: {plan.symbol}")

                if plan.needs_rebalance:
                    action = "SELL" if plan.trade_amount < 0 else "BUY"
                    logger.info(f"  → ACTION: {action} ${abs(plan.trade_amount):.2f}")
                else:
                    logger.info("  → SKIPPED: below threshold")

            if needs_rebalance_count > 0:
                logger.info("PLANS_TO_EXECUTE:")
                for symbol, plan in plans_to_execute.items():
                    action = "SELL" if plan.trade_amount < 0 else "BUY"
                    logger.info(f"  {symbol}: {action} ${abs(plan.trade_amount):.2f}")
            else:
                logger.warning("❌ NO PLANS TO EXECUTE after filtering")

            if logger.isEnabledFor(logging.DEBUG):
                for symbol, plan in rebalance_plan.items():
                    logger.debug(
                        f"Plan {symbol}: needs_rebalance={plan.needs_rebalance}, "
                        f"trade_amount={plan.trade_amount}, weight_diff={plan.weight_diff}"
                    )

            if not plans_to_execute:
                logger.info(
                    "✅ EXECUTION_SERVICE: No rebalancing required - returning success with 0 orders"
                )
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

            # === EXECUTION PHASES ===
            logger.info("=== EXECUTION PHASE 1: SELL ORDERS ===")
            # Execute sells first to free up capital
            sell_results = self._execute_sell_orders(plans_to_execute, dry_run)
            logger.info(f"SELL_PHASE_COMPLETE: {len(sell_results)} sell orders processed")

            logger.info("=== EXECUTION PHASE 2: BUY ORDERS ===")
            # Execute buys with freed capital
            buy_results = self._execute_buy_orders(plans_to_execute, dry_run)
            logger.info(f"BUY_PHASE_COMPLETE: {len(buy_results)} buy orders processed")

            # Combine results
            all_orders = {**sell_results, **buy_results}

            # === FINAL EXECUTION RESULTS ===
            logger.info("=== EXECUTION SERVICE FINAL RESULTS ===")
            logger.info(f"TOTAL_ORDERS_CREATED: {len(all_orders)}")
            logger.info(f"SELL_ORDERS: {len(sell_results)}")
            logger.info(f"BUY_ORDERS: {len(buy_results)}")

            if all_orders:
                logger.info("ORDERS_CREATED_DETAILS:")
                for symbol, order_data in all_orders.items():
                    logger.info(f"  {symbol}: {order_data}")
            else:
                logger.warning("❌ NO ORDERS CREATED despite having plans to execute")
                logger.warning(
                    f"❌ This indicates order creation failed for {needs_rebalance_count} planned trades"
                )

            execution_summary = self._create_execution_summary(all_orders)
            logger.info(f"EXECUTION_SUMMARY: {execution_summary}")

            result = {
                "status": "success",
                "message": f"Executed {len(all_orders)} rebalancing orders",
                "orders_placed": all_orders,
                "execution_summary": execution_summary,
                "sell_orders": sell_results,
                "buy_orders": buy_results,
            }

            logger.info("=== EXECUTION SERVICE COMPLETE ===")
            return result

        except Exception as e:
            logger.error(f"❌ EXECUTION_SERVICE_EXCEPTION: {e}")
            logger.exception("Full execution service exception details:")
            self.error_handler.handle_error(
                error=e,
                component="RebalanceExecutionService.execute_rebalancing_plan",
                context="rebalancing_execution",
                additional_data={"plan_symbols": list(rebalance_plan.keys()), "dry_run": dry_run},
            )
            raise StrategyExecutionError(f"Rebalancing execution failed: {e}") from e

    def execute_rebalancing_plan_direct(
        self, rebalance_plan: dict[str, RebalancePlan], dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute rebalancing plan directly from plan data without position validation.
        
        This method addresses the core issue by executing trades directly from the 
        rebalance plan without requiring additional position data fetching or validation.
        The plan already contains all necessary trade specifications.

        Args:
            rebalance_plan: Complete rebalancing plan to execute
            dry_run: If True, only simulate execution without placing real orders

        Returns:
            Execution results with order details and status

        """
        try:
            logger.info("=== REBALANCE EXECUTION SERVICE: DIRECT EXECUTION (NO POSITION VALIDATION) ===")
            logger.info(f"EXECUTION_SERVICE_TYPE: {type(self).__name__}")
            logger.info(f"RECEIVED_REBALANCE_PLAN_TYPE: {type(rebalance_plan)}")
            logger.info(f"RECEIVED_PLAN_COUNT: {len(rebalance_plan) if rebalance_plan else 0}")
            logger.info(f"DRY_RUN_MODE: {dry_run}")
            logger.info("BYPASSING_POSITION_DATA_VALIDATION: Using plan data directly")

            if not rebalance_plan:
                logger.error("❌ EXECUTION_SERVICE: Empty rebalance plan received")
                return {
                    "status": "error",
                    "message": "Empty rebalance plan received",
                    "orders_placed": {},
                    "execution_summary": {
                        "total_orders": 0,
                        "successful_orders": 0,
                        "failed_orders": 0,
                    },
                }

            # Direct execution from plan data - no position validation required
            logger.info("=== EXECUTING DIRECTLY FROM PLAN DATA ===")
            
            # Filter plans that need rebalancing (plan data is trusted)
            plans_to_execute = {
                symbol: plan
                for symbol, plan in rebalance_plan.items()
                if hasattr(plan, "needs_rebalance") and isinstance(plan.needs_rebalance, bool) and plan.needs_rebalance
            }

            logger.info(f"PLANS_TO_EXECUTE_COUNT: {len(plans_to_execute)}")
            
            if not plans_to_execute:
                logger.info("✅ No rebalancing required - returning success with 0 orders")
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

            # Execute all trades directly from plan specifications
            all_orders = {}
            
            # Process all trades in plan order (sells will naturally come first if needed)
            for symbol, plan in plans_to_execute.items():
                if plan.trade_amount > 0:
                    # Buy order
                    result = self._place_buy_order(symbol, abs(plan.trade_amount), dry_run)
                    all_orders[symbol] = result
                    logger.info(f"BUY_ORDER_PLACED: {symbol} ${abs(plan.trade_amount)}")
                elif plan.trade_amount < 0:
                    # Sell order  
                    result = self._place_sell_order(symbol, abs(plan.trade_amount), dry_run)
                    all_orders[symbol] = result
                    logger.info(f"SELL_ORDER_PLACED: {symbol} ${abs(plan.trade_amount)}")

            execution_summary = self._create_execution_summary(all_orders)
            logger.info(f"DIRECT_EXECUTION_SUMMARY: {execution_summary}")

            result = {
                "status": "success",
                "message": f"Executed {len(all_orders)} rebalancing orders directly from plan",
                "orders_placed": all_orders,
                "execution_summary": execution_summary,
            }

            logger.info("=== DIRECT EXECUTION SERVICE COMPLETE ===")
            return result

        except Exception as e:
            logger.error(f"❌ DIRECT_EXECUTION_SERVICE_EXCEPTION: {e}")
            logger.exception("Full direct execution service exception details:")
            self.error_handler.handle_error(
                error=e,
                component="RebalanceExecutionService.execute_rebalancing_plan_direct",
                context="direct_rebalancing_execution",
                additional_data={"plan_symbols": list(rebalance_plan.keys()), "dry_run": dry_run},
            )
            raise StrategyExecutionError(f"Direct rebalancing execution failed: {e}") from e

    def execute_single_rebalance(
        self, symbol: str, plan: RebalancePlan, dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute rebalancing for a single symbol.

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
        """Validate a rebalancing plan before execution.

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
                    # Do not fail validation; we will scale buys to available buying power during execution
                    validation_results["warnings"].append(
                        {
                            "type": "INSUFFICIENT_BUYING_POWER",
                            "message": (
                                "Insufficient buying power for full rebalance; buys will be scaled "
                                "to available funds."
                            ),
                            "need": str(buy_amount),
                            "have": str(buying_power),
                            "sell_proceeds": str(sell_proceeds),
                        }
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
                    # Extract quantity robustly from position object
                    if position is None:
                        qty = Decimal("0")
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
        """Execute all buy orders from the rebalancing plan, capped to available buying power."""
        import logging

        buy_orders: dict[str, Any] = {}

        # Determine available buying power now (after sells, if any)
        try:
            account_summary = self.trading_manager.account.get_account_summary()
            remaining_bp = Decimal(str(account_summary.get("buying_power", 0)))
        except Exception:
            remaining_bp = Decimal("0")

        # Apply a tiny safety buffer (e.g., 5 bps of remaining bp) to avoid broker-side rounding rejects
        safety_buffer = (remaining_bp * Decimal("0.0005")).quantize(Decimal("0.01"))
        if safety_buffer > 0 and remaining_bp > safety_buffer:
            remaining_bp -= safety_buffer

        logging.debug(
            "Starting buy execution with available buying power: %s (after buffer %s)",
            str(remaining_bp),
            str(safety_buffer),
        )

        # Execute buys in arbitrary but stable order
        for symbol, plan in rebalance_plan.items():
            if not (plan.needs_rebalance and plan.trade_amount > 0):
                continue

            if remaining_bp <= Decimal("0"):
                logging.info("No remaining buying power; skipping remaining buy orders")
                break

            requested_amount = plan.trade_amount
            amount_to_buy = requested_amount if requested_amount <= remaining_bp else remaining_bp

            # Place scaled order (or full if within limit)
            result = self._place_buy_order(symbol, amount_to_buy, dry_run)

            # Annotate result if scaled down
            if amount_to_buy < requested_amount:
                result["status"] = result.get("status", "placed")
                result["message"] = (
                    result.get("message", "") + f" (scaled to ${amount_to_buy} due to buying power)"
                ).strip()

            buy_orders[symbol] = result

            # Update remaining buying power optimistically by amount used
            remaining_bp -= amount_to_buy

        return buy_orders

    def _place_sell_order(self, symbol: str, amount: Decimal, dry_run: bool) -> dict[str, Any]:
        """Place a sell order for the specified amount."""
        logger.debug(
            f"_place_sell_order called: symbol={symbol}, amount={amount}, dry_run={dry_run}"
        )
        try:
            if dry_run:
                logger.debug(f"Placing DRY RUN sell order for {symbol}")
                return {
                    "symbol": symbol,
                    "side": "sell",
                    "amount": amount,
                    "status": "simulated",
                    "order_id": f"DRY_SELL_{symbol}",
                    "message": f"Would sell ${amount} of {symbol}",
                }

            # Use smart execution for sell order
            logger.debug(f"Placing LIVE sell order for {symbol}")
            price_val = self.trading_manager.alpaca_manager.get_current_price(symbol)
            try:
                price = Decimal(str(price_val))
            except Exception:
                price = Decimal("0")

            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}: {price_val}")

            shares_to_sell = amount / price
            logger.debug(f"Calculated shares to sell: {shares_to_sell} at price ${price}")

            order_result = self.smart_execution.place_order(
                symbol=symbol, qty=float(shares_to_sell), side=BrokerOrderSide.SELL.to_alpaca()
            )

            result = {
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "shares": shares_to_sell,
                "status": "placed",
                "order_id": order_result,
                "message": f"Placed sell order for {shares_to_sell} shares of {symbol}",
            }
            logger.debug(f"Sell order result: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to place sell order for {symbol}: {e}")
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
        logger.debug(
            f"_place_buy_order called: symbol={symbol}, amount={amount}, dry_run={dry_run}"
        )
        try:
            if dry_run:
                logger.debug(f"Placing DRY RUN buy order for {symbol}")
                return {
                    "symbol": symbol,
                    "side": "buy",
                    "amount": amount,
                    "status": "simulated",
                    "order_id": f"DRY_BUY_{symbol}",
                    "message": f"Would buy ${amount} of {symbol}",
                }

            # Use smart execution for buy order
            logger.debug(f"Placing LIVE buy order for {symbol}")
            price_val = self.trading_manager.alpaca_manager.get_current_price(symbol)
            try:
                price = Decimal(str(price_val))
            except Exception:
                price = Decimal("0")

            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}: {price_val}")

            shares_to_buy = amount / price
            logger.debug(f"Calculated shares to buy: {shares_to_buy} at price ${price}")

            order_result = self.smart_execution.place_order(
                symbol=symbol, qty=float(shares_to_buy), side=BrokerOrderSide.BUY.to_alpaca()
            )

            result = {
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "shares": shares_to_buy,
                "status": "placed",
                "order_id": order_result,
                "message": f"Placed buy order for {shares_to_buy} shares of {symbol}",
            }
            logger.debug(f"Buy order result: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to place buy order for {symbol}: {e}")
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
