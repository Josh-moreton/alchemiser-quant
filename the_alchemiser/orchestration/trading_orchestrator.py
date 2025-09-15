"""Business Unit: orchestration | Status: current.

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
from the_alchemiser.shared.dto.portfolio_state_dto import (
    PortfolioMetricsDTO,
    PortfolioStateDTO,
)
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.events import EventBus, TradeExecuted, TradeExecutionStarted
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.types.exceptions import (
    NotificationError,
    TradingClientError,
)

# Constants for repeated literals
DECIMAL_ZERO = Decimal("0")
MIN_TRADE_AMOUNT_USD = Decimal("100")


class TradingOrchestrator:
    """Orchestrates trading execution workflow."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        ignore_market_hours: bool = False,
    ) -> None:
        """Initialize trading orchestrator with settings and container."""
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)
        self.live_trading = not self.container.config.paper_trading()

        self.ignore_market_hours = ignore_market_hours

        # Get event bus from container for dual-path emission
        self.event_bus: EventBus = container.services.event_bus()

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
        """Generate strategy signals AND execute trades, returning comprehensive execution data."""
        return self._execute_strategy_signals_internal(execute_trades=True)

    def execute_strategy_signals(self) -> dict[str, Any] | None:
        """Generate strategy signals and return comprehensive execution data (signal mode)."""
        return self._execute_strategy_signals_internal(execute_trades=False)

    def _execute_strategy_signals_internal(
        self, execute_trades: bool
    ) -> dict[str, Any] | None:
        """Generate strategy signals with optional trade execution.

        Args:
            execute_trades: Whether to execute actual trades or just analyze signals

        Returns:
            Dictionary with strategy signals, portfolio, and execution data, or None if failed

        """
        try:
            # Generate signals using signal orchestrator with direct DTO access
            strategy_signals, consolidated_portfolio_dto = (
                self.signal_orchestrator.generate_signals()
            )
            if not strategy_signals:
                self.logger.error("Failed to generate strategy signals")
                return None

            # Validate signal quality before proceeding
            if not self.signal_orchestrator.validate_signal_quality(strategy_signals):
                self.logger.error(
                    "Signal analysis failed validation - no meaningful data available"
                )
                return None

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
                if account_info and consolidated_portfolio_dto:
                    allocation_comparison = (
                        self.portfolio_orchestrator.analyze_allocation_comparison(
                            consolidated_portfolio_dto
                        )
                    )
                    if allocation_comparison:
                        self.logger.info("Generated allocation comparison analysis")

                # Execute trades if requested and data is available
                if execute_trades and allocation_comparison and account_info:
                    self.logger.info("🚀 EXECUTING ACTUAL TRADES")

                    # Convert allocation comparison to RebalancePlanDTO
                    rebalance_plan = self._create_rebalance_plan_from_allocation(
                        allocation_comparison, account_info
                    )

                    if rebalance_plan:
                        self.logger.info(
                            f"📋 Generated rebalance plan with {len(rebalance_plan.items)} items"
                        )

                        # DUAL-PATH: Emit TradeExecutionStarted event for event-driven consumers
                        execution_plan = {
                            "plan_id": rebalance_plan.plan_id,
                            "trade_count": len(rebalance_plan.items),
                            "total_trade_value": float(
                                rebalance_plan.total_trade_value
                            ),
                            "trades": [
                                {
                                    "symbol": item.symbol,
                                    "action": item.action,
                                    "trade_amount": float(item.trade_amount),
                                    "target_value": float(item.target_value),
                                    "current_value": float(item.current_value),
                                }
                                for item in rebalance_plan.items
                            ],
                        }
                        mode_str = "LIVE" if self.live_trading else "PAPER"
                        self._emit_trade_execution_started_event(
                            execution_plan, mode_str
                        )

                        # Get ExecutionManager from container
                        execution_manager = self.container.services.execution_manager()

                        # Execute the rebalance plan
                        execution_result = execution_manager.execute_rebalance_plan(
                            rebalance_plan
                        )

                        # Convert ExecutionResultDTO to format expected by CLI
                        orders_executed = self._convert_execution_result_to_orders(
                            execution_result
                        )

                        self.logger.info(
                            f"✅ Execution completed: {execution_result.orders_succeeded}/"
                            f"{execution_result.orders_placed} orders succeeded"
                        )

                        # DUAL-PATH: Emit TradeExecuted event for event-driven consumers
                        execution_success = (
                            execution_result.orders_succeeded > 0
                            and execution_result.orders_succeeded
                            == execution_result.orders_placed
                        )
                        self._emit_trade_executed_event(
                            execution_result, execution_success
                        )

                        # Log detailed execution results
                        self._log_detailed_execution_results(execution_result)
                    else:
                        self.logger.info(
                            "📊 No significant trades needed - portfolio already balanced"
                        )

                        # DUAL-PATH: Emit TradeExecuted event for successful no-trade scenario
                        # Create empty execution result to represent successful no-op

                        no_trade_result = ExecutionResultDTO(
                            success=True,
                            plan_id=f"no-trade-{uuid.uuid4()}",
                            correlation_id=str(uuid.uuid4()),
                            orders=[],
                            orders_placed=0,
                            orders_succeeded=0,
                            total_trade_value=DECIMAL_ZERO,
                            execution_timestamp=datetime.now(UTC),
                            metadata={"scenario": "no_trades_needed"},
                        )
                        self._emit_trade_executed_event(no_trade_result, True)
                elif execute_trades:
                    self.logger.warning(
                        "Could not calculate trades - missing allocation comparison data"
                    )
            else:
                warning_msg = (
                    "Could not retrieve account data for trading"
                    if execute_trades
                    else "Could not retrieve account data - continuing with basic signal data"
                )
                self.logger.warning(warning_msg)

            # Determine success message based on mode
            success_message = (
                "Strategy execution with trading completed successfully"
                if execute_trades
                else "Signal generation completed successfully with account integration"
            )

            return {
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio_dto.to_dict_allocation(),
                "account_info": account_info,
                "current_positions": current_positions,
                "allocation_comparison": allocation_comparison,
                "orders_executed": orders_executed,
                "execution_result": execution_result,
                "open_orders": open_orders,
                "success": True,
                "message": success_message,
            }

        except Exception as e:
            error_context = "with trading" if execute_trades else "signal execution"
            self.logger.error(f"Strategy execution {error_context} failed: {e}")

            # DUAL-PATH: Emit TradeExecuted event for failure case
            if execute_trades:
                try:
                    failed_result = ExecutionResultDTO(
                        success=False,
                        plan_id=f"failed-{uuid.uuid4()}",
                        correlation_id=str(uuid.uuid4()),
                        orders=[],
                        orders_placed=0,
                        orders_succeeded=0,
                        total_trade_value=DECIMAL_ZERO,
                        execution_timestamp=datetime.now(UTC),
                        metadata={"error": str(e)},
                    )
                    self._emit_trade_executed_event(failed_result, False, str(e))
                except Exception as emit_error:
                    self.logger.warning(f"Failed to emit failure event: {emit_error}")

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
            self.logger.warning(
                f"Failed to send error notification: {notification_error}"
            )

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
        self,
        allocation_comparison: AllocationComparisonDTO,
        account_info: dict[str, Any],
    ) -> RebalancePlanDTO | None:
        """Convert allocation comparison DTO to RebalancePlanDTO.

        Args:
            allocation_comparison: AllocationComparisonDTO with target/current values, deltas
            account_info: Account information including portfolio_value

        Returns:
            RebalancePlanDTO ready for execution, or None if no significant trades needed

        """
        try:
            # Extract allocation comparison data directly from DTO
            target_values = allocation_comparison.target_values
            current_values = allocation_comparison.current_values
            deltas = allocation_comparison.deltas

            if not target_values or not deltas:
                self.logger.warning("Missing allocation comparison data")
                return None

            # Calculate portfolio value once
            portfolio_value_decimal = self._extract_portfolio_value(account_info)
            # Create plan items for significant trades
            plan_items, total_trade_value = self._create_plan_items(
                deltas, target_values, current_values, portfolio_value_decimal
            )

            if not plan_items:
                self.logger.info(
                    "No significant trades needed - all deltas below threshold"
                )
                return None

            # Create final rebalance plan
            return self._build_rebalance_plan_dto(
                plan_items, total_trade_value, portfolio_value_decimal
            )

        except Exception as e:
            self.logger.error(f"Failed to create rebalance plan: {e}")
            return None

    def _extract_portfolio_value(self, account_info: dict[str, Any]) -> Decimal:
        """Extract portfolio value from account info."""
        portfolio_value = account_info.get(
            "portfolio_value", account_info.get("equity", 0)
        )
        return Decimal(str(portfolio_value))

    def _create_plan_items(
        self,
        deltas: dict[str, Decimal],
        target_values: dict[str, Decimal],
        current_values: dict[str, Decimal],
        portfolio_value_decimal: Decimal,
    ) -> tuple[list[RebalancePlanItemDTO], Decimal]:
        """Create plan items for symbols with significant deltas."""
        plan_items = []
        total_trade_value = DECIMAL_ZERO

        for symbol, delta in deltas.items():
            # Only include trades above minimum threshold
            if abs(delta) >= MIN_TRADE_AMOUNT_USD:
                plan_item = self._create_single_plan_item(
                    symbol,
                    delta,
                    target_values,
                    current_values,
                    portfolio_value_decimal,
                )
                plan_items.append(plan_item)
                total_trade_value += abs(delta)

        return plan_items, total_trade_value

    def _create_single_plan_item(
        self,
        symbol: str,
        delta: Decimal,
        target_values: dict[str, Decimal],
        current_values: dict[str, Decimal],
        portfolio_value_decimal: Decimal,
    ) -> RebalancePlanItemDTO:
        """Create a single rebalance plan item."""
        # Determine trade action
        action = "BUY" if delta > 0 else "SELL"

        # Get values directly from DTO (already Decimal)
        target_val = target_values.get(symbol, DECIMAL_ZERO)
        current_val = current_values.get(symbol, DECIMAL_ZERO)

        # Calculate weights
        target_weight, current_weight = self._calculate_weights(
            target_val, current_val, portfolio_value_decimal
        )

        return RebalancePlanItemDTO(
            symbol=symbol,
            current_weight=current_weight,
            target_weight=target_weight,
            weight_diff=target_weight - current_weight,
            target_value=target_val,
            current_value=current_val,
            trade_amount=delta,  # delta is already Decimal
            action=action,
            priority=1,  # All trades have equal priority for now
        )

    def _calculate_weights(
        self,
        target_val: Decimal,
        current_val: Decimal,
        portfolio_value_decimal: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calculate target and current weights safely."""
        if portfolio_value_decimal > 0:
            target_weight = target_val / portfolio_value_decimal
            current_weight = current_val / portfolio_value_decimal
        else:
            target_weight = DECIMAL_ZERO
            current_weight = DECIMAL_ZERO

        return target_weight, current_weight

    def _build_rebalance_plan_dto(
        self,
        plan_items: list[RebalancePlanItemDTO],
        total_trade_value: Decimal,
        portfolio_value_decimal: Decimal,
    ) -> RebalancePlanDTO:
        """Build the final RebalancePlanDTO."""
        # Create correlation IDs
        correlation_id = str(uuid.uuid4())
        plan_id = f"rebalance-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

        return RebalancePlanDTO(
            correlation_id=correlation_id,
            causation_id=f"trading-orchestrator-{correlation_id}",
            timestamp=datetime.now(UTC),
            plan_id=plan_id,
            items=plan_items,
            total_portfolio_value=portfolio_value_decimal,
            total_trade_value=total_trade_value,
            execution_urgency="NORMAL",
        )

    def _convert_execution_result_to_orders(
        self, execution_result: ExecutionResultDTO
    ) -> list[dict[str, Any]]:
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
                "filled_qty": (
                    float(order.shares) if order.success and order.shares else 0
                ),
                "filled_avg_price": float(order.price) if order.price else 0,
                "estimated_value": float(abs(order.trade_amount)),
                "order_id": order.order_id,
                "status": "FILLED" if order.success else "FAILED",
                "error": order.error_message,
            }
            orders_executed.append(order_dict)

        return orders_executed

    def _log_detailed_execution_results(
        self, execution_result: ExecutionResultDTO
    ) -> None:
        """Log detailed execution results for each order.

        Args:
            execution_result: ExecutionResultDTO with order details

        """
        for order in execution_result.orders:
            if order.success:
                shares_price_str = (
                    f"{float(order.shares):.4f} shares @ ${float(order.price):.2f}"
                    if order.shares is not None and order.price is not None
                    else "shares/price unavailable"
                )
                self.logger.info(
                    f"✅ {order.action} {order.symbol}: {shares_price_str} "
                    f"(Order ID: {order.order_id})"
                )
            else:
                self.logger.error(
                    f"❌ {order.action} {order.symbol} FAILED: {order.error_message}"
                )

        # Log summary
        self.logger.info(
            f"📊 Execution Summary: {execution_result.orders_succeeded}/"
            f"{execution_result.orders_placed} orders succeeded, "
            f"${execution_result.total_trade_value} total trade value"
        )

    def _emit_trade_executed_event(
        self,
        execution_result: ExecutionResultDTO,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """Emit TradeExecuted event for event-driven architecture.

        Converts trading execution data to event format for new event-driven consumers.

        Args:
            execution_result: The execution result from trading
            success: Whether the execution was successful overall
            error_message: Error message if execution failed

        """
        try:
            correlation_id = str(uuid.uuid4())
            causation_id = f"trade-execution-{datetime.now(UTC).isoformat()}"

            # Create execution results dictionary
            execution_data = {
                "orders_placed": (
                    execution_result.orders_placed if execution_result else 0
                ),
                "orders_succeeded": (
                    execution_result.orders_succeeded if execution_result else 0
                ),
                "total_trade_value": (
                    float(execution_result.total_trade_value)
                    if execution_result
                    else 0.0
                ),
                "orders": (
                    [
                        {
                            "symbol": order.symbol,
                            "action": order.action,
                            "shares": float(order.shares) if order.shares else 0.0,
                            "price": float(order.price) if order.price else 0.0,
                            "trade_amount": (
                                float(order.trade_amount) if order.trade_amount else 0.0
                            ),
                            "success": order.success,
                            "error_message": order.error_message,
                            "order_id": order.order_id,
                        }
                        for order in execution_result.orders
                    ]
                    if execution_result
                    else []
                ),
            }

            # Create portfolio state after execution (minimal for now)
            portfolio_state_after = None
            if success and execution_result:
                minimal_metrics = PortfolioMetricsDTO(
                    total_value=execution_result.total_trade_value,
                    cash_value=DECIMAL_ZERO,
                    equity_value=execution_result.total_trade_value,
                    buying_power=DECIMAL_ZERO,
                    day_pnl=DECIMAL_ZERO,
                    day_pnl_percent=DECIMAL_ZERO,
                    total_pnl=DECIMAL_ZERO,
                    total_pnl_percent=DECIMAL_ZERO,
                )

                portfolio_state_after = PortfolioStateDTO(
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    timestamp=datetime.now(UTC),
                    portfolio_id="main_portfolio",
                    account_id=None,
                    positions=[],  # Would be populated from portfolio service
                    metrics=minimal_metrics,
                )

            # Create and emit the event
            event = TradeExecuted(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=f"trade-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="TradingOrchestrator",
                execution_results=execution_data,
                portfolio_state_after=portfolio_state_after,
                success=success,
                error_message=error_message,
            )

            self.event_bus.publish(event)
            self.logger.debug(f"Emitted TradeExecuted event {event.event_id}")

        except Exception as e:
            # Don't let event emission failure break the traditional workflow
            self.logger.warning(f"Failed to emit TradeExecuted event: {e}")

    def _emit_trade_execution_started_event(
        self, execution_plan: dict[str, Any], trade_mode: str
    ) -> None:
        """Emit TradeExecutionStarted event for event-driven architecture.

        Args:
            execution_plan: The trading execution plan
            trade_mode: Trading mode (LIVE/PAPER)

        """
        try:
            correlation_id = str(uuid.uuid4())
            causation_id = f"trade-execution-start-{datetime.now(UTC).isoformat()}"

            # Create and emit the event
            event = TradeExecutionStarted(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=f"trade-start-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="TradingOrchestrator",
                execution_plan=execution_plan,
                portfolio_state_before=None,  # Would be populated from portfolio analysis
                trade_mode=trade_mode,
                market_conditions=None,  # Would be populated from market data
            )

            self.event_bus.publish(event)
            self.logger.debug(f"Emitted TradeExecutionStarted event {event.event_id}")

        except Exception as e:
            # Don't let event emission failure break the traditional workflow
            self.logger.warning(f"Failed to emit TradeExecutionStarted event: {e}")
