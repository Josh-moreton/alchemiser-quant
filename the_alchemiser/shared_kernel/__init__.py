"""Business Unit: utilities; Status: current.

Shared kernel: cross-context value objects, enums, and utilities.

This package must remain framework-agnostic and side-effect free.
Contains domain primitives and utilities that can be safely used
across different bounded contexts.
"""

from __future__ import annotations

from .tooling import floats_equal
from .types import ActionType

# Re-export canonical value objects from the value_objects package
from the_alchemiser.shared_kernel.value_objects.identifier import Identifier
from the_alchemiser.shared_kernel.value_objects.money import Money
from the_alchemiser.shared_kernel.value_objects.percentage import Percentage

__all__ = [
    "ActionType",
    "Identifier",
    "Money",
    "Percentage",
    "floats_equal",
]
