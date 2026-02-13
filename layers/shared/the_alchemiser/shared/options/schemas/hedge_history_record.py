"""Business Unit: shared | Status: current.

Hedge history record data transfer object.

Represents an audit trail entry for hedge actions.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...constants import CONTRACT_VERSION
from ...utils.timezone_utils import ensure_timezone_aware


class HedgeAction(StrEnum):
    """Hedge action enumeration for audit trail."""

    HEDGE_OPENED = "hedge_opened"  # New hedge position created
    HEDGE_ROLLED = "hedge_rolled"  # Position rolled to new expiry
    HEDGE_CLOSED = "hedge_closed"  # Position closed (profit-taking or expiry)
    HEDGE_EXPIRED = "hedge_expired"  # Position expired worthless
    ROLL_TRIGGERED = "roll_triggered"  # Roll event triggered (but not yet executed)
    EVALUATION_COMPLETED = "evaluation_completed"  # Hedge evaluation run
    # Assignment handling actions (FR-8)
    ASSIGNMENT_DETECTED = "assignment_detected"  # Short leg delta > threshold
    ASSIGNMENT_EXERCISED = "assignment_exercised"  # Long leg exercised to offset
    ASSIGNMENT_CLOSED = "assignment_closed"  # Both legs closed at market
    ASSIGNMENT_UNRESOLVED = "assignment_unresolved"  # Remediation failed/delayed
    # Emergency actions
    EMERGENCY_UNWIND = "emergency_unwind"  # Emergency position liquidation


class HedgeHistoryRecord(BaseModel):
    """DTO for hedge history audit trail record.

    Tracks all hedge actions for compliance and audit purposes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    __schema_version__: str = CONTRACT_VERSION

    # Identification
    account_id: str = Field(..., min_length=1, description="Account ID")
    timestamp: datetime = Field(..., description="Action timestamp")
    action: HedgeAction = Field(..., description="Action type")

    # Hedge details
    hedge_id: str = Field(..., min_length=1, description="Hedge identifier")
    option_symbol: str = Field(default="", description="OCC option symbol")
    underlying_symbol: str = Field(..., min_length=1, description="Underlying ETF symbol")
    contracts: int = Field(default=0, ge=0, description="Number of contracts")
    premium: Decimal = Field(default=Decimal("0"), ge=0, description="Premium amount")

    # Action-specific metadata
    details: dict[str, Any] = Field(default_factory=dict, description="Action-specific metadata")

    # Tracing
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracing")

    @field_validator("underlying_symbol")
    @classmethod
    def normalize_underlying(cls, v: str) -> str:
        """Normalize underlying symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_tz_aware(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware."""
        return ensure_timezone_aware(v)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = self.model_dump()

        # Convert timestamp
        data["timestamp"] = self.timestamp.isoformat()

        # Convert action enum
        data["action"] = self.action.value

        # Convert Decimal
        data["premium"] = str(self.premium)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HedgeHistoryRecord:
        """Create from dictionary."""
        # Convert timestamp
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert action enum
        if isinstance(data.get("action"), str):
            data["action"] = HedgeAction(data["action"])

        # Convert Decimal
        if data.get("premium") is not None and isinstance(data["premium"], str):
            data["premium"] = Decimal(data["premium"])

        return cls(**data)
