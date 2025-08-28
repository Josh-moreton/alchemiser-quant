"""Business Unit: order execution/placement; Status: current.

Order type value object for execution domain.
"""

from __future__ import annotations

from enum import Enum


class OrderType(Enum):
    """Order type enumeration for type safety."""

    MARKET = "market"
    LIMIT = "limit"