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

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode

from engines.dsl.context import DslContext
from engines.dsl.dispatcher import DslDispatcher
from engines.dsl.types import DslEvaluationError, DSLValue

logger = get_logger(__name__)

# Binary operators require exactly 2 arguments
BINARY_ARG_COUNT = 2


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
