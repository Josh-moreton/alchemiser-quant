"""Business Unit: order execution/placement; Status: current.

Execution application orders package.
"""

from __future__ import annotations

from .order_service import OrderService

__all__ = [
    "OrderService",
]