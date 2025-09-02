"""Business Unit: order execution/placement; Status: current.

Canonical lowercase order status literals for system boundaries.

This module now imports from shared.types.order_status for consistency.
"""

from __future__ import annotations

from the_alchemiser.shared.types.order_status import OrderStatusLiteral

__all__ = ["OrderStatusLiteral"]
