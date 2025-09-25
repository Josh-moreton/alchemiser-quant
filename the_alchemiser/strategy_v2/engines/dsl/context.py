#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL evaluation context for operator calls.

Provides a typed context object that carries shared state and utilities
for DSL operator implementations, keeping operators stateless and testable.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.schemas.dsl.ast_nodes import ASTNode
from the_alchemiser.shared.schemas.dsl.traces import Trace

from .types import DSLValue

if TYPE_CHECKING:
    from the_alchemiser.strategy_v2.indicators.indicator_service import IndicatorService

    from .events import DslEventPublisher


class DslContext:
    """Context object for DSL operator evaluation.

    Carries shared state and utilities for DSL operators, including
    indicator service, event publisher, correlation tracking, and
    type coercion utilities.
    """

    def __init__(
        self,
        indicator_service: IndicatorService,
        event_publisher: DslEventPublisher,
        correlation_id: str,
        trace: Trace,
        evaluate_node: Callable[[ASTNode, str, Trace], DSLValue],
    ) -> None:
        """Initialize DSL context.

        Args:
            indicator_service: Service for computing indicators
            event_publisher: Publisher for DSL events
            correlation_id: Correlation ID for request tracking
            trace: Trace object for logging evaluation steps
            evaluate_node: Function to evaluate AST nodes

        """
        self.indicator_service = indicator_service
        self.event_publisher = event_publisher
        self.correlation_id = correlation_id
        self.trace = trace
        self.evaluate_node = evaluate_node
        self.timestamp = datetime.now(UTC)

    def as_decimal(self, val: DSLValue) -> Decimal:
        """Coerce a DSLValue to Decimal for numeric comparisons.

        Args:
            val: Value to convert to Decimal

        Returns:
            Decimal representation of the value

        """
        if isinstance(val, Decimal):
            return val
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        if isinstance(val, str):
            try:
                return Decimal(val)
            except Exception:
                return Decimal("0")
        return Decimal("0")

    def coerce_param_value(self, val: DSLValue) -> float | int | Decimal | str:
        """Coerce a parameter value to an appropriate primitive type.

        Args:
            val: DSL value to coerce

        Returns:
            Coerced primitive value

        """
        if isinstance(val, (float, int, Decimal, str)):
            return val
        if isinstance(val, bool):
            return int(val)
        if val is None:
            return 0
        if isinstance(val, list) and len(val) == 1:
            return self.coerce_param_value(val[0])
        return str(val)
