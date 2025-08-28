#!/usr/bin/env python3
"""Business Unit: strategy & signal generation; Status: current.

Aggressive Limit Strategy.

Orchestrates RepegStrategy until order is filled or all attempts are exhausted.
Handles order lifecycle, error management, and execution flow.
"""

import logging
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from alpaca.trading.enums import OrderSide

from the_alchemiser.services.errors.exceptions import (
    OrderPlacementError,
    OrderTimeoutError,
    SpreadAnalysisError,
)

from .config import StrategyConfig
from .repeg_strategy import AttemptState, RepegStrategy

if TYPE_CHECKING:
    from the_alchemiser.application.trading.lifecycle import (
        LifecycleEventDispatcher,
        OrderLifecycleManager,
    )


class ExecutionContext(Protocol):
    """Protocol for execution context dependencies."""

    def place_limit_order(
        self, symbol: str, qty: float, side: OrderSide, limit_price: float
    ) -> str | None:  # Boundary still uses float; internal strategy uses Decimal
        """Place a limit order."""
        ...

    def place_market_order(
        self, symbol: str, side: OrderSide, qty: float | None = None
    ) -> str | None:
        """Place a market order."""
        ...

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> Any:  # WebSocketResultDTO
        """Wait for order completion."""
        ...

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest quote for a symbol."""
        ...


class AggressiveLimitStrategy:
    """Strategy orchestrating RepegStrategy until filled or exhausted.

    This strategy coordinates the overall execution flow by:
    1. Using RepegStrategy for pricing and timing decisions
    2. Managing order lifecycle events
    3. Handling errors and fallback logic
    4. Providing structured logging with strategy context
    """

    def __init__(
        self,
        config: StrategyConfig,
        repeg_strategy: RepegStrategy | None = None,
        enable_market_order_fallback: bool = False,
        lifecycle_manager: "OrderLifecycleManager | None" = None,
        lifecycle_dispatcher: "LifecycleEventDispatcher | None" = None,
        strategy_name: str = "AggressiveLimitStrategy",
    ) -> None:
        """Initialize aggressive limit strategy.

        Args:
            config: Strategy configuration
            repeg_strategy: Repeg strategy instance (created if None)
            enable_market_order_fallback: Whether to fall back to market orders
            lifecycle_manager: Order lifecycle manager
            lifecycle_dispatcher: Event dispatcher
            strategy_name: Name for logging identification

        """
        self.config = config
        self.repeg_strategy = repeg_strategy or RepegStrategy(
            config, f"{strategy_name}.RepegStrategy"
        )
        self.enable_market_order_fallback = enable_market_order_fallback
        self.lifecycle_manager = lifecycle_manager
        self.lifecycle_dispatcher = lifecycle_dispatcher
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(__name__)

    def execute(
        self,
        context: ExecutionContext,
        symbol: str,
        qty: float,
        side: OrderSide,
        bid: Decimal,
        ask: Decimal,
    ) -> str | None:
        """Execute aggressive limit strategy with repeg attempts.

        Simplified re-write to correct indentation issues.
        """
        original_spread_cents = (ask - bid) * Decimal("100")
        last_attempt_time = 0.0
        self.logger.info(
            "aggressive_limit_strategy_started",
            extra={
                "strategy_name": self.strategy_name,
                "symbol": symbol,
                "side": side.value,
                "quantity": qty,
                "initial_bid": bid,
                "initial_ask": ask,
                "original_spread_cents": original_spread_cents,
                "max_attempts": self.config.max_attempts,
                "adaptive_pricing_enabled": self.config.enable_adaptive_pricing,
            },
        )
        attempt_plan = self.repeg_strategy.plan_attempts()
        self.logger.debug(
            "strategy_attempt_plan",
            extra={
                "strategy_name": self.strategy_name,
                "symbol": symbol,
                "attempt_plan": attempt_plan,
            },
        )
        cumulative_expected_timeout = 0.0
        for attempt_index in range(self.config.max_attempts):
            state = AttemptState(
                bid=bid,
                ask=ask,
                original_spread_cents=original_spread_cents,
                last_attempt_time=time.time(),
                side=side,
                symbol=symbol,
            )
            attempt_result = self.repeg_strategy.next_attempt(state, attempt_index)
            cumulative_expected_timeout += attempt_result.timeout_seconds
            self.logger.info(
                "strategy_attempt_starting",
                extra={
                    "strategy_name": self.strategy_name,
                    "symbol": symbol,
                    "attempt_index": attempt_index,
                    "limit_price": attempt_result.price,
                    "timeout_seconds": attempt_result.timeout_seconds,
                    "reason": attempt_result.reason,
                    "cumulative_expected_timeout": cumulative_expected_timeout,
                },
            )
            if attempt_index > 0:
                current_time = time.time()
                time_since_last = current_time - last_attempt_time
                if time_since_last < self.config.min_repeg_interval_seconds:
                    sleep_time = self.config.min_repeg_interval_seconds - time_since_last
                    self.logger.debug(
                        "strategy_repeg_interval_throttle",
                        extra={
                            "strategy_name": self.strategy_name,
                            "symbol": symbol,
                            "attempt_index": attempt_index,
                            "sleep_time": sleep_time,
                        },
                    )
                    time.sleep(sleep_time)
            last_attempt_time = time.time()
            order_id = context.place_limit_order(symbol, qty, side, float(attempt_result.price))
            if not order_id:
                error_msg = f"Limit order placement returned None ID: {symbol} {side.value} {qty}@{attempt_result.price}"
                self.logger.error(
                    "strategy_order_placement_failed",
                    extra={
                        "strategy_name": self.strategy_name,
                        "symbol": symbol,
                        "attempt_index": attempt_index,
                        "limit_price": attempt_result.price,
                    },
                )
                raise OrderPlacementError(
                    error_msg,
                    symbol=symbol,
                    order_type="limit",
                    quantity=qty,
                    price=float(attempt_result.price),
                    reason="none_order_id_returned",
                )
            # Phase 5: Lifecycle tracking removed - handled by canonical executor path
            # Order lifecycle events are now emitted uniformly from CanonicalOrderExecutor
            try:
                order_result = context.wait_for_order_completion(
                    [order_id], max_wait_seconds=int(attempt_result.timeout_seconds)
                )
            except Exception as e:
                self.logger.error(
                    "strategy_order_completion_wait_error",
                    extra={
                        "strategy_name": self.strategy_name,
                        "symbol": symbol,
                        "order_id": order_id,
                        "attempt_index": attempt_index,
                        "error": str(e),
                    },
                )
                if attempt_index < self.config.max_attempts - 1:
                    continue
                raise OrderTimeoutError(
                    f"Failed to wait for order completion on final attempt: {e!s}",
                    symbol=symbol,
                    order_id=order_id,
                    timeout_seconds=attempt_result.timeout_seconds,
                    attempt_number=attempt_index + 1,
                )
            order_completed = order_id in order_result.orders_completed
            if order_completed and order_result.status == "completed":
                # Phase 5: Lifecycle tracking removed - handled by canonical executor path
                self.logger.info(
                    "strategy_order_filled",
                    extra={
                        "strategy_name": self.strategy_name,
                        "symbol": symbol,
                        "order_id": order_id,
                        "attempt_index": attempt_index,
                        "limit_price": attempt_result.price,
                        "timeout_used": attempt_result.timeout_seconds,
                    },
                )
                return order_id
            # Phase 5: Lifecycle tracking removed - handled by canonical executor path
            if attempt_index < self.config.max_attempts - 1:
                self.logger.info(
                    "strategy_preparing_next_attempt",
                    extra={
                        "strategy_name": self.strategy_name,
                        "symbol": symbol,
                        "attempt_index": attempt_index,
                        "next_attempt": attempt_index + 1,
                    },
                )
                try:
                    fresh_quote = context.get_latest_quote(symbol)
                    if not fresh_quote or len(fresh_quote) < 2:
                        raise SpreadAnalysisError(
                            f"Invalid fresh quote for re-peg: {fresh_quote}",
                            symbol=symbol,
                        )
                    bid, ask = Decimal(str(fresh_quote[0])), Decimal(str(fresh_quote[1]))
                    if bid <= 0 or ask <= 0:
                        raise SpreadAnalysisError(
                            f"Invalid bid/ask prices for re-peg: bid={bid}, ask={ask}",
                            symbol=symbol,
                            bid=float(bid),
                            ask=float(ask),
                        )
                    current_spread_cents = (ask - bid) * Decimal("100")
                    if self.repeg_strategy.should_pause_for_volatility(
                        original_spread_cents, current_spread_cents
                    ):
                        self.logger.warning(
                            "strategy_paused_for_volatility",
                            extra={
                                "strategy_name": self.strategy_name,
                                "symbol": symbol,
                                "attempt_index": attempt_index,
                                "original_spread_cents": original_spread_cents,
                                "current_spread_cents": current_spread_cents,
                                "spread_change_pct": (current_spread_cents - original_spread_cents)
                                / original_spread_cents
                                * 100,
                            },
                        )
                        break
                except SpreadAnalysisError:
                    raise
                except Exception as e:
                    raise SpreadAnalysisError(
                        f"Failed to get fresh quote for re-peg: {e!s}",
                        symbol=symbol,
                    )
            else:
                self.logger.warning(
                    "strategy_max_attempts_reached",
                    extra={
                        "strategy_name": self.strategy_name,
                        "symbol": symbol,
                        "max_attempts": self.config.max_attempts,
                        "final_order_id": order_id,
                    },
                )
        if self.enable_market_order_fallback:
            self.logger.info(
                "strategy_market_order_fallback",
                extra={
                    "strategy_name": self.strategy_name,
                    "symbol": symbol,
                    "reason": "limit_attempts_exhausted",
                    "max_attempts": self.config.max_attempts,
                },
            )
            fallback_order_id = context.place_market_order(symbol, side, qty=qty)
            if not fallback_order_id:
                raise OrderPlacementError(
                    f"Market order fallback also failed: {symbol} {side.value} {qty}",
                    symbol=symbol,
                    order_type="market",
                    quantity=qty,
                    reason="market_fallback_none_id",
                )
            # Phase 5: Lifecycle tracking removed - handled by canonical executor path
            return fallback_order_id
        raise OrderTimeoutError(
            f"All limit order attempts failed and market fallback disabled: {symbol} {side.value} {qty}",
            symbol=symbol,
            timeout_seconds=cumulative_expected_timeout,
            attempt_number=self.config.max_attempts,
        )

    # Phase 5: Lifecycle tracking method removed - all lifecycle events
    # are now emitted uniformly from CanonicalOrderExecutor path
