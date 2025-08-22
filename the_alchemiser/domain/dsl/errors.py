"""
DSL-specific exceptions for the S-expression Strategy Engine.

Provides clear, actionable error messages with context about what went wrong
and suggestions for fixing DSL syntax or evaluation issues.
"""

from __future__ import annotations

from typing import Any


class DSLError(Exception):
    """Base exception for all DSL-related errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ParseError(DSLError):
    """Raised when S-expression parsing fails."""

    def __init__(
        self,
        message: str,
        expression: str | None = None,
        position: int | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, context)
        self.expression = expression
        self.position = position


class SchemaError(DSLError):
    """Raised when DSL construct validation fails."""

    def __init__(
        self,
        message: str,
        construct: str | None = None,
        expected_arity: int | None = None,
        actual_arity: int | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, context)
        self.construct = construct
        self.expected_arity = expected_arity
        self.actual_arity = actual_arity


class EvaluationError(DSLError):
    """Raised when DSL evaluation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        ast_node: Any = None,
        context: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, context)
        self.symbol = symbol
        self.ast_node = ast_node


class SecurityError(DSLError):
    """Raised when DSL security constraints are violated."""

    def __init__(
        self,
        message: str,
        violation_type: str | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, context)
        self.violation_type = violation_type


class IndicatorError(DSLError):
    """Raised when indicator calculations fail."""

    def __init__(
        self,
        message: str,
        indicator: str | None = None,
        symbol: str | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, context)
        self.indicator = indicator
        self.symbol = symbol


class PortfolioError(DSLError):
    """Raised when portfolio construction or algebra fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        assets: list[str] | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, context)
        self.operation = operation
        self.assets = assets
