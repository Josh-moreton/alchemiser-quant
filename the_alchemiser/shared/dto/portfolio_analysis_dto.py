#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio analysis data transfer objects for orchestration module.

Provides typed DTOs for portfolio analysis results that replace dict[str, Any]
usage in orchestration business logic methods.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AccountInfoDTO(BaseModel):
    """DTO for account information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    cash: Decimal = Field(..., ge=0, description="Available cash")
    buying_power: Decimal = Field(..., ge=0, description="Buying power")
    equity: Decimal = Field(..., ge=0, description="Total equity")


class PositionDataDTO(BaseModel):
    """DTO for position data in comprehensive account view."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    qty: Decimal = Field(..., description="Position quantity")
    market_value: Decimal = Field(..., description="Current market value")
    avg_entry_price: Decimal = Field(..., ge=0, description="Average entry price")
    current_price: Decimal = Field(..., ge=0, description="Current price")
    unrealized_pl: Decimal = Field(..., description="Unrealized P&L")
    unrealized_plpc: Decimal = Field(..., description="Unrealized P&L percentage")


class OrderDataDTO(BaseModel):
    """DTO for order data in comprehensive account view."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    id: str = Field(..., min_length=1, description="Order ID")
    symbol: str = Field(..., min_length=1, description="Symbol")
    type: str = Field(..., min_length=1, description="Order type")
    qty: Decimal = Field(..., gt=0, description="Order quantity")
    limit_price: Decimal | None = Field(default=None, description="Limit price if applicable")
    status: str = Field(..., min_length=1, description="Order status")
    created_at: str = Field(..., min_length=1, description="Creation timestamp")


class PortfolioAnalysisDTO(BaseModel):
    """DTO for portfolio analysis results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    snapshot: Any = Field(..., description="Portfolio snapshot data")
    analysis_timestamp: datetime | None = Field(
        default=None, description="When analysis was performed"
    )
    position_count: int = Field(..., ge=0, description="Number of positions")
    total_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    correlation_id: str | None = Field(
        default=None, description="Correlation ID for tracking"
    )

    @classmethod
    def from_snapshot(
        cls,
        snapshot: Any,
        correlation_id: str | None = None,
    ) -> PortfolioAnalysisDTO:
        """Create DTO from portfolio snapshot.
        
        Args:
            snapshot: Portfolio snapshot object
            correlation_id: Optional correlation ID
            
        Returns:
            PortfolioAnalysisDTO instance
        """
        return cls(
            snapshot=snapshot,
            analysis_timestamp=getattr(snapshot, "timestamp", None),
            position_count=len(getattr(snapshot, "positions", [])),
            total_value=Decimal(str(getattr(snapshot, "total_value", 0))),
            correlation_id=correlation_id,
        )


class ComprehensiveAccountDataDTO(BaseModel):
    """DTO for comprehensive account data including positions and orders."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    account_info: AccountInfoDTO | None = Field(
        default=None, description="Account information"
    )
    current_positions: dict[str, PositionDataDTO] = Field(
        default_factory=dict, description="Current positions by symbol"
    )
    open_orders: list[OrderDataDTO] = Field(
        default_factory=list, description="Open orders"
    )
    retrieval_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="When data was retrieved"
    )