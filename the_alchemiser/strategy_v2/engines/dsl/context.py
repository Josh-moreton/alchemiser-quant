#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL evaluation context for operator calls.

Provides a typed context object that carries shared state and utilities
for DSL operator implementations, keeping operators stateless and testable.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, DecimalException
from typing import TYPE_CHECKING, Any, TypedDict

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.trace import Trace

from .types import DSLValue

if TYPE_CHECKING:
    from the_alchemiser.strategy_v2.indicators.indicator_service import IndicatorService

    from .events import DslEventPublisher

logger = get_logger(__name__)


class DecisionNode(TypedDict, total=False):
    """Represents a single decision point in strategy evaluation.

    Attributes:
        condition: Human-readable condition expression (e.g., "SPY RSI(10) > 79")
        result: Boolean result of the condition evaluation
        branch: Branch taken ("then" or "else")
        values: Dictionary mapping indicator references to their values.
            Values may be placeholder strings like "<computed>" when actual
            values are not available without re-evaluation.
        condition_type: Type of condition (e.g., "rsi_check", "ma_comparison", "price_check")
        symbols_involved: List of symbols referenced in condition (e.g., ["SPY", "TQQQ"])
        operator_type: Type of comparison operator (e.g., "greater_than", "less_than", "and", "or")
        threshold: Numeric threshold value for comparisons (e.g., 79.0 for "RSI > 79")
        indicator_name: Name of indicator function (e.g., "rsi", "moving_average", "current_price")
        indicator_params: Parameters passed to indicator function (e.g., {"window": 10})
        market_context: Overall market sentiment (e.g., "bullish", "bearish", "neutral", "volatile")
        strategic_intent: Strategic positioning (e.g., "risk_on", "risk_off", "defensive")

    """

    # Required fields
    condition: str
    result: bool
    branch: str
    values: dict[str, Any]
    # Optional fields for natural language generation
    condition_type: str
    symbols_involved: list[str]
    operator_type: str
    threshold: float | None
    indicator_name: str | None
    indicator_params: dict[str, Any] | None
    market_context: str | None
    strategic_intent: str | None


class DslContext:
    """Context object for DSL operator evaluation.

    Carries shared state and utilities for DSL operators, including
    indicator service, event publisher, correlation tracking, decision
    path capture, and type coercion utilities.
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
        # Decision path stored as list of dicts for serialization compatibility.
        # Note: This is initialized here but immediately replaced with evaluator's
        # shared list (see dsl_evaluator.py line 289) to ensure all contexts
        # accumulate decisions to the same list.
        self.decision_path: list[dict[str, Any]] = []

    def as_decimal(self, val: DSLValue) -> Decimal:
        """Coerce a DSLValue to Decimal for numeric comparisons.

        Args:
            val: Value to convert to Decimal

        Returns:
            Decimal representation of the value. Returns Decimal("0") for
            non-numeric values, invalid strings, None, or boolean values.

        Raises:
            No exceptions raised - invalid inputs return Decimal("0")

        """
        if isinstance(val, Decimal):
            return val
        # Check bool BEFORE int/float since bool is subclass of int
        if isinstance(val, bool):
            return Decimal("1") if val else Decimal("0")
        if isinstance(val, int):
            return Decimal(val)
        if isinstance(val, float):
            return Decimal(str(val))
        if isinstance(val, str):
            try:
                return Decimal(val)
            except (DecimalException, ValueError) as e:
                # Log warning for invalid string conversions with context
                logger.warning(
                    f"Invalid string to Decimal conversion: '{val}' - returning Decimal('0')",
                    extra={
                        "correlation_id": self.correlation_id,
                        "value": val,
                        "error": str(e),
                        "component": "dsl_context",
                    },
                )
                return Decimal("0")
        return Decimal("0")

    def coerce_param_value(self, val: DSLValue) -> float | int | Decimal | str:
        """Coerce a parameter value to an appropriate primitive type.

        Args:
            val: DSL value to coerce

        Returns:
            Coerced primitive value. Booleans are converted to int (0 or 1),
            None is converted to 0, single-element lists are unwrapped,
            and other complex types are stringified.

        """
        # Check bool FIRST before other types since bool is subclass of int
        if isinstance(val, bool):
            return int(val)
        if isinstance(val, (float, int, Decimal, str)):
            return val
        if val is None:
            return 0
        if isinstance(val, list) and len(val) == 1:
            return self.coerce_param_value(val[0])
        return str(val)
