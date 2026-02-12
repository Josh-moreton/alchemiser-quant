#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Comparison operators for DSL evaluation.

Implements DSL comparison and logical operators:
- >: Greater than comparison
- <: Less than comparison
- >=: Greater than or equal comparison
- <=: Less than or equal comparison
- =: Equality comparison
"""

from __future__ import annotations

from decimal import Decimal

from engines.dsl.context import DslContext
from engines.dsl.dispatcher import DslDispatcher
from engines.dsl.types import DslEvaluationError, DSLValue

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode

logger = get_logger(__name__)

# Binary operators require exactly 2 arguments
BINARY_ARG_COUNT = 2

# Proximity thresholds for fragile decision detection.
# When the absolute margin between compared values is below these thresholds,
# the decision is flagged as "fragile" -- a small calculation difference
# (e.g., RSI convergence from different history lengths) could flip the branch.
#
# RSI scale: 0-100, so 2.0 points means values like 39.5 vs threshold 40
# Price comparison: 0.5% relative margin for current-price vs MA comparisons
FRAGILE_ABSOLUTE_MARGIN = 2.0  # For RSI and similar 0-100 scale indicators
FRAGILE_RELATIVE_MARGIN = 0.005  # 0.5% for price-level comparisons


def _validate_binary_args(args: list[ASTNode], operator: str) -> None:
    """Validate that a binary operator receives exactly 2 arguments.

    Args:
        args: List of argument nodes
        operator: Name of the operator for error messages

    Raises:
        DslEvaluationError: If the number of arguments is not exactly 2

    """
    if len(args) != BINARY_ARG_COUNT:
        raise DslEvaluationError(f"{operator} requires exactly 2 arguments")


def _ast_to_expr_string(node: ASTNode) -> str:
    """Convert AST node to a human-readable expression string.

    Args:
        node: AST node to convert

    Returns:
        String representation of the expression

    """
    if node.is_atom():
        return str(node.get_atom_value())
    if node.is_symbol():
        return node.get_symbol_name() or "?"
    if node.is_list() and node.children:
        first = node.children[0]
        if first.is_symbol():
            func_name = first.get_symbol_name() or "?"
            # Special case for indicator calls like (rsi "SPY" {:window 10})
            if (
                func_name in ("rsi", "moving-average", "max-drawdown", "current-price")
                and len(node.children) >= 2
            ):
                symbol = node.children[1]
                if symbol.is_atom():
                    sym_val = symbol.get_atom_value()
                    if len(node.children) >= 3:
                        # Has params
                        params = node.children[2]
                        if params.is_list():
                            return f"{func_name}({sym_val})"
                    return f"{func_name}({sym_val})"
            return f"({func_name} ...)"
    return "<expr>"


def _detect_fragile_decision(
    left_value: Decimal,
    right_value: Decimal,
    operator: str,
    left_expr: str,
    right_expr: str,
    context: DslContext,
) -> None:
    """Detect and log fragile decisions where values are near the threshold.

    A fragile decision is one where a small change in indicator calculation
    (e.g., different RSI history length) could flip the branch. This is the
    primary cause of Composer parity mismatches.

    Uses absolute margin for small-scale indicators (RSI 0-100) and relative
    margin for price-level comparisons (current-price vs MA).

    Args:
        left_value: Left operand value
        right_value: Right operand value
        operator: Comparison operator string
        left_expr: Human-readable left expression
        right_expr: Human-readable right expression
        context: DSL evaluation context

    """
    margin = abs(float(left_value - right_value))

    # Determine if this is a price-level comparison (both sides > 100)
    # or an indicator-scale comparison (RSI, cumulative-return, etc.)
    max_val = max(abs(float(left_value)), abs(float(right_value)))
    is_price_comparison = max_val > 100.0

    if is_price_comparison:
        # Relative margin for price comparisons
        relative_margin = margin / max_val if max_val > 0 else 0.0
        is_fragile = relative_margin < FRAGILE_RELATIVE_MARGIN
    else:
        # Absolute margin for RSI-scale indicators
        is_fragile = margin < FRAGILE_ABSOLUTE_MARGIN

    if is_fragile:
        fragile_entry = {
            "condition": f"{left_expr} {operator} {right_expr}",
            "left_value": float(left_value),
            "right_value": float(right_value),
            "margin": round(margin, 4),
            "is_price_comparison": is_price_comparison,
        }
        context.fragile_decisions.append(fragile_entry)

        logger.warning(
            "Fragile decision detected: values near threshold, parity mismatch risk with Composer",
            condition=f"{left_expr} {operator} {right_expr}",
            left_value=float(left_value),
            right_value=float(right_value),
            margin=round(margin, 4),
            correlation_id=context.correlation_id,
        )


def greater_than(args: list[ASTNode], context: DslContext) -> bool:
    """Evaluate > - greater than comparison.

    Args:
        args: List of exactly 2 ASTNode arguments to compare
        context: DSL evaluation context with correlation tracking

    Returns:
        bool: True if left > right, False otherwise

    Raises:
        DslEvaluationError: If not exactly 2 arguments provided

    """
    _validate_binary_args(args, ">")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)

    left_decimal = context.as_decimal(left_v)
    right_decimal = context.as_decimal(right_v)
    result = left_decimal > right_decimal

    left_expr_str = _ast_to_expr_string(args[0])
    right_expr_str = _ast_to_expr_string(args[1])

    # Detect fragile decisions where values are near the threshold
    _detect_fragile_decision(
        left_decimal, right_decimal, ">", left_expr_str, right_expr_str, context
    )

    # Add debug trace if debug mode is enabled
    context.add_debug_trace(
        operator=">",
        left_expr=left_expr_str,
        left_value=float(left_decimal),
        right_expr=right_expr_str,
        right_value=float(right_decimal),
        result=result,
    )

    logger.debug(
        "DSL comparison: greater_than",
        operator=">",
        left=str(left_decimal),
        right=str(right_decimal),
        result=result,
        correlation_id=context.correlation_id,
    )

    return result


def less_than(args: list[ASTNode], context: DslContext) -> bool:
    """Evaluate < - less than comparison.

    Args:
        args: List of exactly 2 ASTNode arguments to compare
        context: DSL evaluation context with correlation tracking

    Returns:
        bool: True if left < right, False otherwise

    Raises:
        DslEvaluationError: If not exactly 2 arguments provided

    """
    _validate_binary_args(args, "<")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)

    left_decimal = context.as_decimal(left_v)
    right_decimal = context.as_decimal(right_v)
    result = left_decimal < right_decimal

    left_expr_str = _ast_to_expr_string(args[0])
    right_expr_str = _ast_to_expr_string(args[1])

    # Detect fragile decisions where values are near the threshold
    _detect_fragile_decision(
        left_decimal, right_decimal, "<", left_expr_str, right_expr_str, context
    )

    # Add debug trace if debug mode is enabled
    context.add_debug_trace(
        operator="<",
        left_expr=left_expr_str,
        left_value=float(left_decimal),
        right_expr=right_expr_str,
        right_value=float(right_decimal),
        result=result,
    )

    logger.debug(
        "DSL comparison: less_than",
        operator="<",
        left=str(left_decimal),
        right=str(right_decimal),
        result=result,
        correlation_id=context.correlation_id,
    )

    return result


def greater_equal(args: list[ASTNode], context: DslContext) -> bool:
    """Evaluate >= - greater than or equal comparison.

    Args:
        args: List of exactly 2 ASTNode arguments to compare
        context: DSL evaluation context with correlation tracking

    Returns:
        bool: True if left >= right, False otherwise

    Raises:
        DslEvaluationError: If not exactly 2 arguments provided

    """
    _validate_binary_args(args, ">=")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)

    left_decimal = context.as_decimal(left_v)
    right_decimal = context.as_decimal(right_v)
    result = left_decimal >= right_decimal

    # Add debug trace if debug mode is enabled
    context.add_debug_trace(
        operator=">=",
        left_expr=_ast_to_expr_string(args[0]),
        left_value=float(left_decimal),
        right_expr=_ast_to_expr_string(args[1]),
        right_value=float(right_decimal),
        result=result,
    )

    logger.debug(
        "DSL comparison: greater_equal",
        operator=">=",
        left=str(left_decimal),
        right=str(right_decimal),
        result=result,
        correlation_id=context.correlation_id,
    )

    return result


def less_equal(args: list[ASTNode], context: DslContext) -> bool:
    """Evaluate <= - less than or equal comparison.

    Args:
        args: List of exactly 2 ASTNode arguments to compare
        context: DSL evaluation context with correlation tracking

    Returns:
        bool: True if left <= right, False otherwise

    Raises:
        DslEvaluationError: If not exactly 2 arguments provided

    """
    _validate_binary_args(args, "<=")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)

    left_decimal = context.as_decimal(left_v)
    right_decimal = context.as_decimal(right_v)
    result = left_decimal <= right_decimal

    # Add debug trace if debug mode is enabled
    context.add_debug_trace(
        operator="<=",
        left_expr=_ast_to_expr_string(args[0]),
        left_value=float(left_decimal),
        right_expr=_ast_to_expr_string(args[1]),
        right_value=float(right_decimal),
        result=result,
    )

    logger.debug(
        "DSL comparison: less_equal",
        operator="<=",
        left=str(left_decimal),
        right=str(right_decimal),
        result=result,
        correlation_id=context.correlation_id,
    )

    return result


def equal(args: list[ASTNode], context: DslContext) -> bool:
    """Evaluate = - equality comparison.

    Compares numeric values (int, float, Decimal) using exact Decimal equality,
    and string values using exact string equality. Mixed-type comparisons
    (e.g., number vs string) return False.

    Args:
        args: List of exactly 2 ASTNode arguments to compare
        context: DSL evaluation context with correlation tracking

    Returns:
        bool: True if values are equal, False otherwise
            - For numeric types: converted to Decimal and compared exactly
            - For strings: compared directly
            - Mixed types: returns False with warning log

    Raises:
        DslEvaluationError: If not exactly 2 arguments provided

    Notes:
        Decimal equality uses `==` which is safe because Decimal.__eq__
        implements exact equality comparison, unlike float equality which
        can have precision issues. For example: Decimal("0.1") == Decimal("0.1")
        is always exact, whereas 0.1 == 0.1 in float may have rounding errors.

    """
    _validate_binary_args(args, "=")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)

    def to_decimal_if_number(val: DSLValue) -> Decimal | None:
        """Convert numeric values to Decimal for exact comparison.

        Args:
            val: DSL value to potentially convert

        Returns:
            Decimal if val is numeric (Decimal, int, float), None otherwise

        """
        if isinstance(val, Decimal):
            return val
        if isinstance(val, int | float):
            return Decimal(str(val))
        return None

    l_num = to_decimal_if_number(left_v)
    r_num = to_decimal_if_number(right_v)

    # Both numeric - compare as Decimal
    if l_num is not None and r_num is not None:
        result = l_num == r_num
        logger.debug(
            "DSL comparison: equal (numeric)",
            operator="=",
            left=str(l_num),
            right=str(r_num),
            result=result,
            correlation_id=context.correlation_id,
        )
        return result

    # Both strings - direct comparison
    if isinstance(left_v, str) and isinstance(right_v, str):
        result = left_v == right_v
        logger.debug(
            "DSL comparison: equal (string)",
            operator="=",
            left=left_v,
            right=right_v,
            result=result,
            correlation_id=context.correlation_id,
        )
        return result

    # Mixed types - log warning and return False
    logger.warning(
        "DSL comparison: equal with mixed types",
        operator="=",
        left_type=type(left_v).__name__,
        right_type=type(right_v).__name__,
        left_value=str(left_v),
        right_value=str(right_v),
        result=False,
        correlation_id=context.correlation_id,
    )
    return False


def register_comparison_operators(dispatcher: DslDispatcher) -> None:
    """Register all comparison operators with the dispatcher.

    Args:
        dispatcher: DslDispatcher instance to register operators with

    """
    dispatcher.register(">", greater_than)
    dispatcher.register("<", less_than)
    dispatcher.register(">=", greater_equal)
    dispatcher.register("<=", less_equal)
    dispatcher.register("=", equal)
