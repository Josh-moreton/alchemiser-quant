#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Engine for evaluating Clojure strategy files.

Implements DSL engine for Strategy_v2 that interprets Clojure/S-expr strategy files
and produces portfolio allocations using event-driven architecture with DTO integration.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from the_alchemiser.shared.constants import DSL_ENGINE_MODULE
from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    PortfolioAllocationProduced,
    StrategyEvaluated,
    StrategyEvaluationRequested,
)
from the_alchemiser.shared.events.handlers import EventHandler
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.market_data_port import MarketDataPort

from .dsl_evaluator import DslEvaluator, IndicatorService
from .sexpr_parser import SexprParseError, SexprParser

if TYPE_CHECKING:
    pass


class DslEngine(EventHandler):
    """DSL Engine for evaluating Clojure strategy files.

    Subscribes to StrategyEvaluationRequested events and produces
    PortfolioAllocationProduced events with complete trace logging.
    """

    def __init__(
        self,
        strategy_config_path: str | None = None,
        event_bus: EventBus | None = None,
        market_data_service: MarketDataPort | None = None,
    ) -> None:
        """Initialize DSL engine.

        Args:
            strategy_config_path: Optional path to strategy config directory
            event_bus: Optional event bus for pub/sub
            market_data_service: Optional market data service for real indicators

        """
        self.logger = get_logger(__name__)
        self.event_bus = event_bus
        self.strategy_config_path = strategy_config_path or "."

        # Initialize components
        self.parser = SexprParser()

        # Use real market data service if provided, otherwise fallback
        if market_data_service:
            self.indicator_service = IndicatorService(market_data_service)
        else:
            # Fallback to mock service for backward compatibility
            self.indicator_service = IndicatorService(None)  # Will use fallback indicators

        self.evaluator = DslEvaluator(self.indicator_service, event_bus)

        # Subscribe to events if event bus provided
        if self.event_bus:
            self.event_bus.subscribe("StrategyEvaluationRequested", self)

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type.

        Args:
            event_type: Type of event

        Returns:
            True if can handle, False otherwise

        """
        return event_type == "StrategyEvaluationRequested"

    def handle_event(self, event: BaseEvent) -> None:
        """Handle incoming events.

        Args:
            event: Event to handle

        """
        if isinstance(event, StrategyEvaluationRequested):
            self._handle_evaluation_request(event)
        else:
            self.logger.warning(f"Received unhandled event type: {type(event)}")

    def evaluate_strategy(
        self, strategy_config_path: str, correlation_id: str | None = None
    ) -> tuple[StrategyAllocationDTO, TraceDTO]:
        """Evaluate strategy from configuration file.

        Args:
            strategy_config_path: Path to .clj strategy file
            correlation_id: Optional correlation ID for tracking

        Returns:
            Tuple of (StrategyAllocationDTO, TraceDTO)

        Raises:
            DslEngineError: If evaluation fails

        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        try:
            self.logger.info(
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

            self.logger.info(
                "DSL strategy evaluation completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "allocation_symbols": list(allocation.target_weights.keys()),
                    "component": "dsl_engine",
                },
            )

            return allocation, trace

        except Exception as e:
            self.logger.error(
                f"DSL strategy evaluation failed: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_config_path": strategy_config_path,
                    "component": "dsl_engine",
                    "error_type": type(e).__name__,
                },
            )
            raise DslEngineError(f"Strategy evaluation failed: {e}") from e

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
                f"Failed to handle evaluation request: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_id": event.strategy_id,
                    "component": "dsl_engine",
                },
            )

            # Publish error events
            self._publish_error_events(event, str(e))

    def _parse_strategy_file(self, strategy_config_path: str) -> ASTNodeDTO:
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
                raise DslEngineError(f"Strategy file not found: {strategy_config_path}")

            self.logger.debug(
                f"Parsing strategy file: {full_path}", extra={"component": "dsl_engine"}
            )

            return self.parser.parse_file(str(full_path))

        except SexprParseError as e:
            raise DslEngineError(f"Failed to parse strategy file: {e}") from e
        except Exception as e:
            raise DslEngineError(f"Error reading strategy file: {e}") from e

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
        allocation: StrategyAllocationDTO,
        trace: TraceDTO,
    ) -> None:
        """Publish completion events.

        Args:
            request_event: Original request event
            allocation: Strategy allocation result
            trace: Evaluation trace

        """
        if not self.event_bus:
            return

        correlation_id = request_event.correlation_id

        # Publish StrategyEvaluated event
        strategy_evaluated = StrategyEvaluated(
            correlation_id=correlation_id,
            causation_id=request_event.event_id,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
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
            timestamp=datetime.now(UTC),
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

        correlation_id = request_event.correlation_id

        # Create failed trace
        failed_trace = TraceDTO(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id=request_event.strategy_id,
            started_at=datetime.now(UTC),
        ).mark_completed(success=False, error_message=error_message)

        # Create dummy allocation for failed case
        failed_allocation = StrategyAllocationDTO(
            target_weights={}, correlation_id=correlation_id, as_of=datetime.now(UTC)
        )

        # Publish StrategyEvaluated event with error
        strategy_evaluated = StrategyEvaluated(
            correlation_id=correlation_id,
            causation_id=request_event.event_id,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            source_module=DSL_ENGINE_MODULE,
            strategy_id=request_event.strategy_id,
            allocation=failed_allocation,
            trace=failed_trace,
            success=False,
            error_message=error_message,
        )
        self.event_bus.publish(strategy_evaluated)


class DslEngineError(Exception):
    """Error in DSL engine operation."""
