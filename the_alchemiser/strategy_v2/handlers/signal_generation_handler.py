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
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine
from the_alchemiser.strategy_v2.indicators.indicator_service import IndicatorService


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

    def _handle_signal_generation_request(self, event: StartupEvent | WorkflowStarted) -> None:
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
        consolidated_portfolio_dict, contributing_strategies = self._build_consolidated_portfolio(
            signals
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
            raise DataProviderError("No positive target allocations produced by strategy signals")

        # Create ConsolidatedPortfolio - from_dict_allocation handles Decimal conversion
        # Convert Decimal to float for the factory method which handles conversion internally
        allocation_dict_float = {
            symbol: float(allocation) for symbol, allocation in consolidated_portfolio_dict.items()
        }
        consolidated_portfolio = ConsolidatedPortfolio.from_dict_allocation(
            allocation_dict=allocation_dict_float,
            correlation_id=f"signal_handler_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            source_strategies=contributing_strategies,
        )

        return strategy_signals, consolidated_portfolio

    def _convert_signals_to_display_format(self, signals: list[StrategySignal]) -> dict[str, Any]:
        """Convert strategy signals to display format for notifications.

        Groups signals by strategy and shows all symbols allocated to by each strategy.

        Args:
            signals: List of strategy signals from DSL engine (one per symbol per strategy)

        Returns:
            Dictionary mapping strategy name to signal data
            Example: {"grail": {"symbols": ["TQQQ"], "action": "BUY", ...}}

        """
        # Group signals by strategy
        strategy_groups: dict[str, list[StrategySignal]] = {}
        for signal in signals:
            strategy_name = signal.strategy_name or "DSL"
            if strategy_name not in strategy_groups:
                strategy_groups[strategy_name] = []
            strategy_groups[strategy_name].append(signal)

        strategy_signals: dict[str, Any] = {}

        for strategy_name, strategy_signals_list in strategy_groups.items():
            # Collect all symbols and their allocations for this strategy
            symbols_and_allocations = []
            total_allocation = Decimal("0")

            for signal in strategy_signals_list:
                symbols_and_allocations.append(f"{signal.symbol.value}")
                if signal.target_allocation:
                    total_allocation += signal.target_allocation

            # Use first signal for action and reasoning (they should be the same for a strategy)
            first_signal = strategy_signals_list[0]

            # Build signal display string showing all symbols
            symbols_str = ", ".join(symbols_and_allocations)
            signal_display = f"{first_signal.action} {symbols_str}"

            # Extract technical indicators for all symbols in this strategy
            symbol_list = [signal.symbol.value for signal in strategy_signals_list]
            technical_indicators = self._extract_technical_indicators_for_symbols(symbol_list)

            strategy_signals[strategy_name] = {
                "symbols": symbols_and_allocations,
                "action": first_signal.action,
                "reasoning": first_signal.reasoning,
                "signal": signal_display,
                "total_allocation": float(total_allocation),
                "technical_indicators": technical_indicators,
            }

        return strategy_signals

    def _extract_technical_indicators_for_symbols(
        self, symbols: list[str]
    ) -> dict[str, dict[str, float]]:
        """Extract current technical indicators for given symbols.

        Fetches RSI(10), RSI(20), current price, and 200-day MA for each symbol
        to enable detailed email content with actual indicator values.

        Args:
            symbols: List of trading symbols to get indicators for

        Returns:
            Dict mapping symbol to technical indicators:
            {
                "SPY": {
                    "rsi_10": 82.5,
                    "rsi_20": 78.3,
                    "current_price": 505.10,
                    "ma_200": 487.50
                },
                ...
            }

        Note:
            Falls back to 0.0 values if indicator fetch fails for a symbol.
            This ensures email generation doesn't break on data issues.

        """
        indicators: dict[str, dict[str, float]] = {}

        # Get market data service from container
        market_data_port = self.container.infrastructure.market_data_service()
        indicator_service = IndicatorService(market_data_port)

        for symbol in symbols:
            try:
                # Create indicator requests
                correlation_id = str(uuid.uuid4())
                request_id_base = str(uuid.uuid4())

                rsi_10_request = IndicatorRequest(
                    request_id=f"{request_id_base}-rsi10",
                    indicator_type="rsi",
                    symbol=symbol,
                    parameters={"window": 10},
                    correlation_id=correlation_id,
                )

                rsi_20_request = IndicatorRequest(
                    request_id=f"{request_id_base}-rsi20",
                    indicator_type="rsi",
                    symbol=symbol,
                    parameters={"window": 20},
                    correlation_id=correlation_id,
                )

                price_request = IndicatorRequest(
                    request_id=f"{request_id_base}-price",
                    indicator_type="current_price",
                    symbol=symbol,
                    parameters={},
                    correlation_id=correlation_id,
                )

                ma_200_request = IndicatorRequest(
                    request_id=f"{request_id_base}-ma200",
                    indicator_type="moving_average",
                    symbol=symbol,
                    parameters={"window": 200},
                    correlation_id=correlation_id,
                )

                # Fetch indicators
                rsi_10_ind = indicator_service.get_indicator(rsi_10_request)
                rsi_20_ind = indicator_service.get_indicator(rsi_20_request)
                price_ind = indicator_service.get_indicator(price_request)
                ma_200_ind = indicator_service.get_indicator(ma_200_request)

                # Build indicators dict
                indicators[symbol] = {
                    "rsi_10": float(rsi_10_ind.rsi_10 or 0.0),
                    "rsi_20": float(rsi_20_ind.rsi_20 or 0.0),
                    "current_price": float(price_ind.current_price or 0.0),
                    "ma_200": float(ma_200_ind.ma_200 or 0.0),
                }

                self.logger.debug(
                    f"Fetched technical indicators for {symbol}",
                    extra={
                        "symbol": symbol,
                        "rsi_10": indicators[symbol]["rsi_10"],
                        "rsi_20": indicators[symbol]["rsi_20"],
                        "current_price": indicators[symbol]["current_price"],
                        "ma_200": indicators[symbol]["ma_200"],
                    },
                )

            except Exception as e:
                self.logger.warning(
                    f"Failed to fetch technical indicators for {symbol}: {e}",
                    extra={"symbol": symbol, "error": str(e)},
                )
                # Fallback to zero values so email generation doesn't break
                indicators[symbol] = {
                    "rsi_10": 0.0,
                    "rsi_20": 0.0,
                    "current_price": 0.0,
                    "ma_200": 0.0,
                }

        return indicators

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
                # Sum allocations if the same symbol appears in multiple strategies
                if symbol in consolidated_portfolio:
                    consolidated_portfolio[symbol] += allocation
                else:
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
            required_fields = ["symbols", "action"]
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
        """Format individual signal detail for logging.

        Handles both single and multi-symbol signals uniformly since symbols is always a list.
        """
        name = str(raw_name)
        action = str(data.get("action", "")).upper() or "UNKNOWN"

        symbols_list = data.get("symbols", [])
        if symbols_list:
            symbols_str = ", ".join(str(symbol) for symbol in symbols_list)
            return f"{name}: {action} {symbols_str}"
        return f"{name}: {action}"

    def _log_portfolio_allocations(self, consolidated_portfolio: ConsolidatedPortfolio) -> None:
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

    def _safe_convert_to_percentage(self, allocation: float | int | str | Decimal) -> float:
        """Safely convert allocation to percentage."""
        try:
            return float(allocation) * 100
        except (TypeError, ValueError):
            return 0.0
