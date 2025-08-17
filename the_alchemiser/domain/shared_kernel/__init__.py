"""Shared kernel: cross-context value objects and errors.

This package must remain framework-agnostic and side-effect free.
"""

from .types import Identifier, Money, Percentage

__all__ = [
    "Money",
    "Percentage",
    "Identifier",
]
