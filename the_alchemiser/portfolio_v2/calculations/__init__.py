"""Business Unit: portfolio | Status: current.

Portfolio calculation utilities and algorithms.

This module provides calculation utilities for portfolio analysis,
allocation comparison, and rebalancing computations.
"""

from __future__ import annotations

from .portfolio_calculations import build_allocation_comparison

__all__ = [
    "build_allocation_comparison",
]