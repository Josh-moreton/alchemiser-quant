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

from the_alchemiser.shared.schemas.ast_nodes import ASTNode
from the_alchemiser.shared.dto.indicator_request_dto import PortfolioFragmentDTO

from ..context import DslContext
from ..dispatcher import DslDispatcher
from ..types import DslEvaluationError, DSLValue


def defsymphony(args: list[ASTNode], context: DslContext) -> DSLValue:
    """Evaluate defsymphony - main strategy definition."""
    if len(args) < 3:
        raise DslEvaluationError("defsymphony requires at least 3 arguments")

    _name = args[0]  # Strategy name (unused in evaluation)
    _config = args[1]  # Strategy config (unused in evaluation)
    body = args[2]

    # Evaluate the strategy body
    return context.evaluate_node(body, context.correlation_id, context.trace)


def if_condition(args: list[ASTNode], context: DslContext) -> DSLValue:
    """Evaluate if - conditional expression."""
    if len(args) < 2:
        raise DslEvaluationError("if requires at least 2 arguments")

    condition = args[0]
    then_expr = args[1]
    else_expr = args[2] if len(args) > 2 else None

    # Evaluate condition
    condition_result = context.evaluate_node(condition, context.correlation_id, context.trace)

    # Determine branch
    if condition_result:
        branch_taken = "then"
        result = context.evaluate_node(then_expr, context.correlation_id, context.trace)
    elif else_expr:
        branch_taken = "else"
        result = context.evaluate_node(else_expr, context.correlation_id, context.trace)
    else:
        branch_taken = "else"
        result = None

    # Publish decision event
    context.event_publisher.publish_decision_evaluated(
        decision_expression=condition,
        condition_result=bool(condition_result),
        branch_taken=branch_taken,
        branch_result=(result if isinstance(result, PortfolioFragmentDTO) else None),
        correlation_id=context.correlation_id,
    )

    return result


def create_indicator_with_symbol(indicator_expr: ASTNode, symbol: str) -> ASTNode:
    """Create indicator expression with specific symbol."""
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
            default_window = 10
            if func_name == "moving-average-price":
                default_window = 200
            elif func_name == "moving-average-return":
                default_window = 21
            elif func_name == "cumulative-return":
                default_window = 60
            elif func_name == "exponential-moving-average-price":
                default_window = 12
            elif func_name == "stdev-return":
                default_window = 6
            elif func_name == "rsi":
                default_window = 14
            elif func_name == "max-drawdown":
                default_window = 60

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
    """Register all control flow operators with the dispatcher."""
    dispatcher.register("defsymphony", defsymphony)
    dispatcher.register("if", if_condition)
