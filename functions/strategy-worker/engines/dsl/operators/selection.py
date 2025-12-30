#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Asset selection operators for DSL evaluation.

Implements DSL operators for selecting subsets of assets:
- select-top: Select top N assets by some criteria
- select-bottom: Select bottom N assets by some criteria

These operators determine the number of assets to select from a portfolio.
The actual ranking/sorting is performed by parent operators.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode

from engines.dsl.context import DslContext
from engines.dsl.dispatcher import DslDispatcher
from engines.dsl.types import DslEvaluationError

logger = get_logger(__name__)


def select_top(args: list[ASTNode], context: DslContext) -> int:
    """Evaluate select-top - select top N assets by ranking criteria.

    Determines the number of top-ranked assets to select. The actual ranking
    is performed by parent operators (e.g., weight-equal, weight-inverse-volatility).

    Args:
        args: List of AST nodes, where args[0] is the number of assets to select
        context: DSL evaluation context with correlation tracking

    Returns:
        Integer count of assets to select (truncated if float provided)

    Raises:
        DslEvaluationError: If no arguments provided or evaluation fails

    Pre-conditions:
        - args must contain at least one node
        - args[0] must evaluate to a numeric value

    Post-conditions:
        - Returns integer >= 0 (negative values allowed but logged as unusual)
        - Float values are truncated (not rounded) to integers

    Example:
        >>> # DSL: (select-top 5)  -> selects top 5 assets
        >>> # DSL: (select-top 10.7) -> selects top 10 assets (truncated)

    """
    if not args:
        msg = "select-top requires at least 1 argument"
        logger.error(
            "DSL evaluation error in select-top",
            correlation_id=context.correlation_id,
            error=msg,
        )
        raise DslEvaluationError(msg)

    n_node = args[0]
    n_raw = context.evaluate_node(n_node, context.correlation_id, context.trace)

    # Coerce to integer
    if isinstance(n_raw, int):
        n = n_raw
    elif isinstance(n_raw, float | Decimal):
        n = int(n_raw)
    else:
        n_decimal = context.as_decimal(n_raw)
        n = int(n_decimal)

    # Business rule validation: negative values are unusual
    if n < 0:
        logger.warning(
            "select-top called with negative value (unusual but allowed)",
            correlation_id=context.correlation_id,
            n=n,
            operator="select-top",
        )

    logger.debug(
        "select-top evaluated",
        correlation_id=context.correlation_id,
        n=n,
        operator="select-top",
    )

    return n


def select_bottom(args: list[ASTNode], context: DslContext) -> int:
    """Evaluate select-bottom - select bottom N assets by ranking criteria.

    Determines the number of bottom-ranked assets to select. The actual ranking
    is performed by parent operators (e.g., weight-equal, weight-inverse-volatility).

    Args:
        args: List of AST nodes, where args[0] is the number of assets to select
        context: DSL evaluation context with correlation tracking

    Returns:
        Integer count of assets to select (truncated if float provided)

    Raises:
        DslEvaluationError: If no arguments provided or evaluation fails

    Pre-conditions:
        - args must contain at least one node
        - args[0] must evaluate to a numeric value

    Post-conditions:
        - Returns integer >= 0 (negative values allowed but logged as unusual)
        - Float values are truncated (not rounded) to integers

    Example:
        >>> # DSL: (select-bottom 3)  -> selects bottom 3 assets
        >>> # DSL: (select-bottom 7.9) -> selects bottom 7 assets (truncated)

    """
    if not args:
        msg = "select-bottom requires at least 1 argument"
        logger.error(
            "DSL evaluation error in select-bottom",
            correlation_id=context.correlation_id,
            error=msg,
        )
        raise DslEvaluationError(msg)

    n_node = args[0]
    n_raw = context.evaluate_node(n_node, context.correlation_id, context.trace)

    # Coerce to integer
    if isinstance(n_raw, int):
        n = n_raw
    elif isinstance(n_raw, float | Decimal):
        n = int(n_raw)
    else:
        n_decimal = context.as_decimal(n_raw)
        n = int(n_decimal)

    # Business rule validation: negative values are unusual
    if n < 0:
        logger.warning(
            "select-bottom called with negative value (unusual but allowed)",
            correlation_id=context.correlation_id,
            n=n,
            operator="select-bottom",
        )

    logger.debug(
        "select-bottom evaluated",
        correlation_id=context.correlation_id,
        n=n,
        operator="select-bottom",
    )

    return n


def register_selection_operators(dispatcher: DslDispatcher) -> None:
    """Register all selection operators with the dispatcher.

    Registers:
        - select-top: Select top N assets by ranking
        - select-bottom: Select bottom N assets by ranking

    Args:
        dispatcher: DSL dispatcher to register operators with

    """
    dispatcher.register("select-top", select_top)
    dispatcher.register("select-bottom", select_bottom)
