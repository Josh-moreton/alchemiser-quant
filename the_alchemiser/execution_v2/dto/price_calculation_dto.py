#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

DTOs for execution-related data transfer.

Provides typed DTOs for execution results, price calculations, and order metadata
to replace dict[str, Any] usage in smart execution strategies.

Part of the typing architecture enforcement initiative.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PriceCalculationMetadataDTO(BaseModel):
    """DTO for price calculation metadata from smart execution strategies."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    spread_pct: float = Field(..., ge=0, description="Spread percentage")
    bid_ask_ratio: float = Field(..., ge=0, description="Bid to ask ratio")
    volume_ratio: float = Field(..., ge=0, description="Volume ratio")
    bid_volume: float = Field(..., ge=0, description="Bid volume")
    ask_volume: float = Field(..., ge=0, description="Ask volume")
    calculation_method: str = Field(..., min_length=1, description="Calculation method used")


class PriceCalculationResultDTO(BaseModel):
    """DTO for price calculation results from smart execution strategies."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    anchor_price: Decimal = Field(..., gt=0, description="Calculated anchor price")
    metadata: PriceCalculationMetadataDTO = Field(..., description="Calculation metadata")