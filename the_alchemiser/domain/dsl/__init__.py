"""Business Unit: utilities; Status: current.

S-expression Strategy DSL Engine.

A minimal, secure DSL for evaluating trading strategies written as S-expressions.
Provides deterministic evaluation with structured tracing and strict whitelisting.
"""

from __future__ import annotations

from the_alchemiser.strategy.dsl.errors import DSLError, EvaluationError, ParseError
from the_alchemiser.domain.dsl.evaluator import DSLEvaluator
from the_alchemiser.domain.dsl.parser import DSLParser

__all__ = [
    "DSLError",
    "DSLEvaluator",
    "DSLParser",
    "EvaluationError",
    "ParseError",
]
