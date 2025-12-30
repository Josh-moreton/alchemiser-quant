#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Engine for evaluating Clojure strategy files.

Implements DSL engine for Strategy_v2 that interprets Clojure/S-expr strategy files
and produces portfolio allocations using event-driven architecture with DTO integration.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from the_alchemiser.shared.constants import DSL_ENGINE_MODULE
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    PortfolioAllocationProduced,
    StrategyEvaluated,
    StrategyEvaluationRequested,
)
from the_alchemiser.shared.events.handlers import EventHandler
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.shared.types.indicator_port import IndicatorPort
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from errors import StrategyV2Error

from engines.dsl.dsl_evaluator import DslEvaluator
from engines.dsl.sexpr_parser import SexprParseError, SexprParser


class DslEngine(EventHandler):
    """DSL Engine for evaluating Clojure strategy files.

    Subscribes to StrategyEvaluationRequested events and produces
    PortfolioAllocationProduced events with complete trace logging.
    """

    def __init__(
        self,
        strategy_config_path: str | None = None,
        event_bus: EventBus | None = None,
        indicator_service: IndicatorPort | None = None,
        market_data_adapter: MarketDataPort | None = None,
    ) -> None:
        """Initialize DSL engine.

        Args:
            strategy_config_path: Optional path to strategy config directory
            event_bus: Optional event bus for pub/sub
            indicator_service: Optional pre-configured indicator service (for testing)
            market_data_adapter: Optional injected market data adapter (from DI container)

        """
        from indicators.indicator_service import IndicatorService

        self.logger = get_logger(__name__)
        self.event_bus = event_bus
        self.strategy_config_path = strategy_config_path or "."

        # Track processed events for idempotency
        self._processed_events: set[str] = set()

        # Initialize components
        self.parser = SexprParser()

        # Use provided indicator service or create one with injected/default adapter
        if indicator_service:
            self.indicator_service = indicator_service
        else:
            # Use injected adapter from DI container, or create default for testing
            if market_data_adapter is None:
                from the_alchemiser.data_v2.cached_market_data_adapter import (
                    CachedMarketDataAdapter,
                )

                market_data_adapter = CachedMarketDataAdapter()
            # IndicatorService computes indicators locally using pandas/numpy
            self.indicator_service = IndicatorService(market_data_service=market_data_adapter)

        self.evaluator = DslEvaluator(self.indicator_service, event_bus)

        # Subscribe to events if event bus provided
        if self.event_bus:
            self.event_bus.subscribe("StrategyEvaluationRequested", self)
            self.logger.debug(
                "DSL engine subscribed to events",
                extra={"event_type": "StrategyEvaluationRequested", "component": "dsl_engine"},
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type.

        Args:
            event_type: Type of event

        Returns:
            True if can handle, False otherwise

        """
        return event_type == "StrategyEvaluationRequested"

    def handle_event(self, event: BaseEvent) -> None:
        """Handle incoming events with idempotency check.

        Args:
            event: Event to handle

        """
        # Check for duplicate event (idempotency)
        if event.event_id in self._processed_events:
            self.logger.debug(
                "Skipping duplicate event",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "event_type": type(event).__name__,
                    "component": "dsl_engine",
                },
            )
            return

        # Mark event as processed
        self._processed_events.add(event.event_id)

        if isinstance(event, StrategyEvaluationRequested):
            self._handle_evaluation_request(event)
        else:
            self.logger.warning(
                "Received unhandled event type",
                extra={
                    "event_type": type(event).__name__,
                    "event_id": event.event_id,
                    "component": "dsl_engine",
                },
            )

    def evaluate_strategy(
        self, strategy_config_path: str, correlation_id: str | None = None
    ) -> tuple[StrategyAllocation, Trace]:
        """Evaluate strategy from configuration file.

        Args:
            strategy_config_path: Path to .clj strategy file
            correlation_id: Optional correlation ID for tracking

        Returns:
            Tuple of (StrategyAllocation, Trace)

        Raises:
            DslEngineError: If evaluation fails

        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        try:
            self.logger.debug(
                "Starting DSL strategy evaluation",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_config_path": strategy_config_path,
                    "component": "dsl_engine",
                },
            )

            # Parse strategy file
            ast = self._parse_strategy_file(strategy_config_path)

            # Evaluate AST
            allocation, trace = self.evaluator.evaluate(ast, correlation_id)

            # Add decision path to trace metadata for signal reasoning
            if self.evaluator.decision_path:
                trace = trace.model_copy(
                    update={
                        "metadata": {
                            **trace.metadata,
                            "decision_path": self.evaluator.decision_path,
                        }
                    }
                )

            self.logger.debug(
                "DSL strategy evaluation completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "allocation_symbols": list(allocation.target_weights.keys()),
                    "decision_nodes": len(self.evaluator.decision_path),
                    "component": "dsl_engine",
                },
            )

            return allocation, trace

        except Exception as e:
            self.logger.error(
                "DSL strategy evaluation failed",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_config_path": strategy_config_path,
                    "component": "dsl_engine",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise DslEngineError(
                f"Strategy evaluation failed: {e}",
                correlation_id=correlation_id,
                strategy_path=strategy_config_path,
            ) from e

    def _handle_evaluation_request(self, event: StrategyEvaluationRequested) -> None:
        """Handle strategy evaluation request event.

        Args:
            event: Strategy evaluation request event

        """
        correlation_id = event.correlation_id

        try:
            # Get strategy config path
            strategy_config_path = self._resolve_strategy_path(
                event.strategy_config_path, event.strategy_id
            )

            # Evaluate strategy
            allocation, trace = self.evaluate_strategy(strategy_config_path, correlation_id)

            # Publish completion events
            self._publish_completion_events(event, allocation, trace)

        except Exception as e:
            self.logger.error(
                "Failed to handle evaluation request",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_id": event.strategy_id,
                    "component": "dsl_engine",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )

            # Publish error events
            self._publish_error_events(event, str(e))

    def _parse_strategy_file(self, strategy_config_path: str) -> ASTNode:
        """Parse strategy configuration file.

        Args:
            strategy_config_path: Path to strategy file

        Returns:
            Parsed AST

        Raises:
            DslEngineError: If parsing fails

        """
        try:
            # Resolve full path
            full_path = Path(self.strategy_config_path) / strategy_config_path
            if not full_path.exists():
                # Try as absolute path
                full_path = Path(strategy_config_path)

            if not full_path.exists():
                raise DslEngineError(
                    f"Strategy file not found: {strategy_config_path}",
                    correlation_id=None,
                    strategy_path=strategy_config_path,
                )

            self.logger.debug(
                "Parsing strategy file",
                extra={"component": "dsl_engine", "strategy_file": str(full_path)},
            )

            return self.parser.parse_file(str(full_path))

        except SexprParseError as e:
            raise DslEngineError(
                f"Failed to parse strategy file: {e}",
                correlation_id=None,
                strategy_path=strategy_config_path,
            ) from e
        except Exception as e:
            raise DslEngineError(
                f"Error reading strategy file: {e}",
                correlation_id=None,
                strategy_path=strategy_config_path,
            ) from e

    def _resolve_strategy_path(self, config_path: str, strategy_id: str) -> str:
        """Resolve strategy configuration path.

        Args:
            config_path: Provided config path
            strategy_id: Strategy identifier

        Returns:
            Resolved path to strategy file

        """
        # If config_path is provided, use it directly
        if config_path and config_path.strip():
            return config_path

        # Otherwise, try to resolve based on strategy_id
        possible_paths = [
            f"{strategy_id}.clj",
            f"{strategy_id} original.clj",
            f"strategies/{strategy_id}.clj",
            "Nuclear.clj",  # Default fallback
        ]

        for path in possible_paths:
            full_path = Path(self.strategy_config_path) / path
            if full_path.exists():
                return str(full_path)

        # Last resort - return the first option and let parsing handle the error
        return possible_paths[0]

    def _publish_completion_events(
        self,
        request_event: StrategyEvaluationRequested,
        allocation: StrategyAllocation,
        trace: Trace,
    ) -> None:
        """Publish completion events.

        Args:
            request_event: Original request event
            allocation: Strategy allocation result
            trace: Evaluation trace

        """
        if not self.event_bus:
            return

        # Capture timestamp once for consistency
        timestamp = datetime.now(UTC)
        correlation_id = request_event.correlation_id

        # Publish StrategyEvaluated event
        strategy_evaluated = StrategyEvaluated(
            correlation_id=correlation_id,
            causation_id=request_event.event_id,
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            source_module=DSL_ENGINE_MODULE,
            strategy_id=request_event.strategy_id,
            allocation=allocation,
            trace=trace,
            success=trace.success,
            error_message=trace.error_message,
        )
        self.event_bus.publish(strategy_evaluated)

        # Publish PortfolioAllocationProduced event
        allocation_produced = PortfolioAllocationProduced(
            correlation_id=correlation_id,
            causation_id=request_event.event_id,
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            source_module=DSL_ENGINE_MODULE,
            strategy_id=request_event.strategy_id,
            allocation=allocation,
            allocation_type="final",
        )
        self.event_bus.publish(allocation_produced)

    def _publish_error_events(
        self, request_event: StrategyEvaluationRequested, error_message: str
    ) -> None:
        """Publish error events.

        Args:
            request_event: Original request event
            error_message: Error message

        """
        if not self.event_bus:
            return

        # Capture timestamp once for consistency
        timestamp = datetime.now(UTC)
        correlation_id = request_event.correlation_id

        # Create failed trace
        failed_trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id=request_event.strategy_id,
            started_at=timestamp,
        ).mark_completed(success=False, error_message=error_message)

        # Create dummy allocation for failed case (with dummy symbol to satisfy validation)
        failed_allocation = StrategyAllocation(
            target_weights={"CASH": Decimal("1.0")},
            correlation_id=correlation_id,
            as_of=timestamp,
        )

        # Publish StrategyEvaluated event with error
        strategy_evaluated = StrategyEvaluated(
            correlation_id=correlation_id,
            causation_id=request_event.event_id,
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            source_module=DSL_ENGINE_MODULE,
            strategy_id=request_event.strategy_id,
            allocation=failed_allocation,
            trace=failed_trace,
            success=False,
            error_message=error_message,
        )
        self.event_bus.publish(strategy_evaluated)


class DslEngineError(StrategyV2Error):
    """Error in DSL engine operation.

    Typed exception for DSL engine failures with correlation tracking
    and structured context for observability.
    """

    def __init__(
        self,
        message: str,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        **context: str | float | int | bool | None,
    ) -> None:
        """Initialize DSL engine error with context.

        Args:
            message: Error message describing the failure
            correlation_id: Optional correlation ID for tracking
            causation_id: Optional causation ID for event workflows
            **context: Additional error context (strategy_path, etc.)

        """
        super().__init__(
            message,
            module="strategy_v2.engines.dsl",
            correlation_id=correlation_id,
            causation_id=causation_id,
            **context,
        )
