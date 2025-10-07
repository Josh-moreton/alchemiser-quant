#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL event publishing utilities for strategy evaluation.

Provides a wrapper around EventBus for publishing DSL-related events with
proper correlation/causation ID handling and metadata enforcement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from the_alchemiser.shared.constants import DSL_ENGINE_MODULE
from the_alchemiser.shared.errors.exceptions import AlchemiserError
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    DecisionEvaluated,
    IndicatorComputed,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator

logger = get_logger(__name__)


class EventPublishError(AlchemiserError):
    """Raised when event publishing fails."""

    def __init__(
        self,
        message: str,
        event_type: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize event publish error with context."""
        context = {}
        if event_type:
            context["event_type"] = event_type
        if correlation_id:
            context["correlation_id"] = correlation_id
        super().__init__(message, context)
        self.event_type = event_type
        self.correlation_id = correlation_id


class DslEventPublisher:
    """Publisher for DSL evaluation events.

    Wraps EventBus to provide DSL-specific event publishing with automatic
    correlation/causation ID handling and consistent metadata.

    Args:
        event_bus: Optional event bus for publishing events. If None,
            publishing will be a no-op (silently skipped with debug logging).

    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize DSL event publisher.

        Args:
            event_bus: Optional event bus for publishing events. When None,
                events are not published (no-op mode for testing/disabled scenarios).

        """
        self.event_bus = event_bus

    def publish_indicator_computed(
        self,
        request_id: str,
        indicator: TechnicalIndicator,
        computation_time_ms: float,
        correlation_id: str,
        causation_id: str | None = None,
        *,
        event_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Publish an indicator computed event.

        Args:
            request_id: Original request identifier
            indicator: Computed indicator data
            computation_time_ms: Computation time in milliseconds (must be non-negative)
            correlation_id: Correlation ID for tracking
            causation_id: Optional causation ID (triggering event ID)
            event_id: Optional event ID (for testing; auto-generated if not provided)
            timestamp: Optional timestamp (for testing; current time if not provided)

        Raises:
            ValueError: If computation_time_ms is negative or request_id is empty
            EventPublishError: If event publishing fails

        """
        if not self.event_bus:
            logger.debug(
                "Event publishing skipped (no event bus configured)",
                extra={"correlation_id": correlation_id, "event_type": "IndicatorComputed"},
            )
            return

        # Input validation
        if computation_time_ms < 0:
            msg = f"computation_time_ms must be non-negative, got: {computation_time_ms}"
            raise ValueError(msg)

        if not request_id or not request_id.strip():
            msg = "request_id must not be empty"
            raise ValueError(msg)

        try:
            event = IndicatorComputed(
                correlation_id=correlation_id,
                causation_id=causation_id or correlation_id,
                event_id=event_id or str(uuid.uuid4()),
                timestamp=timestamp or datetime.now(UTC),
                source_module=DSL_ENGINE_MODULE,
                request_id=request_id,
                indicator=indicator,
                computation_time_ms=computation_time_ms,
            )

            logger.debug(
                "Publishing IndicatorComputed event",
                extra={
                    "correlation_id": correlation_id,
                    "causation_id": event.causation_id,
                    "event_id": event.event_id,
                    "request_id": request_id,
                    "symbol": indicator.symbol,
                    "computation_time_ms": computation_time_ms,
                },
            )

            self.event_bus.publish(event)

        except Exception as e:
            logger.error(
                "Failed to publish IndicatorComputed event",
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise EventPublishError(
                f"Failed to publish IndicatorComputed event: {e}",
                event_type="IndicatorComputed",
                correlation_id=correlation_id,
            ) from e

    def publish_decision_evaluated(
        self,
        decision_expression: ASTNode,
        *,
        condition_result: bool,
        branch_taken: Literal["then", "else"],
        branch_result: PortfolioFragment | None,
        correlation_id: str,
        causation_id: str | None = None,
        event_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Publish a decision evaluated event.

        Args:
            decision_expression: The decision expression that was evaluated
            condition_result: Result of the condition evaluation
            branch_taken: Which branch was taken ("then" or "else")
            branch_result: Result from the taken branch, if any
            correlation_id: Correlation ID for tracking
            causation_id: Optional causation ID (triggering event ID)
            event_id: Optional event ID (for testing; auto-generated if not provided)
            timestamp: Optional timestamp (for testing; current time if not provided)

        Raises:
            ValueError: If branch_taken is not "then" or "else"
            EventPublishError: If event publishing fails

        """
        if not self.event_bus:
            logger.debug(
                "Event publishing skipped (no event bus configured)",
                extra={"correlation_id": correlation_id, "event_type": "DecisionEvaluated"},
            )
            return

        # Note: branch_taken validation is enforced by Literal type hint at runtime
        # via Pydantic when the event is created

        try:
            event = DecisionEvaluated(
                correlation_id=correlation_id,
                causation_id=causation_id or correlation_id,
                event_id=event_id or str(uuid.uuid4()),
                timestamp=timestamp or datetime.now(UTC),
                source_module=DSL_ENGINE_MODULE,
                decision_expression=decision_expression,
                condition_result=condition_result,
                branch_taken=branch_taken,
                branch_result=branch_result,
            )

            logger.debug(
                "Publishing DecisionEvaluated event",
                extra={
                    "correlation_id": correlation_id,
                    "causation_id": event.causation_id,
                    "event_id": event.event_id,
                    "condition_result": condition_result,
                    "branch_taken": branch_taken,
                    "has_branch_result": branch_result is not None,
                },
            )

            self.event_bus.publish(event)

        except Exception as e:
            logger.error(
                "Failed to publish DecisionEvaluated event",
                extra={
                    "correlation_id": correlation_id,
                    "branch_taken": branch_taken,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise EventPublishError(
                f"Failed to publish DecisionEvaluated event: {e}",
                event_type="DecisionEvaluated",
                correlation_id=correlation_id,
            ) from e
