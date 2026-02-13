"""Business Unit: shared | Status: current.

Option contract data transfer object.

Represents an option contract with its Greeks and market data,
used for option chain queries and selection.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...constants import CONTRACT_VERSION


class OptionType(StrEnum):
    """Option type enumeration."""

    PUT = "put"
    CALL = "call"


class OptionContract(BaseModel):
    """DTO for an option contract.

    Represents a single option contract with pricing, Greeks, and
    liquidity metrics for selection and execution.

    OCC Symbol Format:
        - Standard: {UNDERLYING}{YYMMDD}{P/C}{STRIKE*1000}
        - Example: SPY250117P00400000 = SPY Jan 17, 2025 $400 Put
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    __schema_version__: str = CONTRACT_VERSION

    # Contract identification
    symbol: str = Field(
        ...,
        min_length=10,
        max_length=30,
        description="OCC option symbol (e.g., SPY250117P00400000)",
    )
    underlying_symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Underlying equity symbol (e.g., SPY)",
    )
    option_type: OptionType = Field(..., description="Option type (put or call)")
    strike_price: Decimal = Field(..., gt=0, description="Strike price")
    expiration_date: date = Field(..., description="Expiration date")

    # Market data
    bid_price: Decimal | None = Field(default=None, ge=0, description="Current bid")
    ask_price: Decimal | None = Field(default=None, ge=0, description="Current ask")
    last_price: Decimal | None = Field(default=None, ge=0, description="Last trade price")
    volume: int = Field(default=0, ge=0, description="Daily trading volume")
    open_interest: int = Field(default=0, ge=0, description="Open interest")

    # Greeks (optional - may not be available for all contracts)
    delta: Decimal | None = Field(
        default=None,
        ge=Decimal("-1"),
        le=Decimal("1"),
        description="Delta (-1 to 1)",
    )
    gamma: Decimal | None = Field(default=None, ge=0, description="Gamma")
    theta: Decimal | None = Field(default=None, description="Theta (time decay)")
    vega: Decimal | None = Field(default=None, ge=0, description="Vega (IV sensitivity)")
    implied_volatility: Decimal | None = Field(
        default=None,
        ge=0,
        description="Implied volatility (0-5 typical)",
    )

    @field_validator("underlying_symbol")
    @classmethod
    def normalize_underlying(cls, v: str) -> str:
        """Normalize underlying symbol to uppercase."""
        return v.strip().upper()

    @property
    def mid_price(self) -> Decimal | None:
        """Calculate mid-price from bid/ask.

        Returns:
            Mid-price if both bid and ask available, None otherwise.

        """
        if self.bid_price is not None and self.ask_price is not None:
            return (self.bid_price + self.ask_price) / 2
        return None

    @property
    def spread(self) -> Decimal | None:
        """Calculate bid-ask spread.

        Returns:
            Spread in dollars if both bid and ask available, None otherwise.

        """
        if self.bid_price is not None and self.ask_price is not None:
            return self.ask_price - self.bid_price
        return None

    @property
    def spread_pct(self) -> Decimal | None:
        """Calculate bid-ask spread as percentage of mid.

        Returns:
            Spread as percentage (e.g., 0.05 = 5%) if calculable, None otherwise.

        """
        mid = self.mid_price
        spread = self.spread
        if mid is not None and spread is not None and mid > 0:
            return spread / mid
        return None

    @property
    def days_to_expiry(self) -> int:
        """Calculate days until expiration.

        Returns:
            Number of calendar days until expiration.

        """
        return (self.expiration_date - datetime.now(UTC).date()).days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with properly serialized values.

        """
        data = self.model_dump()

        # Convert date to ISO string
        data["expiration_date"] = self.expiration_date.isoformat()

        # Convert option_type enum to string
        data["option_type"] = self.option_type.value

        # Convert Decimal fields to strings
        decimal_fields = [
            "strike_price",
            "bid_price",
            "ask_price",
            "last_price",
            "delta",
            "gamma",
            "theta",
            "vega",
            "implied_volatility",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OptionContract:
        """Create from dictionary.

        Args:
            data: Dictionary containing contract data

        Returns:
            OptionContract instance

        """
        # Convert date string to date
        if isinstance(data.get("expiration_date"), str):
            data["expiration_date"] = date.fromisoformat(data["expiration_date"])

        # Convert option_type string to enum
        if isinstance(data.get("option_type"), str):
            data["option_type"] = OptionType(data["option_type"])

        # Convert decimal strings to Decimal
        decimal_fields = [
            "strike_price",
            "bid_price",
            "ask_price",
            "last_price",
            "delta",
            "gamma",
            "theta",
            "vega",
            "implied_volatility",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None and isinstance(data[field_name], str):
                data[field_name] = Decimal(data[field_name])

        return cls(**data)
