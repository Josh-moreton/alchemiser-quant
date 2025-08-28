"""Business Unit: order execution/placement; Status: current."""

from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""

    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
