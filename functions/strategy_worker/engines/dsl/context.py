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
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from engines.dsl.types import DSLValue

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.shared.types.indicator_port import IndicatorPort
from the_alchemiser.shared.types.market_data_port import MarketDataPort

if TYPE_CHECKING:
    from engines.dsl.events import DslEventPublisher

logger = get_logger(__name__)


class DecisionNodeBase(TypedDict):
    """Base decision node with required fields.

    Attributes:
        condition: Human-readable condition expression (e.g., "SPY RSI(10) > 79")
        result: Boolean result of the condition evaluation
        branch: Branch taken ("then" or "else")
        values: Dictionary mapping indicator references to their values.
            Values may be placeholder strings like "<computed>" when actual
            values are not available without re-evaluation.

    """

    condition: str
    result: bool
    branch: str
    values: dict[str, Any]


class DecisionNode(DecisionNodeBase, total=False):
    """Decision node with optional metadata fields for natural language generation.

    Extends DecisionNodeBase with optional fields that enable rich natural language
    narrative generation. All base fields remain required; only metadata is optional.

    Attributes:
        condition_type: Type of condition (e.g., "rsi_check", "ma_comparison", "price_check")
        symbols_involved: List of symbols referenced in condition (e.g., ["SPY", "TQQQ"])
        operator_type: Type of comparison operator (e.g., "greater_than", "less_than", "and", "or")
        threshold: Numeric threshold value for comparisons (e.g., 79.0 for "RSI > 79")
        indicator_name: Name of indicator function (e.g., "rsi", "moving_average", "current_price")
        indicator_params: Parameters passed to indicator function (e.g., {"window": 10})
        market_context: Overall market sentiment (e.g., "bullish", "bearish", "neutral", "volatile")
        strategic_intent: Strategic positioning (e.g., "risk_on", "risk_off", "defensive")

    """

    # Optional metadata fields for natural language generation
    condition_type: str
    symbols_involved: list[str]
    operator_type: str
    threshold: float | None
    indicator_name: str | None
    indicator_params: dict[str, Any] | None
    market_context: str | None
    strategic_intent: str | None


class DebugTrace(TypedDict, total=False):
    """Debug trace entry for condition evaluations.

    Captures detailed information about DSL condition evaluations for debugging.

    Attributes:
        operator: The comparison/logical operator (e.g., ">", "<", "and", "or")
        left_expr: String representation of left expression
        left_value: Evaluated left value
        right_expr: String representation of right expression
        right_value: Evaluated right value
        result: Boolean result of evaluation
        timestamp: ISO timestamp of evaluation
        indicator_calls: List of indicator calls made during evaluation

    """

    operator: str
    left_expr: str
    left_value: Any
    right_expr: str
    right_value: Any
    result: bool
    timestamp: str
    indicator_calls: list[dict[str, Any]]


class FilterCandidate(TypedDict, total=False):
    """Candidate item scored during a DSL filter.

    Notes:
        This is debug/trace data, not domain state.

    """

    candidate_id: str
    candidate_type: Literal["symbol", "portfolio"]
    candidate_name: str | None
    score: float
    rank: int
    symbol_count: int
    symbols_sample: list[str]


class FilterTrace(TypedDict, total=False):
    """Trace entry for a DSL filter evaluation.

    Captures ranking inputs/outputs so we can diagnose Composer parity issues.
    """

    mode: Literal["symbol", "portfolio"]
    order: Literal["top", "bottom"]
    limit: int | None
    condition: dict[str, Any]
    scored_candidates: list[FilterCandidate]
    selected_candidate_ids: list[str]
    timestamp: str


class DslContext:
    """Context object for DSL operator evaluation.

    Carries shared state and utilities for DSL operators, including
    indicator service, event publisher, correlation tracking, decision
    path capture, and type coercion utilities.
    """

    def __init__(
        self,
        indicator_service: IndicatorPort,
        event_publisher: DslEventPublisher,
        correlation_id: str,
        trace: Trace,
        evaluate_node: Callable[[ASTNode, str, Trace], DSLValue],
        *,
        debug_mode: bool = False,
        market_data_service: MarketDataPort | None = None,
    ) -> None:
        """Initialize DSL context.

        Args:
            indicator_service: Service for computing indicators (IndicatorPort)
            event_publisher: Publisher for DSL events
            correlation_id: Correlation ID for request tracking
            trace: Trace object for logging evaluation steps
            evaluate_node: Function to evaluate AST nodes
            debug_mode: If True, enables detailed condition tracing for debugging
            market_data_service: Optional market data port for on-demand backfill

        """
        self.indicator_service = indicator_service
        self.event_publisher = event_publisher
        self.correlation_id = correlation_id
        self.trace = trace
        self.evaluate_node = evaluate_node
        self.timestamp = datetime.now(UTC)
        self.debug_mode = debug_mode
        self.market_data_service = market_data_service
        # Decision path stored as list of dicts for serialization compatibility.
        # Note: This is initialized here but immediately replaced with evaluator's
        # shared list (see dsl_evaluator.py line 289) to ensure all contexts
        # accumulate decisions to the same list.
        self.decision_path: list[dict[str, Any]] = []
        # Debug traces for detailed condition logging (when debug_mode=True)
        self.debug_traces: list[DebugTrace] = []
        # Filter traces for ranking/selection debugging (when debug_mode=True)
        self.filter_traces: list[FilterTrace] = []

    def add_debug_trace(
        self,
        operator: str,
        left_expr: str,
        left_value: DSLValue,
        right_expr: str,
        right_value: DSLValue,
        *,
        result: bool,
        indicator_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add a debug trace entry for condition evaluation.

        Only adds traces when debug_mode is enabled.

        Args:
            operator: The comparison/logical operator
            left_expr: String representation of left expression
            left_value: Evaluated left value
            right_expr: String representation of right expression
            right_value: Evaluated right value
            result: Boolean result of evaluation
            indicator_calls: Optional list of indicator calls made

        """
        if not self.debug_mode:
            return

        trace_entry: DebugTrace = {
            "operator": operator,
            "left_expr": left_expr,
            "left_value": left_value,
            "right_expr": right_expr,
            "right_value": right_value,
            "result": result,
            "timestamp": datetime.now(UTC).isoformat(),
            "indicator_calls": indicator_calls or [],
        }
        self.debug_traces.append(trace_entry)

        # Also log immediately for visibility
        logger.info(
            f"DEBUG TRACE: {left_expr} = {left_value} {operator} {right_expr} = {right_value} -> {result}",
            extra={
                "correlation_id": self.correlation_id,
                "component": "dsl_debug",
                "operator": operator,
                "left_value": str(left_value),
                "right_value": str(right_value),
                "result": result,
            },
        )

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

    def add_filter_trace(self, trace_entry: FilterTrace) -> None:
        """Add a filter trace entry.

        Only records traces when debug_mode is enabled.

        Args:
            trace_entry: Structured filter trace data

        """
        if not self.debug_mode:
            return

        # Ensure we always stamp a timestamp for ordering.
        if "timestamp" not in trace_entry:
            trace_entry["timestamp"] = datetime.now(UTC).isoformat()

        self.filter_traces.append(trace_entry)

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
        if isinstance(val, float | int | Decimal | str):
            return val
        if val is None:
            return 0
        if isinstance(val, list) and len(val) == 1:
            return self.coerce_param_value(val[0])
        return str(val)
