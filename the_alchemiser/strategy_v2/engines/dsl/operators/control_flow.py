#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Control flow operators for DSL evaluation.

Implements DSL control flow and conditional operators:
- defsymphony: Main strategy definition wrapper
- if: Conditional branching with optional else clause
- create_indicator_with_symbol: Helper for indicator expression modification
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

import structlog

from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment

from ..context import DslContext
from ..dispatcher import DslDispatcher
from ..types import DslEvaluationError, DSLValue

# Initialize structured logger
logger = structlog.get_logger(__name__)

# Default window sizes for technical indicators
DEFAULT_INDICATOR_WINDOWS = {
    "rsi": 14,
    "moving-average-price": 200,
    "moving-average-return": 21,
    "cumulative-return": 60,
    "exponential-moving-average-price": 12,
    "stdev-return": 6,
    "max-drawdown": 60,
}


def defsymphony(args: list[ASTNode], context: DslContext) -> DSLValue:
    """Evaluate defsymphony - main strategy definition.

    Wrapper operator for strategy definitions in DSL. Validates argument count
    and evaluates the strategy body expression.

    Args:
        args: List of AST nodes [name, config, body]
            - name: Strategy name (unused in evaluation)
            - config: Strategy configuration (unused in evaluation)
            - body: Strategy body expression to evaluate
        context: DSL evaluation context with services and correlation tracking

    Returns:
        Result of evaluating the strategy body (typically PortfolioFragment)

    Raises:
        DslEvaluationError: If fewer than 3 arguments provided

    Example:
        (defsymphony "my-strategy" {} (portfolio {...}))

    """
    if len(args) < 3:
        logger.error(
            "defsymphony requires at least 3 arguments",
            extra={
                "correlation_id": context.correlation_id,
                "args_provided": len(args),
                "component": "dsl_control_flow",
            },
        )
        raise DslEvaluationError("defsymphony requires at least 3 arguments")

    _name = args[0]  # Strategy name (unused in evaluation)
    _config = args[1]  # Strategy config (unused in evaluation)
    body = args[2]

    logger.debug(
        "Evaluating strategy body",
        extra={
            "correlation_id": context.correlation_id,
            "component": "dsl_control_flow",
        },
    )

    # Evaluate the strategy body
    result = context.evaluate_node(body, context.correlation_id, context.trace)

    logger.debug(
        "Strategy body evaluation completed",
        extra={
            "correlation_id": context.correlation_id,
            "result_type": type(result).__name__,
            "component": "dsl_control_flow",
        },
    )

    return result


def if_condition(args: list[ASTNode], context: DslContext) -> DSLValue:
    """Evaluate if - conditional expression.

    Evaluates condition and selects then/else branch based on truthiness.
    Publishes DecisionEvaluated event for observability and audit trail.

    Args:
        args: List of AST nodes [condition, then_expr, else_expr?]
            - condition: Expression to evaluate for branch selection
            - then_expr: Expression to evaluate if condition is truthy
            - else_expr: Optional expression to evaluate if condition is falsy
        context: DSL evaluation context with services and correlation tracking

    Returns:
        Result of evaluating the selected branch, or None if no else and condition is falsy

    Raises:
        DslEvaluationError: If fewer than 2 arguments provided

    Example:
        (if (> rsi 70) (sell 100) (hold))

    Notes:
        - Condition uses Python truthiness semantics (0, None, "", [] are falsy)
        - Publishes DecisionEvaluated event with branch selection details
        - Only evaluates the selected branch (lazy evaluation)

    """
    if len(args) < 2:
        logger.error(
            "if requires at least 2 arguments",
            extra={
                "correlation_id": context.correlation_id,
                "args_provided": len(args),
                "component": "dsl_control_flow",
            },
        )
        raise DslEvaluationError("if requires at least 2 arguments")

    condition = args[0]
    then_expr = args[1]
    else_expr = args[2] if len(args) > 2 else None

    # Evaluate condition
    condition_result = context.evaluate_node(
        condition, context.correlation_id, context.trace
    )

    logger.debug(
        "Evaluating conditional expression",
        extra={
            "correlation_id": context.correlation_id,
            "condition_result": bool(condition_result),
            "has_else": else_expr is not None,
            "component": "dsl_control_flow",
        },
    )

    # Determine branch
    branch_taken: Literal["then", "else"]
    if condition_result:
        branch_taken = "then"
        result = context.evaluate_node(then_expr, context.correlation_id, context.trace)
    elif else_expr:
        branch_taken = "else"
        result = context.evaluate_node(else_expr, context.correlation_id, context.trace)
    else:
        branch_taken = "else"
        result = None

    logger.debug(
        "Conditional branch evaluated",
        extra={
            "correlation_id": context.correlation_id,
            "branch_taken": branch_taken,
            "result_type": type(result).__name__,
            "component": "dsl_control_flow",
        },
    )

    # Publish decision event for observability
    context.event_publisher.publish_decision_evaluated(
        decision_expression=condition,
        condition_result=bool(condition_result),
        branch_taken=branch_taken,
        branch_result=(result if isinstance(result, PortfolioFragment) else None),
        correlation_id=context.correlation_id,
        causation_id=context.correlation_id,  # Explicitly set causation_id
    )

    return result


def create_indicator_with_symbol(indicator_expr: ASTNode, symbol: str) -> ASTNode:
    """Create indicator expression with specific symbol.

    Transforms indicator expressions by injecting a symbol parameter and adding
    default window parameters if not present. Used for per-symbol indicator
    computation in filtering and selection operations.

    Args:
        indicator_expr: AST node representing indicator expression
            Expected form: (indicator-name {...params})
        symbol: Stock symbol to inject into expression

    Returns:
        New ASTNode with symbol injected and default params added if needed.
        Returns original node unchanged if not a recognized indicator expression.

    Example:
        Input:  (rsi {:window 14})
        Output: (rsi "AAPL" {:window 14})

        Input:  (moving-average-price)
        Output: (moving-average-price "AAPL" {:window 200})

    Notes:
        - Only processes recognized indicator functions (see DEFAULT_INDICATOR_WINDOWS)
        - Non-list or empty nodes returned unchanged
        - Adds default window parameter if missing (per indicator type)

    """
    if not indicator_expr.is_list() or not indicator_expr.children:
        return indicator_expr

    # For RSI indicator, create: (rsi "SYMBOL" {:window N})
    func_name = indicator_expr.children[0].get_symbol_name()
    if func_name in {
        "rsi",
        "moving-average-price",
        "moving-average-return",
        "cumulative-return",
        "exponential-moving-average-price",
        "stdev-return",
        "max-drawdown",
    }:
        children = [ASTNode.symbol(func_name), ASTNode.atom(symbol)]
        # Add parameters if present
        if len(indicator_expr.children) > 1:
            children.append(indicator_expr.children[1])
        else:
            # Add default window parameter per indicator
            default_window = DEFAULT_INDICATOR_WINDOWS.get(func_name, 10)

            children.append(
                ASTNode.list_node(
                    [
                        ASTNode.symbol(":window"),
                        ASTNode.atom(Decimal(str(default_window))),
                    ],
                    metadata={"node_subtype": "map"},
                )
            )

        return ASTNode.list_node(children)

    return indicator_expr


def register_control_flow_operators(dispatcher: DslDispatcher) -> None:
    """Register all control flow operators with the dispatcher.

    Registers DSL control flow operators (defsymphony, if) with the provided
    dispatcher for use in strategy evaluation.

    Args:
        dispatcher: DslDispatcher instance to register operators with

    """
    dispatcher.register("defsymphony", defsymphony)
    dispatcher.register("if", if_condition)
