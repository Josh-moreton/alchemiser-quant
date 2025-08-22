"""
S-expression Strategy DSL Engine

A minimal, secure DSL for evaluating trading strategies written as S-expressions.
Provides deterministic evaluation with structured tracing and strict whitelisting.
"""

from the_alchemiser.domain.dsl.parser import DSLParser
from the_alchemiser.domain.dsl.evaluator import DSLEvaluator
from the_alchemiser.domain.dsl.errors import DSLError, ParseError, EvaluationError

__all__ = [
    "DSLParser",
    "DSLEvaluator",
    "DSLError",
    "ParseError",
    "EvaluationError",
]