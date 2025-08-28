"""Business Unit: utilities; Status: legacy.

Shared kernel type exports for cross-context value objects (Legacy Location).

This module is deprecated. Use `shared_kernel.value_objects.*` instead.
"""

from __future__ import annotations

# Re-export from new location for backward compatibility
from shared_kernel.value_objects.identifier import Identifier
from shared_kernel.value_objects.money import Money
from shared_kernel.value_objects.percentage import Percentage
from shared_kernel.value_objects.symbol import Symbol

__all__ = ["Identifier", "Money", "Percentage", "Symbol"]
