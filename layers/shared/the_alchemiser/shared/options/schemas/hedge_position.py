"""Business Unit: shared | Status: current.

Hedge position data transfer object.

Represents an active options hedge position with roll state tracking.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...constants import CONTRACT_VERSION
from ...utils.timezone_utils import ensure_timezone_aware
from .option_contract import OptionType


class RollState(str, Enum):
    """Hedge roll state enumeration."""

    HOLDING = "holding"  # Hedge active, no action needed
    ROLL_DUE = "roll_due"  # DTE < threshold, needs rolling
    ROLLING = "rolling"  # In process of closing old / opening new
    PROFIT_TAKING = "profit_taking"  # Delta moved high, taking partial profit
    CLOSED = "closed"  # Position closed


class HedgePositionState(str, Enum):
    """Hedge position state enumeration."""

    ACTIVE = "active"
    ROLLING = "rolling"
    CLOSED = "closed"
    EXPIRED = "expired"


class HedgePosition(BaseModel):
    """DTO for an active hedge position.

    Tracks the state of a protective options position including
    entry details, current valuation, and roll schedule.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    __schema_version__: str = CONTRACT_VERSION

    # Position identification
    hedge_id: str = Field(..., min_length=1, description="Unique hedge identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracing")

    # Contract details
    option_symbol: str = Field(..., min_length=10, description="OCC option symbol")
    underlying_symbol: str = Field(..., min_length=1, description="Underlying ETF symbol")
    option_type: OptionType = Field(..., description="Option type (put or call)")
    strike_price: Decimal = Field(..., gt=0, description="Strike price")
    expiration_date: date = Field(..., description="Expiration date")
    contracts: int = Field(..., gt=0, description="Number of contracts held")

    # Entry details
    entry_price: Decimal = Field(..., ge=0, description="Average entry price per contract")
    entry_date: datetime = Field(..., description="Position entry date")
    entry_delta: Decimal = Field(
        ...,
        ge=Decimal("-1"),
        le=Decimal("1"),
        description="Delta at entry",
    )
    total_premium_paid: Decimal = Field(
        ...,
        ge=0,
        description="Total premium paid (entry_price * contracts * 100)",
    )

    # Current valuation
    current_price: Decimal | None = Field(default=None, ge=0, description="Current option price")
    current_delta: Decimal | None = Field(
        default=None,
        ge=Decimal("-1"),
        le=Decimal("1"),
        description="Current delta",
    )
    current_value: Decimal | None = Field(
        default=None,
        ge=0,
        description="Current position value",
    )
    unrealized_pnl: Decimal | None = Field(default=None, description="Unrealized P&L")

    # State tracking
    state: HedgePositionState = Field(
        default=HedgePositionState.ACTIVE,
        description="Position state",
    )
    roll_state: RollState = Field(default=RollState.HOLDING, description="Roll state")
    last_updated: datetime | None = Field(default=None, description="Last update timestamp")

    # Hedge metadata
    hedge_template: str = Field(default="tail_first", description="Hedge template used")
    nav_at_entry: Decimal | None = Field(
        default=None,
        ge=0,
        description="Portfolio NAV at hedge entry",
    )
    nav_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=Decimal("1"),
        description="Premium as percentage of NAV at entry",
    )

    @field_validator("underlying_symbol")
    @classmethod
    def normalize_underlying(cls, v: str) -> str:
        """Normalize underlying symbol to uppercase."""
        return v.strip().upper()

    @field_validator("entry_date", "last_updated", mode="before")
    @classmethod
    def ensure_tz_aware(cls, v: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)

    @property
    def days_to_expiry(self) -> int:
        """Calculate days until expiration."""
        return (self.expiration_date - date.today()).days

    def should_roll(self, roll_trigger_dte: int = 45) -> RollState:
        """Determine if hedge should be rolled.

        Args:
            roll_trigger_dte: DTE threshold below which to trigger roll

        Returns:
            RollState indicating recommended action

        """
        dte = self.days_to_expiry

        # Roll due if DTE below threshold
        if dte < roll_trigger_dte:
            return RollState.ROLL_DUE

        # Profit taking if delta moved significantly (put went deep ITM)
        if self.current_delta is not None:
            abs_delta = abs(self.current_delta)
            # If 15-delta put is now >35-delta, consider profit taking
            if abs_delta > Decimal("0.35") and abs(self.entry_delta) < Decimal("0.20"):
                return RollState.PROFIT_TAKING

        return RollState.HOLDING

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = self.model_dump()

        # Convert dates
        data["expiration_date"] = self.expiration_date.isoformat()
        data["entry_date"] = self.entry_date.isoformat()
        if self.last_updated:
            data["last_updated"] = self.last_updated.isoformat()

        # Convert enums
        data["option_type"] = self.option_type.value
        data["state"] = self.state.value
        data["roll_state"] = self.roll_state.value

        # Convert Decimals
        decimal_fields = [
            "strike_price",
            "entry_price",
            "entry_delta",
            "total_premium_paid",
            "current_price",
            "current_delta",
            "current_value",
            "unrealized_pnl",
            "nav_at_entry",
            "nav_percentage",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HedgePosition:
        """Create from dictionary."""
        # Convert dates
        if isinstance(data.get("expiration_date"), str):
            data["expiration_date"] = date.fromisoformat(data["expiration_date"])
        if isinstance(data.get("entry_date"), str):
            data["entry_date"] = datetime.fromisoformat(data["entry_date"])
        if isinstance(data.get("last_updated"), str):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])

        # Convert enums
        if isinstance(data.get("option_type"), str):
            data["option_type"] = OptionType(data["option_type"])
        if isinstance(data.get("state"), str):
            data["state"] = HedgePositionState(data["state"])
        if isinstance(data.get("roll_state"), str):
            data["roll_state"] = RollState(data["roll_state"])

        # Convert Decimals
        decimal_fields = [
            "strike_price",
            "entry_price",
            "entry_delta",
            "total_premium_paid",
            "current_price",
            "current_delta",
            "current_value",
            "unrealized_pnl",
            "nav_at_entry",
            "nav_percentage",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None and isinstance(data[field_name], str):
                data[field_name] = Decimal(data[field_name])

        return cls(**data)
