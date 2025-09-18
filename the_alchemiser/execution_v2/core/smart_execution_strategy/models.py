"""Business Unit: execution | Status: current.

Data models and configuration for smart execution strategy.

This module contains all the data classes, type definitions, and configuration
objects used throughout the smart execution strategy components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TypedDict


class LiquidityMetadata(TypedDict, total=False):
    """Metadata for liquidity analysis and execution."""

    # Core liquidity metrics
    liquidity_score: float
    volume_imbalance: float
    confidence: float
    volume_available: float
    volume_ratio: float
    strategy_recommendation: str
    bid_volume: float
    ask_volume: float

    # Market data context
    method: str
    mid: float
    bid: float
    ask: float
    bid_price: float
    ask_price: float
    spread_percent: float
    bid_size: float
    ask_size: float

    # Execution context
    used_fallback: bool
    original_order_id: str
    original_price: float | None
    new_price: float


@dataclass
class ExecutionConfig:
    """Configuration for smart execution strategy."""

    # Market timing
    market_open_delay_minutes: int = 5  # Wait 5 minutes after 9:30am ET

    # Spread limits
    max_spread_percent: Decimal = Decimal(
        "0.50"
    )  # 0.50% maximum spread (increased from 0.25%)

    # Re-pegging configuration
    repeg_threshold_percent: Decimal = Decimal("0.10")  # Re-peg if market moves >0.1%
    max_repegs_per_order: int = 5  # Maximum re-pegs before escalation

    # Volume requirements - ADJUSTED FOR LOW LIQUIDITY ETFS
    min_bid_ask_size: Decimal = Decimal("10")  # Reduced from 100 to 10 shares minimum
    min_bid_ask_size_high_liquidity: Decimal = Decimal(
        "100"
    )  # For liquid stocks like SPY

    # Order timing
    quote_freshness_seconds: int = 5  # Require quote within 5 seconds
    order_placement_timeout_seconds: int = 30  # Timeout for order placement
    fill_wait_seconds: int = 15  # Wait time before attempting re-peg
    max_wait_time_seconds: int = 30  # Maximum wait time for quote data

    # Anchoring offsets (in cents)
    bid_anchor_offset_cents: Decimal = Decimal("0.01")  # Place at bid + $0.01 for buys
    ask_anchor_offset_cents: Decimal = Decimal("0.01")  # Place at ask - $0.01 for sells

    # Symbol-specific overrides for low-liquidity ETFs
    low_liquidity_symbols: set[str] = field(
        default_factory=lambda: {"BTAL", "UVXY", "TECL", "KMLM"}
    )


@dataclass
class SmartOrderRequest:
    """Request for smart order placement."""

    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: Decimal
    correlation_id: str
    urgency: str = "NORMAL"  # "LOW", "NORMAL", "HIGH"
    is_complete_exit: bool = False


@dataclass
class SmartOrderResult:
    """Result of smart order placement attempt."""

    success: bool
    order_id: str | None = None
    final_price: Decimal | None = None
    anchor_price: Decimal | None = None
    repegs_used: int = 0
    execution_strategy: str = "smart_limit"
    error_message: str | None = None
    placement_timestamp: datetime | None = None
    metadata: LiquidityMetadata | None = None