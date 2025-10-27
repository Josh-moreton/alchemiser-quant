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
from typing import Any, Literal

import structlog

from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment

from ..context import DecisionNode, DslContext
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

# Recognized indicators for symbol injection
RECOGNIZED_INDICATORS = {
    "rsi",
    "moving-average-price",
    "moving-average-return",
    "cumulative-return",
    "exponential-moving-average-price",
    "stdev-return",
    "max-drawdown",
}

# Indicators that commonly appear in decision conditions
DECISION_INDICATORS = {
    "rsi",
    "moving-average-price",
    "moving-average-return",
    "current-price",
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
    Captures decision node in context.decision_path for signal reasoning.

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
        - Captures decision node with condition, result, and branch info

    """
    _validate_if_args(args, context)
    condition, then_expr, else_expr = _parse_if_args(args)

    condition_result = context.evaluate_node(condition, context.correlation_id, context.trace)
    _log_condition_evaluation(context, condition_result, else_expr)

    branch_taken, result = _evaluate_branch(condition_result, then_expr, else_expr, context)
    _log_branch_result(context, branch_taken, result)

    _capture_decision(condition, condition_result, branch_taken, context)
    _publish_decision_event(condition, condition_result, branch_taken, result, context)

    return result


def _validate_if_args(args: list[ASTNode], context: DslContext) -> None:
    """Validate if condition arguments.

    Args:
        args: List of AST nodes to validate
        context: DSL evaluation context for logging

    Raises:
        DslEvaluationError: If fewer than 2 arguments provided

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


def _parse_if_args(args: list[ASTNode]) -> tuple[ASTNode, ASTNode, ASTNode | None]:
    """Parse if condition arguments.

    Args:
        args: List of AST nodes [condition, then_expr, else_expr?]

    Returns:
        Tuple of (condition, then_expr, else_expr)

    """
    condition = args[0]
    then_expr = args[1]
    else_expr = args[2] if len(args) > 2 else None
    return condition, then_expr, else_expr


def _log_condition_evaluation(
    context: DslContext,
    condition_result: DSLValue,
    else_expr: ASTNode | None,
) -> None:
    """Log condition evaluation details.

    Args:
        context: DSL evaluation context
        condition_result: Result of evaluating the condition
        else_expr: Optional else expression

    """
    logger.debug(
        "Evaluating conditional expression",
        extra={
            "correlation_id": context.correlation_id,
            "condition_result": bool(condition_result),
            "has_else": else_expr is not None,
            "component": "dsl_control_flow",
        },
    )


def _evaluate_branch(
    condition_result: DSLValue,
    then_expr: ASTNode,
    else_expr: ASTNode | None,
    context: DslContext,
) -> tuple[Literal["then", "else"], DSLValue]:
    """Evaluate the appropriate branch based on condition result.

    Args:
        condition_result: Result of evaluating the condition
        then_expr: Expression to evaluate if condition is truthy
        else_expr: Optional expression to evaluate if condition is falsy
        context: DSL evaluation context

    Returns:
        Tuple of (branch_taken, result)

    """
    if condition_result:
        branch_taken: Literal["then", "else"] = "then"
        result = context.evaluate_node(then_expr, context.correlation_id, context.trace)
        return branch_taken, result

    if else_expr:
        branch_taken = "else"
        result = context.evaluate_node(else_expr, context.correlation_id, context.trace)
        return branch_taken, result

    return "else", None


def _log_branch_result(
    context: DslContext,
    branch_taken: Literal["then", "else"],
    result: DSLValue,
) -> None:
    """Log branch evaluation result.

    Args:
        context: DSL evaluation context
        branch_taken: Which branch was taken ("then" or "else")
        result: Result of evaluating the branch

    """
    logger.debug(
        "Conditional branch evaluated",
        extra={
            "correlation_id": context.correlation_id,
            "branch_taken": branch_taken,
            "result_type": type(result).__name__,
            "component": "dsl_control_flow",
        },
    )


def _capture_decision(
    condition: ASTNode,
    condition_result: DSLValue,
    branch_taken: Literal["then", "else"],
    context: DslContext,
) -> None:
    """Capture decision node in context for signal reasoning.

    Args:
        condition: The condition AST node that was evaluated
        condition_result: Result of evaluating the condition
        branch_taken: Which branch was taken ("then" or "else")
        context: DSL evaluation context

    """
    decision_node = _build_decision_node(condition, bool(condition_result), branch_taken, context)
    context.decision_path.append(dict(decision_node))


def _publish_decision_event(
    condition: ASTNode,
    condition_result: DSLValue,
    branch_taken: Literal["then", "else"],
    result: DSLValue,
    context: DslContext,
) -> None:
    """Publish decision evaluated event for observability.

    Args:
        condition: The condition AST node that was evaluated
        condition_result: Result of evaluating the condition
        branch_taken: Which branch was taken ("then" or "else")
        result: Result of evaluating the selected branch
        context: DSL evaluation context

    """
    context.event_publisher.publish_decision_evaluated(
        decision_expression=condition,
        condition_result=bool(condition_result),
        branch_taken=branch_taken,
        branch_result=(result if isinstance(result, PortfolioFragment) else None),
        correlation_id=context.correlation_id,
        causation_id=context.correlation_id,
    )


def _build_decision_node(
    condition: ASTNode,
    result: bool,  # noqa: FBT001
    branch: str,
    context: DslContext,
) -> DecisionNode:
    """Build a decision node from condition evaluation.

    Formats the condition as a human-readable string and captures any
    indicator values that were referenced during evaluation.

    Args:
        condition: The condition AST node that was evaluated
        result: The boolean result of the condition evaluation
        branch: The branch that was taken ("then" or "else")
        context: DSL evaluation context

    Returns:
        DecisionNode with formatted condition and metadata

    """
    # Format condition as human-readable string
    condition_str = _format_condition(condition)

    # Try to extract indicator values from the condition
    values = _extract_indicator_values(condition, context)

    return DecisionNode(
        condition=condition_str,
        result=result,
        branch=branch,
        values=values,
    )


def _format_condition(condition: ASTNode) -> str:
    """Format an AST condition node as a human-readable string.

    Args:
        condition: The condition AST node to format

    Returns:
        Human-readable string representation of the condition

    """
    if condition.is_atom():
        return str(condition.get_atom_value())

    if condition.is_symbol():
        symbol_name = condition.get_symbol_name()
        return symbol_name if symbol_name else ""

    if condition.is_list() and condition.children:
        return _format_list_condition(condition)

    return str(condition)


def _format_list_condition(condition: ASTNode) -> str:
    """Format a list condition node as a human-readable string.

    Args:
        condition: The list condition AST node to format

    Returns:
        Human-readable string representation of the list condition

    """
    # Handle comparison operators like (> (rsi "SPY" {:window 10}) 79)
    if len(condition.children) >= 3:
        return _format_binary_operator(condition)

    # Fallback: format as function call
    return _format_function_call(condition)


def _format_binary_operator(condition: ASTNode) -> str:
    """Format a binary operator expression.

    Args:
        condition: The binary operator AST node to format

    Returns:
        Human-readable string representation like "left OP right"

    """
    op = condition.children[0].get_symbol_name() if condition.children[0].is_symbol() else ""
    left = _format_condition(condition.children[1])
    right = _format_condition(condition.children[2])

    # Map Clojure operators to readable format (only operators needing transformation)
    op_map = {
        "=": "==",
        "and": "AND",
        "or": "OR",
    }
    readable_op = op_map.get(op, op) if op else ""

    return f"{left} {readable_op} {right}"


def _format_function_call(condition: ASTNode) -> str:
    """Format a function call expression.

    Args:
        condition: The function call AST node to format

    Returns:
        Human-readable string representation like "func(arg1, arg2)"

    """
    func_name = condition.children[0].get_symbol_name() if condition.children[0].is_symbol() else ""
    args = [_format_condition(child) for child in condition.children[1:]]
    return f"{func_name}({', '.join(args)})"


def _extract_indicator_values(condition: ASTNode, context: DslContext) -> dict[str, Any]:
    """Extract indicator values referenced in a condition.

    Traverses the condition AST and extracts values for any indicators
    that were computed during evaluation.

    Args:
        condition: The condition AST node
        context: DSL evaluation context

    Returns:
        Dictionary mapping indicator names to their computed values

    """
    values: dict[str, Any] = {}

    if not condition.is_list() or not condition.children:
        return values

    # Look for indicator function calls in the condition tree
    for child in condition.children:
        _process_child_node(child, values, context)

    return values


def _process_child_node(child: ASTNode, values: dict[str, Any], context: DslContext) -> None:
    """Process a child node to extract indicator values.

    Args:
        child: The child AST node to process
        values: Dictionary to update with extracted values
        context: DSL evaluation context

    """
    if child.is_list() and child.children:
        _extract_from_indicator_call(child, values)

    # Recursively check nested conditions
    if child.is_list():
        nested_values = _extract_indicator_values(child, context)
        values.update(nested_values)


def _extract_from_indicator_call(child: ASTNode, values: dict[str, Any]) -> None:
    """Extract indicator value from a function call node.

    Args:
        child: The function call AST node
        values: Dictionary to update with extracted values

    """
    func_name = child.children[0].get_symbol_name() if child.children[0].is_symbol() else ""

    # Check if it's an indicator function
    if func_name and _is_indicator_function(func_name):
        symbol = _extract_symbol_from_call(child)
        if symbol:
            key = f"{symbol}_{func_name.replace('-', '_')}"
            # Note: We don't have the actual computed value here without re-evaluating
            # Mark that this indicator was referenced in the decision
            values[key] = "<computed>"


def _is_indicator_function(func_name: str) -> bool:
    """Check if a function name is a recognized indicator function.

    Used for detecting indicator functions in decision conditions
    to extract their values for signal reasoning.

    Args:
        func_name: The function name to check

    Returns:
        True if the function is an indicator function

    """
    return func_name in DECISION_INDICATORS


def _extract_symbol_from_call(child: ASTNode) -> str:
    """Extract symbol parameter from an indicator function call.

    Args:
        child: The function call AST node

    Returns:
        The symbol string if found, empty string otherwise

    """
    if len(child.children) > 1 and child.children[1].is_atom():
        atom_val = child.children[1].get_atom_value()
        if isinstance(atom_val, str):
            return atom_val
    return ""


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
    if not _is_valid_indicator_expr(indicator_expr):
        return indicator_expr

    func_name = indicator_expr.children[0].get_symbol_name()
    if not func_name or not _is_recognized_indicator(func_name):
        return indicator_expr

    return _build_indicator_node(indicator_expr, func_name, symbol)


def _is_valid_indicator_expr(indicator_expr: ASTNode) -> bool:
    """Check if expression is a valid indicator expression.

    Args:
        indicator_expr: AST node to check

    Returns:
        True if the expression is a non-empty list node

    """
    return indicator_expr.is_list() and bool(indicator_expr.children)


def _is_recognized_indicator(func_name: str) -> bool:
    """Check if function name is a recognized indicator.

    Used for validating indicators that can have symbols injected
    during expression transformation.

    Args:
        func_name: The function name to check

    Returns:
        True if the function is a recognized indicator

    """
    return func_name in RECOGNIZED_INDICATORS


def _build_indicator_node(
    indicator_expr: ASTNode,
    func_name: str,
    symbol: str,
) -> ASTNode:
    """Build a new indicator node with symbol injected.

    Args:
        indicator_expr: Original indicator expression
        func_name: Name of the indicator function
        symbol: Stock symbol to inject

    Returns:
        New ASTNode with symbol and parameters

    """
    children = [ASTNode.symbol(func_name), ASTNode.atom(symbol)]

    if len(indicator_expr.children) > 1:
        children.append(indicator_expr.children[1])
    else:
        children.append(_create_default_window_param(func_name))

    return ASTNode.list_node(children)


def _create_default_window_param(func_name: str) -> ASTNode:
    """Create default window parameter node for an indicator.

    Args:
        func_name: Name of the indicator function

    Returns:
        ASTNode representing default window parameter map

    """
    default_window = DEFAULT_INDICATOR_WINDOWS.get(func_name, 10)
    return ASTNode.list_node(
        [
            ASTNode.symbol(":window"),
            ASTNode.atom(Decimal(str(default_window))),
        ],
        metadata={"node_subtype": "map"},
    )


def register_control_flow_operators(dispatcher: DslDispatcher) -> None:
    """Register all control flow operators with the dispatcher.

    Registers DSL control flow operators (defsymphony, if) with the provided
    dispatcher for use in strategy evaluation.

    Args:
        dispatcher: DslDispatcher instance to register operators with

    """
    dispatcher.register("defsymphony", defsymphony)
    dispatcher.register("if", if_condition)
