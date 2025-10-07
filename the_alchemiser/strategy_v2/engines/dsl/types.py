#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL value types and type aliases for DSL evaluation.

Defines the core types used throughout the DSL evaluation system,
including the DSLValue union type and related type helpers.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.shared.errors.exceptions import StrategyExecutionError
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment

# Values that may result from evaluating a DSL node
# Note: float is included for intermediate calculations but should be converted
# to Decimal for financial operations. None represents absence of value in conditional flows.
type DSLValue = (
    PortfolioFragment
    | dict[str, float | int | Decimal | str]
    | list["DSLValue"]
    | str
    | int
    | float
    | bool
    | Decimal
    | None
)


class DslEvaluationError(StrategyExecutionError):
    """Raised when DSL evaluation fails.

    This exception is raised when the DSL evaluator encounters errors during
    expression evaluation, including invalid syntax, type mismatches, operator
    failures, or runtime evaluation errors.

    Inherits from StrategyExecutionError to integrate with the broader
    Alchemiser error hierarchy and enable consistent error handling and logging.

    Args:
        message: Human-readable error description
        expression: Optional DSL expression that caused the error
        node_type: Optional AST node type that failed
        correlation_id: Optional correlation ID for tracking across system

    Example:
        >>> raise DslEvaluationError(
        ...     "Invalid operator 'unknown-op'",
        ...     expression="(unknown-op AAPL)",
        ...     correlation_id="abc-123"
        ... )

    """

    def __init__(
        self,
        message: str,
        expression: str | None = None,
        node_type: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize DSL evaluation error with contextual information."""
        context: dict[str, Any] = {}
        if expression:
            context["expression"] = expression
        if node_type:
            context["node_type"] = node_type
        if correlation_id:
            context["correlation_id"] = correlation_id

        # Call parent with strategy_name set to "dsl_engine"
        super().__init__(
            message=message,
            strategy_name="dsl_engine",
            operation="evaluate",
        )
        self.expression = expression
        self.node_type = node_type
        self.correlation_id = correlation_id
        # Merge additional context
        self.context.update(context)
