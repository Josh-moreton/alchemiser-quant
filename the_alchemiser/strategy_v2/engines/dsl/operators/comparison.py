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

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO

from ..context import DslContext
from ..dispatcher import DslDispatcher
from ..types import DSLValue, DslEvaluationError


def greater_than(args: list[ASTNodeDTO], context: DslContext) -> bool:
    """Evaluate > - greater than comparison."""
    if len(args) != 2:
        raise DslEvaluationError("> requires exactly 2 arguments")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)
    return context.as_decimal(left_v) > context.as_decimal(right_v)


def less_than(args: list[ASTNodeDTO], context: DslContext) -> bool:
    """Evaluate < - less than comparison."""
    if len(args) != 2:
        raise DslEvaluationError("< requires exactly 2 arguments")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)
    return context.as_decimal(left_v) < context.as_decimal(right_v)


def greater_equal(args: list[ASTNodeDTO], context: DslContext) -> bool:
    """Evaluate >= - greater than or equal comparison."""
    if len(args) != 2:
        raise DslEvaluationError(">= requires exactly 2 arguments")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)
    return context.as_decimal(left_v) >= context.as_decimal(right_v)


def less_equal(args: list[ASTNodeDTO], context: DslContext) -> bool:
    """Evaluate <= - less than or equal comparison."""
    if len(args) != 2:
        raise DslEvaluationError("<= requires exactly 2 arguments")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)
    return context.as_decimal(left_v) <= context.as_decimal(right_v)


def equal(args: list[ASTNodeDTO], context: DslContext) -> bool:
    """Evaluate = - equality comparison."""
    if len(args) != 2:
        raise DslEvaluationError("= requires exactly 2 arguments")

    left_v = context.evaluate_node(args[0], context.correlation_id, context.trace)
    right_v = context.evaluate_node(args[1], context.correlation_id, context.trace)

    def to_decimal_if_number(val: DSLValue) -> Decimal | None:
        if isinstance(val, Decimal):
            return val
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        return None

    l_num = to_decimal_if_number(left_v)
    r_num = to_decimal_if_number(right_v)
    if l_num is not None and r_num is not None:
        return l_num == r_num
    if isinstance(left_v, str) and isinstance(right_v, str):
        return left_v == right_v
    return False


def register_comparison_operators(dispatcher: DslDispatcher) -> None:
    """Register all comparison operators with the dispatcher."""
    dispatcher.register(">", greater_than)
    dispatcher.register("<", less_than)
    dispatcher.register(">=", greater_equal)
    dispatcher.register("<=", less_equal)
    dispatcher.register("=", equal)