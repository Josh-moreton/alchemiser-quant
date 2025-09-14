"""Business Unit: execution | Status: legacy

Order schemas for backward compatibility.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class RawOrderEnvelope(BaseModel):
    """Raw order envelope for backward compatibility.
    
    This is a minimal implementation to satisfy imports.
    """
    raw_order: Optional[Any] = None
    original_request: Optional[Any] = None
    request_timestamp: datetime
    response_timestamp: datetime
    success: bool = False
    error_message: Optional[str] = None


class OrderRequest(BaseModel):
    """Order request for backward compatibility."""
    symbol: Any
    side: Any
    quantity: Any
    order_type: Any
    time_in_force: Optional[Any] = None