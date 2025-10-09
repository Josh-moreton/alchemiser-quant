"""Business Unit: shared | Status: current.

Alpaca-specific Protocol Definitions.

Protocols for interacting with Alpaca SDK objects while maintaining type safety.
These are more specific than the generic OrderLikeProtocol and include
Alpaca-specific attributes like time_in_force and timestamps.

The protocols use flexible types (str | datetime, str | UUID) to support both
native Alpaca SDK objects and their serialized forms (e.g., from JSON/dict).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class AlpacaOrderProtocol(Protocol):
    """Protocol for complete Alpaca order objects.

    This protocol defines the structure for full order information from the
    Alpaca Trading API. It supports both native SDK Order objects and
    serialized/deserialized forms.

    Use this protocol when you need access to complete order details including
    timestamps, pricing, and order identification.

    Attributes support multiple types to handle both SDK objects (UUID, datetime)
    and their serialized forms (str).
    """

    id: str | UUID
    client_order_id: str
    symbol: str
    qty: str | float | None
    side: str
    order_type: str
    time_in_force: str
    status: str
    filled_qty: str | float | None
    filled_avg_price: str | float | None
    created_at: str | datetime
    submitted_at: str | datetime
    updated_at: str | datetime | None


@runtime_checkable
class AlpacaOrderObject(Protocol):
    """Protocol for minimal order monitoring.

    This protocol defines only the essential fields needed for order status
    monitoring and tracking. It's a lightweight alternative to AlpacaOrderProtocol.

    Use this protocol when you only need to check order status and fill progress,
    such as in polling loops or status dashboards.

    This is a structural subset of AlpacaOrderProtocol - any object satisfying
    AlpacaOrderProtocol will also satisfy this protocol.
    """

    id: str | UUID
    status: str
    filled_qty: str | float | None


__all__ = ["AlpacaOrderProtocol", "AlpacaOrderObject"]
