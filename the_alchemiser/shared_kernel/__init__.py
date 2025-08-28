"""Business Unit: utilities; Status: current.

Shared kernel: cross-context value objects and errors.

This package contains value objects and types that are shared across multiple
bounded contexts. It must remain framework-agnostic and side-effect free.
"""

from __future__ import annotations

from .value_objects.identifier import Identifier
from .value_objects.money import Money
from .value_objects.percentage import Percentage
from .value_objects.symbol import Symbol

__all__ = [
    "Identifier",
    "Money",
    "Percentage",
    "Symbol",
]