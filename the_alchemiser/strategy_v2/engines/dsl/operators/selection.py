#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Asset selection operators for DSL evaluation.

Implements DSL operators for selecting subsets of assets:
- select-top: Select top N assets by some criteria
- select-bottom: Select bottom N assets by some criteria
"""

from __future__ import annotations

from the_alchemiser.shared.schemas.ast_node import ASTNodeDTO

from ..context import DslContext
from ..dispatcher import DslDispatcher
from ..types import DslEvaluationError


def select_top(args: list[ASTNodeDTO], context: DslContext) -> int:
    """Evaluate select-top - select top N assets."""
    if not args:
        raise DslEvaluationError("select-top requires at least 1 argument")

    n_node = args[0]
    n = context.evaluate_node(n_node, context.correlation_id, context.trace)

    if not isinstance(n, (int, float)):
        n = context.as_decimal(n)
        n = int(n)

    return int(n)


def select_bottom(args: list[ASTNodeDTO], context: DslContext) -> int:
    """Evaluate select-bottom - select bottom N assets."""
    if not args:
        raise DslEvaluationError("select-bottom requires at least 1 argument")

    n_node = args[0]
    n = context.evaluate_node(n_node, context.correlation_id, context.trace)

    if not isinstance(n, (int, float)):
        n = context.as_decimal(n)
        n = int(n)

    return int(n)


def register_selection_operators(dispatcher: DslDispatcher) -> None:
    """Register all selection operators with the dispatcher."""
    dispatcher.register("select-top", select_top)
    dispatcher.register("select-bottom", select_bottom)
