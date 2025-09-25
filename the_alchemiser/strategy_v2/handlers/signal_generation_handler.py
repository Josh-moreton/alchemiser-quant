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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    SignalGenerated,
    StartupEvent,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.persistence.signal_idempotency_store import (
    get_signal_idempotency_store,
)
from the_alchemiser.shared.schemas import ConsolidatedPortfolioDTO
from the_alchemiser.shared.types import StrategySignal
from the_alchemiser.shared.types.exceptions import DataProviderError
from the_alchemiser.shared.utils.event_hashing import (
    generate_market_snapshot_id,
    generate_signal_hash,
)
from the_alchemiser.shared.value_objects.symbol import Symbol
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

        # Initialize idempotency store for signal replay detection
        self.idempotency_store = get_signal_idempotency_store()

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
                    f"SignalGenerationHandler ignoring event type: {event.event_type}"
                )

        except Exception as e:
            self.logger.error(
                f"SignalGenerationHandler event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

            # Emit workflow failure event
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

    def _handle_signal_generation_request(self, event: StartupEvent | WorkflowStarted) -> None:
        """Handle signal generation request from startup or workflow events.

        Args:
            event: The event that triggered signal generation

        """
        self.logger.info("🔄 Starting signal generation from event-driven handler")

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

            # Generate signal hash for idempotency checking
            # Use model_dump for Pydantic object; fallback not needed now that DTO alias is Pydantic
            signal_hash = generate_signal_hash(
                strategy_signals,
                consolidated_portfolio.model_dump(),
            )

            # Check if this signal was already processed
            if self.idempotency_store.has_signal_hash(signal_hash):
                existing_metadata = self.idempotency_store.get_signal_metadata(signal_hash)
                existing_correlation = (
                    existing_metadata.get("correlation_id") if existing_metadata else "unknown"
                )

                self.logger.info(
                    f"🔄 Skipping duplicate signal generation - hash {signal_hash} "
                    f"already processed (original correlation: {existing_correlation})"
                )
                return

            # Store signal hash for future idempotency checks
            self.idempotency_store.store_signal_hash(
                signal_hash=signal_hash,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                metadata={
                    "event_type": event.event_type,
                    "signal_count": len(strategy_signals),
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            )

            # Emit SignalGenerated event with enhanced metadata
            self._emit_signal_generated_event(
                strategy_signals,
                consolidated_portfolio,
                event.correlation_id,
                signal_hash,
            )

            self.logger.info("✅ Signal generation completed successfully")

        except Exception as e:
            self.logger.error(f"Signal generation failed: {e}")
            self._emit_workflow_failure(event, str(e))

    def _generate_signals(self) -> tuple[dict[str, Any], ConsolidatedPortfolioDTO]:
        """Generate strategy signals and consolidated portfolio allocation.

        Returns:
            Tuple of (strategy_signals dict, ConsolidatedPortfolioDTO)

        """
        # Use DSL strategy engine directly for signal generation
        market_data_port = self.container.infrastructure.market_data_service()

        # Create DSL strategy engine
        dsl_engine = DslStrategyEngine(market_data_port)
        signals = dsl_engine.generate_signals(datetime.now(UTC))

        # Convert signals to display format
        strategy_signals = self._convert_signals_to_display_format(signals)

        # Create consolidated portfolio from signals
        consolidated_portfolio_dict, contributing_strategies = self._build_consolidated_portfolio(
            signals
        )

        # Create ConsolidatedPortfolioDTO (alias of ConsolidatedPortfolio)
        consolidated_portfolio = ConsolidatedPortfolioDTO.from_dict_allocation(
            allocation_dict=consolidated_portfolio_dict,
            correlation_id=f"signal_handler_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            source_strategies=contributing_strategies,
        )

        return strategy_signals, consolidated_portfolio

    def _convert_signals_to_display_format(self, signals: list[StrategySignal]) -> dict[str, Any]:
        """Convert DSL signals to display format."""
        strategy_signals = {}

        if signals:
            # For DSL engine, we group all signals under "DSL" strategy type
            if len(signals) > 1:
                # Multiple signals - present a concise primary symbol; keep full list separately
                symbols = [signal.symbol.value for signal in signals if signal.action == "BUY"]
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
    ) -> tuple[dict[str, float], list[str]]:
        """Build consolidated portfolio from strategy signals."""
        consolidated_portfolio: dict[str, float] = {}
        contributing_strategies: list[str] = []

        for signal in signals:
            symbol = signal.symbol.value
            allocation = self._extract_signal_allocation(signal)

            if allocation > 0:
                consolidated_portfolio[symbol] = allocation
                contributing_strategies.append("DSL")

        return consolidated_portfolio, contributing_strategies

    def _generate_signals_from_portfolio(
        self, consolidated_portfolio: ConsolidatedPortfolioDTO
    ) -> list[StrategySignal]:
        """Generate StrategySignal objects from portfolio for market snapshot ID.

        This is a helper method to create signals from portfolio data for snapshot ID generation.
        """
        signals = []
        for symbol_str, allocation in consolidated_portfolio.target_allocations.items():
            if allocation > 0:
                signal = StrategySignal(
                    symbol=Symbol(symbol_str),
                    action="BUY",
                    target_allocation=allocation,
                    reasoning="Generated from consolidated portfolio",
                )
                signals.append(signal)

        return signals

    def _extract_signal_allocation(self, signal: StrategySignal) -> float:
        """Extract allocation percentage from signal."""
        if signal.target_allocation is not None:
            return float(signal.target_allocation)
        return 0.0

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

        self.logger.info(f"✅ Signal validation passed for {len(strategy_signals)} strategies")
        return True

    def _emit_signal_generated_event(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: ConsolidatedPortfolioDTO,
        correlation_id: str,
        signal_hash: str,
    ) -> None:
        """Emit SignalGenerated event with enhanced metadata for idempotency.

        Args:
            strategy_signals: Generated strategy signals
            consolidated_portfolio: Consolidated portfolio allocation
            correlation_id: Correlation ID from the triggering event
            signal_hash: Deterministic hash for idempotency checking

        """
        try:
            # Generate market snapshot ID from the signal data
            dsl_signals = self._generate_signals_from_portfolio(consolidated_portfolio)
            market_snapshot_id = generate_market_snapshot_id(dsl_signals)

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
                # Enhanced metadata for event-driven architecture
                schema_version="1.0",
                signal_hash=signal_hash,
                market_snapshot_id=market_snapshot_id,
                metadata={
                    "generation_timestamp": datetime.now(UTC).isoformat(),
                    "source": "event_driven_handler",
                    "signal_hash": signal_hash,  # Also include in metadata for convenience
                    "market_snapshot_id": market_snapshot_id,
                },
            )

            self.event_bus.publish(event)
            self.logger.info(
                f"📡 Emitted SignalGenerated event with {len(strategy_signals)} signals "
                f"(hash: {signal_hash}, snapshot: {market_snapshot_id})",
                extra={
                    "correlation_id": correlation_id,
                    "signal_hash": signal_hash,
                    "market_snapshot_id": market_snapshot_id,
                    "signal_count": len(strategy_signals),
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to emit SignalGenerated event: {e}")
            raise

    def _emit_workflow_failure(self, original_event: BaseEvent, error_message: str) -> None:
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
