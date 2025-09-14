"""Business Unit: orchestration | Status: current

Trading execution orchestration workflow.

Coordinates the complete trading execution workflow including signal generation,
portfolio rebalancing, order execution, and result reporting. Uses the new
orchestration and execution_v2 modules.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from the_alchemiser.orchestration.signal_orchestrator import SignalOrchestrator
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.exceptions import (
    NotificationError,
    TradingClientError,
)


class TradingOrchestrator:
    """Orchestrates trading execution workflow."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        live_trading: bool = False,  # DEPRECATED - determined by stage
        ignore_market_hours: bool = False,
    ) -> None:
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)
        
        # Get trading mode from container (ignore deprecated parameter)
        self.live_trading = not self.container.config.paper_trading()

        if live_trading != self.live_trading:
            self.logger.warning(
                f"live_trading parameter ({live_trading}) ignored. "
                f"Using endpoint-determined mode: {'live' if self.live_trading else 'paper'}"
            )

        self.ignore_market_hours = ignore_market_hours

        # Create signal orchestrator for signal generation
        self.signal_orchestrator = SignalOrchestrator(settings, container)

        # Create portfolio orchestrator for allocation analysis
        self.portfolio_orchestrator = PortfolioOrchestrator(settings, container)

    def check_market_hours(self) -> bool:
        """Check if market is open for trading."""
        if self.ignore_market_hours:
            return True

        # Use AlpacaManager's is_market_open method
        alpaca_manager = self.container.infrastructure.alpaca_manager()
        if not alpaca_manager.is_market_open():
            self.logger.warning("Market is closed. No trades will be placed.")
            self._send_market_closed_notification()
            return False

        return True

    def _send_market_closed_notification(self) -> None:
        """Send market closed notification."""
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            html_content = build_error_email_html(
                "Market Closed Alert",
                "Market is currently closed. No trades will be placed.",
            )
            send_email_notification(
                subject="📈 The Alchemiser - Market Closed Alert",
                html_content=html_content,
                text_content="Market is CLOSED. No trades will be placed.",
            )
        except NotificationError as e:
            self.logger.warning(f"Failed to send market closed notification: {e}")

    def execute_strategy_signals_with_trading(self) -> dict[str, Any] | None:
        """Generate strategy signals AND execute actual trades, returning comprehensive execution data."""
        try:
            # Generate signals using signal orchestrator
            result = self.signal_orchestrator.analyze_signals()
            if result is None:
                self.logger.error("Failed to generate strategy signals")
                return None

            strategy_signals, consolidated_portfolio = result

            # Get comprehensive account data using portfolio orchestrator
            account_data = self.portfolio_orchestrator.get_comprehensive_account_data()
            account_info = None
            current_positions = {}
            allocation_comparison = None
            execution_result = None
            orders_executed = []
            open_orders = []

            if account_data:
                account_info = account_data.get("account_info")
                current_positions = account_data.get("current_positions", {})
                open_orders = account_data.get("open_orders", [])

                # Calculate allocation comparison if we have the necessary data
                if account_info and consolidated_portfolio:
                    allocation_analysis = self.portfolio_orchestrator.analyze_allocation_comparison(
                        consolidated_portfolio
                    )
                    if allocation_analysis:
                        allocation_comparison = allocation_analysis.get("comparison")
                        self.logger.info("Generated allocation comparison analysis")

                # NOW DO ACTUAL TRADING: Use proper ExecutionManager to place trades
                if allocation_comparison and account_info:
                    self.logger.info("🚀 EXECUTING ACTUAL TRADES")

                    # Convert allocation comparison to RebalancePlanDTO
                    rebalance_plan = self._create_rebalance_plan_from_allocation(
                        allocation_comparison, account_info
                    )

                    if rebalance_plan:
                        self.logger.info(f"📋 Generated rebalance plan with {len(rebalance_plan.items)} items")

                        # Get ExecutionManager from container
                        execution_manager = self.container.services.execution_manager()

                        # Execute the rebalance plan
                        execution_result = execution_manager.execute_rebalance_plan(rebalance_plan)

                        # Convert ExecutionResultDTO to format expected by CLI
                        orders_executed = self._convert_execution_result_to_orders(execution_result)

                        self.logger.info(
                            f"✅ Execution completed: {execution_result.orders_succeeded}/{execution_result.orders_placed} orders succeeded"
                        )

                        # Log detailed execution results
                        self._log_detailed_execution_results(execution_result)
                    else:
                        self.logger.info(
                            "📊 No significant trades needed - portfolio already balanced"
                        )
                else:
                    self.logger.warning(
                        "Could not calculate trades - missing allocation comparison data"
                    )
            else:
                self.logger.warning("Could not retrieve account data for trading")

            return {
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio,
                "account_info": account_info,
                "current_positions": current_positions,
                "allocation_comparison": allocation_comparison,
                "orders_executed": orders_executed,
                "execution_result": execution_result,
                "open_orders": open_orders,
                "success": True,
                "message": "Strategy execution with trading completed successfully",
            }

        except Exception as e:
            self.logger.error(f"Strategy execution with trading failed: {e}")
            return None

    def execute_strategy_signals(self) -> dict[str, Any] | None:
        """Generate strategy signals and return comprehensive execution data including account info (signal mode)."""
        try:
            # Generate signals using signal orchestrator
            result = self.signal_orchestrator.analyze_signals()
            if result is None:
                self.logger.error("Failed to generate strategy signals")
                return None

            strategy_signals, consolidated_portfolio = result

            # Get comprehensive account data using portfolio orchestrator
            account_data = self.portfolio_orchestrator.get_comprehensive_account_data()
            account_info = None
            current_positions = {}
            allocation_comparison = None
            open_orders = []

            if account_data:
                account_info = account_data.get("account_info")
                current_positions = account_data.get("current_positions", {})
                open_orders = account_data.get("open_orders", [])

                # Calculate allocation comparison if we have the necessary data
                if account_info and consolidated_portfolio:
                    allocation_analysis = self.portfolio_orchestrator.analyze_allocation_comparison(
                        consolidated_portfolio
                    )
                    if allocation_analysis:
                        allocation_comparison = allocation_analysis.get("comparison")
                        self.logger.info("Generated allocation comparison analysis")
            else:
                self.logger.warning(
                    "Could not retrieve account data - continuing with basic signal data"
                )

            return {
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio,
                "account_info": account_info,
                "current_positions": current_positions,
                "allocation_comparison": allocation_comparison,
                "open_orders": open_orders,
                "success": True,
                "message": "Signal generation completed successfully with account integration",
            }

        except Exception as e:
            self.logger.error(f"Strategy signal execution failed: {e}")
            return None

    def send_trading_notification(self, result: dict[str, Any], mode_str: str) -> None:
        """Send trading completion notification.

        Args:
            result: The execution result dictionary
            mode_str: Trading mode string for display

        """
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            # Create simple HTML content for the result
            success = result.get("success", False)
            message = result.get("message", "Trading execution completed")

            if success:
                html_content = f"""
                <h2>Trading Execution Report - {mode_str.upper()}</h2>
                <p><strong>Status:</strong> Success</p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Timestamp:</strong> {datetime.now(UTC)}</p>
                """
            else:
                html_content = build_error_email_html(
                    "Trading Execution Failed",
                    message,
                )

            send_email_notification(
                subject=f"📈 The Alchemiser - {mode_str.upper()} Trading Report",
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {success}",
            )

        except NotificationError as e:
            self.logger.warning(f"Email notification failed: {e}")
        except Exception as e:
            self.logger.warning(f"Email formatting/connection error: {e}")

    def handle_trading_error(self, error: Exception, mode_str: str) -> None:
        """Handle trading execution errors."""
        try:
            from the_alchemiser.shared.errors.error_handler import (
                TradingSystemErrorHandler,
                send_error_notification_if_needed,
            )

            # Use TradingSystemErrorHandler directly for consistency
            error_handler = TradingSystemErrorHandler()
            error_handler.handle_error(
                error=error,
                context="multi-strategy trading execution",
                component="TradingOrchestrator.execute",
                additional_data={
                    "mode": mode_str,
                    "live_trading": self.live_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )

            send_error_notification_if_needed()

        except NotificationError as notification_error:
            self.logger.warning(f"Failed to send error notification: {notification_error}")

    def execute_trading_workflow(self) -> bool:
        """Execute complete trading workflow.

        Returns:
            True if trading succeeded, False otherwise

        """
        mode_str = "LIVE" if self.live_trading else "PAPER"

        try:
            # System now uses fully typed domain model
            self.logger.info("Using typed StrategySignal domain model")

            # Check market hours
            if not self.check_market_hours():
                self.logger.info("Market closed - no action taken")
                return True  # Not an error, just market closed

            # Execute strategy signals with actual trading
            result = self.execute_strategy_signals_with_trading()
            if result is None:
                self.logger.error("Strategy execution failed")
                return False

            # Send notification
            self.send_trading_notification(result, mode_str)

            return bool(result.get("success", False))

        except TradingClientError as e:
            self.handle_trading_error(e, mode_str)
            return False

        except Exception as e:
            self.handle_trading_error(e, mode_str)
            return False

    def execute_trading_workflow_with_details(self) -> dict[str, Any] | None:
        """Execute complete trading workflow and return detailed results.

        Returns:
            Dictionary with strategy signals, portfolio, and success status, or None if failed

        """
        mode_str = "LIVE" if self.live_trading else "PAPER"

        try:
            # System now uses fully typed domain model
            self.logger.info("Using typed StrategySignal domain model")

            # Check market hours
            if not self.check_market_hours():
                self.logger.info("Market closed - no action taken")
                return {
                    "strategy_signals": {},
                    "consolidated_portfolio": {},
                    "success": True,
                    "message": "Market closed - no action taken",
                }

            # Execute strategy signals with actual trading
            result = self.execute_strategy_signals_with_trading()
            if result is None:
                self.logger.error("Strategy execution failed")
                return None

            # Send notification
            self.send_trading_notification(result, mode_str)

            return result

        except TradingClientError as e:
            self.handle_trading_error(e, mode_str)
            return None

        except Exception as e:
            self.handle_trading_error(e, mode_str)
            return None

    def _create_rebalance_plan_from_allocation(
        self, allocation_comparison: dict[str, Any], account_info: dict[str, Any]
    ) -> RebalancePlanDTO | None:
        """Convert allocation comparison data to RebalancePlanDTO.

        Args:
            allocation_comparison: Allocation comparison data with target_values, current_values, deltas
            account_info: Account information including portfolio_value

        Returns:
            RebalancePlanDTO ready for execution, or None if no significant trades needed

        """
        try:
            # Extract allocation comparison data
            target_values = allocation_comparison.get("target_values", {})
            current_values = allocation_comparison.get("current_values", {})
            deltas = allocation_comparison.get("deltas", {})

            if not target_values or not deltas:
                self.logger.warning("Missing allocation comparison data")
                return None

            # Filter for significant trades (> $100)
            min_trade_amount = Decimal("100")
            plan_items = []
            total_trade_value = Decimal("0")

            portfolio_value = account_info.get("portfolio_value", account_info.get("equity", 0))
            portfolio_value_decimal = Decimal(str(portfolio_value))

            for symbol, delta in deltas.items():
                delta_decimal = Decimal(str(delta))
                if abs(delta_decimal) >= min_trade_amount:
                    # Determine action
                    action = "BUY" if delta_decimal > 0 else "SELL"

                    # Calculate weights
                    target_val = target_values.get(symbol, Decimal("0"))
                    current_val = current_values.get(symbol, Decimal("0"))

                    target_weight = target_val / portfolio_value_decimal if portfolio_value_decimal > 0 else Decimal("0")
                    current_weight = current_val / portfolio_value_decimal if portfolio_value_decimal > 0 else Decimal("0")

                    plan_item = RebalancePlanItemDTO(
                        symbol=symbol,
                        current_weight=current_weight,
                        target_weight=target_weight,
                        weight_diff=target_weight - current_weight,
                        target_value=target_val,
                        current_value=current_val,
                        trade_amount=delta_decimal,
                        action=action,
                        priority=1,  # All trades have equal priority for now
                    )
                    plan_items.append(plan_item)
                    total_trade_value += abs(delta_decimal)

            if not plan_items:
                self.logger.info("No significant trades needed - all deltas below threshold")
                return None

            # Create correlation IDs
            correlation_id = str(uuid.uuid4())
            plan_id = f"rebalance-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

            rebalance_plan = RebalancePlanDTO(
                correlation_id=correlation_id,
                causation_id=f"trading-orchestrator-{correlation_id}",
                timestamp=datetime.now(UTC),
                plan_id=plan_id,
                items=plan_items,
                total_portfolio_value=portfolio_value_decimal,
                total_trade_value=total_trade_value,
                execution_urgency="NORMAL",
            )

            return rebalance_plan

        except Exception as e:
            self.logger.error(f"Failed to create rebalance plan: {e}")
            return None

    def _convert_execution_result_to_orders(self, execution_result: ExecutionResultDTO) -> list[dict[str, Any]]:
        """Convert ExecutionResultDTO to format expected by CLI display.

        Args:
            execution_result: ExecutionResultDTO from ExecutionManager

        Returns:
            List of order dictionaries in format expected by CLI

        """
        orders_executed = []

        for order in execution_result.orders:
            order_dict = {
                "symbol": order.symbol,
                "side": order.action,
                "qty": float(order.shares) if order.shares else 0,
                "filled_qty": float(order.shares) if order.success and order.shares else 0,
                "filled_avg_price": float(order.price) if order.price else 0,
                "estimated_value": float(abs(order.trade_amount)),
                "order_id": order.order_id,
                "status": "FILLED" if order.success else "FAILED",
                "error": order.error_message,
            }
            orders_executed.append(order_dict)

        return orders_executed

    def _log_detailed_execution_results(self, execution_result: ExecutionResultDTO) -> None:
        """Log detailed execution results for each order.

        Args:
            execution_result: ExecutionResultDTO with order details

        """
        for order in execution_result.orders:
            if order.success:
                self.logger.info(
                    f"✅ {order.action} {order.symbol}: "
                    f"{order.shares:.4f} shares @ ${order.price:.2f} "
                    f"(Order ID: {order.order_id})"
                )
            else:
                self.logger.error(
                    f"❌ {order.action} {order.symbol} FAILED: {order.error_message}"
                )

        # Log summary
        self.logger.info(
            f"📊 Execution Summary: {execution_result.orders_succeeded}/{execution_result.orders_placed} "
            f"orders succeeded, ${execution_result.total_trade_value} total trade value"
        )
