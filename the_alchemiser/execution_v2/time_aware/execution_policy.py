"""Business Unit: Execution | Status: current.

Execution policy configuration for time-aware execution framework.

Policies define the behavioural parameters for each execution phase:
- Phase time boundaries
- Peg strategies and aggression curves
- Participation caps and child order sizing
- Auction participation rules

Policies are configurable per portfolio, asset class, or individual trade.
"""

from dataclasses import dataclass, field
from datetime import time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.execution_v2.time_aware.models import ExecutionPhase, PegType


class PhaseConfig(BaseModel):
    """Configuration for a single execution phase.

    Attributes:
        start_time: Phase start (ET, 24-hour format)
        end_time: Phase end (ET, 24-hour format)
        allowed_peg_types: Which peg strategies are permitted
        default_peg_type: Default peg for new orders
        max_participation_rate: Max fraction of ADV to consume per phase
        max_order_size_fraction: Max child order as fraction of remaining qty
        min_order_size: Minimum child order size (shares)
        repeg_interval_seconds: How often to reassess pegs
        allow_spread_crossing: Whether crossing is permitted
        allow_market_orders: Whether market orders are permitted

    """

    model_config = ConfigDict(frozen=True, strict=True)

    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # HH:MM ET
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    allowed_peg_types: frozenset[PegType] = frozenset()
    default_peg_type: PegType = PegType.MID
    max_participation_rate: Decimal = Decimal("0.10")  # 10% of ADV
    max_order_size_fraction: Decimal = Decimal("0.25")  # 25% of remaining
    min_order_size: int = 1
    repeg_interval_seconds: int = 300  # 5 minutes
    allow_spread_crossing: bool = False
    allow_market_orders: bool = False

    def get_start_time(self) -> time:
        """Parse start_time string to time object."""
        parts = self.start_time.split(":")
        return time(int(parts[0]), int(parts[1]))

    def get_end_time(self) -> time:
        """Parse end_time string to time object."""
        parts = self.end_time.split(":")
        return time(int(parts[0]), int(parts[1]))


# Default phase configurations reflecting institutional best practices
DEFAULT_OPEN_AVOIDANCE = PhaseConfig(
    start_time="09:30",
    end_time="10:30",
    allowed_peg_types=frozenset({PegType.FAR_TOUCH, PegType.MID}),
    default_peg_type=PegType.FAR_TOUCH,  # Very passive
    max_participation_rate=Decimal("0.02"),  # Only 2% of ADV
    max_order_size_fraction=Decimal("0.10"),  # Tiny slices
    min_order_size=1,
    repeg_interval_seconds=600,  # Check every 10 min
    allow_spread_crossing=False,
    allow_market_orders=False,
)

DEFAULT_PASSIVE_ACCUMULATION = PhaseConfig(
    start_time="10:30",
    end_time="14:30",
    allowed_peg_types=frozenset({PegType.FAR_TOUCH, PegType.MID, PegType.NEAR_TOUCH}),
    default_peg_type=PegType.MID,  # Midpoint seeking
    max_participation_rate=Decimal("0.10"),  # 10% of ADV
    max_order_size_fraction=Decimal("0.25"),  # Moderate slices
    min_order_size=1,
    repeg_interval_seconds=300,  # Check every 5 min
    allow_spread_crossing=False,
    allow_market_orders=False,
)

DEFAULT_URGENCY_RAMP = PhaseConfig(
    start_time="14:30",
    end_time="15:30",
    allowed_peg_types=frozenset(
        {
            PegType.MID,
            PegType.NEAR_TOUCH,
            PegType.INSIDE_25,
            PegType.INSIDE_50,
            PegType.INSIDE_75,
        }
    ),
    default_peg_type=PegType.NEAR_TOUCH,  # More aggressive
    max_participation_rate=Decimal("0.25"),  # 25% of ADV
    max_order_size_fraction=Decimal("0.40"),  # Larger slices
    min_order_size=1,
    repeg_interval_seconds=180,  # Check every 3 min
    allow_spread_crossing=False,  # Not yet
    allow_market_orders=False,
)

