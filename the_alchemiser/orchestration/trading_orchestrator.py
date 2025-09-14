"""Business Unit: orchestration | Status: current.

Event-driven trading execution orchestration workflow.

Coordinates complete trading workflows via event-driven architecture,
eliminating tight coupling between orchestrators while maintaining
full functionality. Handles signal-to-execution pipelines through
event coordination with proper correlation tracking.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    EventHandler,
    PortfolioAnalysisCompleted,
    PortfolioAnalysisRequested,
    RebalancePlanned,
    SignalGenerated,
    SignalGenerationRequested,
    TradeExecuted,
    TradingWorkflowRequested,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.exceptions import (
    NotificationError,
)


class TradingOrchestrator(EventHandler):
    """Event-driven trading execution orchestrator.
    
    Coordinates complete trading workflows through event-driven architecture:
    1. Receives TradingWorkflowRequested events
    2. Coordinates with SignalOrchestrator via SignalGenerated events
    3. Triggers portfolio analysis via PortfolioAnalysisRequested events
    4. Executes trades via RebalancePlanned events
    5. Tracks workflow completion with correlation IDs
    
    No direct dependencies on other orchestrators - all coordination via events.
    """

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        ignore_market_hours: bool = False,
    ) -> None:
        """Initialize event-driven trading orchestrator.
        
        Args:
            settings: Application settings
            container: Dependency injection container
            ignore_market_hours: Whether to ignore market hours check

        """
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)
        self.ignore_market_hours = ignore_market_hours
        
        # Get trading mode from container
        self.live_trading = not self.container.config.paper_trading()
        
        # Event bus for coordination
        self.event_bus: EventBus = container.services.event_bus()
        
        # Workflow state tracking
        self.active_workflows: dict[str, dict[str, Any]] = {}
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="trading-")
        
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register event handlers for trading workflow coordination."""
        self.event_bus.subscribe("TradingWorkflowRequested", self)
        self.event_bus.subscribe("SignalGenerated", self)
        self.event_bus.subscribe("PortfolioAnalysisCompleted", self)
        self.event_bus.subscribe("RebalancePlanned", self)
        self.event_bus.subscribe("TradeExecuted", self)
        
        self.logger.info("Trading orchestrator registered for event-driven coordination")

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the given event type."""
        return event_type in [
            "TradingWorkflowRequested",
            "SignalGenerated", 
            "PortfolioAnalysisCompleted",
            "RebalancePlanned",
            "TradeExecuted",
        ]

    def handle_event(self, event: BaseEvent) -> None:
        """Handle trading workflow events with comprehensive error handling."""
        try:
            if isinstance(event, TradingWorkflowRequested):
                self._handle_trading_workflow_requested(event)
            elif isinstance(event, SignalGenerated):
                self._handle_signal_generated(event)
            elif isinstance(event, PortfolioAnalysisCompleted):
                self._handle_portfolio_analysis_completed(event)
            elif isinstance(event, RebalancePlanned):
                self._handle_rebalance_planned(event)
            elif isinstance(event, TradeExecuted):
                self._handle_trade_executed(event)
                
        except Exception as e:
            self.logger.error(
                f"Trading orchestrator event handling failed: {e}",
                extra={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def execute_strategy_signals_with_trading(self) -> dict[str, Any] | None:
        """Execute full trading workflow via events and return results."""
        return self._execute_workflow_via_events(execute_trades=True)

    def execute_strategy_signals(self) -> dict[str, Any] | None:
        """Execute signal-only workflow via events and return results."""
        return self._execute_workflow_via_events(execute_trades=False)

    def _execute_workflow_via_events(self, execute_trades: bool) -> dict[str, Any] | None:
        """Execute trading workflow via event coordination.
        
        Args:
            execute_trades: Whether to execute actual trades or signal-only mode
            
        Returns:
            Workflow results or None if failed

        """
        workflow_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        self.logger.info(
            f"🚀 Starting {'full trading' if execute_trades else 'signal-only'} workflow",
            extra={"workflow_id": workflow_id, "correlation_id": correlation_id}
        )
        
        # Emit workflow request event
        workflow_event = TradingWorkflowRequested(
            correlation_id=correlation_id,
            causation_id=f"cli-request-{datetime.now(UTC).isoformat()}",
            event_id=workflow_id,
            timestamp=datetime.now(UTC),
            source_module="orchestration",
            source_component="TradingOrchestrator",
            workflow_mode="full_trading" if execute_trades else "signal_only",
            ignore_market_hours=self.ignore_market_hours,
            execution_parameters={},
        )
        
        self.event_bus.publish(workflow_event)
        
        # Wait for workflow completion with timeout
        import time
        timeout_seconds = 120
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                if workflow.get("status") == "completed":
                    self.logger.info(
                        f"✅ Workflow {workflow_id} completed successfully",
                        extra={"workflow_id": workflow_id}
                    )
                    return workflow.get("results")
                if workflow.get("status") == "failed":
                    self.logger.error(
                        f"❌ Workflow {workflow_id} failed: {workflow.get('error')}",
                        extra={"workflow_id": workflow_id}
                    )
                    return None
            
            time.sleep(0.5)  # Poll every 500ms
            
        self.logger.error(f"⏰ Workflow {workflow_id} timed out after {timeout_seconds}s")
        return None

    def _handle_trading_workflow_requested(self, event: TradingWorkflowRequested) -> None:
        """Handle workflow initiation request."""
        workflow_id = event.event_id
        
        self.logger.info(
            f"📋 Initializing trading workflow: {event.workflow_mode}",
            extra={"workflow_id": workflow_id, "correlation_id": event.correlation_id}
        )
        
        # Initialize workflow state
        self.active_workflows[workflow_id] = {
            "id": workflow_id,
            "correlation_id": event.correlation_id,
            "mode": event.workflow_mode,
            "ignore_market_hours": event.ignore_market_hours,
            "execution_parameters": event.execution_parameters,
            "status": "started",
            "start_time": datetime.now(UTC),
            "signals": None,
            "portfolio_analysis": None,
            "execution_results": None,
        }
        
        # Check market hours if required
        if not event.ignore_market_hours and not self._check_market_hours():
            self._fail_workflow(workflow_id, "Market is closed")
            return
            
        # Trigger signal generation by emitting SignalGenerationRequested event
        self._request_signal_generation(event)

    def _request_signal_generation(self, workflow_event: TradingWorkflowRequested) -> None:
        """Request signal generation via SignalGenerationRequested event."""
        # Create signal generation request event
        signal_request_event = SignalGenerationRequested(
            correlation_id=workflow_event.correlation_id,
            causation_id=workflow_event.event_id,
            event_id=f"signal-request-{workflow_event.event_id}",
            timestamp=datetime.now(UTC),
            source_module="orchestration",
            source_component="TradingOrchestrator",
            workflow_id=workflow_event.event_id,
            analysis_mode="comprehensive",
            strategy_filters=None,
        )
        
        # Emit the signal generation request
        self.event_bus.publish(signal_request_event)
        
        self.logger.info(
            f"📊 Requested signal generation for workflow {workflow_event.event_id}",
            extra={
                "workflow_id": workflow_event.event_id,
                "correlation_id": workflow_event.correlation_id,
                "signal_request_id": signal_request_event.event_id,
            }
        )

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance plan completion for workflow tracking."""
        # Find workflow that should receive this rebalance plan
        target_workflow = self._find_workflow_by_correlation(event.correlation_id)
        if not target_workflow:
            return
            
        workflow_id = target_workflow["id"]
        self.logger.info(
            f"📋 Rebalance plan completed for workflow {workflow_id}",
            extra={"workflow_id": workflow_id, "correlation_id": event.correlation_id}
        )
        
        # Update workflow state
        target_workflow["rebalance_plan"] = event.rebalance_plan
        target_workflow["status"] = "rebalance_planned"

    def _handle_trade_executed(self, event: TradeExecuted) -> None:
        """Handle trade execution completion for workflow tracking."""
        # Find workflow that should receive this trade result
        target_workflow = self._find_workflow_by_correlation(event.correlation_id)
        if not target_workflow:
            return
            
        workflow_id = target_workflow["id"]
        self.logger.info(
            f"💰 Trade executed for workflow {workflow_id}: {event.success}",
            extra={"workflow_id": workflow_id, "correlation_id": event.correlation_id}
        )
        
        # Update workflow state
        if "trades_executed" not in target_workflow:
            target_workflow["trades_executed"] = []
        target_workflow["trades_executed"].append(event)

    def _handle_signal_generated(self, event: SignalGenerated) -> None:
        """Handle signal generation completion."""
        # Find workflow that should receive these signals
        target_workflow = self._find_workflow_by_correlation(event.correlation_id)
        if not target_workflow:
            return
            
        workflow_id = target_workflow["id"]
        
        self.logger.info(
            f"📊 Signals received for workflow {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "signal_count": len(event.signals),
                "correlation_id": event.correlation_id,
            }
        )
        
        # Update workflow state
        target_workflow["signals"] = event.signals
        target_workflow["consolidated_portfolio"] = event.consolidated_portfolio
        target_workflow["status"] = "signals_received"
        
        # Request portfolio analysis
        self._request_portfolio_analysis(target_workflow, event)

    def _request_portfolio_analysis(self, workflow: dict[str, Any], signal_event: SignalGenerated) -> None:
        """Request portfolio analysis via events."""
        analysis_event = PortfolioAnalysisRequested(
            correlation_id=workflow["correlation_id"],
            causation_id=signal_event.event_id,
            event_id=f"portfolio-analysis-{workflow['id']}",
            timestamp=datetime.now(UTC),
            source_module="orchestration",
            source_component="TradingOrchestrator",
            trigger_event_id=signal_event.event_id,
            target_allocations=signal_event.consolidated_portfolio,
            analysis_type="comprehensive",
        )
        
        self.event_bus.publish(analysis_event)
        
        self.logger.info(
            f"📈 Requested portfolio analysis for workflow {workflow['id']}",
            extra={"workflow_id": workflow["id"], "analysis_event_id": analysis_event.event_id}
        )

    def _handle_portfolio_analysis_completed(self, event: PortfolioAnalysisCompleted) -> None:
        """Handle portfolio analysis completion."""
        target_workflow = self._find_workflow_by_correlation(event.correlation_id)
        if not target_workflow:
            return
            
        workflow_id = target_workflow["id"]
        
        self.logger.info(
            f"🏦 Portfolio analysis completed for workflow {workflow_id}",
            extra={"workflow_id": workflow_id, "correlation_id": event.correlation_id}
        )
        
        # Update workflow state
        target_workflow["portfolio_analysis"] = {
            "portfolio_state": event.portfolio_state,
            "account_data": event.account_data,
            "allocation_comparison": event.allocation_comparison,
        }
        target_workflow["status"] = "portfolio_analyzed"
        
        # Check if we should execute trades
        if target_workflow["mode"] == "full_trading":
            self._initiate_trade_execution(target_workflow, event)
        else:
            # Signal-only mode - complete workflow
            self._complete_workflow(target_workflow)

    def _initiate_trade_execution(self, workflow: dict[str, Any], analysis_event: PortfolioAnalysisCompleted) -> None:
        """Initiate trade execution via rebalance planning."""
        workflow_id = workflow["id"]
        
        # Check if we have allocation comparison data
        allocation_comparison = analysis_event.allocation_comparison
        if not allocation_comparison:
            self._fail_workflow(workflow_id, "No allocation comparison data for trade execution")
            return
            
        account_data = analysis_event.account_data
        if not account_data or not account_data.get("account_info"):
            self._fail_workflow(workflow_id, "No account data for trade execution")
            return

        self.logger.info(
            f"🔄 Initiating trade execution for workflow {workflow_id}",
            extra={"workflow_id": workflow_id}
        )

        try:
            # Convert allocation comparison to rebalance plan
            rebalance_plan = self._create_rebalance_plan_from_allocation(
                allocation_comparison, account_data["account_info"]
            )
            
            if not rebalance_plan or not rebalance_plan.items:
                self.logger.info(f"📊 No trades needed for workflow {workflow_id} - portfolio balanced")
                self._complete_workflow(workflow, {"trades_executed": 0, "message": "No rebalancing needed"})
                return
                
            # Execute rebalance plan
            execution_manager = self.container.services.execution_manager()
            execution_result = execution_manager.execute_rebalance_plan(rebalance_plan)
            
            # Update workflow with execution results
            workflow["execution_results"] = execution_result
            workflow["status"] = "trades_executed"
            
            # Convert results for CLI compatibility
            orders_executed = self._convert_execution_result_to_orders(execution_result)
            
            self.logger.info(
                f"✅ Trade execution completed for workflow {workflow_id}: "
                f"{execution_result.orders_succeeded}/{execution_result.orders_placed} orders succeeded",
                extra={"workflow_id": workflow_id}
            )
            
            self._complete_workflow(workflow, {
                "trades_executed": execution_result.orders_succeeded,
                "orders_executed": orders_executed,
                "execution_summary": {
                    "orders_placed": execution_result.orders_placed,
                    "orders_succeeded": execution_result.orders_succeeded,
                    "orders_failed": execution_result.orders_failed,
                },
            })
            
        except Exception as e:
            self._fail_workflow(workflow_id, f"Trade execution failed: {e}")

    def _complete_workflow(self, workflow: dict[str, Any], additional_results: dict[str, Any] | None = None) -> None:
        """Complete a trading workflow with results."""
        workflow_id = workflow["id"]
        workflow["status"] = "completed"
        workflow["end_time"] = datetime.now(UTC)
        
        # Compile comprehensive results
        results = {
            "workflow_id": workflow_id,
            "correlation_id": workflow["correlation_id"], 
            "mode": workflow["mode"],
            "success": True,
            "duration": (workflow["end_time"] - workflow["start_time"]).total_seconds(),
            "signals": workflow.get("signals", []),
            "consolidated_portfolio": workflow.get("consolidated_portfolio", {}),
            "portfolio_analysis": workflow.get("portfolio_analysis", {}),
            "execution_results": workflow.get("execution_results"),
        }
        
        if additional_results:
            results.update(additional_results)
            
        workflow["results"] = results
        
        self.logger.info(
            f"✅ Workflow {workflow_id} completed successfully",
            extra={"workflow_id": workflow_id, "duration": results["duration"]}
        )

    def _fail_workflow(self, workflow_id: str, error_message: str) -> None:
        """Fail a workflow with error message."""
        if workflow_id not in self.active_workflows:
            return
            
        workflow = self.active_workflows[workflow_id]
        workflow["status"] = "failed"
        workflow["error"] = error_message
        workflow["end_time"] = datetime.now(UTC)
        
        self.logger.error(
            f"❌ Workflow {workflow_id} failed: {error_message}",
            extra={"workflow_id": workflow_id}
        )

    def _find_workflow_by_correlation(self, correlation_id: str) -> dict[str, Any] | None:
        """Find active workflow by correlation ID."""
        for workflow in self.active_workflows.values():
            if workflow["correlation_id"] == correlation_id and workflow["status"] != "completed":
                return workflow
        return None

    def _check_market_hours(self) -> bool:
        """Check if market is open for trading."""
        if self.ignore_market_hours:
            return True

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

    def _create_rebalance_plan_from_allocation(
        self, allocation_comparison: dict[str, Any], account_info: dict[str, Any]
    ) -> RebalancePlanDTO | None:
        """Create rebalance plan from allocation comparison data."""
        try:
            # Import DTO conversion utility
            from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
            
            # Convert dict to DTO if needed
            if isinstance(allocation_comparison, dict):
                comparison_dto = AllocationComparisonDTO(
                    target_values=allocation_comparison.get("target_values", {}),
                    current_values=allocation_comparison.get("current_values", {}),
                    deltas=allocation_comparison.get("deltas", {}),
                )
            else:
                comparison_dto = allocation_comparison

            buying_power = Decimal(str(account_info.get("buying_power", 0)))
            if buying_power <= 0:
                self.logger.warning("No buying power available for rebalancing")
                return None

            rebalance_items = []
            for symbol, delta_value in comparison_dto.deltas.items():
                delta_decimal = Decimal(str(delta_value))
                if abs(delta_decimal) > Decimal("10"):  # $10 minimum threshold
                    action = "BUY" if delta_decimal > 0 else "SELL"
                    rebalance_items.append(
                        RebalancePlanItemDTO(
                            symbol=symbol,
                            action=action,
                            current_weight=Decimal("0"),  # Will be calculated properly in production
                            target_weight=Decimal("0"),   # Will be calculated properly in production
                            weight_diff=Decimal("0"),     # Will be calculated properly in production
                            target_value=Decimal(str(comparison_dto.target_values.get(symbol, 0))),
                            current_value=Decimal(str(comparison_dto.current_values.get(symbol, 0))),
                            trade_amount=delta_decimal if action == "BUY" else -delta_decimal,
                            priority=1,  # Default priority
                        )
                    )

            if not rebalance_items:
                return None

            return RebalancePlanDTO(
                correlation_id=str(uuid.uuid4()),
                causation_id=f"allocation-comparison-{datetime.now(UTC).isoformat()}",
                timestamp=datetime.now(UTC),
                plan_id=f"rebalance-{uuid.uuid4()}",
                items=rebalance_items,
                total_portfolio_value=sum(
                    Decimal(str(v)) for v in comparison_dto.current_values.values()
                ) or Decimal("0"),
                total_trade_value=sum(abs(item.trade_amount) for item in rebalance_items) or Decimal("0"),
            )

        except Exception as e:
            self.logger.error(f"Failed to create rebalance plan: {e}")
            return None

    def _convert_execution_result_to_orders(self, execution_result: ExecutionResultDTO) -> list[dict[str, Any]]:
        """Convert execution result to orders list for CLI compatibility."""
        orders = []
        
        for order_result in execution_result.orders:
            if order_result.success:
                orders.append({
                    "symbol": order_result.symbol,
                    "action": order_result.action.upper(),
                    "quantity": str(order_result.shares),
                    "status": "filled",
                    "order_id": order_result.order_id or "unknown",
                })
            else:
                orders.append({
                    "symbol": order_result.symbol,
                    "action": order_result.action.upper(),
                    "quantity": str(order_result.shares),
                    "status": "failed", 
                    "error": order_result.error_message or "Unknown error",
                })
            
        return orders

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status for monitoring."""
        active = [w for w in self.active_workflows.values() if w["status"] not in ["completed", "failed"]]
        completed = [w for w in self.active_workflows.values() if w["status"] == "completed"]
        failed = [w for w in self.active_workflows.values() if w["status"] == "failed"]
        
        return {
            "total_workflows": len(self.active_workflows),
            "active_workflows": len(active),
            "completed_workflows": len(completed),
            "failed_workflows": len(failed),
            "workflows": list(self.active_workflows.values()),
        }

    def shutdown(self) -> None:
        """Shutdown orchestrator and cleanup resources."""
        self.logger.info("Shutting down TradingOrchestrator")
        self.executor.shutdown(wait=True)
        
        # Complete any active workflows with shutdown status
        for workflow in self.active_workflows.values():
            if workflow["status"] not in ["completed", "failed"]:
                workflow["status"] = "shutdown"
                workflow["end_time"] = datetime.now(UTC)
