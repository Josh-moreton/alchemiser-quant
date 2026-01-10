"""Business Unit: shared | Status: current.

Trade message schema for per-trade parallel execution.

This module defines the TradeMessage DTO used for SQS Standard queue messages
in the per-trade execution architecture. Each message represents a single
trade to be executed by an Execution Lambda invocation.

Architecture (Two-Phase Parallel Execution):
- Portfolio Lambda enqueues SELL trades first (BUY trades stored in DynamoDB)
- Multiple Execution Lambdas (up to 10 concurrent) process SELLs in parallel
- When all SELLs complete, the last Lambda enqueues BUY trades
- BUY trades execute in parallel via fresh Lambda invocations

Note: Despite env var name (EXECUTION_FIFO_QUEUE_URL), we use a Standard queue.
The sequence_number field is preserved for debugging/ordering visibility but
does not provide FIFO guarantees - ordering is controlled by enqueue timing.

The message includes:
- Run/trade identifiers for tracking and aggregation
- Trade details (symbol, action, amounts)
- Phase field (SELL or BUY) for two-phase execution
- Context fields for validation and correlation
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..constants import CONTRACT_VERSION
from ..utils.timezone_utils import ensure_timezone_aware


class TradeMessage(BaseModel):
    """SQS Standard queue message payload for per-trade parallel execution.

    Each TradeMessage represents a single trade extracted from a RebalancePlan.
    Portfolio Lambda decomposes plans into individual TradeMessages and enqueues
    them to the SQS Standard queue. Multiple Lambdas process trades in parallel.

    Two-Phase Ordering (via enqueue timing, NOT FIFO):
    - Portfolio Lambda enqueues only SELL trades initially
    - BUY trades are stored in DynamoDB until all SELLs complete
    - When last SELL completes, Execution Lambda enqueues BUY trades
    - This guarantees all sells complete before buys start

    The sequence_number field is preserved for debugging/visibility but does
    not provide ordering guarantees with a Standard queue.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    __schema_version__: str = CONTRACT_VERSION
    schema_version: str = Field(default=CONTRACT_VERSION, description="Message schema version")

    # ========== Execution identifiers ==========
    run_id: str = Field(..., min_length=1, description="Unique execution run identifier (UUID)")
    trade_id: str = Field(..., min_length=1, description="Unique trade identifier (UUID)")
    plan_id: str = Field(..., min_length=1, description="Source RebalancePlan identifier")
    correlation_id: str = Field(..., min_length=1, description="Workflow correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    strategy_id: str | None = Field(
        default=None, description="Strategy identifier for attribution tracking"
    )

    # ========== Trade content (from RebalancePlanItem) ==========
    symbol: str = Field(..., min_length=1, max_length=50, description="Trading symbol (supports extended notation like EQUITIES::SYMBOL//USD)")
    action: str = Field(..., description="Trading action (BUY or SELL)")
    trade_amount: Decimal = Field(
        ..., description="Dollar amount to trade (positive=buy, negative=sell)"
    )
    current_weight: Decimal = Field(..., ge=0, le=1, description="Current portfolio weight (0-1)")
    target_weight: Decimal = Field(..., ge=0, le=1, description="Target portfolio weight (0-1)")
    target_value: Decimal = Field(..., ge=0, description="Target dollar value")
    current_value: Decimal = Field(..., ge=0, description="Current dollar value")
    priority: int = Field(..., ge=1, le=5, description="Execution priority (1=highest)")

    # ========== Execution control ==========
    phase: str = Field(..., description="Execution phase (SELL or BUY)")
    sequence_number: int = Field(
        ...,
        ge=1000,
        le=2999,
        description="FIFO sequence number (1000-1999=SELL, 2000-2999=BUY)",
    )
    is_complete_exit: bool = Field(
        default=False, description="Whether this trade is a complete position exit"
    )
    is_full_liquidation: bool = Field(
        default=False, description="Whether this is a full position liquidation (target_weight=0)"
    )

    # ========== Optional pre-computed values ==========
    shares: Decimal | None = Field(
        default=None, ge=0, description="Pre-computed shares to trade (optional)"
    )
    estimated_price: Decimal | None = Field(
        default=None, ge=0, description="Estimated price at plan time (optional)"
    )
    current_position: Decimal | None = Field(
        default=None, ge=0, description="Current position quantity (optional)"
    )
    target_position: Decimal | None = Field(
        default=None, ge=0, description="Target position quantity (optional)"
    )

    # ========== Run context ==========
    total_portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value for run")
    total_run_trades: int = Field(..., ge=1, description="Total number of trades in this run")
    run_timestamp: datetime = Field(..., description="When the run started")

    # ========== Metadata ==========
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata (strategy attribution, etc.)"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action is BUY or SELL."""
        action_upper = v.strip().upper()
        if action_upper not in {"BUY", "SELL"}:
            raise ValueError(f"Action must be BUY or SELL, got {action_upper}")
        return action_upper

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        """Validate phase is SELL or BUY."""
        phase_upper = v.strip().upper()
        if phase_upper not in {"SELL", "BUY"}:
            raise ValueError(f"Phase must be SELL or BUY, got {phase_upper}")
        return phase_upper

    @field_validator("run_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("run_timestamp cannot be None")
        return result

    def to_sqs_message_body(self) -> str:
        """Convert to JSON string for SQS message body.

        Returns:
            JSON string representation of the message.

        """
        import json

        data = self.model_dump(mode="json")
        # Convert Decimal fields to string for JSON serialization
        decimal_fields = [
            "trade_amount",
            "current_weight",
            "target_weight",
            "target_value",
            "current_value",
            "total_portfolio_value",
            "shares",
            "estimated_price",
            "current_position",
            "target_position",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])
        return json.dumps(data)

    @classmethod
    def from_sqs_message_body(cls, body: str) -> TradeMessage:
        """Create TradeMessage from SQS message body.

        Args:
            body: JSON string from SQS message body.

        Returns:
            TradeMessage instance.

        """
        import json

        data = json.loads(body)

        # Convert string Decimal fields back to Decimal
        decimal_fields = [
            "trade_amount",
            "current_weight",
            "target_weight",
            "target_value",
            "current_value",
            "total_portfolio_value",
            "shares",
            "estimated_price",
            "current_position",
            "target_position",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = Decimal(str(data[field_name]))

        # Convert ISO timestamp to datetime
        if data.get("run_timestamp") is not None:
            ts = data["run_timestamp"]
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                data["run_timestamp"] = dt

        return cls(**data)

    @classmethod
    def compute_sequence_number(cls, action: str, priority: int) -> int:
        """Compute sequence number ensuring sells before buys.

        Args:
            action: Trade action (BUY or SELL).
            priority: Execution priority (1-5, 1=highest).

        Returns:
            Sequence number: 1000-1999 for SELL, 2000-2999 for BUY.

        """
        if action.upper() == "SELL":
            return 1000 + priority
        if action.upper() == "BUY":
            return 2000 + priority
        raise ValueError(f"Invalid action for sequence: {action}")