DEFAULT_DEADLINE_CLOSE = PhaseConfig(
    start_time="15:30",
    end_time="16:00",
    allowed_peg_types=frozenset(
        {
            PegType.NEAR_TOUCH,
            PegType.INSIDE_75,
            PegType.INSIDE_90,
            PegType.CROSS,
            PegType.MARKET,
        }
    ),
    default_peg_type=PegType.INSIDE_75,  # Aggressive
    max_participation_rate=Decimal("1.00"),  # No limit
    max_order_size_fraction=Decimal("1.00"),  # Can take all remaining
    min_order_size=1,
    repeg_interval_seconds=60,  # Check every minute
    allow_spread_crossing=True,
    allow_market_orders=True,
)


class ExecutionPolicy(BaseModel):
    """Complete execution policy defining behaviour across all phases.

    Policies can be configured per:
    - Portfolio (conservative vs aggressive)
    - Asset class (ETFs vs single stocks)
    - Liquidity tier (mega-cap vs small-cap)
    - Trade urgency (rebalance vs liquidation)

    Attributes:
        policy_id: Unique identifier for this policy
        name: Human-readable name
        description: Policy rationale
        phases: Configuration for each execution phase
        tick_interval_minutes: How often scheduler fires
        auction_participation: Whether to use CLS orders at close
        auction_reserve_fraction: Fraction of remaining qty to reserve for auction
        auction_cutoff_time: Last time to submit CLS orders (ET)
        max_spread_bps: Maximum acceptable spread to trade
        halt_behaviour: What to do on trading halts
        early_close_adjustment: Shift phase times for half-days

    """

    model_config = ConfigDict(frozen=True, strict=True)

    policy_id: str = "default"
    name: str = "Default Time-Aware Execution"
    description: str = "Institutional-style time-phased execution policy"

    # Phase configurations
    open_avoidance: PhaseConfig = DEFAULT_OPEN_AVOIDANCE
    passive_accumulation: PhaseConfig = DEFAULT_PASSIVE_ACCUMULATION
    urgency_ramp: PhaseConfig = DEFAULT_URGENCY_RAMP
    deadline_close: PhaseConfig = DEFAULT_DEADLINE_CLOSE

    # Scheduler configuration
    tick_interval_minutes: int = 10  # EventBridge trigger frequency

    # Closing auction configuration
    auction_participation: bool = True
    auction_reserve_fraction: Decimal = Decimal("0.30")  # Reserve 30% for auction
    auction_cutoff_time: str = "15:50"  # Must submit CLS by this time

    # Risk controls
    max_spread_bps: Decimal = Decimal("50")  # 50 bps max spread
    max_daily_notional: Decimal | None = None  # Optional cap

    # Halt behaviour
    halt_behaviour: Literal["pause", "cancel", "continue"] = "pause"

    # Early close adjustments (half-days close at 13:00)
    early_close_adjustment: bool = True
    early_close_time: str = "13:00"

    def get_phase_config(self, phase: ExecutionPhase) -> PhaseConfig | None:
        """Get configuration for a specific phase."""
        mapping = {
            ExecutionPhase.OPEN_AVOIDANCE: self.open_avoidance,
            ExecutionPhase.PASSIVE_ACCUMULATION: self.passive_accumulation,
            ExecutionPhase.URGENCY_RAMP: self.urgency_ramp,
            ExecutionPhase.DEADLINE_CLOSE: self.deadline_close,
        }
        return mapping.get(phase)

    def get_auction_cutoff(self) -> time:
        """Parse auction_cutoff_time to time object."""
        parts = self.auction_cutoff_time.split(":")
        return time(int(parts[0]), int(parts[1]))


# Pre-defined policies for common use cases
CONSERVATIVE_POLICY = ExecutionPolicy(
    policy_id="conservative",
    name="Conservative Execution",
    description="Maximum price improvement, willing to leave unfilled",
    open_avoidance=PhaseConfig(
        start_time="09:30",
        end_time="11:00",  # Longer avoidance
        allowed_peg_types=frozenset({PegType.FAR_TOUCH}),
        default_peg_type=PegType.FAR_TOUCH,
        max_participation_rate=Decimal("0.01"),
        max_order_size_fraction=Decimal("0.05"),
        min_order_size=1,
        repeg_interval_seconds=900,
        allow_spread_crossing=False,
        allow_market_orders=False,
    ),
    auction_reserve_fraction=Decimal("0.50"),  # Half to auction
)

