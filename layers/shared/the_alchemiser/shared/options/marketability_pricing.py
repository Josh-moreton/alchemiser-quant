"""Business Unit: shared | Status: current.

Marketability pricing algorithm for options execution.

Implements adaptive limit pricing that:
- Starts at mid price
- Steps toward ask in controlled increments
- Enforces slippage controls (per trade and per day)
- Handles explicit "no fill" outcomes
- Adapts to market conditions (open vs close, calm vs high IV)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import (
    MAX_DAILY_SLIPPAGE_PCT,
    MAX_FILL_ATTEMPTS,
    MAX_FILL_TIME_SECONDS,
    MAX_SLIPPAGE_PER_TRADE_CLOSE,
    MAX_SLIPPAGE_PER_TRADE_OPEN,
    PRICE_STEP_PCT_CALM,
    PRICE_STEP_PCT_HIGH_IV,
    PRICE_UPDATE_INTERVAL_SECONDS,
    VIX_HIGH_THRESHOLD,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.options.schemas import OptionContract

logger = get_logger(__name__)


class OrderSide(str, Enum):
    """Order side for pricing rules."""

    OPEN = "open"  # Opening a new position
    CLOSE = "close"  # Closing an existing position


class MarketCondition(str, Enum):
    """Market condition for pricing rules."""

    CALM = "calm"  # VIX < threshold (patient pricing)
    HIGH_IV = "high_iv"  # VIX >= threshold (aggressive pricing)


@dataclass(frozen=True)
class MarketSnapshot:
    """Recorded market snapshot for testing and reproducibility.

    Captures bid/ask/mid prices at a specific point in time.
    """

    option_symbol: str
    timestamp: str
    bid_price: Decimal
    ask_price: Decimal
    mid_price: Decimal
    spread_pct: Decimal
    vix_level: Decimal | None = None


@dataclass(frozen=True)
class PricingStep:
    """A single pricing step in the marketability algorithm."""

    step_number: int
    limit_price: Decimal
    slippage_from_mid_pct: Decimal
    elapsed_seconds: float


@dataclass(frozen=True)
class MarketabilityResult:
    """Result of marketability pricing algorithm.

    Tracks the progression of limit prices and final outcome.
    """

    success: bool
    final_limit_price: Decimal | None
    total_attempts: int
    total_slippage_pct: Decimal
    elapsed_seconds: float
    pricing_steps: list[PricingStep]
    no_fill_reason: str | None = None
    max_slippage_reached: bool = False
    max_attempts_reached: bool = False
    timeout_reached: bool = False


class SlippageTracker:
    """Tracks daily slippage across all trades.

    Enforces daily slippage limits by accumulating slippage
    across all trades in a single trading day.
    """

    def __init__(self) -> None:
        """Initialize tracker."""
        self._daily_total_premium = Decimal("0")
        self._daily_slippage_amount = Decimal("0")
        self._trade_count = 0

    def record_trade(
        self,
        premium_paid: Decimal,
        mid_price: Decimal,
        slippage_amount: Decimal,
    ) -> None:
        """Record a completed trade.

        Args:
            premium_paid: Total premium paid for the trade
            mid_price: Mid price at time of trade
            slippage_amount: Actual slippage (filled - mid)

        """
        self._daily_total_premium += premium_paid
        self._daily_slippage_amount += slippage_amount
        self._trade_count += 1

        logger.info(
            "Slippage recorded",
            trade_count=self._trade_count,
            premium_paid=str(premium_paid),
            slippage_amount=str(slippage_amount),
            daily_total_premium=str(self._daily_total_premium),
            daily_slippage_total=str(self._daily_slippage_amount),
        )

    def check_daily_limit(self, proposed_slippage: Decimal) -> tuple[bool, Decimal]:
        """Check if proposed slippage would exceed daily limit.

        Args:
            proposed_slippage: Additional slippage to add

        Returns:
            Tuple of (allowed, current_slippage_pct)

        """
        if self._daily_total_premium == 0:
            return True, Decimal("0")

        projected_slippage = self._daily_slippage_amount + proposed_slippage
        projected_pct = projected_slippage / self._daily_total_premium

        allowed = projected_pct <= MAX_DAILY_SLIPPAGE_PCT

        if not allowed:
            logger.warning(
                "Daily slippage limit would be exceeded",
                projected_slippage_pct=str(projected_pct),
                max_daily_slippage_pct=str(MAX_DAILY_SLIPPAGE_PCT),
                daily_total_premium=str(self._daily_total_premium),
                current_slippage=str(self._daily_slippage_amount),
                proposed_additional=str(proposed_slippage),
            )

        return allowed, projected_pct

    def reset_daily(self) -> None:
        """Reset daily counters (call at start of trading day)."""
        self._daily_total_premium = Decimal("0")
        self._daily_slippage_amount = Decimal("0")
        self._trade_count = 0
        logger.info("Daily slippage tracker reset")


class MarketabilityPricer:
    """Calculates adaptive limit prices for options execution.

    Implements the marketability algorithm:
    1. Start at mid price
    2. Step toward ask in controlled increments
    3. Enforce per-trade and daily slippage limits
    4. Adapt to order side (open vs close) and market conditions (calm vs high IV)
    """

    def __init__(
        self,
        slippage_tracker: SlippageTracker | None = None,
    ) -> None:
        """Initialize pricer.

        Args:
            slippage_tracker: Optional shared tracker for daily slippage

        """
        self._slippage_tracker = slippage_tracker or SlippageTracker()

    def calculate_initial_limit_price(
        self,
        contract: OptionContract,
        order_side: OrderSide,
        vix_level: Decimal | None = None,
    ) -> Decimal:
        """Calculate initial limit price (starts at mid).

        Args:
            contract: Option contract with bid/ask data
            order_side: Whether opening or closing position
            vix_level: Current VIX level (optional, affects stepping)

        Returns:
            Initial limit price (mid price)

        """
        mid_price = contract.mid_price
        if mid_price is None or mid_price <= 0:
            # Fallback to ask if mid unavailable
            mid_price = contract.ask_price or Decimal("1")
            logger.warning(
                "Mid price unavailable, using ask",
                symbol=contract.symbol,
                ask_price=str(contract.ask_price),
            )

        logger.info(
            "Initial limit price (at mid)",
            symbol=contract.symbol,
            bid=str(contract.bid_price),
            mid=str(mid_price),
            ask=str(contract.ask_price),
            order_side=order_side.value,
        )

        return mid_price

    def calculate_next_limit_price(
        self,
        current_limit: Decimal,
        contract: OptionContract,
        order_side: OrderSide,
        vix_level: Decimal | None = None,
        attempt_number: int = 1,
    ) -> Decimal | None:
        """Calculate next limit price by stepping toward ask.

        Args:
            current_limit: Current limit price
            contract: Option contract with bid/ask data
            order_side: Whether opening or closing position
            vix_level: Current VIX level (affects step size)
            attempt_number: Current attempt number

        Returns:
            Next limit price, or None if max slippage reached

        """
        bid = contract.bid_price or Decimal("0")
        ask = contract.ask_price or Decimal("1")
        mid = contract.mid_price or ((bid + ask) / Decimal("2"))

        # Calculate spread
        spread = ask - bid
        if spread <= 0:
            logger.error(
                "Invalid spread (ask <= bid)",
                symbol=contract.symbol,
                bid=str(bid),
                ask=str(ask),
            )
            return None

        # Determine step size based on market conditions
        market_condition = self._determine_market_condition(vix_level)
        step_pct = (
            PRICE_STEP_PCT_HIGH_IV
            if market_condition == MarketCondition.HIGH_IV
            else PRICE_STEP_PCT_CALM
        )

        # Calculate price increment
        price_step = spread * step_pct

        # Calculate next limit price
        next_limit = current_limit + price_step

        # Check slippage constraint
        slippage_from_mid = next_limit - mid
        slippage_pct = slippage_from_mid / mid if mid > 0 else Decimal("0")

        # Determine max slippage based on order side
        max_slippage = (
            MAX_SLIPPAGE_PER_TRADE_OPEN
            if order_side == OrderSide.OPEN
            else MAX_SLIPPAGE_PER_TRADE_CLOSE
        )

        if slippage_pct > max_slippage:
            logger.warning(
                "Max slippage per trade reached",
                symbol=contract.symbol,
                next_limit=str(next_limit),
                slippage_pct=str(slippage_pct),
                max_slippage=str(max_slippage),
                order_side=order_side.value,
            )
            return None

        # Check daily slippage limit
        # Assume 1 contract for estimation (actual will be checked at fill)
        estimated_slippage = slippage_from_mid * Decimal("100")  # 100 shares per contract
        allowed, current_daily_pct = self._slippage_tracker.check_daily_limit(
            estimated_slippage
        )

        if not allowed:
            logger.warning(
                "Daily slippage limit would be exceeded",
                symbol=contract.symbol,
                next_limit=str(next_limit),
                estimated_trade_slippage=str(estimated_slippage),
                current_daily_slippage_pct=str(current_daily_pct),
            )
            return None

        logger.info(
            "Stepping limit price toward ask",
            symbol=contract.symbol,
            attempt=attempt_number,
            current_limit=str(current_limit),
            next_limit=str(next_limit),
            price_step=str(price_step),
            step_pct=str(step_pct),
            slippage_from_mid_pct=str(slippage_pct),
            market_condition=market_condition.value,
        )

        return next_limit

    def generate_pricing_sequence(
        self,
        contract: OptionContract,
        order_side: OrderSide,
        vix_level: Decimal | None = None,
    ) -> MarketabilityResult:
        """Generate complete pricing sequence for testing.

        This method simulates the full pricing algorithm without
        actually placing orders. Useful for testing with recorded
        market snapshots.

        Args:
            contract: Option contract with bid/ask data
            order_side: Whether opening or closing position
            vix_level: Current VIX level

        Returns:
            MarketabilityResult with pricing progression

        """
        start_time = time.time()
        pricing_steps: list[PricingStep] = []

        # Calculate initial limit price (at mid)
        current_limit = self.calculate_initial_limit_price(contract, order_side, vix_level)
        mid = contract.mid_price or Decimal("0")

        # Initial step
        initial_slippage = (current_limit - mid) / mid if mid > 0 else Decimal("0")
        pricing_steps.append(
            PricingStep(
                step_number=1,
                limit_price=current_limit,
                slippage_from_mid_pct=initial_slippage,
                elapsed_seconds=0.0,
            )
        )

        # Step through pricing attempts
        for attempt in range(2, MAX_FILL_ATTEMPTS + 1):
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > MAX_FILL_TIME_SECONDS:
                return MarketabilityResult(
                    success=False,
                    final_limit_price=current_limit,
                    total_attempts=len(pricing_steps),
                    total_slippage_pct=pricing_steps[-1].slippage_from_mid_pct,
                    elapsed_seconds=elapsed,
                    pricing_steps=pricing_steps,
                    no_fill_reason="Timeout reached",
                    timeout_reached=True,
                )

            # Calculate next limit price
            next_limit = self.calculate_next_limit_price(
                current_limit=current_limit,
                contract=contract,
                order_side=order_side,
                vix_level=vix_level,
                attempt_number=attempt,
            )

            if next_limit is None:
                # Max slippage or daily limit reached
                return MarketabilityResult(
                    success=False,
                    final_limit_price=current_limit,
                    total_attempts=len(pricing_steps),
                    total_slippage_pct=pricing_steps[-1].slippage_from_mid_pct,
                    elapsed_seconds=elapsed,
                    pricing_steps=pricing_steps,
                    no_fill_reason="Max slippage or daily limit reached",
                    max_slippage_reached=True,
                )

            # Add pricing step
            current_limit = next_limit
            slippage_pct = (current_limit - mid) / mid if mid > 0 else Decimal("0")
            pricing_steps.append(
                PricingStep(
                    step_number=attempt,
                    limit_price=current_limit,
                    slippage_from_mid_pct=slippage_pct,
                    elapsed_seconds=elapsed,
                )
            )

        # Max attempts reached
        return MarketabilityResult(
            success=False,
            final_limit_price=current_limit,
            total_attempts=len(pricing_steps),
            total_slippage_pct=pricing_steps[-1].slippage_from_mid_pct,
            elapsed_seconds=time.time() - start_time,
            pricing_steps=pricing_steps,
            no_fill_reason="Max attempts reached",
            max_attempts_reached=True,
        )

    @staticmethod
    def _determine_market_condition(vix_level: Decimal | None) -> MarketCondition:
        """Determine market condition based on VIX level.

        Args:
            vix_level: Current VIX level (optional)

        Returns:
            MarketCondition enum (calm or high_iv)

        """
        if vix_level is None:
            # Default to calm if VIX unavailable
            return MarketCondition.CALM

        if vix_level >= VIX_HIGH_THRESHOLD:
            return MarketCondition.HIGH_IV

        return MarketCondition.CALM

    @property
    def slippage_tracker(self) -> SlippageTracker:
        """Get the slippage tracker."""
        return self._slippage_tracker
