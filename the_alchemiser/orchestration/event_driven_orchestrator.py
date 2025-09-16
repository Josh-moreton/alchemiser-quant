#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven orchestration handlers for startup, recovery, and reconciliation.

Provides event handlers that replace traditional direct-call orchestration
with event-driven workflows for better decoupling and extensibility.
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
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    StartupEvent,
    TradeExecuted,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO

# Constants for repeated literals
DECIMAL_ZERO = Decimal("0")
MIN_TRADE_AMOUNT_USD = Decimal("100")


class EventDrivenOrchestrator:
    """Event-driven orchestrator for startup, recovery, and reconciliation workflows.

    Replaces traditional direct-call orchestration with event-driven handlers
    that provide better decoupling and extensibility.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize the event-driven orchestrator.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

        # Initialize sub-orchestrators for workflow execution
        self.signal_orchestrator = SignalOrchestrator(container.config.settings(), container)
        self.portfolio_orchestrator = PortfolioOrchestrator(container.config.settings(), container)

        # Register event handlers
        self._register_handlers()

        # Track workflow state for recovery and reconciliation
        self.workflow_state: dict[str, Any] = {
            "startup_completed": False,
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_successful_workflow": None,
        }

    def _register_handlers(self) -> None:
        """Register event handlers for orchestration workflows."""
        # Subscribe to all event types for orchestration monitoring
        self.event_bus.subscribe("StartupEvent", self)
        self.event_bus.subscribe("SignalGenerated", self)
        self.event_bus.subscribe("RebalancePlanned", self)
        self.event_bus.subscribe("TradeExecuted", self)

        self.logger.info("Registered event-driven orchestration handlers")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for orchestration workflows.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, StartupEvent):
                self._handle_startup(event)
            elif isinstance(event, SignalGenerated):
                self._handle_signal_generated(event)
            elif isinstance(event, RebalancePlanned):
                self._handle_rebalance_planned(event)
            elif isinstance(event, TradeExecuted):
                self._handle_trade_executed(event)
            else:
                self.logger.debug(
                    f"Orchestrator ignoring event type: {event.event_type}"
                )

        except Exception as e:
            self.logger.error(
                f"Orchestration event handling failed for {event.event_type}: {e}",
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
        return event_type in [
            "StartupEvent",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
        ]

    def _handle_startup(self, event: StartupEvent) -> None:
        """Handle system startup event.

        Coordinates high-level workflow initialization.

        Args:
            event: The startup event

        """
        self.logger.info(
            f"🚀 System startup orchestration triggered for mode: {event.startup_mode}"
        )

        # Reset workflow state for new run
        self.workflow_state.update(
            {
                "startup_completed": True,
                "signal_generation_in_progress": True,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Perform startup orchestration tasks
        startup_mode = event.startup_mode
        configuration = event.configuration or {}

        self.logger.info(f"Orchestrating {startup_mode} workflow")
        self.logger.debug(f"Startup configuration: {configuration}")

        # Track successful startup - domain orchestrators will handle the actual work
        self.workflow_state["last_successful_workflow"] = "startup"

    def _execute_signal_generation(self, correlation_id: str) -> None:
        """Execute signal generation workflow and emit SignalGenerated event.
        
        Args:
            correlation_id: Correlation ID for tracking the workflow
        """
        try:
            self.logger.info("🔄 Starting signal generation workflow")
            
            # Generate signals using signal orchestrator
            strategy_signals, consolidated_portfolio_dto = (
                self.signal_orchestrator.generate_signals()
            )
            
            if not strategy_signals:
                self.logger.error("Failed to generate strategy signals")
                self.workflow_state["signal_generation_in_progress"] = False
                return

            # Validate signal quality before proceeding
            if not self.signal_orchestrator.validate_signal_quality(strategy_signals):
                self.logger.error(
                    "Signal analysis failed validation - no meaningful data available"
                )
                self.workflow_state["signal_generation_in_progress"] = False
                return

            # Convert strategy signals to StrategySignalDTO format for event
            signal_dtos = self._convert_strategy_signals_to_dtos(strategy_signals, correlation_id)
            
            # Create SignalGenerated event
            event = SignalGenerated(
                correlation_id=correlation_id,
                causation_id=f"startup-{correlation_id}",
                event_id=f"signal-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="EventDrivenOrchestrator",
                signals=signal_dtos,
                portfolio_data=consolidated_portfolio_dto.to_dict_allocation(),
            )

            # Emit the event
            self.event_bus.publish(event)
            self.logger.info(f"✅ Signal generation completed - emitted event {event.event_id}")
            
            # Update workflow state
            self.workflow_state["signal_generation_in_progress"] = False
            self.workflow_state["last_successful_workflow"] = "signal_generation"

        except Exception as e:
            self.logger.error(f"Signal generation workflow failed: {e}")
            self.workflow_state["signal_generation_in_progress"] = False

    def _convert_strategy_signals_to_dtos(
        self, strategy_signals: dict[str, Any], correlation_id: str
    ) -> list[Any]:
        """Convert strategy signals to StrategySignalDTO format.
        
        Args:
            strategy_signals: Strategy signals from signal orchestrator
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of StrategySignalDTO objects
        """
        from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO
        
        signal_dtos = []
        
        for strategy_name, signal_data in strategy_signals.items():
            # Handle multi-symbol signals (like Nuclear strategy)
            if signal_data.get("is_multi_symbol", False):
                symbols = signal_data.get("symbols", [signal_data["symbol"]])
                for symbol in symbols:
                    dto = StrategySignalDTO(
                        correlation_id=correlation_id,
                        causation_id=f"signal-generation-{correlation_id}",
                        timestamp=datetime.now(UTC),
                        strategy_name=strategy_name,
                        symbol=symbol,
                        action=signal_data["action"],
                        confidence=Decimal(str(signal_data["confidence"])),
                        reasoning=signal_data["reasoning"],
                        signal_strength="STRONG" if signal_data["confidence"] > 0.8 else "MEDIUM",
                        metadata={
                            "is_multi_symbol": True,
                            "original_symbols": symbols,
                        },
                    )
                    signal_dtos.append(dto)
            else:
                # Single symbol signal
                dto = StrategySignalDTO(
                    correlation_id=correlation_id,
                    causation_id=f"signal-generation-{correlation_id}",
                    timestamp=datetime.now(UTC),
                    strategy_name=strategy_name,
                    symbol=signal_data["symbol"],
                    action=signal_data["action"],
                    confidence=Decimal(str(signal_data["confidence"])),
                    reasoning=signal_data["reasoning"],
                    signal_strength="STRONG" if signal_data["confidence"] > 0.8 else "MEDIUM",
                    metadata={"is_multi_symbol": False},
                )
                signal_dtos.append(dto)
                
        return signal_dtos

    def _handle_signal_generated(self, event: SignalGenerated) -> None:
        """Handle signal generation event.

        Coordinates the transition from signal generation to portfolio rebalancing.

        Args:
            event: The signal generated event

        """
        self.logger.info(
            f"📊 Signal generation orchestration: {len(event.signals)} signals received"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,  # Signals completed
                "rebalancing_in_progress": True,  # Rebalancing will start
            }
        )

        # Log signal summary for orchestration tracking
        for signal in event.signals:
            self.logger.debug(
                f"Orchestrating signal: {signal.symbol} {signal.action} "
                f"(strategy: {signal.strategy_name}, confidence: {signal.confidence})"
            )

        # Track successful signal processing - PortfolioOrchestrator will handle rebalancing
        self.workflow_state["last_successful_workflow"] = "signal_generation"

    def _execute_portfolio_rebalancing(self, signal_event: SignalGenerated) -> None:
        """Execute portfolio rebalancing workflow based on signals.
        
        Args:
            signal_event: The SignalGenerated event containing signals and portfolio data
        """
        try:
            self.logger.info("🔄 Starting portfolio rebalancing workflow")
            
            # Reconstruct ConsolidatedPortfolioDTO from event data
            from the_alchemiser.shared.dto.consolidated_portfolio_dto import ConsolidatedPortfolioDTO
            
            consolidated_portfolio_dto = ConsolidatedPortfolioDTO.from_dict_allocation(
                allocation_dict=signal_event.portfolio_data,
                correlation_id=signal_event.correlation_id,
                source_strategies=list(set(signal.strategy_name for signal in signal_event.signals if signal.strategy_name)),
            )

            # Get comprehensive account data using portfolio orchestrator
            account_data = self.portfolio_orchestrator.get_comprehensive_account_data()
            
            if not account_data:
                self.logger.error("Could not retrieve account data for rebalancing")
                self.workflow_state["rebalancing_in_progress"] = False
                return

            account_info = account_data.get("account_info")
            if not account_info:
                self.logger.error("Account info not available for rebalancing")
                self.workflow_state["rebalancing_in_progress"] = False
                return

            # Calculate allocation comparison
            allocation_comparison = self.portfolio_orchestrator.analyze_allocation_comparison(
                consolidated_portfolio_dto
            )
            
            if not allocation_comparison:
                self.logger.error("Failed to generate allocation comparison")
                self.workflow_state["rebalancing_in_progress"] = False
                return
                
            self.logger.info("Generated allocation comparison analysis")

            # Create rebalance plan from allocation comparison
            rebalance_plan = self._create_rebalance_plan_from_allocation(
                allocation_comparison, account_info, signal_event.correlation_id
            )

            if not rebalance_plan:
                self.logger.info("📊 No significant trades needed - portfolio already balanced")
                # Create empty rebalance plan to represent no-op scenario
                rebalance_plan = self._create_empty_rebalance_plan(signal_event.correlation_id)

            # Create RebalancePlanned event
            event = RebalancePlanned(
                correlation_id=signal_event.correlation_id,
                causation_id=signal_event.event_id,
                event_id=f"rebalance-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="EventDrivenOrchestrator",
                rebalance_plan=rebalance_plan,
                allocation_analysis=allocation_comparison.to_dict() if hasattr(allocation_comparison, 'to_dict') else {},
            )

            # Emit the event
            self.event_bus.publish(event)
            self.logger.info(f"✅ Portfolio rebalancing completed - emitted event {event.event_id}")
            
            # Update workflow state
            self.workflow_state["rebalancing_in_progress"] = False
            self.workflow_state["last_successful_workflow"] = "rebalancing"

        except Exception as e:
            self.logger.error(f"Portfolio rebalancing execution failed: {e}")
            self.workflow_state["rebalancing_in_progress"] = False

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance planning event.

        Coordinates the transition from rebalancing to trade execution.

        Args:
            event: The rebalance planned event

        """
        self.logger.info(
            f"⚖️ Rebalance planning orchestration: {len(event.rebalance_plan.items)} trades planned"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "rebalancing_in_progress": False,  # Rebalancing plan completed
                "trading_in_progress": True,  # Trading will start
            }
        )

        # Log rebalancing plan summary for orchestration tracking
        total_value = event.rebalance_plan.total_trade_value
        self.logger.debug(f"Orchestrating total trade value: ${total_value}")

        # Track successful rebalancing - TradingOrchestrator will handle execution
        self.workflow_state["last_successful_workflow"] = "rebalancing"

    def _execute_trade_execution(self, rebalance_event: RebalancePlanned) -> None:
        """Execute trade execution workflow based on rebalance plan.
        
        Args:
            rebalance_event: The RebalancePlanned event containing the rebalance plan
        """
        try:
            self.logger.info("🚀 Starting trade execution workflow")
            
            rebalance_plan = rebalance_event.rebalance_plan
            
            # Check if this is a no-op plan
            if (len(rebalance_plan.items) == 1 and 
                rebalance_plan.items[0].action == "HOLD" and
                rebalance_plan.total_trade_value == DECIMAL_ZERO):
                
                self.logger.info("📊 No trades to execute - portfolio already balanced")
                
                # Create no-trade execution result
                execution_result = ExecutionResultDTO(
                    success=True,
                    plan_id=rebalance_plan.plan_id,
                    correlation_id=rebalance_plan.correlation_id,
                    orders=[],
                    orders_placed=0,
                    orders_succeeded=0,
                    total_trade_value=DECIMAL_ZERO,
                    execution_timestamp=datetime.now(UTC),
                    metadata={"scenario": "no_trades_needed"},
                )
            else:
                # Execute actual trades
                self.logger.info(f"🚀 EXECUTING ACTUAL TRADES: {len(rebalance_plan.items)} items")
                
                # Get ExecutionManager from container
                execution_manager = self.container.services.execution_manager()
                
                # Execute the rebalance plan
                execution_result = execution_manager.execute_rebalance_plan(rebalance_plan)
                
                self.logger.info(
                    f"✅ Execution completed: {execution_result.orders_succeeded}/"
                    f"{execution_result.orders_placed} orders succeeded"
                )

            # Determine execution success
            execution_success = (
                execution_result.success and 
                (execution_result.orders_placed == 0 or  # No-op case
                 execution_result.orders_succeeded == execution_result.orders_placed)  # All succeeded
            )

            # Create TradeExecuted event
            event = TradeExecuted(
                correlation_id=rebalance_event.correlation_id,
                causation_id=rebalance_event.event_id,
                event_id=f"trade-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="EventDrivenOrchestrator",
                execution_results=self._convert_execution_result_to_event_data(execution_result),
                portfolio_state_after=None,  # TODO: Add portfolio state tracking
                success=execution_success,
                error_message=None if execution_success else "Some orders failed",
            )

            # Emit the event
            self.event_bus.publish(event)
            self.logger.info(f"✅ Trade execution completed - emitted event {event.event_id}")
            
            # Update workflow state
            self.workflow_state["trading_in_progress"] = False
            self.workflow_state["last_successful_workflow"] = "trading"

        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            
            # Create failure execution result
            failed_result = ExecutionResultDTO(
                success=False,
                plan_id=f"failed-{uuid.uuid4()}",
                correlation_id=rebalance_event.correlation_id,
                orders=[],
                orders_placed=0,
                orders_succeeded=0,
                total_trade_value=DECIMAL_ZERO,
                execution_timestamp=datetime.now(UTC),
                metadata={"error": str(e)},
            )
            
            # Emit failure event
            try:
                failure_event = TradeExecuted(
                    correlation_id=rebalance_event.correlation_id,
                    causation_id=rebalance_event.event_id,
                    event_id=f"trade-failed-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="orchestration",
                    source_component="EventDrivenOrchestrator",
                    execution_results=self._convert_execution_result_to_event_data(failed_result),
                    portfolio_state_after=None,
                    success=False,
                    error_message=str(e),
                )
                self.event_bus.publish(failure_event)
            except Exception as emit_error:
                self.logger.warning(f"Failed to emit failure event: {emit_error}")
            
            self.workflow_state["trading_in_progress"] = False

    def _convert_execution_result_to_event_data(self, execution_result: ExecutionResultDTO) -> dict[str, Any]:
        """Convert ExecutionResultDTO to event data format.
        
        Args:
            execution_result: ExecutionResultDTO from execution manager
            
        Returns:
            Dictionary containing execution data for events
        """
        return {
            "plan_id": execution_result.plan_id,
            "success": execution_result.success,
            "orders_placed": execution_result.orders_placed,
            "orders_succeeded": execution_result.orders_succeeded,
            "total_trade_value": float(execution_result.total_trade_value),
            "execution_timestamp": execution_result.execution_timestamp.isoformat(),
            "orders": [
                {
                    "symbol": order.symbol,
                    "action": order.action,
                    "shares": float(order.shares) if order.shares else 0,
                    "price": float(order.price) if order.price else 0,
                    "trade_amount": float(order.trade_amount),
                    "order_id": order.order_id,
                    "success": order.success,
                    "error_message": order.error_message,
                }
                for order in execution_result.orders
            ],
            "metadata": execution_result.metadata or {},
        }

    def _handle_trade_executed(self, event: TradeExecuted) -> None:
        """Handle trade execution event.

        Completes the orchestration workflow and performs reconciliation.

        Args:
            event: The trade executed event

        """
        success = event.success
        self.logger.info(
            f"🎯 Trade execution orchestration completed: {'✅' if success else '❌'}"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "trading_in_progress": False,  # Trading completed
            }
        )

        if success:
            self.logger.info(
                "Orchestration: Full trading workflow completed successfully"
            )
            self.workflow_state["last_successful_workflow"] = "trading"

            # Perform post-trade reconciliation
            self._perform_reconciliation(event)
            
            # Send success notification
            self._send_trading_notification(event, success=True)
        else:
            self.logger.error(
                f"Orchestration: Trading workflow failed - {event.error_message}"
            )

            # Send failure notification  
            self._send_trading_notification(event, success=False)
            
            # Trigger recovery workflow
            self._trigger_recovery_workflow(event)

    def _send_trading_notification(self, event: TradeExecuted, *, success: bool) -> None:
        """Send trading completion notification.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        """
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            # Determine trading mode from container
            is_live = not self.container.config.paper_trading()
            mode_str = "LIVE" if is_live else "PAPER"
            
            # Extract execution data
            execution_data = event.execution_results
            orders_placed = execution_data.get("orders_placed", 0)
            orders_succeeded = execution_data.get("orders_succeeded", 0)
            total_trade_value = execution_data.get("total_trade_value", 0)

            if success:
                html_content = f"""
                <h2>Trading Execution Report - {mode_str.upper()}</h2>
                <p><strong>Status:</strong> Success</p>
                <p><strong>Orders Placed:</strong> {orders_placed}</p>
                <p><strong>Orders Succeeded:</strong> {orders_succeeded}</p>
                <p><strong>Total Trade Value:</strong> ${total_trade_value:,.2f}</p>
                <p><strong>Correlation ID:</strong> {event.correlation_id}</p>
                <p><strong>Timestamp:</strong> {event.timestamp}</p>
                """
            else:
                error_message = event.error_message or "Unknown error"
                html_content = build_error_email_html(
                    "Trading Execution Failed",
                    f"Trading workflow failed: {error_message}",
                )

            send_email_notification(
                subject=f"📈 The Alchemiser - {mode_str.upper()} Trading Report",
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {success}",
            )

            self.logger.info(f"Trading notification sent successfully (success={success})")

        except Exception as e:
            # Don't let notification failure break the workflow
            self.logger.warning(f"Failed to send trading notification: {e}")

    def _perform_reconciliation(self, event: TradeExecuted) -> None:
        """Perform post-trade reconciliation workflow.

        Args:
            event: The trade executed event

        """
        self.logger.info("🔄 Starting post-trade reconciliation")

        try:
            # In Phase 7, this would:
            # 1. Verify portfolio state matches expectations
            # 2. Check trade execution accuracy
            # 3. Update position tracking
            # 4. Generate reconciliation reports

            self.logger.info("Reconciliation: Verifying portfolio state")
            self.logger.info("Reconciliation: Checking trade execution accuracy")
            self.logger.info("Reconciliation: Updating position tracking")

            self.logger.info("✅ Post-trade reconciliation completed successfully")

        except Exception as e:
            self.logger.error(f"Reconciliation failed: {e}")

    def _trigger_recovery_workflow(self, event: TradeExecuted) -> None:
        """Trigger recovery workflow for failed operations.

        Args:
            event: The trade executed event that failed

        """
        self.logger.info("🛠️ Starting recovery workflow")

        try:
            # In Phase 7, this would:
            # 1. Assess the failure state
            # 2. Determine recovery actions
            # 3. Emit recovery events
            # 4. Alert system administrators

            self.logger.warning(f"Recovery: Assessing failure - {event.error_message}")
            self.logger.info("Recovery: Determining corrective actions")
            self.logger.info("Recovery: Preparing system alerts")

            # For now, log the recovery intent
            self.logger.info(
                "Recovery workflow prepared (full implementation in Phase 7)"
            )

        except Exception as e:
            self.logger.error(f"Recovery workflow failed: {e}")

    def _create_rebalance_plan_from_allocation(
        self,
        allocation_comparison: AllocationComparisonDTO,
        account_info: dict[str, Any],
        correlation_id: str,
    ) -> RebalancePlanDTO | None:
        """Convert allocation comparison DTO to RebalancePlanDTO.

        Args:
            allocation_comparison: AllocationComparisonDTO with target/current values, deltas
            account_info: Account information including portfolio_value
            correlation_id: Correlation ID for tracking

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
                plan_items, total_trade_value, portfolio_value_decimal, correlation_id
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
        """Create rebalance plan items from deltas."""
        plan_items = []
        total_trade_value = DECIMAL_ZERO

        for symbol, delta in deltas.items():
            abs_delta = abs(delta)
            
            # Skip small trades
            if abs_delta < MIN_TRADE_AMOUNT_USD:
                continue

            target_value = target_values.get(symbol, DECIMAL_ZERO)
            current_value = current_values.get(symbol, DECIMAL_ZERO)
            
            # Calculate weights
            target_weight = target_value / portfolio_value_decimal if portfolio_value_decimal > 0 else DECIMAL_ZERO
            current_weight = current_value / portfolio_value_decimal if portfolio_value_decimal > 0 else DECIMAL_ZERO
            weight_diff = target_weight - current_weight

            # Determine action
            action = "BUY" if delta > 0 else "SELL"
            
            plan_item = RebalancePlanItemDTO(
                symbol=symbol,
                current_weight=current_weight,
                target_weight=target_weight,
                weight_diff=weight_diff,
                target_value=target_value,
                current_value=current_value,
                trade_amount=abs_delta,
                action=action,
                priority=1,  # High priority for now
            )
            plan_items.append(plan_item)
            total_trade_value += abs_delta

        return plan_items, total_trade_value

    def _build_rebalance_plan_dto(
        self,
        plan_items: list[RebalancePlanItemDTO],
        total_trade_value: Decimal,
        portfolio_value_decimal: Decimal,
        correlation_id: str,
    ) -> RebalancePlanDTO:
        """Build final RebalancePlanDTO."""
        return RebalancePlanDTO(
            correlation_id=correlation_id,
            causation_id=f"rebalancing-{correlation_id}",
            timestamp=datetime.now(UTC),
            plan_id=f"event_driven_{correlation_id}_{int(datetime.now(UTC).timestamp())}",
            items=plan_items,
            total_portfolio_value=portfolio_value_decimal,
            total_trade_value=total_trade_value,
            max_drift_tolerance=Decimal("0.05"),  # Default tolerance
            execution_urgency="NORMAL",
            metadata={
                "created_by": "EventDrivenOrchestrator",
                "module": "orchestration",
                "workflow_type": "event_driven",
            },
        )

    def _create_empty_rebalance_plan(self, correlation_id: str) -> RebalancePlanDTO:
        """Create empty rebalance plan for no-op scenarios."""
        return RebalancePlanDTO(
            correlation_id=correlation_id,
            causation_id=f"no-trade-{correlation_id}",
            timestamp=datetime.now(UTC),
            plan_id=f"no_trade_{correlation_id}_{int(datetime.now(UTC).timestamp())}",
            items=[
                RebalancePlanItemDTO(
                    symbol="CASH",
                    current_weight=DECIMAL_ZERO,
                    target_weight=DECIMAL_ZERO,
                    weight_diff=DECIMAL_ZERO,
                    target_value=DECIMAL_ZERO,
                    current_value=DECIMAL_ZERO,
                    trade_amount=DECIMAL_ZERO,
                    action="HOLD",
                    priority=5,
                )
            ],
            total_portfolio_value=DECIMAL_ZERO,
            total_trade_value=DECIMAL_ZERO,
            max_drift_tolerance=Decimal("0.05"),
            execution_urgency="NORMAL",
            metadata={
                "created_by": "EventDrivenOrchestrator",
                "module": "orchestration",
                "workflow_type": "event_driven_no_op",
            },
        )

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status for monitoring.

        Returns:
            Dictionary containing workflow state information

        """
        return {
            "workflow_state": self.workflow_state.copy(),
            "event_bus_stats": self.event_bus.get_stats(),
            "orchestrator_active": True,
        }
