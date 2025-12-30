"""Business Unit: shared; Status: current.

Asset Information DTO.

Defines the AssetInfo for standardized asset metadata representation
including fractionability support as required for non-fractionable asset handling.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetInfo(BaseModel):
    """DTO for asset information including trading characteristics.

    This DTO provides standardized asset metadata with strict typing
    and validation, particularly for fractionability support.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    symbol: str = Field(..., min_length=1, description="Asset symbol (e.g., 'AAPL', 'EDZ')")
    name: str | None = Field(default=None, description="Full asset name")
    exchange: str | None = Field(default=None, description="Exchange where asset is traded")
    asset_class: str | None = Field(default=None, description="Asset class (e.g., 'us_equity')")
    tradable: bool = Field(default=True, description="Whether asset is tradable")
    fractionable: bool = Field(..., description="Whether asset supports fractional shares")
    marginable: bool | None = Field(
        default=None, description="Whether asset can be traded on margin"
    )
    shortable: bool | None = Field(default=None, description="Whether asset can be sold short")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()
