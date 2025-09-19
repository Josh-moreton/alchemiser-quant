"""Business Unit: shared | Status: current.

Alpaca data models and type definitions.

Defines typed data structures for Alpaca broker operations,
providing clean interfaces between broker responses and domain logic.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AccountInfoModel(BaseModel):
    """Account information model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    id: str | None = None
    account_number: str | None = None
    status: str | None = None
    currency: str | None = None
    buying_power: Decimal | None = None
    cash: Decimal | None = None
    equity: Decimal | None = None
    portfolio_value: Decimal | None = None


class PositionModel(BaseModel):
    """Position information model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    symbol: str
    qty: Decimal
    qty_available: Decimal | None = None
    market_value: Decimal | None = None
    cost_basis: Decimal | None = None
    unrealized_pl: Decimal | None = None
    unrealized_plpc: Decimal | None = None
    current_price: Decimal | None = None
    lastday_price: Decimal | None = None
    change_today: Decimal | None = None


class OrderModel(BaseModel):
    """Order information model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    id: str
    client_order_id: str | None = None
    symbol: str
    asset_class: str | None = None
    order_class: str | None = None
    order_type: str | None = None
    qty: Decimal | None = None
    filled_qty: Decimal | None = None
    side: str | None = None
    time_in_force: str | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    expired_at: datetime | None = None
    canceled_at: datetime | None = None
    failed_at: datetime | None = None
    replaced_at: datetime | None = None
    avg_fill_price: Decimal | None = None


class QuoteModel(BaseModel):
    """Quote information model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    symbol: str
    bid: Decimal
    ask: Decimal
    bid_size: int | None = None
    ask_size: int | None = None
    timestamp: datetime | None = None


class BarModel(BaseModel):
    """Historical bar model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    vwap: Decimal | None = None


class OrderExecutionModel(BaseModel):
    """Order execution result model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    success: bool
    order_id: str
    status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]
    filled_qty: Decimal
    avg_fill_price: Decimal | None = None
    submitted_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class WebSocketResultModel(BaseModel):
    """WebSocket operation result model."""
    
    model_config = ConfigDict(frozen=True, strict=True)

    status: Literal["connected", "disconnected", "error", "timeout"]
    completed_orders: list[str] = []
    pending_orders: list[str] = []
    message: str | None = None
    error: str | None = None