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
from the_alchemiser.shared.constants import (
    APPLICATION_NAME,
    DECIMAL_ZERO,
    MIN_TRADE_AMOUNT_USD,
    NO_TRADES_REQUIRED,
    REBALANCE_PLAN_GENERATED,
)
from the_alchemiser.shared.dto.portfolio_state_dto import (
    PortfolioMetricsDTO,
    PortfolioStateDTO,
)
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    TradeExecuted,
    TradeExecutionStarted,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
)
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.types.exceptions import (
    NotificationError,
    TradingClientError,
)

# Constants for repeated literals


class TradingOrchestrator:
    """Orchestrates trading execution workflow."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
    ) -> None:
        """Initialize trading orchestrator with settings and container."""
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)
        self.live_trading = not self.container.config.paper_trading()

        # Get event bus from container for dual-path emission
        self.event_bus: EventBus = container.services.event_bus()

        # Create signal orchestrator for signal generation
        self.signal_orchestrator = SignalOrchestrator(settings, container)

        # Create portfolio orchestrator for allocation analysis
        self.portfolio_orchestrator = PortfolioOrchestrator(settings, container)

        # Track workflow state for monitoring
        self.workflow_state: dict[str, Any] = {
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_correlation_id": None,
            "last_successful_step": None,
        }

        # Results collection for CLI compatibility
        self.workflow_results: dict[str, Any] = {}

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for trading workflow coordination.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, SignalGenerated):
                self._handle_signal_generated_coordination(event)
            elif isinstance(event, RebalancePlanned):
                self._handle_rebalance_planned_coordination(event)
            else:
                self.logger.debug(f"TradingOrchestrator ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"TradingOrchestrator event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type

        """
        return event_type in ["SignalGenerated", "RebalancePlanned"]

    def _handle_signal_generated_coordination(self, event: SignalGenerated) -> None:
        """Handle SignalGenerated event for workflow coordination.

        Triggers portfolio rebalancing when signals are generated.

        Args:
            event: The SignalGenerated event

        """
        self.logger.info(
            f"🔄 TradingOrchestrator: SignalGenerated coordination - {event.signal_count} signals"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": True,
                "last_correlation_id": event.correlation_id,
                "last_successful_step": "signal_generation",
            }
        )

        try:
            # Get comprehensive account data for rebalancing context
            account_data = self.portfolio_orchestrator.get_comprehensive_account_data()

            # Early return if account data is not available
            if not account_data or not account_data.get("account_info"):
                self.logger.error("Cannot trigger rebalancing: account data not available")
                self._reset_rebalancing_state()
                return

            self.logger.info("🔄 Triggering portfolio rebalancing workflow")

            # Populate workflow results with account data for CLI
            self._populate_workflow_results_for_signal(event.correlation_id, account_data)

            # Process portfolio rebalancing
            self._process_portfolio_rebalancing(event)

        except Exception as e:
            self.logger.error(f"Failed to coordinate portfolio rebalancing: {e}")
            self._reset_rebalancing_state()

    def _populate_workflow_results_for_signal(
        self, correlation_id: str, account_data: dict[str, Any]
    ) -> None:
        """Populate workflow results with account data for CLI display.

        Args:
            correlation_id: Event correlation ID
            account_data: Account data from portfolio orchestrator

        """
        if (
            hasattr(self, "workflow_results")
            and self.workflow_state.get("last_correlation_id") == correlation_id
        ):
            self.workflow_results.update(
                {
                    "account_info": account_data.get("account_info"),
                    "current_positions": account_data.get("current_positions", {}),
                    "open_orders": account_data.get("open_orders", []),
                }
            )

    def _process_portfolio_rebalancing(self, event: SignalGenerated) -> None:
        """Process portfolio rebalancing workflow.

        Args:
            event: The SignalGenerated event

        """
        # Reconstruct consolidated portfolio from event signals for rebalancing
        from the_alchemiser.shared.dto.consolidated_portfolio_dto import (
            ConsolidatedPortfolioDTO,
        )

        # Extract strategy names from signals
        signals_data = event.signals_data.get("signals", [])
        source_strategies = list(
            {signal.get("strategy_name") for signal in signals_data if signal.get("strategy_name")}
        )

        try:
            # Convert Decimal values to float for DTO compatibility
            allocation_dict_float = {
                symbol: float(allocation)
                for symbol, allocation in event.consolidated_portfolio.items()
            }

            # Create a consolidated portfolio DTO from the signals
            portfolio_dto = ConsolidatedPortfolioDTO.from_dict_allocation(
                allocation_dict=allocation_dict_float,
                correlation_id=event.correlation_id,
                source_strategies=source_strategies,
            )

            # Trigger allocation comparison which should emit RebalancePlanned
            allocation_comparison = self.portfolio_orchestrator.analyze_allocation_comparison(
                portfolio_dto
            )

            if not allocation_comparison:
                self.logger.error("Failed to generate allocation comparison")
                self._reset_rebalancing_state()
                return

            # Populate workflow results for CLI
            if (
                hasattr(self, "workflow_results")
                and self.workflow_state.get("last_correlation_id") == event.correlation_id
            ):
                self.workflow_results["allocation_comparison"] = allocation_comparison

            self.logger.info(
                "✅ Portfolio rebalancing analysis completed - RebalancePlanned event should be emitted"
            )

        except Exception as portfolio_error:
            self.logger.error(f"Failed to trigger portfolio orchestrator: {portfolio_error}")
            self._reset_rebalancing_state()

    def _reset_rebalancing_state(self) -> None:
        """Reset rebalancing state when errors occur."""
        self.workflow_state["rebalancing_in_progress"] = False

    def _handle_rebalance_planned_coordination(self, event: RebalancePlanned) -> None:
        """Handle RebalancePlanned event for workflow coordination.

        Executes trades when rebalance plan is ready.

        Args:
            event: The RebalancePlanned event

        """
        self.logger.info(
            f"🚀 TradingOrchestrator: RebalancePlanned coordination - {len(event.rebalance_plan.items)} trades"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "rebalancing_in_progress": False,
                "trading_in_progress": True,
                "last_correlation_id": event.correlation_id,
                "last_successful_step": "rebalancing",
            }
        )

        try:
            # Execute trades using ExecutionManager
            execution_manager = self.container.services.execution_manager()
            execution_result = execution_manager.execute_rebalance_plan(event.rebalance_plan)

            self.logger.info(
                f"✅ Trade execution completed: {execution_result.orders_succeeded}/"
                f"{execution_result.orders_placed} orders succeeded"
            )

            # Populate workflow results for CLI if this is the active correlation
            if self.workflow_state.get("last_correlation_id") == event.correlation_id:
                # Convert ExecutionResultDTO to format expected by CLI
                orders_executed = self._convert_execution_result_to_orders(execution_result)
                self.workflow_results.update(
                    {
                        "orders_executed": orders_executed,
                        "execution_result": execution_result,
                        "success": execution_result.success,
                        "message": "Pure event-driven trading workflow completed",
                    }
                )

            # Emit TradeExecuted event
            execution_success = execution_result.success and (
                execution_result.orders_placed == 0  # No-op case
                or execution_result.orders_succeeded == execution_result.orders_placed
            )  # All succeeded

            self._emit_trade_executed_event(
                execution_result,
                success=execution_success,
                error_message=None if execution_success else "Some orders failed",
            )

            # Update workflow state
            self.workflow_state.update(
                {
                    "trading_in_progress": False,
                    "last_successful_step": ("trading" if execution_success else "trading_failed"),
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to execute trades from rebalance plan: {e}")

            # Create and emit failure event
            try:
                failed_result = ExecutionResultDTO(
                    success=False,
                    plan_id=f"failed-{uuid.uuid4()}",
                    correlation_id=event.correlation_id,
                    orders=[],
                    orders_placed=0,
                    orders_succeeded=0,
                    total_trade_value=DECIMAL_ZERO,
                    execution_timestamp=datetime.now(UTC),
                    metadata={"error": str(e)},
                )
                self._emit_trade_executed_event(failed_result, success=False, error_message=str(e))
            except Exception as emit_error:
                self.logger.warning(f"Failed to emit failure event: {emit_error}")

            self.workflow_state.update(
                {
                    "trading_in_progress": False,
                    "last_successful_step": "trading_failed",
                }
            )

    def execute_strategy_signals_with_trading(self) -> dict[str, Any] | None:
        """Execute trading workflow with direct orchestrator coordination.

        Uses direct calls to domain orchestrators for synchronous execution.
        No event redundancy - pure direct coordination.
        """
        try:
            # Generate correlation ID for this workflow
            correlation_id = str(uuid.uuid4())

            self.logger.info("🚀 Starting direct trading workflow coordination")

            # Update workflow state for tracking
            self.workflow_state.update(
                {
                    "signal_generation_in_progress": True,
                    "rebalancing_in_progress": False,
                    "trading_in_progress": False,
                    "last_correlation_id": correlation_id,
                    "last_successful_step": None,
                }
            )

            # PHASE 1: Generate signals via SignalOrchestrator (event-emitting path)
            self.logger.info("🔄 Generating strategy signals")
            analyzed = self.signal_orchestrator.analyze_signals()
            if analyzed is None:
                self.logger.error("Failed to analyze strategy signals")
                return None

            strategy_signals, consolidated_portfolio_dict = analyzed

            # Build DTO from the consolidated dict to avoid re-running engines
            from the_alchemiser.shared.dto.consolidated_portfolio_dto import (
                ConsolidatedPortfolioDTO,
            )

            consolidated_portfolio_dto = ConsolidatedPortfolioDTO.from_dict_allocation(
                allocation_dict=consolidated_portfolio_dict,
                correlation_id=str(uuid.uuid4()),
                source_strategies=[str(k) for k in strategy_signals],
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

            self.workflow_state["signal_generation_in_progress"] = False
            self.workflow_state["last_successful_step"] = "signal_generation"
            self.logger.info("✅ Signal generation completed")

            # PHASE 2: Get account data and analyze portfolio
            self.logger.info("🔄 Getting account data and analyzing portfolio")
            account_data = self.portfolio_orchestrator.get_comprehensive_account_data()

            if not account_data or not account_data.get("account_info"):
                self.logger.error("Could not retrieve account data for trading")
                return None

            account_info = account_data.get("account_info")
            current_positions = account_data.get("current_positions", {})
            open_orders = account_data.get("open_orders", [])

            # Create allocation comparison
            allocation_comparison = self.portfolio_orchestrator.analyze_allocation_comparison(
                consolidated_portfolio_dto
            )

            if not allocation_comparison:
                self.logger.error("Failed to generate allocation comparison")
                return None

            self.logger.info("✅ Portfolio analysis completed")

            # PHASE 3: Execute trades
            self.workflow_state["rebalancing_in_progress"] = True

            # Create rebalance plan from allocation comparison
            if account_info is None:
                self.logger.error("❌ No account information available for rebalancing")
                return None

            rebalance_plan = self._create_rebalance_plan_from_allocation(
                allocation_comparison, account_info
            )

            orders_executed = []
            execution_result = None

            if rebalance_plan:
                # Print a concise summary of the rebalance plan before executing
                self._print_rebalance_plan_summary(rebalance_plan)
                self.logger.info(f"🚀 Executing trades: {len(rebalance_plan.items)} items")
                self.workflow_state["trading_in_progress"] = True

                # Execute the rebalance plan
                execution_manager = self.container.services.execution_manager()
                execution_result = execution_manager.execute_rebalance_plan(rebalance_plan)

                # Convert ExecutionResultDTO to format expected by CLI
                orders_executed = self._convert_execution_result_to_orders(execution_result)

                self.logger.info(
                    f"✅ Trade execution completed: {execution_result.orders_succeeded}/"
                    f"{execution_result.orders_placed} orders succeeded"
                )

                # Emit TradeExecuted event for monitoring (EventDrivenOrchestrator)
                execution_success = execution_result.success and (
                    execution_result.orders_placed == 0
                    or execution_result.orders_succeeded == execution_result.orders_placed
                )
                self._emit_trade_executed_event(execution_result, success=execution_success)

            else:
                self.logger.info("📊 No significant trades needed - portfolio already balanced")

                # Create empty execution result
                execution_result = ExecutionResultDTO(
                    success=True,
                    plan_id=f"no-trade-{uuid.uuid4()}",
                    correlation_id=correlation_id,
                    orders=[],
                    orders_placed=0,
                    orders_succeeded=0,
                    total_trade_value=DECIMAL_ZERO,
                    execution_timestamp=datetime.now(UTC),
                    metadata={"scenario": "no_trades_needed"},
                )
                self._emit_trade_executed_event(execution_result, success=True)

            # Update workflow state
            self.workflow_state.update(
                {
                    "rebalancing_in_progress": False,
                    "trading_in_progress": False,
                    "last_successful_step": "trading",
                }
            )

            # Return results for CLI
            return {
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio_dto.to_dict_allocation(),
                "account_info": account_info,
                "current_positions": current_positions,
                "allocation_comparison": allocation_comparison,
                "rebalance_plan": rebalance_plan,
                "orders_executed": orders_executed,
                "execution_result": execution_result,
                "open_orders": open_orders,
                "success": True,
                "message": "Direct trading workflow completed successfully",
                "correlation_id": correlation_id,
            }

        except Exception as e:
            self.logger.error(f"Direct trading workflow failed: {e}")
            self.workflow_state.update(
                {
                    "signal_generation_in_progress": False,
                    "rebalancing_in_progress": False,
                    "trading_in_progress": False,
                    "last_successful_step": "failed",
                }
            )
            return None

    def execute_strategy_signals(self) -> dict[str, Any] | None:
        """Execute signal analysis workflow with direct orchestrator coordination.

        Uses direct calls to domain orchestrators for synchronous execution.
        No event redundancy - pure direct coordination.
        """
        try:
            # Generate correlation ID for this workflow
            correlation_id = str(uuid.uuid4())

            self.logger.info("📊 Starting direct signal analysis workflow")

            # Update workflow state for tracking
            self.workflow_state.update(
                {
                    "signal_generation_in_progress": True,
                    "rebalancing_in_progress": False,
                    "trading_in_progress": False,
                    "last_correlation_id": correlation_id,
                    "last_successful_step": None,
                }
            )

            # Generate signals via SignalOrchestrator (event-emitting path)
            self.logger.info("🔄 Generating strategy signals")
            analyzed = self.signal_orchestrator.analyze_signals()
            if analyzed is None:
                self.logger.error("Failed to analyze strategy signals")
                return None

            strategy_signals, consolidated_portfolio_dict = analyzed

            # Build DTO from the consolidated dict to avoid re-running engines
            from the_alchemiser.shared.dto.consolidated_portfolio_dto import (
                ConsolidatedPortfolioDTO,
            )

            consolidated_portfolio_dto = ConsolidatedPortfolioDTO.from_dict_allocation(
                allocation_dict=consolidated_portfolio_dict,
                correlation_id=str(uuid.uuid4()),
                source_strategies=[str(k) for k in strategy_signals],
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

            self.workflow_state["signal_generation_in_progress"] = False
            self.workflow_state["last_successful_step"] = "signal_generation"
            self.logger.info("✅ Signal generation completed")

            # Get account data for context (optional for signal-only mode)
            account_data = self.portfolio_orchestrator.get_comprehensive_account_data()
            account_info = account_data.get("account_info") if account_data else None
            current_positions = account_data.get("current_positions", {}) if account_data else {}
            open_orders = account_data.get("open_orders", []) if account_data else []

            # For signal-only mode, we can optionally get allocation comparison for analysis
            allocation_comparison = None
            if account_data and account_info:
                try:
                    allocation_comparison = (
                        self.portfolio_orchestrator.analyze_allocation_comparison(
                            consolidated_portfolio_dto
                        )
                    )
                    self.logger.info("✅ Portfolio analysis completed (for reference)")
                except Exception as e:
                    self.logger.warning(
                        f"Portfolio analysis failed (optional for signal mode): {e}"
                    )

            # Return results for CLI
            return {
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio_dto.to_dict_allocation(),
                "account_info": account_info,
                "current_positions": current_positions,
                "allocation_comparison": allocation_comparison,
                "orders_executed": [],  # No execution in signal-only mode
                "execution_result": None,  # No execution in signal-only mode
                "open_orders": open_orders,
                "success": True,
                "message": "Direct signal analysis workflow completed successfully",
                "correlation_id": correlation_id,
            }

        except Exception as e:
            self.logger.error(f"Direct signal analysis workflow failed: {e}")
            self.workflow_state.update(
                {
                    "signal_generation_in_progress": False,
                    "last_successful_step": "failed",
                }
            )
            return None

    def send_trading_notification(self, result: dict[str, Any], mode_str: str) -> None:
        """Send trading completion notification using enhanced email templates.

        Args:
            result: The execution result dictionary
            mode_str: Trading mode string for display

        """
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                EmailTemplates,
                send_email_notification,
            )

            success = result.get("success", False)
            message = result.get("message", "Trading execution completed")

            if success:
                # Use the new successful trading run template for better formatting
                # Rather than trying to create a full DTO, use the neutral template directly
                try:
                    # Create a minimal object with just the fields the template actually uses
                    class ResultAdapter:
                        def __init__(self, result_dict: dict[str, Any]) -> None:
                            self.success = result_dict.get("success", True)
                            self.orders_executed = result_dict.get("orders_executed", [])
                            self.strategy_signals = result_dict.get("strategy_signals", {})

                    # Use the neutral report builder directly which is more flexible
                    result_adapter = ResultAdapter(result)
                    html_content = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                        result_adapter,
                        mode_str,
                    )
                except Exception as template_error:
                    # Fallback to enhanced failed template if neutral builder fails
                    self.logger.warning(
                        f"Template generation failed, using enhanced fallback: {template_error}"
                    )
                    try:
                        # Use the enhanced failed template as fallback for consistency
                        context = {
                            "execution_details": message,
                            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "workflow_state": "template_generation_failed",
                        }
                        html_content = EmailTemplates.failed_trading_run(
                            error_details=f"Template generation failed: {template_error}",
                            mode=mode_str,
                            context=context,
                        )
                    except Exception as enhanced_error:
                        # Final fallback to basic template only if enhanced template also fails
                        self.logger.error(
                            f"Enhanced template fallback also failed: {enhanced_error}"
                        )
                        html_content = f"""
                        <h2>Trading Execution Report - {mode_str.upper()}</h2>
                        <p><strong>Status:</strong> Success</p>
                        <p><strong>Message:</strong> {message}</p>
                        <p><strong>Timestamp:</strong> {datetime.now(UTC)}</p>
                        """
                        # Final fallback to basic template only if enhanced template also fails
                        self.logger.error(
                            f"Enhanced template fallback also failed: {enhanced_error}"
                        )
                        html_content = f"""
                        <h2>Trading Execution Report - {mode_str.upper()}</h2>
                        <p><strong>Status:</strong> Success</p>
                        <p><strong>Message:</strong> {message}</p>
                        <p><strong>Timestamp:</strong> {datetime.now(UTC)}</p>
                        """
            else:
                # Use the new failed trading run template for enhanced error reporting
                context = {
                    "execution_details": message,
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "workflow_state": str(
                        self.workflow_state.get("last_successful_step", "unknown")
                    ),
                }

                html_content = EmailTemplates.failed_trading_run(
                    error_details=message, mode=mode_str, context=context
                )

            status_tag = "SUCCESS" if success else "FAILURE"
            send_email_notification(
                subject=f"[{status_tag}] {APPLICATION_NAME} - {mode_str.upper()} Trading Report",
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

            # Execute strategy signals with actual trading
            result = self.execute_strategy_signals_with_trading()
            if result is None:
                self.logger.error("Strategy execution failed")
                return False

            # Note: Notification sending removed from wrapper method to avoid duplicates
            # The main system handles notifications through direct method calls

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

            # Execute strategy signals with actual trading
            result = self.execute_strategy_signals_with_trading()
            if result is None:
                self.logger.error("Strategy execution failed")
                return None

            # Note: Notification sending removed from wrapper method to avoid duplicates
            # The main system handles notifications through direct method calls

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
                self.logger.info("No significant trades needed - all deltas below threshold")
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
        raw = account_info.get("portfolio_value", account_info.get("equity", 0))
        # Sanitize inputs to avoid Decimal ConversionSyntax
        try:
            if isinstance(raw, Decimal):
                return raw
            if isinstance(raw, int | float):
                return Decimal(str(raw))
            if raw is None:
                return Decimal("0")
            # Strings or other types
            return Decimal(str(raw))
        except Exception:
            return Decimal("0")

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
                "filled_qty": (float(order.shares) if order.success and order.shares else 0),
                # Money fields serialized as strings per policy
                "filled_avg_price": str(order.price) if order.price else "0",
                "estimated_value": (
                    str(order.trade_amount) if order.trade_amount is not None else "0"
                ),
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
                shares_price_str = (
                    f"{order.shares} shares @ ${order.price}"
                    if order.shares is not None and order.price is not None
                    else "shares/price unavailable"
                )
                self.logger.info(
                    f"✅ {order.action} {order.symbol}: {shares_price_str} "
                    f"(Order ID: {order.order_id})"
                )
            else:
                self.logger.error(f"❌ {order.action} {order.symbol} FAILED: {order.error_message}")

        # Log summary
        self.logger.info(
            f"📊 Execution Summary: {execution_result.orders_succeeded}/"
            f"{execution_result.orders_placed} orders succeeded, "
            f"${execution_result.total_trade_value} total trade value"
        )

    def _build_portfolio_state_after(
        self,
        *,
        success: bool,
        execution_result: ExecutionResultDTO | None,
        correlation_id: str,
        causation_id: str,
    ) -> PortfolioStateDTO | None:
        """Build portfolio state after execution.

        Args:
            success: Whether the execution was successful
            execution_result: The execution result
            correlation_id: Event correlation ID
            causation_id: Event causation ID

        Returns:
            PortfolioStateDTO if successful execution, None otherwise

        """
        if not success or not execution_result:
            return None

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

        return PortfolioStateDTO(
            correlation_id=correlation_id,
            causation_id=causation_id,
            timestamp=datetime.now(UTC),
            portfolio_id="main_portfolio",
            account_id=None,
            positions=[],  # Would be populated from portfolio service
            metrics=minimal_metrics,
        )

    def _build_execution_data(self, execution_result: ExecutionResultDTO | None) -> dict[str, Any]:
        """Build execution results dictionary from execution result.

        Args:
            execution_result: The execution result to convert

        Returns:
            Dictionary containing execution data for event emission

        """
        return {
            "orders_placed": (execution_result.orders_placed if execution_result else 0),
            "orders_succeeded": (execution_result.orders_succeeded if execution_result else 0),
            # Money serialized as string to avoid float exposure per policy
            "total_trade_value": (
                str(execution_result.total_trade_value) if execution_result else "0"
            ),
            "orders": (
                [
                    {
                        "symbol": order.symbol,
                        "action": order.action,
                        # Quantities are non-financial; keep as float for consumers
                        "shares": float(order.shares) if order.shares else 0.0,
                        # Money fields serialized as strings
                        "price": (str(order.price) if order.price is not None else "0"),
                        "trade_amount": (str(order.trade_amount) if order.trade_amount else "0"),
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

    def _collect_unique_error_messages(self, execution_result: ExecutionResultDTO) -> list[str]:
        """Collect unique error messages from failed orders.

        Args:
            execution_result: The execution result containing orders

        Returns:
            List of unique error messages from failed orders

        """
        msgs: list[str] = []
        for order in execution_result.orders:
            if not order.success and order.error_message:
                msg = str(order.error_message)
                if msg not in msgs:
                    msgs.append(msg)
        return msgs

    def _get_reason_hint(self, msgs: list[str]) -> str:
        """Get reason hint from error messages.

        Args:
            msgs: List of error messages

        Returns:
            Reason hint string based on message content

        """
        if not msgs:
            return ""

        joined = " ".join(msgs).lower()
        market_keywords = [
            "market hours",
            "market closed",
            "outside trading hours",
            "after hours",
            "pre-market",
            "premarket",
        ]

        if any(keyword in joined for keyword in market_keywords):
            return "Market closed or outside regular trading hours"

        # Use up to first 2 unique broker messages
        return "; ".join(msgs[:2])

    def _is_error_message_informative(self, error_message: str | None) -> bool:
        """Check if error message is already informative.

        Args:
            error_message: The error message to check

        Returns:
            True if message is informative, False if needs derivation

        """
        return not (
            error_message is None
            or error_message.strip() == ""
            or error_message == "Some orders failed"
        )

    def _derive_error_message(
        self, execution_result: ExecutionResultDTO, error_message: str | None
    ) -> str | None:
        """Derive a more descriptive error message if not provided.

        Args:
            execution_result: The execution result containing orders
            error_message: The original error message (if any)

        Returns:
            Derived error message or original if none could be derived

        """
        # Early return if error message is already informative
        if self._is_error_message_informative(error_message):
            return error_message

        try:
            msgs = self._collect_unique_error_messages(execution_result)
            reason_hint = self._get_reason_hint(msgs)

            summary = (
                f"{execution_result.orders_succeeded}/{execution_result.orders_placed} succeeded"
            )

            if reason_hint:
                derived_error = f"{summary}. Reason: {reason_hint}"
            else:
                derived_error = f"{summary}. No detailed broker error messages available."

            return derived_error

        except Exception as derivation_exc:
            self.logger.debug(
                "Failed to derive detailed error message: %s",
                derivation_exc,
            )
            return error_message

    def _derive_error_code_from_orders(self, execution_result: ExecutionResultDTO) -> str | None:
        """Derive error code from order failure patterns.

        Args:
            execution_result: The execution result containing orders

        Returns:
            Error code string if derivable, None otherwise

        """
        # Import catalog to map error codes
        from the_alchemiser.shared.errors.catalog import map_exception_to_error_code

        # Look at order error messages to infer the type of error
        for order in execution_result.orders:
            if not order.success and order.error_message:
                msg = str(order.error_message).lower()
                mapped_exc = self._map_error_message_to_exception(msg)

                if mapped_exc:
                    error_code_enum = map_exception_to_error_code(mapped_exc)
                    if error_code_enum:
                        return error_code_enum.value  # Use first mappable error

        return None

    def _map_error_message_to_exception(self, msg: str) -> Exception | None:
        """Map error message to appropriate exception type.

        Args:
            msg: Lowercase error message to analyze

        Returns:
            Exception instance if pattern matches, None otherwise

        """
        from the_alchemiser.shared.types.exceptions import (
            InsufficientFundsError,
            MarketClosedError,
            OrderTimeoutError,
        )

        if self._is_market_closed_error(msg):
            return MarketClosedError("Market closed")
        if self._is_insufficient_funds_error(msg):
            return InsufficientFundsError("Insufficient funds")
        if self._is_timeout_error(msg):
            return OrderTimeoutError("Order timeout")

        return None

    def _is_market_closed_error(self, msg: str) -> bool:
        """Check if message indicates market closed error."""
        market_closed_patterns = [
            "market hours",
            "market closed",
            "outside trading hours",
            "after hours",
            "pre-market",
            "premarket",
        ]
        return any(pattern in msg for pattern in market_closed_patterns)

    def _is_insufficient_funds_error(self, msg: str) -> bool:
        """Check if message indicates insufficient funds error."""
        funds_patterns = [
            "insufficient funds",
            "insufficient cash",
            "buying power",
        ]
        return any(pattern in msg for pattern in funds_patterns)

    def _is_timeout_error(self, msg: str) -> bool:
        """Check if message indicates timeout error."""
        timeout_patterns = ["timeout", "timed out", "execution timeout"]
        return any(pattern in msg for pattern in timeout_patterns)

    def _emit_trade_executed_event(
        self,
        execution_result: ExecutionResultDTO,
        *,
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
            # Derive error code from failure patterns if not successful
            error_code = None
            if not success and execution_result:
                error_code = self._derive_error_code_from_orders(execution_result)

            # Derive a more descriptive error message if not provided
            if not success and execution_result:
                error_message = self._derive_error_message(execution_result, error_message)

            # Generate correlation and causation IDs
            correlation_id = str(uuid.uuid4())
            causation_id = f"trade-execution-{datetime.now(UTC).isoformat()}"

            # Build execution data
            execution_data = self._build_execution_data(execution_result)

            # Create and emit the event
            event = TradeExecuted(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=f"trade-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="TradingOrchestrator",
                execution_data=execution_data,
                success=success,
                orders_placed=execution_data.get("orders_placed", 0),
                orders_succeeded=execution_data.get("orders_succeeded", 0),
                metadata=(
                    {
                        "error_message": error_message,
                        "error_code": error_code,
                    }
                    if error_message or error_code
                    else {}
                ),
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

    def _print_rebalance_plan_summary(self, plan: RebalancePlanDTO) -> None:
        """Print a concise BUY/SELL summary of the rebalance plan before execution."""
        try:
            buy_lines: list[str] = []
            sell_lines: list[str] = []

            for item in plan.items:
                action = item.action.upper()
                symbol = item.symbol
                amt = item.trade_amount
                # Positive for BUY, negative for SELL per DTO contract
                if action == "BUY" and amt > Decimal("0"):
                    buy_lines.append(f"{symbol} ${abs(amt):,.0f}")
                elif action == "SELL" and amt < Decimal("0"):
                    sell_lines.append(f"{symbol} ${abs(amt):,.0f}")

            if buy_lines or sell_lines:
                print(REBALANCE_PLAN_GENERATED)
                if sell_lines:
                    print(f"   → SELL: {', '.join(sell_lines)}")
                if buy_lines:
                    print(f"   → BUY: {', '.join(buy_lines)}")
            else:
                print(NO_TRADES_REQUIRED)
        except Exception as e:
            self.logger.debug(f"Failed printing plan summary: {e}")
