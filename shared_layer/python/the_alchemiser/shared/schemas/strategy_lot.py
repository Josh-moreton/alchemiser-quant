"""Business Unit: shared | Status: current.

Strategy lot schemas for per-strategy position tracking and P&L calculation.

This module provides DTOs for tracking individual strategy "lots" - entries into
positions that can be independently tracked and matched to exits using FIFO.
Enables accurate per-strategy P&L calculation even when multiple strategies
hold the same symbol simultaneously.

Key Concepts:
- A "lot" represents a single strategy's entry into a position
- Each lot tracks its own entry price, quantity, and remaining shares
- Exits are matched to lots using FIFO within each strategy
- Partial exits create LotExitRecords while keeping the lot open
- Lots are marked closed when remaining_qty reaches zero
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from ..constants import CONTRACT_VERSION
from ..utils.timezone_utils import ensure_timezone_aware


class LotExitRecord(BaseModel):
    """Records a partial or full exit against a strategy lot.

    Each exit record captures the details of closing some or all of a lot,
    including the P&L calculation for that specific exit.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Exit identification
    exit_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique exit record identifier",
    )
    exit_order_id: str = Field(..., min_length=1, description="Broker order ID for the exit")

    # Exit details
    exit_timestamp: datetime = Field(..., description="Time of exit execution")
    exit_qty: Decimal = Field(..., gt=0, description="Quantity exited in this trade")
    exit_price: Decimal = Field(..., gt=0, description="Exit fill price")

    # P&L for this exit (calculated: (exit_price - entry_price) * exit_qty)
    realized_pnl: Decimal = Field(..., description="Realized P&L for this exit")

    @field_validator("exit_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure exit timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("exit_timestamp cannot be None")
        return result


class StrategyLot(BaseModel):
    """Represents a single strategy's entry into a position.

    A lot is created when a strategy contributes to a BUY order. The lot tracks:
    - Entry details (price, qty, timestamp)
    - Current state (remaining qty, open/closed)
    - Exit records (partial/full exits with P&L)

    Multiple strategies can hold lots for the same symbol simultaneously.
    Each strategy's lots are matched to exits independently using FIFO.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=False,  # Mutable - remaining_qty and exits are updated
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Lot identification
    lot_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique lot identifier",
    )
    strategy_name: str = Field(..., min_length=1, description="Strategy that owns this lot")
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Trading symbol (supports extended notation like EQUITIES::SYMBOL//USD)",
    )

    # Entry details
    entry_order_id: str = Field(..., min_length=1, description="Broker order ID for entry")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for traceability")
    entry_timestamp: datetime = Field(..., description="Time of entry execution")
    entry_qty: Decimal = Field(..., gt=0, description="Original quantity entered")
    entry_price: Decimal = Field(..., gt=0, description="Entry fill price")

    # Computed entry cost basis
    @computed_field  # type: ignore[prop-decorator]
    @property
    def entry_cost_basis(self) -> Decimal:
        """Calculate entry cost basis (entry_qty * entry_price)."""
        return self.entry_qty * self.entry_price

    # Current state (mutable)
    remaining_qty: Decimal = Field(..., ge=0, description="Quantity still open")
    is_open: bool = Field(default=True, description="True if remaining_qty > 0")

    # Exit tracking
    exit_records: list[LotExitRecord] = Field(
        default_factory=list,
        description="List of partial/full exits against this lot",
    )
    fully_closed_at: datetime | None = Field(
        default=None,
        description="Timestamp when lot was fully closed",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def realized_pnl(self) -> Decimal:
        """Calculate total realized P&L from all exits."""
        return sum((exit.realized_pnl for exit in self.exit_records), Decimal("0"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_exited_qty(self) -> Decimal:
        """Calculate total quantity exited across all exit records."""
        return sum((exit.exit_qty for exit in self.exit_records), Decimal("0"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avg_exit_price(self) -> Decimal | None:
        """Calculate weighted average exit price across all exits."""
        if not self.exit_records:
            return None
        total_value = sum(
            (exit.exit_qty * exit.exit_price for exit in self.exit_records), Decimal("0")
        )
        total_qty = self.total_exited_qty
        if total_qty == 0:
            return None
        return total_value / total_qty

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hold_duration(self) -> timedelta | None:
        """Calculate hold duration if lot is closed."""
        if self.fully_closed_at is None:
            return None
        return self.fully_closed_at - self.entry_timestamp

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("entry_timestamp")
    @classmethod
    def ensure_timezone_aware_entry(cls, v: datetime) -> datetime:
        """Ensure entry timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("entry_timestamp cannot be None")
        return result

    @field_validator("fully_closed_at")
    @classmethod
    def ensure_timezone_aware_closed(cls, v: datetime | None) -> datetime | None:
        """Ensure closed timestamp is timezone-aware if provided."""
        if v is None:
            return None
        return ensure_timezone_aware(v)

    def record_exit(
        self,
        exit_order_id: str,
        exit_timestamp: datetime,
        exit_qty: Decimal,
        exit_price: Decimal,
    ) -> LotExitRecord:
        """Record a partial or full exit against this lot.

        Updates remaining_qty and creates a LotExitRecord with P&L calculation.
        Marks lot as closed if remaining_qty reaches zero.

        Args:
            exit_order_id: Broker order ID for the exit
            exit_timestamp: Time of exit execution
            exit_qty: Quantity to exit (must not exceed remaining_qty)
            exit_price: Exit fill price

        Returns:
            LotExitRecord with P&L details

        Raises:
            ValueError: If exit_qty exceeds remaining_qty

        """
        if exit_qty > self.remaining_qty:
            raise ValueError(
                f"Exit qty {exit_qty} exceeds remaining qty {self.remaining_qty} for lot {self.lot_id}"
            )

        # Calculate P&L for this exit
        pnl = (exit_price - self.entry_price) * exit_qty

        # Create exit record
        exit_record = LotExitRecord(
            exit_order_id=exit_order_id,
            exit_timestamp=exit_timestamp,
            exit_qty=exit_qty,
            exit_price=exit_price,
            realized_pnl=pnl,
        )

        # Update lot state
        self.exit_records.append(exit_record)
        self.remaining_qty -= exit_qty

        # Mark as closed if fully exited
        if self.remaining_qty == Decimal("0"):
            self.is_open = False
            self.fully_closed_at = exit_timestamp

        return exit_record

    def to_dynamodb_item(self) -> dict[str, Any]:
        """Convert to DynamoDB item format.

        Returns:
            Dictionary suitable for DynamoDB put_item

        """
        item = {
            "PK": f"LOT#{self.lot_id}",
            "SK": "METADATA",
            "EntityType": "STRATEGY_LOT",
            "lot_id": self.lot_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "entry_order_id": self.entry_order_id,
            "correlation_id": self.correlation_id,
            "entry_timestamp": self.entry_timestamp.isoformat(),
            "entry_qty": str(self.entry_qty),
            "entry_price": str(self.entry_price),
            "entry_cost_basis": str(self.entry_cost_basis),
            "remaining_qty": str(self.remaining_qty),
            "is_open": self.is_open,
            "exit_records": [
                {
                    "exit_id": er.exit_id,
                    "exit_order_id": er.exit_order_id,
                    "exit_timestamp": er.exit_timestamp.isoformat(),
                    "exit_qty": str(er.exit_qty),
                    "exit_price": str(er.exit_price),
                    "realized_pnl": str(er.realized_pnl),
                }
                for er in self.exit_records
            ],
            "realized_pnl": str(self.realized_pnl),
            "created_at": datetime.now(UTC).isoformat(),
            # GSI5 keys for querying lots by strategy
            "GSI5PK": f"STRATEGY_LOTS#{self.strategy_name}",
            "GSI5SK": f"{'OPEN' if self.is_open else 'CLOSED'}#{self.symbol}#{self.entry_timestamp.isoformat()}",
        }

        if self.fully_closed_at:
            item["fully_closed_at"] = self.fully_closed_at.isoformat()

        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> StrategyLot:
        """Create StrategyLot from DynamoDB item.

        Args:
            item: DynamoDB item dictionary

        Returns:
            StrategyLot instance

        """
        exit_records = [
            LotExitRecord(
                exit_id=er["exit_id"],
                exit_order_id=er["exit_order_id"],
                exit_timestamp=datetime.fromisoformat(er["exit_timestamp"]),
                exit_qty=Decimal(er["exit_qty"]),
                exit_price=Decimal(er["exit_price"]),
                realized_pnl=Decimal(er["realized_pnl"]),
            )
            for er in item.get("exit_records", [])
        ]

        fully_closed_at = None
        if item.get("fully_closed_at"):
            fully_closed_at = datetime.fromisoformat(item["fully_closed_at"])

        return cls(
            lot_id=item["lot_id"],
            strategy_name=item["strategy_name"],
            symbol=item["symbol"],
            entry_order_id=item["entry_order_id"],
            correlation_id=item["correlation_id"],
            entry_timestamp=datetime.fromisoformat(item["entry_timestamp"]),
            entry_qty=Decimal(item["entry_qty"]),
            entry_price=Decimal(item["entry_price"]),
            remaining_qty=Decimal(item["remaining_qty"]),
            is_open=item["is_open"],
            exit_records=exit_records,
            fully_closed_at=fully_closed_at,
        )


class StrategyLotSummary(BaseModel):
    """Summary of a closed lot for reporting purposes.

    Provides a flattened view of a closed lot suitable for CSV export
    with all key metrics pre-calculated.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
    )

    # Identification
    lot_id: str
    strategy_name: str
    symbol: str
    correlation_id: str

    # Entry details
    entry_timestamp: datetime
    entry_qty: Decimal
    entry_price: Decimal
    entry_cost_basis: Decimal

    # Exit details
    exit_timestamp: datetime  # When fully closed
    avg_exit_price: Decimal
    exit_value: Decimal  # entry_qty * avg_exit_price

    # P&L
    realized_pnl: Decimal
    pnl_percent: Decimal  # realized_pnl / entry_cost_basis * 100

    # Duration
    hold_duration_seconds: int

    @classmethod
    def from_lot(cls, lot: StrategyLot) -> StrategyLotSummary:
        """Create summary from a closed StrategyLot.

        Args:
            lot: Closed StrategyLot to summarize

        Returns:
            StrategyLotSummary instance

        Raises:
            ValueError: If lot is not fully closed

        """
        if lot.is_open or lot.fully_closed_at is None:
            raise ValueError(f"Cannot create summary from open lot {lot.lot_id}")

        avg_exit = lot.avg_exit_price
        if avg_exit is None:
            raise ValueError(f"Lot {lot.lot_id} has no exit records")

        exit_value = lot.entry_qty * avg_exit
        pnl_percent = (
            (lot.realized_pnl / lot.entry_cost_basis) * 100
            if lot.entry_cost_basis
            else Decimal("0")
        )
        hold_duration = lot.hold_duration
        hold_seconds = int(hold_duration.total_seconds()) if hold_duration else 0

        return cls(
            lot_id=lot.lot_id,
            strategy_name=lot.strategy_name,
            symbol=lot.symbol,
            correlation_id=lot.correlation_id,
            entry_timestamp=lot.entry_timestamp,
            entry_qty=lot.entry_qty,
            entry_price=lot.entry_price,
            entry_cost_basis=lot.entry_cost_basis,
            exit_timestamp=lot.fully_closed_at,
            avg_exit_price=avg_exit,
            exit_value=exit_value,
            realized_pnl=lot.realized_pnl,
            pnl_percent=pnl_percent,
            hold_duration_seconds=hold_seconds,
        )
