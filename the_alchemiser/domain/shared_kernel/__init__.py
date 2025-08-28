"""Business Unit: utilities; Status: legacy.

Shared kernel: cross-context value objects and errors (Legacy Location).

This package is deprecated. Use top-level `shared_kernel` instead.
This is maintained for backward compatibility during migration.
"""

from __future__ import annotations

# Re-export from new location for backward compatibility
from shared_kernel import Identifier, Money, Percentage, Symbol

__all__ = [
    "Identifier",
    "Money",
    "Percentage", 
    "Symbol",
]
