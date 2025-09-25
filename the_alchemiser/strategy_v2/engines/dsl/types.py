#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL value types and type aliases for DSL evaluation.

Defines the core types used throughout the DSL evaluation system,
including the DSLValue union type and related type helpers.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.schemas.indicator_request import PortfolioFragmentDTO

# Values that may result from evaluating a DSL node
type DSLValue = (
    PortfolioFragmentDTO
    | dict[str, float | int | Decimal | str]
    | list["DSLValue"]
    | str
    | int
    | float
    | bool
    | Decimal
    | None
)


class DslEvaluationError(Exception):
    """Error during DSL evaluation."""
