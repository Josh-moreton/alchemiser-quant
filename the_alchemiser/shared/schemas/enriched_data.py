#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Order and position enrichment schemas for The Alchemiser Trading System.

This module contains schemas for enriched order and position data views,
providing a unified pattern for exposing raw API data, domain objects, and
computed summaries through a consistent interface.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Schema versioning for safe evolution
- Typed nested models for raw, domain, and summary data
- Immutable DTOs (frozen=True)
- Type safety for financial values (Decimal)
- Result-oriented response patterns

The enrichment pattern provides three views of the same data:
- raw: Unprocessed data from external APIs (e.g., Alpaca)
- domain: Domain objects with business logic applied
- summary: Computed metrics and human-readable summaries
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.schemas.base import Result


# Nested data models for type safety

class RawOrderData(BaseModel):
    """Raw order data from Alpaca API."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    id: str = Field(description="Order ID from broker")
    symbol: str = Field(description="Trading symbol")
    # Allow any additional fields from Alpaca API
    # This model can be extended as needed based on actual usage


class DomainOrderData(BaseModel):
    """Domain-specific order representation."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(description="Trading symbol")
    side: Literal["buy", "sell"] = Field(description="Order side")
    # Allow any additional domain fields
    # This model can be extended based on domain requirements


class OrderSummaryData(BaseModel):
    """Summary of order execution details."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    status: str = Field(description="Order execution status")
    qty: Decimal = Field(ge=0, description="Order quantity")
    # Allow any additional summary fields


class RawPositionData(BaseModel):
    """Raw position data from Alpaca API."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(description="Trading symbol")
    qty: Decimal = Field(description="Position quantity")
    # Allow any additional fields from Alpaca API


class PositionSummaryData(BaseModel):
    """Summary of position details."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(description="Trading symbol")
    qty: Decimal = Field(ge=0, description="Position quantity")
    market_value: Decimal = Field(description="Current market value")
    unrealized_pl: Decimal = Field(description="Unrealized profit/loss")
    # Allow any additional summary fields


class EnrichedOrderView(BaseModel):
    """DTO for enriched order data with domain mapping.

    Provides three views of order data:
    - raw: Unprocessed data from broker API
    - domain: Domain model representation
    - summary: Computed execution summary
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    raw: RawOrderData = Field(description="Raw broker API data")
    domain: DomainOrderData = Field(description="Domain order representation")
    summary: OrderSummaryData = Field(description="Order execution summary")


class OpenOrdersView(Result):
    """DTO for open orders list response.

    Wraps a list of enriched order views with success/error status.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    orders: list[EnrichedOrderView] = Field(
        description="List of enriched order views. Empty list if no open orders."
    )
    symbol_filter: str | None = Field(
        default=None,
        max_length=10,
        description="Optional symbol filter applied to results. None if no filter.",
    )


class EnrichedPositionView(BaseModel):
    """DTO for enriched position data with domain mapping.

    Provides two views of position data:
    - raw: Unprocessed data from broker API
    - summary: Computed position summary with P&L
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    raw: RawPositionData = Field(description="Raw broker API data")
    summary: PositionSummaryData = Field(description="Position summary with P&L")


class EnrichedPositionsView(Result):
    """DTO for enriched positions list response.

    Wraps a list of enriched position views with success/error status.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    positions: list[EnrichedPositionView] = Field(
        description="List of enriched position views. Empty list if no positions."
    )


# Backward compatibility aliases - will be removed in future version
EnrichedOrderDTO = EnrichedOrderView
OpenOrdersDTO = OpenOrdersView
EnrichedPositionDTO = EnrichedPositionView
EnrichedPositionsDTO = EnrichedPositionsView