AGGRESSIVE_POLICY = ExecutionPolicy(
    policy_id="aggressive",
    name="Aggressive Execution",
    description="Prioritise completion over price improvement",
    open_avoidance=PhaseConfig(
        start_time="09:30",
        end_time="10:00",  # Shorter avoidance
        allowed_peg_types=frozenset({PegType.MID, PegType.NEAR_TOUCH}),
        default_peg_type=PegType.MID,
        max_participation_rate=Decimal("0.05"),
        max_order_size_fraction=Decimal("0.20"),
        min_order_size=1,
        repeg_interval_seconds=300,
        allow_spread_crossing=False,
        allow_market_orders=False,
    ),
    urgency_ramp=PhaseConfig(
        start_time="14:00",  # Earlier ramp
        end_time="15:30",
        allowed_peg_types=frozenset(
            {
                PegType.NEAR_TOUCH,
                PegType.INSIDE_50,
                PegType.INSIDE_75,
                PegType.INSIDE_90,
            }
        ),
        default_peg_type=PegType.INSIDE_50,
        max_participation_rate=Decimal("0.40"),
        max_order_size_fraction=Decimal("0.50"),
        min_order_size=1,
        repeg_interval_seconds=120,
        allow_spread_crossing=True,
        allow_market_orders=False,
    ),
    auction_reserve_fraction=Decimal("0.20"),  # Less to auction
)

LIQUIDATION_POLICY = ExecutionPolicy(
    policy_id="liquidation",
    name="Liquidation Execution",
    description="Guaranteed completion, price secondary",
    open_avoidance=PhaseConfig(
        start_time="09:30",
        end_time="09:45",  # Minimal avoidance
        allowed_peg_types=frozenset({PegType.MID, PegType.NEAR_TOUCH}),
        default_peg_type=PegType.NEAR_TOUCH,
        max_participation_rate=Decimal("0.10"),
        max_order_size_fraction=Decimal("0.30"),
        min_order_size=1,
        repeg_interval_seconds=180,
        allow_spread_crossing=False,
        allow_market_orders=False,
    ),
    deadline_close=PhaseConfig(
        start_time="15:00",  # Earlier deadline phase
        end_time="16:00",
        allowed_peg_types=frozenset(
            {
                PegType.INSIDE_75,
                PegType.INSIDE_90,
                PegType.CROSS,
                PegType.MARKET,
            }
        ),
        default_peg_type=PegType.INSIDE_90,
        max_participation_rate=Decimal("1.00"),
        max_order_size_fraction=Decimal("1.00"),
        min_order_size=1,
        repeg_interval_seconds=30,
        allow_spread_crossing=True,
        allow_market_orders=True,
    ),
    auction_reserve_fraction=Decimal("0.10"),  # Mostly intraday
)


@dataclass
class PolicyRegistry:
    """Registry of available execution policies.

    Policies can be loaded from configuration or defined in code.
    The registry provides lookup by policy_id.
    """

    policies: dict[str, ExecutionPolicy] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Register default policies."""
        self.register(ExecutionPolicy())
        self.register(CONSERVATIVE_POLICY)
        self.register(AGGRESSIVE_POLICY)
        self.register(LIQUIDATION_POLICY)

    def register(self, policy: ExecutionPolicy) -> None:
        """Register a policy."""
        self.policies[policy.policy_id] = policy

    def get(self, policy_id: str) -> ExecutionPolicy:
        """Get policy by ID, falling back to default."""
        return self.policies.get(policy_id, ExecutionPolicy())

    def list_policies(self) -> list[str]:
        """List available policy IDs."""
        return list(self.policies.keys())


# Global registry instance
POLICY_REGISTRY = PolicyRegistry()
