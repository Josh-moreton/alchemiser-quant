#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Signal generation event handler for event-driven architecture.

Processes StartupEvent and WorkflowStarted events to generate strategy signals
and emit SignalGenerated events. This handler is stateless and focuses on
domain signal generation logic without orchestration concerns.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    SignalGenerated,
    StartupEvent,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas import StrategySignal
from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ConsolidatedPortfolio,
)
from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine


class SignalGenerationHandler:
    """Event handler for strategy signal generation.

    Listens for workflow startup events and generates strategy signals,
    emitting SignalGenerated events for downstream consumption.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize the signal generation handler.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for signal generation.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, (StartupEvent, WorkflowStarted)):
                self._handle_signal_generation_request(event)
            else:
                self.logger.debug(
                    f"SignalGenerationHandler ignoring event type: {event.event_type}",
                    extra={"correlation_id": event.correlation_id},
                )

        except DataProviderError as e:
            # Specific data provider errors - expected failure mode
            self.logger.error(
                f"SignalGenerationHandler data provider error for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "error_type": "DataProviderError",
                },
            )
            self._emit_workflow_failure(event, str(e))
        except Exception as e:
            # Unexpected errors - log with full context for investigation
            self.logger.error(
                f"SignalGenerationHandler unexpected error for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            self._emit_workflow_failure(event, str(e))

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type

        """
        return event_type in [
            "StartupEvent",
            "WorkflowStarted",
        ]

    def _handle_signal_generation_request(
        self, event: StartupEvent | WorkflowStarted
    ) -> None:
        """Handle signal generation request from startup or workflow events.

        Args:
            event: The event that triggered signal generation

        """
        self.logger.info(
            "🔄 Starting signal generation from event-driven handler",
            extra={"correlation_id": event.correlation_id},
        )

        try:
            # Generate signals using domain logic
            strategy_signals, consolidated_portfolio = self._generate_signals()

            if not strategy_signals:
                raise DataProviderError("Failed to generate strategy signals")

            # Validate signal quality
            if not self._validate_signal_quality(strategy_signals):
                raise DataProviderError(
                    "Signal analysis failed validation - no meaningful data available"
                )

            # Emit SignalGenerated event
            self._emit_signal_generated_event(
                strategy_signals, consolidated_portfolio, event.correlation_id
            )

            # Check if workflow failed during event processing
            if self.event_bus.is_workflow_failed(event.correlation_id):
                # Demoted to DEBUG to avoid any INFO logs after downstream processing begins
                self.logger.debug(
                    f"🚫 Workflow {event.correlation_id} failed during event processing - signal generation stopping",
                    extra={"correlation_id": event.correlation_id},
                )
                return

            # Event emission completion indicates signal generation is done
            # No additional logging needed as downstream processing may have failed

        except DataProviderError:
            # Re-raise specific errors to be handled at top level
            raise
        except Exception as e:
            self.logger.error(
                f"Signal generation failed: {e}",
                extra={
                    "correlation_id": event.correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            self._emit_workflow_failure(event, str(e))
            raise

    def _generate_signals(self) -> tuple[dict[str, Any], ConsolidatedPortfolio]:
        """Generate strategy signals and consolidated portfolio allocation.

        Returns:
            Tuple of (strategy_signals dict, ConsolidatedPortfolio)

        """
        # Use DSL strategy engine directly for signal generation
        market_data_port = self.container.infrastructure.market_data_service()

        # Create DSL strategy engine
        dsl_engine = DslStrategyEngine(market_data_port)
        signals = dsl_engine.generate_signals(datetime.now(UTC))

        # Convert signals to display format
        strategy_signals = self._convert_signals_to_display_format(signals)

        # Create consolidated portfolio from signals (returns Decimal allocations)
        consolidated_portfolio_dict, contributing_strategies = (
            self._build_consolidated_portfolio(signals)
        )

        # Instrumentation and fail-fast check for empty allocations
        allocation_count = len(consolidated_portfolio_dict)
        self.logger.info(
            f"Built consolidated portfolio with {allocation_count} allocations",
            extra={
                "symbols": list(consolidated_portfolio_dict.keys())[:10],
                "total_allocations": allocation_count,
            },
        )
        if allocation_count == 0:
            # Avoid constructing DTO with empty payload; surface actionable error
            raise DataProviderError(
                "No positive target allocations produced by strategy signals"
            )

        # Create ConsolidatedPortfolio - from_dict_allocation handles Decimal conversion
        # Convert Decimal to float for the factory method which handles conversion internally
        allocation_dict_float = {
            symbol: float(allocation)
            for symbol, allocation in consolidated_portfolio_dict.items()
        }
        consolidated_portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict=allocation_dict_float,
            correlation_id=f"signal_handler_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            source_strategies=contributing_strategies,
        )

        return strategy_signals, consolidated_portfolio

    def _convert_signals_to_display_format(
        self, signals: list[StrategySignal]
    ) -> dict[str, Any]:
        """Convert DSL signals to display format."""
        strategy_signals = {}

        if signals:
            # For DSL engine, we group all signals under "DSL" strategy type
            if len(signals) > 1:
                # Multiple signals - present a concise primary symbol; keep full list separately
                symbols = [
                    signal.symbol.value for signal in signals if signal.action == "BUY"
                ]
                primary_signal = signals[0]  # Use first signal for other attributes
                primary_symbol = primary_signal.symbol.value
                strategy_signals["DSL"] = {
                    "symbol": primary_symbol,
                    "symbols": symbols,  # Keep individual symbols for other processing and display
                    "action": primary_signal.action,
                    "reasoning": primary_signal.reasoning,
                    "is_multi_symbol": True,
                }
            else:
                # Single signal - existing behavior
                signal = signals[0]
                strategy_signals["DSL"] = {
                    "symbol": signal.symbol.value,
                    "action": signal.action,
                    "reasoning": signal.reasoning,
                    "is_multi_symbol": False,
                }

        return strategy_signals

    def _build_consolidated_portfolio(
        self, signals: list[StrategySignal]
    ) -> tuple[dict[str, Decimal], list[str]]:
        """Build consolidated portfolio from strategy signals.

        Returns allocations as Decimal to preserve precision per copilot instructions:
        "Money: Decimal with explicit contexts; never mix with float."
        """
        consolidated_portfolio: dict[str, Decimal] = {}
        contributing_strategies: list[str] = []

        for signal in signals:
            symbol = signal.symbol.value
            allocation = self._extract_signal_allocation(signal)

            if allocation > 0:
                consolidated_portfolio[symbol] = allocation
                contributing_strategies.append("DSL")

        return consolidated_portfolio, contributing_strategies

    def _extract_signal_allocation(self, signal: StrategySignal) -> Decimal:
        """Extract allocation percentage from signal.

        Returns Decimal to maintain numerical precision per copilot instructions.
        """
        if signal.target_allocation is not None:
            return signal.target_allocation
        return Decimal("0.0")

    def _validate_signal_quality(self, strategy_signals: dict[str, Any]) -> bool:
        """Validate that signals contain meaningful data.

        Args:
            strategy_signals: Dictionary of strategy signals to validate

        Returns:
            True if signals are valid and meaningful, False otherwise

        """
        if not strategy_signals:
            self.logger.warning("No strategy signals generated")
            return False

        # Check for basic signal structure
        for strategy_name, signal_data in strategy_signals.items():
            if not isinstance(signal_data, dict):
                self.logger.warning(f"Invalid signal data for strategy {strategy_name}")
                return False

            # Check for required fields
            required_fields = ["symbol", "action"]
            for field in required_fields:
                if field not in signal_data:
                    self.logger.warning(
                        f"Signal for {strategy_name} missing required field: {field}"
                    )
                    return False

        self.logger.info(
            f"✅ Generated and validated signals for {len(strategy_signals)} strategies"
        )
        return True

    def _emit_signal_generated_event(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: ConsolidatedPortfolio,
        correlation_id: str,
    ) -> None:
        """Emit SignalGenerated event.

        Args:
            strategy_signals: Generated strategy signals
            consolidated_portfolio: Consolidated portfolio allocation
            correlation_id: Correlation ID from the triggering event

        """
        try:
            # Check if workflow has failed before emitting events
            is_failed = self.event_bus.is_workflow_failed(correlation_id)
            self.logger.debug(
                f"🔍 Workflow state check: correlation_id={correlation_id}, is_failed={is_failed}"
            )

            if is_failed:
                self.logger.info(
                    f"🚫 Skipping SignalGenerated event emission - workflow {correlation_id} already failed"
                )
                return

            self._log_final_signal_summary(strategy_signals, consolidated_portfolio)

            self.logger.debug(
                f"🚀 ABOUT TO EMIT SignalGenerated event for correlation_id={correlation_id}"
            )

            event = SignalGenerated(
                correlation_id=correlation_id,
                causation_id=correlation_id,  # This event is caused by the startup/workflow event
                event_id=f"signal-generated-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="strategy_v2.handlers",
                source_component="SignalGenerationHandler",
                signals_data=strategy_signals,
                consolidated_portfolio=consolidated_portfolio.model_dump(),
                signal_count=len(strategy_signals),
                metadata={
                    "generation_timestamp": datetime.now(UTC).isoformat(),
                    "source": "event_driven_handler",
                },
            )

            self.logger.debug(
                f"📡 Publishing SignalGenerated event with {len(strategy_signals)} signals for correlation_id={correlation_id}"
            )
            self.event_bus.publish(event)
            self.logger.debug(
                f"✅ SignalGenerated event publish completed for correlation_id={correlation_id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to emit SignalGenerated event: {e}")
            raise

    def _emit_workflow_failure(
        self, original_event: BaseEvent, error_message: str
    ) -> None:
        """Emit WorkflowFailed event when signal generation fails.

        Args:
            original_event: The event that triggered the failed operation
            error_message: Error message describing the failure

        """
        try:
            failure_event = WorkflowFailed(
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="strategy_v2.handlers",
                source_component="SignalGenerationHandler",
                workflow_type="signal_generation",
                failure_reason=error_message,
                failure_step="signal_generation",
                error_details={
                    "original_event_type": original_event.event_type,
                    "original_event_id": original_event.event_id,
                },
            )

            self.event_bus.publish(failure_event)
            self.logger.error(f"📡 Emitted WorkflowFailed event: {error_message}")

        except Exception as e:
            self.logger.error(f"Failed to emit WorkflowFailed event: {e}")

    def _log_final_signal_summary(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: ConsolidatedPortfolio,
    ) -> None:
        """Log final consolidated signal and portfolio summary."""
        try:
            self._log_strategy_signals(strategy_signals)
            self._log_portfolio_allocations(consolidated_portfolio)
        except Exception as exc:  # pragma: no cover - logging safeguard
            self.logger.warning("Failed to log final signal summary: %s", exc)

    def _log_strategy_signals(self, strategy_signals: dict[str, Any]) -> None:
        """Log strategy signals with formatted details."""
        if not strategy_signals:
            return

        self.logger.info("📡 Final Strategy Signals:")
        for raw_name, data in strategy_signals.items():
            if not isinstance(data, dict):
                continue

            detail = self._format_signal_detail(raw_name, data)
            self.logger.info(f"  • {detail}")

    def _format_signal_detail(self, raw_name: str, data: dict[str, Any]) -> str:
        """Format individual signal detail for logging."""
        name = str(raw_name)
        action = str(data.get("action", "")).upper() or "UNKNOWN"

        if self._is_multi_symbol_signal(data):
            return self._format_multi_symbol_detail(name, action, data)
        return self._format_single_symbol_detail(name, action, data)

    def _is_multi_symbol_signal(self, data: dict[str, Any]) -> bool:
        """Check if signal data represents a multi-symbol signal."""
        return bool(data.get("is_multi_symbol")) and isinstance(
            data.get("symbols"), list
        )

    def _format_multi_symbol_detail(
        self, name: str, action: str, data: dict[str, Any]
    ) -> str:
        """Format multi-symbol signal detail."""
        symbols = ", ".join(str(symbol) for symbol in data["symbols"])
        return f"{name}: {action} {symbols}" if symbols else f"{name}: {action}"

    def _format_single_symbol_detail(
        self, name: str, action: str, data: dict[str, Any]
    ) -> str:
        """Format single symbol signal detail."""
        symbol = data.get("symbol")
        if isinstance(symbol, str) and symbol.strip():
            return f"{name}: {action} {symbol}"
        return f"{name}: {action}"

    def _log_portfolio_allocations(
        self, consolidated_portfolio: ConsolidatedPortfolio
    ) -> None:
        """Log target portfolio allocations."""
        if consolidated_portfolio is None:
            return

        allocations = consolidated_portfolio.target_allocations
        if not allocations:
            return

        self.logger.info("🎯 Target Portfolio Allocations:")
        for symbol, allocation in allocations.items():
            percent = self._safe_convert_to_percentage(allocation)
            self.logger.info(f"  • {symbol}: {percent:.2f}%")

    def _safe_convert_to_percentage(
        self, allocation: float | int | str | Decimal
    ) -> float:
        """Safely convert allocation to percentage."""
        try:
            return float(allocation) * 100
        except (TypeError, ValueError):
            return 0.0
