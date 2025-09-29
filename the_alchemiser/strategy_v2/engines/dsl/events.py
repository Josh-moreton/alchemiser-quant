#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL event publishing utilities for strategy evaluation.

Provides a wrapper around EventBus for publishing DSL-related events with
proper correlation/causation ID handling and metadata enforcement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from the_alchemiser.shared.constants import DSL_ENGINE_MODULE
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    DecisionEvaluated,
    IndicatorComputed,
)
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator


class DslEventPublisher:
    """Publisher for DSL evaluation events.

    Wraps EventBus to provide DSL-specific event publishing with automatic
    correlation/causation ID handling and consistent metadata.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize DSL event publisher.

        Args:
            event_bus: Optional event bus for publishing events

        """
        self.event_bus = event_bus

    def publish_indicator_computed(
        self,
        request_id: str,
        indicator: TechnicalIndicator,
        computation_time_ms: float,
        correlation_id: str,
        causation_id: str | None = None,
    ) -> None:
        """Publish an indicator computed event.

        Args:
            request_id: Original request identifier
            indicator: Computed indicator data
            computation_time_ms: Computation time in milliseconds
            correlation_id: Correlation ID for tracking
            causation_id: Optional causation ID (triggering event ID)

        """
        if not self.event_bus:
            return

        event = IndicatorComputed(
            correlation_id=correlation_id,
            causation_id=causation_id or correlation_id,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            source_module=DSL_ENGINE_MODULE,
            request_id=request_id,
            indicator=indicator,
            computation_time_ms=computation_time_ms,
        )
        self.event_bus.publish(event)

    def publish_decision_evaluated(
        self,
        decision_expression: ASTNode,
        *,
        condition_result: bool,
        branch_taken: str,
        branch_result: PortfolioFragment | None,
        correlation_id: str,
        causation_id: str | None = None,
    ) -> None:
        """Publish a decision evaluated event.

        Args:
            decision_expression: The decision expression that was evaluated
            condition_result: Result of the condition evaluation
            branch_taken: Which branch was taken ("then" or "else")
            branch_result: Result from the taken branch, if any
            correlation_id: Correlation ID for tracking
            causation_id: Optional causation ID (triggering event ID)

        """
        if not self.event_bus:
            return

        event = DecisionEvaluated(
            correlation_id=correlation_id,
            causation_id=causation_id or correlation_id,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            source_module=DSL_ENGINE_MODULE,
            decision_expression=decision_expression,
            condition_result=condition_result,
            branch_taken=branch_taken,
            branch_result=branch_result,
        )
        self.event_bus.publish(event)
