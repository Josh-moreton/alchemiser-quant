"""Rebalance execution service - handles trade execution for rebalancing."""

from decimal import Decimal
from typing import Any

from the_alchemiser.application.smart_execution import SmartExecution
from the_alchemiser.domain.portfolio.types.rebalance_plan import RebalancePlan
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager
from the_alchemiser.services.error_handler import TradingSystemErrorHandler
from the_alchemiser.services.exceptions import StrategyExecutionError


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
        error_handler: TradingSystemErrorHandler | None = None
    ):
        """
        Initialize the rebalance execution service.
        
        Args:
            trading_manager: Service for trading operations
            smart_execution: Smart execution engine (optional)
            error_handler: Error handler for trading errors (optional)
        """
        self.trading_manager = trading_manager
        self.smart_execution = smart_execution or SmartExecution(trading_manager)
        self.error_handler = error_handler or TradingSystemErrorHandler()

    def execute_rebalancing_plan(
        self,
        rebalance_plan: dict[str, RebalancePlan],
        dry_run: bool = True
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
                symbol: plan for symbol, plan in rebalance_plan.items()
                if plan.needs_rebalance
            }

            if not plans_to_execute:
                return {
                    "status": "success",
                    "message": "No rebalancing required",
                    "orders_placed": {},
                    "execution_summary": {
                        "total_orders": 0,
                        "successful_orders": 0,
                        "failed_orders": 0
                    }
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
                "buy_orders": buy_results
            }

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                component="RebalanceExecutionService.execute_rebalancing_plan",
                context="rebalancing_execution",
                additional_data={"plan_symbols": list(rebalance_plan.keys()), "dry_run": dry_run}
            )
            raise StrategyExecutionError(f"Rebalancing execution failed: {e}") from e

    def execute_single_rebalance(
        self,
        symbol: str,
        plan: RebalancePlan,
        dry_run: bool = True
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
                    "order_id": None
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
                additional_data={"symbol": symbol, "trade_amount": str(plan.trade_amount)}
            )
            return {
                "symbol": symbol,
                "status": "failed",
                "message": f"Execution failed: {e}",
                "order_id": None,
                "error": str(e)
            }

    def validate_rebalancing_plan(self, rebalance_plan: dict[str, RebalancePlan]) -> dict[str, Any]:
        """
        Validate a rebalancing plan before execution.
        
        Args:
            rebalance_plan: Plan to validate
            
        Returns:
            Validation results with any issues found
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "total_trade_value": Decimal("0"),
            "symbols_to_trade": []
        }

        try:
            # Check for symbols needing rebalancing
            symbols_to_trade = [
                symbol for symbol, plan in rebalance_plan.items()
                if plan.needs_rebalance
            ]
            validation_results["symbols_to_trade"] = symbols_to_trade

            if not symbols_to_trade:
                validation_results["warnings"].append("No symbols require rebalancing")
                return validation_results

            # Calculate total trade value
            total_trade_value = sum(
                abs(plan.trade_amount) for plan in rebalance_plan.values()
                if plan.needs_rebalance
            )
            validation_results["total_trade_value"] = total_trade_value

            # Validate account balance for buy orders
            buy_amount = sum(
                plan.trade_amount for plan in rebalance_plan.values()
                if plan.needs_rebalance and plan.trade_amount > 0
            )
            
            if buy_amount > 0:
                buying_power = self.trading_manager.get_buying_power()
                if buy_amount > Decimal(str(buying_power)):
                    validation_results["is_valid"] = False
                    validation_results["issues"].append(
                        f"Insufficient buying power: need ${buy_amount}, have ${buying_power}"
                    )

            # Validate positions for sell orders
            for symbol, plan in rebalance_plan.items():
                if plan.needs_rebalance and plan.trade_amount < 0:
                    position = self.trading_manager.get_position(symbol)
                    if not position or position.qty <= 0:
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
                additional_data={"plan_symbols": list(rebalance_plan.keys())}
            )
            validation_results["is_valid"] = False
            validation_results["issues"].append(f"Validation error: {e}")
            return validation_results

    def _execute_sell_orders(
        self,
        rebalance_plan: dict[str, RebalancePlan],
        dry_run: bool
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
        self,
        rebalance_plan: dict[str, RebalancePlan],
        dry_run: bool
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
                    "message": f"Would sell ${amount} of {symbol}"
                }

            # Use smart execution for sell order
            current_price = self.trading_manager.get_latest_price(symbol)
            shares_to_sell = amount / Decimal(str(current_price))
            
            order_result = self.smart_execution.execute_progressive_order(
                symbol=symbol,
                side="sell",
                quantity=float(shares_to_sell),
                order_type="market"
            )

            return {
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "shares": shares_to_sell,
                "status": "placed",
                "order_id": order_result.get("order_id"),
                "message": f"Placed sell order for {shares_to_sell} shares of {symbol}"
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "status": "failed",
                "order_id": None,
                "error": str(e),
                "message": f"Failed to place sell order: {e}"
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
                    "message": f"Would buy ${amount} of {symbol}"
                }

            # Use smart execution for buy order
            current_price = self.trading_manager.get_latest_price(symbol)
            shares_to_buy = amount / Decimal(str(current_price))
            
            order_result = self.smart_execution.execute_progressive_order(
                symbol=symbol,
                side="buy",
                quantity=float(shares_to_buy),
                order_type="market"
            )

            return {
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "shares": shares_to_buy,
                "status": "placed",
                "order_id": order_result.get("order_id"),
                "message": f"Placed buy order for {shares_to_buy} shares of {symbol}"
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "status": "failed",
                "order_id": None,
                "error": str(e),
                "message": f"Failed to place buy order: {e}"
            }

    def _create_execution_summary(self, orders: dict[str, Any]) -> dict[str, Any]:
        """Create summary of execution results."""
        total_orders = len(orders)
        successful_orders = sum(1 for order in orders.values() if order.get("status") in ["placed", "simulated"])
        failed_orders = total_orders - successful_orders

        return {
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "failed_orders": failed_orders,
            "success_rate": successful_orders / total_orders if total_orders > 0 else 0
        }
