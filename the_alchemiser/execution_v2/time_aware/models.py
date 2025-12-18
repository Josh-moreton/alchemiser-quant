"""Business Unit: Execution | Status: current.

Core models for time-aware execution framework.

This module defines the state machine phases, execution state tracking,
and child order management for institutional-style time-phased execution.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ExecutionPhase(str, Enum):
    """Trading day execution phases.

    Each phase has distinct behavioural characteristics:
    - OPEN_AVOIDANCE: Avoid open volatility, wide spreads, adverse selection
    - PASSIVE_ACCUMULATION: Price improvement focus, no urgency
    - URGENCY_RAMP: Time-based escalation, tightening pegs
    - DEADLINE_CLOSE: Guarantee completion, auction participation
    - MARKET_CLOSED: No execution permitted
    """

    OPEN_AVOIDANCE = "open_avoidance"
    PASSIVE_ACCUMULATION = "passive_accumulation"
    URGENCY_RAMP = "urgency_ramp"
    DEADLINE_CLOSE = "deadline_close"
    MARKET_CLOSED = "market_closed"


class OrderStatus(str, Enum):
    """Status of a child order in the execution lifecycle."""

    PENDING_SUBMIT = "pending_submit"  # Not yet submitted to broker
    OPEN = "open"  # Submitted, awaiting fill
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PegType(str, Enum):
    """Peg strategy for limit order pricing.

    Determines how aggressively to price limit orders relative to NBBO.
    """

    # Passive pegs (price improvement focus)
    FAR_TOUCH = "far_touch"  # At far side of spread (best bid for buy)
    MID = "mid"  # Midpoint of NBBO
    NEAR_TOUCH = "near_touch"  # At near side of spread

    # Aggressive pegs (fill probability focus)
    INSIDE_25 = "inside_25"  # 25% through spread toward aggressive side
    INSIDE_50 = "inside_50"  # 50% through spread (same as mid)
    INSIDE_75 = "inside_75"  # 75% through spread
    INSIDE_90 = "inside_90"  # 90% through spread

    # Crossing pegs (guarantee fill)
    CROSS = "cross"  # Cross the spread (aggressive side)
    MARKET = "market"  # Market order (no peg)


class ChildOrder(BaseModel):
    """A child order within a parent execution.

    Child orders are the actual orders submitted to the broker. A single
    parent execution may spawn multiple child orders over time as pegs
    are adjusted or cancelled/replaced.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    child_order_id: str  # Internal tracking ID
    broker_order_id: str | None = None  # Alpaca order ID once submitted
    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    limit_price: Decimal | None = None  # None for market orders
    peg_type: PegType
    time_in_force: Literal["day", "gtc", "ioc", "fok", "cls"]
    status: OrderStatus = OrderStatus.PENDING_SUBMIT
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    average_fill_price: Decimal | None = None
    phase_at_submit: ExecutionPhase | None = None

    @property
    def remaining_quantity(self) -> Decimal:
        """Quantity still to be filled."""
        return self.quantity - self.filled_quantity

    @property
    def is_terminal(self) -> bool:
        """True if order is in a terminal state."""
        return self.status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        )


class ExecutionState(str, Enum):
    """Overall state of a pending execution."""

    PENDING = "pending"  # Not yet started
    ACTIVE = "active"  # Actively executing
    PAUSED = "paused"  # Temporarily halted (e.g., halt detection)
    COMPLETED = "completed"  # Target quantity filled
    FAILED = "failed"  # Unrecoverable error
    CANCELLED = "cancelled"  # User/system cancelled


@dataclass
class PendingExecution:
    """State for a single parent execution across the trading day.

    This is the primary state object persisted in DynamoDB between tick
    invocations. It tracks progress toward filling the target quantity
    and maintains audit trail of child orders.

    Attributes:
        execution_id: Unique identifier (typically run_id + trade_id)
        correlation_id: For distributed tracing
        causation_id: ID of triggering event
        symbol: Ticker symbol
        side: buy or sell
        target_quantity: Total quantity to execute
        filled_quantity: Quantity filled so far
        strategy_id: Strategy that generated the signal
        portfolio_id: Portfolio context
        deadline: Hard deadline for completion (typically 16:00 ET)
        created_at: When execution was created
        updated_at: Last state update
        state: Overall execution state
        current_phase: Current execution phase
        urgency_score: 0.0-1.0 computed urgency
        child_orders: List of child orders spawned
        execution_policy_id: Which policy governs this execution
        auction_eligible: Whether to participate in closing auction
        notes: Audit notes for debugging

    """

    execution_id: str
    correlation_id: str
    causation_id: str | None
    symbol: str
    side: Literal["buy", "sell"]
    target_quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    average_fill_price: Decimal | None = None
    strategy_id: str | None = None
    portfolio_id: str | None = None
    deadline: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    state: ExecutionState = ExecutionState.PENDING
    current_phase: ExecutionPhase = ExecutionPhase.MARKET_CLOSED
    urgency_score: float = 0.0
    child_orders: list[ChildOrder] = field(default_factory=list)
    execution_policy_id: str = "default"
    auction_eligible: bool = True
    notes: list[str] = field(default_factory=list)
    version: int = 1  # Optimistic locking

    @property
    def remaining_quantity(self) -> Decimal:
        """Quantity still to be filled."""
        return self.target_quantity - self.filled_quantity

    @property
    def fill_ratio(self) -> float:
        """Fraction of target quantity filled (0.0 to 1.0)."""
        if self.target_quantity == Decimal("0"):
            return 1.0
        return float(self.filled_quantity / self.target_quantity)

    @property
    def is_complete(self) -> bool:
        """True if execution has reached target or terminal state."""
        return self.state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        )

    @property
    def active_child_orders(self) -> list[ChildOrder]:
        """Child orders that are still open."""
        return [o for o in self.child_orders if not o.is_terminal]

    def add_note(self, note: str) -> None:
        """Add an audit note with timestamp."""
        timestamp = datetime.now(UTC).isoformat()
        self.notes.append(f"[{timestamp}] {note}")
        self.updated_at = datetime.now(UTC)


@dataclass
class ExecutionTickContext:
    """Context passed to the execution service on each tick.

    Contains market state and timing information needed to make
    execution decisions.
    """

    tick_time: datetime  # Current time (UTC)
    market_open: datetime  # Today's market open (UTC)
    market_close: datetime  # Today's market close (UTC)
    current_phase: ExecutionPhase
    is_trading_day: bool
    is_market_open: bool
    is_early_close: bool = False  # Half-day
    halt_symbols: frozenset[str] = field(default_factory=frozenset)

    @property
    def time_to_close_seconds(self) -> float:
        """Seconds until market close."""
        if not self.is_market_open:
            return 0.0
        delta = self.market_close - self.tick_time
        return max(0.0, delta.total_seconds())

    @property
    def time_since_open_seconds(self) -> float:
        """Seconds since market open."""
        if not self.is_market_open:
            return 0.0
        delta = self.tick_time - self.market_open
        return max(0.0, delta.total_seconds())

    @property
    def session_progress(self) -> float:
        """Progress through trading session (0.0 at open, 1.0 at close)."""
        if not self.is_market_open:
            return 0.0
        total = (self.market_close - self.market_open).total_seconds()
        if total <= 0:
            return 0.0
        elapsed = self.time_since_open_seconds
        return min(1.0, elapsed / total)
