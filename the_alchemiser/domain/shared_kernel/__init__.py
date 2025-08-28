"""Business Unit: utilities; Status: current.

Shared kernel: cross-context value objects and errors.

This package must remain framework-agnostic and side-effect free.
"""
from __future__ import annotations


from .types import Identifier, Money, Percentage

__all__ = [
    "Identifier",
    "Money",
    "Percentage",
]
