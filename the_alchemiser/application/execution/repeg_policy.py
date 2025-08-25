"""Configurable re-pegging policy for order execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List

from the_alchemiser.application.execution.error_taxonomy import (
    OrderError,
    OrderErrorCode,
)
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class RepegStrategy(str, Enum):
    """Re-pegging strategy options."""

    DISABLED = "disabled"  # No re-pegging
    CONSERVATIVE = "conservative"  # Small price improvements
    AGGRESSIVE = "aggressive"  # Larger price improvements
    ADAPTIVE = "adaptive"  # Adjust based on market conditions


class RepegTrigger(str, Enum):
    """Conditions that trigger re-pegging."""

    TIME_BASED = "time_based"  # Re-peg after time threshold
    SPREAD_CHANGE = "spread_change"  # Re-peg when spread changes
    VOLUME_BASED = "volume_based"  # Re-peg based on volume
    MARKET_IMPACT = "market_impact"  # Re-peg when price moves away


@dataclass(frozen=True)
class RepegConfig:
    """Configuration for re-pegging behavior."""

    strategy: RepegStrategy = RepegStrategy.CONSERVATIVE
    max_repeg_attempts: int = 3
    repeg_interval_seconds: int = 5
    
    # Price improvement settings
    base_improvement_cents: Decimal = Decimal("0.01")  # 1 cent base improvement
    max_improvement_cents: Decimal = Decimal("0.05")   # 5 cents maximum
    improvement_escalation: Decimal = Decimal("1.5")   # 50% increase per attempt
    
    # Market condition thresholds
    max_spread_bps_for_repeg: Decimal = Decimal("50")  # 50 basis points
    min_volume_threshold: int = 1000  # Minimum volume for re-pegging
    max_price_deviation_pct: Decimal = Decimal("2.0")  # 2% max price deviation
    
    # Abandon conditions
    abandon_after_repeg_count: int = 3
    abandon_if_spread_exceeds_bps: Decimal = Decimal("100")  # 100 basis points
    abandon_on_market_close: bool = True
    
    # Fallback settings
    enable_market_fallback: bool = False  # Explicit feature flag
    market_fallback_after_attempts: int = 3


@dataclass
class RepegDecision:
    """Decision result for re-pegging an order."""

    should_repeg: bool
    new_price: Money | None = None
    reason: str = ""
    abandon: bool = False
    fallback_to_market: bool = False
    retry_count: int = 0


@dataclass
class MarketSnapshot:
    """Current market conditions for re-pegging decisions."""

    symbol: Symbol
    bid: Money
    ask: Money
    last_price: Money | None = None
    volume: int = 0
    spread_bps: Decimal = Decimal("0")
    timestamp: Any | None = None  # datetime


class RepegPolicyEngine:
    """Engine for making re-pegging decisions based on configured policy."""

    def __init__(self, config: RepegConfig | None = None) -> None:
        """Initialize the re-pegging policy engine."""
        self.config = config or RepegConfig()
        self.logger = logging.getLogger(__name__)
        
        # Track re-pegging attempts per order
        self._repeg_history: Dict[OrderId, List[Dict[str, Any]]] = {}

    def evaluate_repeg_decision(
        self,
        order_id: OrderId,
        symbol: Symbol,
        side: str,
        current_limit_price: Money,
        market_snapshot: MarketSnapshot,
        time_since_submission: int,
        previous_repeg_count: int = 0,
    ) -> RepegDecision:
        """Evaluate whether to re-peg an order and determine new price."""
        
        # Check if re-pegging is disabled
        if self.config.strategy == RepegStrategy.DISABLED:
            return RepegDecision(
                should_repeg=False,
                reason="Re-pegging disabled by configuration",
            )

        # Check abandon conditions first
        abandon_decision = self._check_abandon_conditions(
            order_id, market_snapshot, previous_repeg_count
        )
        if abandon_decision.abandon:
            return abandon_decision

        # Check if we should re-peg based on triggers
        should_repeg = self._evaluate_repeg_triggers(
            time_since_submission, market_snapshot, previous_repeg_count
        )
        
        if not should_repeg:
            return RepegDecision(
                should_repeg=False,
                reason="Re-peg triggers not met",
                retry_count=previous_repeg_count,
            )

        # Calculate new price based on strategy
        new_price = self._calculate_repeg_price(
            side, current_limit_price, market_snapshot, previous_repeg_count
        )
        
        if new_price is None:
            return RepegDecision(
                should_repeg=False,
                reason="Unable to calculate improved price",
                retry_count=previous_repeg_count,
            )

        # Validate the new price
        validation_error = self._validate_repeg_price(
            side, new_price, market_snapshot, current_limit_price
        )
        
        if validation_error:
            return RepegDecision(
                should_repeg=False,
                reason=f"Price validation failed: {validation_error}",
                retry_count=previous_repeg_count,
            )

        # Record the re-peg decision
        self._record_repeg_attempt(order_id, {
            "new_price": str(new_price.amount),
            "previous_price": str(current_limit_price.amount),
            "market_bid": str(market_snapshot.bid.amount),
            "market_ask": str(market_snapshot.ask.amount),
            "spread_bps": str(market_snapshot.spread_bps),
            "attempt_number": previous_repeg_count + 1,
        })

        self.logger.info(
            "repeg_decision_made",
            extra={
                "order_id": str(order_id.value),
                "symbol": str(symbol.value),
                "side": side,
                "old_price": str(current_limit_price.amount),
                "new_price": str(new_price.amount),
                "attempt": previous_repeg_count + 1,
                "strategy": self.config.strategy.value,
            },
        )

        return RepegDecision(
            should_repeg=True,
            new_price=new_price,
            reason=f"Re-peg attempt {previous_repeg_count + 1} using {self.config.strategy.value} strategy",
            retry_count=previous_repeg_count + 1,
        )

    def _check_abandon_conditions(
        self,
        order_id: OrderId,
        market_snapshot: MarketSnapshot,
        repeg_count: int,
    ) -> RepegDecision:
        """Check if order should be abandoned based on configured conditions."""
        
        # Too many re-peg attempts
        if repeg_count >= self.config.abandon_after_repeg_count:
            should_fallback = (
                self.config.enable_market_fallback and 
                repeg_count >= self.config.market_fallback_after_attempts
            )
            
            return RepegDecision(
                should_repeg=False,
                abandon=True,
                fallback_to_market=should_fallback,
                reason=f"Exceeded maximum re-peg attempts ({self.config.abandon_after_repeg_count})",
                retry_count=repeg_count,
            )

        # Spread too wide
        if market_snapshot.spread_bps > self.config.abandon_if_spread_exceeds_bps:
            return RepegDecision(
                should_repeg=False,
                abandon=True,
                reason=f"Spread {market_snapshot.spread_bps} bps exceeds abandon threshold {self.config.abandon_if_spread_exceeds_bps} bps",
                retry_count=repeg_count,
            )

        # Market conditions unsuitable for re-pegging
        if market_snapshot.spread_bps > self.config.max_spread_bps_for_repeg:
            return RepegDecision(
                should_repeg=False,
                reason=f"Spread {market_snapshot.spread_bps} bps too wide for re-pegging",
                retry_count=repeg_count,
            )

        return RepegDecision(should_repeg=False)  # No abandon conditions met

    def _evaluate_repeg_triggers(
        self,
        time_since_submission: int,
        market_snapshot: MarketSnapshot,
        repeg_count: int,
    ) -> bool:
        """Evaluate if re-peg triggers are met."""
        
        # Time-based trigger
        if time_since_submission >= self.config.repeg_interval_seconds:
            self.logger.debug(
                "repeg_trigger_time",
                extra={
                    "time_elapsed": time_since_submission,
                    "threshold": self.config.repeg_interval_seconds,
                },
            )
            return True

        # Volume-based trigger (if volume drops significantly)
        if market_snapshot.volume < self.config.min_volume_threshold:
            self.logger.debug(
                "repeg_trigger_volume",
                extra={
                    "current_volume": market_snapshot.volume,
                    "threshold": self.config.min_volume_threshold,
                },
            )
            return True

        return False

    def _calculate_repeg_price(
        self,
        side: str,
        current_price: Money,
        market_snapshot: MarketSnapshot,
        repeg_count: int,
    ) -> Money | None:
        """Calculate new re-pegged price based on strategy."""
        
        if self.config.strategy == RepegStrategy.CONSERVATIVE:
            return self._calculate_conservative_price(
                side, current_price, market_snapshot, repeg_count
            )
        elif self.config.strategy == RepegStrategy.AGGRESSIVE:
            return self._calculate_aggressive_price(
                side, current_price, market_snapshot, repeg_count
            )
        elif self.config.strategy == RepegStrategy.ADAPTIVE:
            return self._calculate_adaptive_price(
                side, current_price, market_snapshot, repeg_count
            )
        else:
            return None

    def _calculate_conservative_price(
        self,
        side: str,
        current_price: Money,
        market_snapshot: MarketSnapshot,
        repeg_count: int,
    ) -> Money | None:
        """Calculate conservative re-peg price with minimal improvement."""
        
        improvement = self.config.base_improvement_cents
        if repeg_count > 0:
            # Escalate improvement with each attempt
            improvement *= (self.config.improvement_escalation ** repeg_count)
            improvement = min(improvement, self.config.max_improvement_cents)

        if side.upper() == "BUY":
            # Move closer to ask
            new_price = current_price.amount + improvement
            # Don't exceed ask + reasonable buffer
            max_price = market_snapshot.ask.amount + self.config.max_improvement_cents
            new_price = min(new_price, max_price)
        else:
            # Move closer to bid
            new_price = current_price.amount - improvement
            # Don't go below bid - reasonable buffer
            min_price = market_snapshot.bid.amount - self.config.max_improvement_cents
            new_price = max(new_price, min_price)

        # Ensure price is positive
        if new_price <= 0:
            return None

        return Money(new_price, current_price.currency)

    def _calculate_aggressive_price(
        self,
        side: str,
        current_price: Money,
        market_snapshot: MarketSnapshot,
        repeg_count: int,
    ) -> Money | None:
        """Calculate aggressive re-peg price for faster execution."""
        
        if side.upper() == "BUY":
            # Jump to ask or slightly above
            new_price = market_snapshot.ask.amount + self.config.base_improvement_cents
        else:
            # Jump to bid or slightly below
            new_price = market_snapshot.bid.amount - self.config.base_improvement_cents

        # Ensure price is positive
        if new_price <= 0:
            return None

        return Money(new_price, current_price.currency)

    def _calculate_adaptive_price(
        self,
        side: str,
        current_price: Money,
        market_snapshot: MarketSnapshot,
        repeg_count: int,
    ) -> Money | None:
        """Calculate adaptive re-peg price based on market conditions."""
        
        # Adjust strategy based on spread width
        if market_snapshot.spread_bps <= Decimal("10"):  # Tight spread
            return self._calculate_conservative_price(side, current_price, market_snapshot, repeg_count)
        elif market_snapshot.spread_bps <= Decimal("25"):  # Medium spread
            return self._calculate_aggressive_price(side, current_price, market_snapshot, repeg_count)
        else:  # Wide spread - be more conservative
            improvement = self.config.base_improvement_cents * Decimal("0.5")  # Half normal improvement
            
            if side.upper() == "BUY":
                new_price = current_price.amount + improvement
            else:
                new_price = current_price.amount - improvement

            if new_price <= 0:
                return None

            return Money(new_price, current_price.currency)

    def _validate_repeg_price(
        self,
        side: str,
        new_price: Money,
        market_snapshot: MarketSnapshot,
        current_price: Money,
    ) -> str | None:
        """Validate the proposed re-peg price."""
        
        # Check price deviation limits
        price_change_pct = abs(new_price.amount - current_price.amount) / current_price.amount * 100
        if price_change_pct > self.config.max_price_deviation_pct:
            return f"Price change {price_change_pct:.1f}% exceeds limit {self.config.max_price_deviation_pct}%"

        # Check that price is moving in the right direction
        if side.upper() == "BUY":
            if new_price.amount < current_price.amount:
                return "Buy re-peg price cannot be lower than current price"
            if new_price.amount > market_snapshot.ask.amount * Decimal("1.1"):  # 10% above ask
                return "Buy re-peg price too far above market ask"
        else:
            if new_price.amount > current_price.amount:
                return "Sell re-peg price cannot be higher than current price"
            if new_price.amount < market_snapshot.bid.amount * Decimal("0.9"):  # 10% below bid
                return "Sell re-peg price too far below market bid"

        return None  # Price is valid

    def _record_repeg_attempt(self, order_id: OrderId, details: Dict[str, Any]) -> None:
        """Record re-peg attempt for tracking and analysis."""
        if order_id not in self._repeg_history:
            self._repeg_history[order_id] = []
        
        self._repeg_history[order_id].append({
            **details,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    def get_repeg_history(self, order_id: OrderId) -> List[Dict[str, Any]]:
        """Get re-peg history for an order."""
        return self._repeg_history.get(order_id, [])

    def cleanup_history(self, order_id: OrderId) -> None:
        """Clean up re-peg history for a completed order."""
        self._repeg_history.pop(order_id, None)

    def get_repeg_statistics(self) -> Dict[str, Any]:
        """Get overall re-pegging statistics."""
        total_orders = len(self._repeg_history)
        total_attempts = sum(len(history) for history in self._repeg_history.values())
        
        if total_orders == 0:
            return {
                "total_orders": 0,
                "total_attempts": 0,
                "average_attempts_per_order": 0.0,
            }

        return {
            "total_orders": total_orders,
            "total_attempts": total_attempts,
            "average_attempts_per_order": total_attempts / total_orders,
            "orders_with_repegs": total_orders,
            "max_attempts_single_order": max(len(history) for history in self._repeg_history.values()),
        }