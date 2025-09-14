"""Business Unit: execution | Status: legacy.

Order schemas for backward compatibility.
"""
# ruff: noqa

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RawOrderEnvelope(BaseModel):
    """Raw order envelope for backward compatibility.
    
    This is a minimal implementation to satisfy imports.
    """

    raw_order: Any | None = None
    original_request: Any | None = None
    request_timestamp: datetime
    response_timestamp: datetime
    success: bool = False
    error_message: str | None = None


class OrderRequest(BaseModel):
    """Order request for backward compatibility."""

    symbol: Any
    side: Any
    quantity: Any
    order_type: Any
    time_in_force: Any | None = None