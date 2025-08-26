"""AST node definitions for the S-expression Strategy DSL.

Defines dataclasses for all supported DSL constructs with type safety
and clear semantics for evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Base AST node
@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes."""

    # Node ID for caching and interning (set by interning system)
    node_id: str | None = field(default=None, init=False, compare=False)


# Literals and symbols
@dataclass(frozen=True)
class NumberLiteral(ASTNode):
    """Numeric literal (int or float)."""

    value: float


@dataclass(frozen=True)
class Symbol(ASTNode):
    """Symbol reference for function calls or variables."""

    name: str


# Comparison operators
@dataclass(frozen=True)
class GreaterThan(ASTNode):
    """Greater than comparison (>)."""

    left: ASTNode
    right: ASTNode


@dataclass(frozen=True)
class LessThan(ASTNode):
    """Less than comparison (<)."""

    left: ASTNode
    right: ASTNode


# Control flow
@dataclass(frozen=True)
class If(ASTNode):
    """Conditional expression (if condition then_expr else_expr)."""

    condition: ASTNode
    then_expr: ASTNode
    else_expr: ASTNode | None = None


# Indicators
@dataclass(frozen=True)
class RSI(ASTNode):
    """RSI indicator calculation."""

    symbol: str
    window: int


@dataclass(frozen=True)
class MovingAveragePrice(ASTNode):
    """Moving average of prices."""

    symbol: str
    window: int


@dataclass(frozen=True)
class MovingAverageReturn(ASTNode):
    """Moving average of returns."""

    symbol: str
    window: int


@dataclass(frozen=True)
class CumulativeReturn(ASTNode):
    """Cumulative return over window."""

    symbol: str
    window: int


@dataclass(frozen=True)
class CurrentPrice(ASTNode):
    """Current/latest price."""

    symbol: str


@dataclass(frozen=True)
class StdevReturn(ASTNode):
    """Standard deviation of returns over window."""

    symbol: str
    window: int


# Portfolio construction
@dataclass(frozen=True)
class Asset(ASTNode):
    """Individual asset/ticker."""

    symbol: str
    name: str | None = None


@dataclass(frozen=True)
class Group(ASTNode):
    """Named group containing sub-expressions."""

    name: str
    expressions: list[ASTNode]


@dataclass(frozen=True)
class WeightEqual(ASTNode):
    """Equal-weight portfolio across expressions."""

    expressions: list[ASTNode]


@dataclass(frozen=True)
class WeightSpecified(ASTNode):
    """Explicitly weighted portfolio."""

    weights_and_expressions: list[tuple[float, ASTNode]]


@dataclass(frozen=True)
class WeightInverseVolatility(ASTNode):
    """Inverse volatility weighted portfolio."""

    lookback: int
    expressions: list[ASTNode]


# Selectors
@dataclass(frozen=True)
class Filter(ASTNode):
    """Filter assets by metric with selection criteria."""

    metric_fn: ASTNode
    selector: ASTNode  # select-top, select-bottom, etc.
    assets: list[ASTNode]


@dataclass(frozen=True)
class SelectTop(ASTNode):
    """Select top N assets by metric."""

    count: int


@dataclass(frozen=True)
class SelectBottom(ASTNode):
    """Select bottom N assets by metric."""

    count: int


# Function calls (for extensibility)
@dataclass(frozen=True)
class FunctionCall(ASTNode):
    """Generic function call with arguments."""

    function_name: str
    args: list[ASTNode]


# Root node for complete strategies
@dataclass(frozen=True)
class Strategy(ASTNode):
    """Root strategy node with metadata."""

    name: str
    metadata: dict[str, Any]
    expression: ASTNode


# Type alias for any AST node
ASTNodeType = (
    NumberLiteral
    | Symbol
    | GreaterThan
    | LessThan
    | If
    | RSI
    | MovingAveragePrice
    | MovingAverageReturn
    | CumulativeReturn
    | CurrentPrice
    | StdevReturn
    | Asset
    | Group
    | WeightEqual
    | WeightSpecified
    | WeightInverseVolatility
    | Filter
    | SelectTop
    | SelectBottom
    | FunctionCall
    | Strategy
)
