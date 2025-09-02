"""Business Unit: shared | Status: current

Order status literal type for inter-module communication.
"""

from __future__ import annotations

from typing import Literal

OrderStatusLiteral = Literal[
    "new",
    "partially_filled",
    "filled",
    "canceled",
    "expired",
    "rejected",
]

__all__ = ["OrderStatusLiteral"]
