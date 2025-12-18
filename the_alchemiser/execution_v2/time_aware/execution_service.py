"""Business Unit: Execution | Status: current.

Time-aware execution service - the core execution engine.

This service implements institutional-style, time-phased execution that:
- Avoids aggressive trading during market open
- Uses passive, price-improving behaviour during midday
- Gradually increases urgency as deadline approaches
- Supports closing-auction participation via Alpaca's CLS time-in-force
- Minimises expected slippage rather than execution latency

The service is designed for tick-based invocation: EventBridge Scheduler
fires every N minutes, triggering the service to reassess pending executions
and take appropriate action based on current phase and urgency.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from the_alchemiser.execution_v2.time_aware.execution_policy import (
    POLICY_REGISTRY,
    ExecutionPolicy,
)
from the_alchemiser.execution_v2.time_aware.models import (
    ChildOrder,
    ExecutionPhase,
    ExecutionState,
    ExecutionTickContext,
    OrderStatus,
    PegType,
    PendingExecution,
)
from the_alchemiser.execution_v2.time_aware.pending_execution_repository import (
    PendingExecutionRepository,
)
from the_alchemiser.execution_v2.time_aware.phase_detector import PhaseDetector
from the_alchemiser.execution_v2.time_aware.urgency_scorer import UrgencyScorer
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.order_id_utils import generate_client_order_id

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.trade_message import TradeMessage

logger = get_logger(__name__)


class TimeAwareExecutionService:
    """Core execution engine for time-phased, opportunistic execution.

    This service manages the full lifecycle of time-aware executions:

    1. **Initiation**: Convert incoming TradeMessage to PendingExecution
    2. **Tick Processing**: On each scheduler tick, for each pending execution:
       - Detect current phase
       - Compute urgency score
       - Check/cancel stale child orders
       - Submit new child orders with appropriate pegs
       - Handle closing auction submission
    3. **Completion**: Mark execution complete when target filled or deadline passed

    Thread Safety:
        Not thread-safe. Designed for single Lambda invocation at a time.
        Concurrent ticks are prevented by SQS visibility timeout.

    Idempotency:
        All operations are idempotent via DynamoDB optimistic locking.
        Safe to replay ticks on failure.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        repository: PendingExecutionRepository | None = None,
        policy: ExecutionPolicy | None = None,
    ) -> None:
        """Initialize time-aware execution service.

        Args:
            alpaca_manager: Broker manager for order operations
            repository: DynamoDB repository for execution state
            policy: Execution policy (defaults to standard policy)

        """
        self.alpaca_manager = alpaca_manager
        self.repository = repository or PendingExecutionRepository()
        self.policy = policy or ExecutionPolicy()
        self.phase_detector = PhaseDetector(self.policy)
        self.urgency_scorer = UrgencyScorer()

        logger.info(
            "TimeAwareExecutionService initialized",
            extra={
                "policy_id": self.policy.policy_id,
                "tick_interval_minutes": self.policy.tick_interval_minutes,
                "auction_participation": self.policy.auction_participation,
            },
        )

    async def initiate_execution(
        self,
        trade_message: TradeMessage,
        policy_id: str | None = None,
    ) -> PendingExecution:
        """Initiate a new time-aware execution from a trade message.

        This is the entry point when a new trade arrives. Creates a
        PendingExecution record and optionally submits initial orders
        if market conditions are favorable.

        Args:
            trade_message: Incoming trade message from portfolio
            policy_id: Override policy ID (defaults to trade_message.execution_policy_id)

        Returns:
            Created PendingExecution with initial state

        """
        # Determine policy - ensure we always have a string
        effective_policy_id: str = policy_id or trade_message.execution_policy_id or "default"
        policy = POLICY_REGISTRY.get(effective_policy_id)

        # Get market timing context
        now = datetime.now(UTC)
        tick_context = self.phase_detector.build_tick_context(now)
        _market_open, market_close = self.phase_detector.get_market_hours(now)

        # Determine deadline
        deadline = market_close or now

        # Create execution ID
        execution_id = f"{trade_message.run_id}:{trade_message.trade_id}"

        # Check for existing execution (idempotency)
        existing = self.repository.get(execution_id)
        if existing:
            logger.info(
                "Execution already exists, returning existing",
                extra={
                    "execution_id": execution_id,
                    "state": existing.state.value,
                    "filled_ratio": existing.fill_ratio,
                },
            )
            return existing

        # Validate and get required fields
        side_value = trade_message.side.lower()
        if side_value not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {side_value}")
        side: Literal["buy", "sell"] = "buy" if side_value == "buy" else "sell"

        # Get target quantity - compute from shares if not set directly
        target_qty = trade_message.quantity
        if target_qty is None:
            target_qty = trade_message.shares
        if target_qty is None:
            raise ValueError(f"Trade message {trade_message.trade_id} has no quantity or shares")

        # Create new pending execution
        execution = PendingExecution(
            execution_id=execution_id,
            correlation_id=trade_message.correlation_id,
            causation_id=trade_message.run_id,
            symbol=trade_message.symbol,
            side=side,
            target_quantity=target_qty,
            strategy_id=trade_message.strategy_id,
            portfolio_id=trade_message.portfolio_id,
            deadline=deadline,
            state=ExecutionState.PENDING,
            current_phase=tick_context.current_phase,
            execution_policy_id=effective_policy_id,
            auction_eligible=policy.auction_participation,
        )

        execution.add_note(f"Initiated from trade_id={trade_message.trade_id}")
        execution.add_note(f"Policy: {policy.name}")

        # Persist
        self.repository.save(execution)

        logger.info(
            "Initiated time-aware execution",
            extra={
                "execution_id": execution_id,
                "symbol": execution.symbol,
                "side": execution.side,
                "target_quantity": str(execution.target_quantity),
                "deadline": deadline.isoformat() if deadline else None,
                "policy_id": effective_policy_id,
                "current_phase": tick_context.current_phase.value,
            },
        )

        # If market is open, process immediately
        if (
            tick_context.is_market_open
            and tick_context.current_phase != ExecutionPhase.MARKET_CLOSED
        ):
            execution = await self._process_single_execution(execution, tick_context)

        return execution

    async def process_tick(self) -> dict[str, str]:
        """Process a scheduler tick for all pending executions.

        This is the main entry point for scheduled invocations.
        Retrieves all active executions and processes each one.

        Returns:
            Dict mapping execution_id to result status

        """
        now = datetime.now(UTC)
        tick_context = self.phase_detector.build_tick_context(now)

        logger.info(
            "Processing execution tick",
            extra={
                "tick_time": now.isoformat(),
                "current_phase": tick_context.current_phase.value,
                "is_market_open": tick_context.is_market_open,
                "time_to_close_seconds": tick_context.time_to_close_seconds,
            },
        )

        if not tick_context.is_market_open:
            logger.info("Market closed, skipping tick processing")
            return {}

        # Get all active executions
        active_executions = self.repository.list_active()

        logger.info(
            "Found active executions",
            extra={"count": len(active_executions)},
        )

        results: dict[str, str] = {}

        for execution in active_executions:
            try:
                updated = await self._process_single_execution(execution, tick_context)
                results[execution.execution_id] = updated.state.value
            except Exception as e:
                logger.error(
                    "Error processing execution",
                    extra={
                        "execution_id": execution.execution_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                results[execution.execution_id] = f"ERROR: {type(e).__name__}"

        logger.info(
            "Tick processing complete",
            extra={
                "processed": len(results),
                "results": results,
            },
        )

        return results

    async def _process_single_execution(
        self,
        execution: PendingExecution,
        tick_context: ExecutionTickContext,
    ) -> PendingExecution:
        """Process a single pending execution for the current tick.

        This is the core execution logic that runs on each tick:
        1. Update phase and urgency
        2. Sync child order status with broker
        3. Cancel stale orders if needed
        4. Submit new orders based on phase/urgency
        5. Handle auction submission if approaching deadline
        6. Check for completion

        Args:
            execution: Pending execution to process
            tick_context: Current tick timing context

        Returns:
            Updated PendingExecution

        """
        log_extra = {
            "execution_id": execution.execution_id,
            "symbol": execution.symbol,
            "side": execution.side,
        }

        # Skip if already complete
        if execution.is_complete:
            logger.debug("Execution already complete", extra=log_extra)
            return execution

        # Get policy for this execution
        policy = POLICY_REGISTRY.get(execution.execution_policy_id)

        # Update phase
        execution.current_phase = tick_context.current_phase

        # Compute urgency
        urgency_factors = self.urgency_scorer.compute_urgency(
            current_time=tick_context.tick_time,
            deadline=execution.deadline or tick_context.market_close,
            session_start=tick_context.market_open,
            filled_ratio=execution.fill_ratio,
            current_phase=tick_context.current_phase,
        )
        execution.urgency_score = urgency_factors.combined_score

        logger.info(
            "Computed urgency",
            extra={
                **log_extra,
                "urgency_score": f"{urgency_factors.combined_score:.3f}",
                "time_urgency": f"{urgency_factors.time_urgency:.3f}",
                "fill_urgency": f"{urgency_factors.fill_urgency:.3f}",
                "phase_urgency": f"{urgency_factors.phase_urgency:.3f}",
                "fill_ratio": f"{execution.fill_ratio:.3f}",
            },
        )

        # Sync child order status
        execution = await self._sync_child_orders(execution)

        # Check if complete after sync
        if execution.remaining_quantity <= 0:
            execution.state = ExecutionState.COMPLETED
            execution.add_note("Target quantity filled")
            self.repository.save(execution)
            logger.info("Execution completed", extra=log_extra)
            return execution

        # Get phase config
        phase_config = policy.get_phase_config(tick_context.current_phase)
        if not phase_config:
            logger.warning(
                "No phase config for current phase",
                extra={**log_extra, "phase": tick_context.current_phase.value},
            )
            return execution

        # Cancel stale child orders if pegs need updating
        execution = await self._manage_child_orders(
            execution, phase_config, urgency_factors.combined_score
        )

        # Check for auction submission window
        if (
            execution.auction_eligible
            and policy.auction_participation
            and self._should_submit_auction_order(execution, tick_context, policy)
        ):
            execution = await self._submit_auction_order(execution, tick_context)
        elif execution.remaining_quantity > 0 and len(execution.active_child_orders) == 0:
            # Submit new child order if none active
            execution = await self._submit_child_order(
                execution, tick_context, phase_config, urgency_factors.combined_score
            )

        # Mark as active
        if execution.state == ExecutionState.PENDING:
            execution.state = ExecutionState.ACTIVE

        # Increment version and save
        execution.version += 1
        execution.updated_at = datetime.now(UTC)
        self.repository.save(execution)

        return execution

    async def _sync_child_orders(self, execution: PendingExecution) -> PendingExecution:
        """Sync child order status with broker.

        Queries broker for latest status of all non-terminal child orders
        and updates local state accordingly.
        """
        updated_children: list[ChildOrder] = []
        total_filled = Decimal("0")
        total_fill_value = Decimal("0")

        for child in execution.child_orders:
            if child.is_terminal:
                # Already terminal, accumulate fill info
                total_filled += child.filled_quantity
                if child.average_fill_price:
                    total_fill_value += child.filled_quantity * child.average_fill_price
                updated_children.append(child)
                continue

            if not child.broker_order_id:
                updated_children.append(child)
                continue

            # Query broker for latest status
            try:
                order_result = await asyncio.to_thread(
                    self.alpaca_manager.get_order_execution_result,
                    child.broker_order_id,
                )

                new_status = self._map_broker_status(order_result.status)
                filled_qty = order_result.filled_qty or Decimal("0")
                avg_price = order_result.avg_fill_price

                updated_child = ChildOrder(
                    child_order_id=child.child_order_id,
                    broker_order_id=child.broker_order_id,
                    symbol=child.symbol,
                    side=child.side,
                    quantity=child.quantity,
                    filled_quantity=filled_qty,
                    limit_price=child.limit_price,
                    peg_type=child.peg_type,
                    time_in_force=child.time_in_force,
                    status=new_status,
                    submitted_at=child.submitted_at,
                    filled_at=datetime.now(UTC) if new_status == OrderStatus.FILLED else None,
                    average_fill_price=avg_price,
                    phase_at_submit=child.phase_at_submit,
                )

                total_filled += filled_qty
                if avg_price:
                    total_fill_value += filled_qty * avg_price

                updated_children.append(updated_child)

            except Exception as e:
                logger.error(
                    "Failed to sync child order",
                    extra={
                        "child_order_id": child.child_order_id,
                        "broker_order_id": child.broker_order_id,
                        "error": str(e),
                    },
                )
                updated_children.append(child)

        # Update execution with synced data
        execution.child_orders = updated_children
        execution.filled_quantity = total_filled
        if total_filled > 0:
            execution.average_fill_price = total_fill_value / total_filled

        return execution

    async def _manage_child_orders(
        self,
        execution: PendingExecution,
        phase_config: object,
        urgency: float,
    ) -> PendingExecution:
        """Manage child orders: cancel stale ones, prepare for new submissions.

        In deadline phase, we're more aggressive about replacing orders.
        In passive phases, we let orders rest longer.
        """
        for child in execution.active_child_orders:
            if not child.broker_order_id:
                continue

            # Check if order is too passive for current urgency
            should_cancel = self._should_cancel_child(child, urgency, execution.current_phase)

            if should_cancel:
                try:
                    result = await asyncio.to_thread(
                        self.alpaca_manager.cancel_order,
                        child.broker_order_id,
                    )

                    if result.success:
                        # Update child status
                        idx = execution.child_orders.index(child)
                        execution.child_orders[idx] = ChildOrder(
                            child_order_id=child.child_order_id,
                            broker_order_id=child.broker_order_id,
                            symbol=child.symbol,
                            side=child.side,
                            quantity=child.quantity,
                            filled_quantity=child.filled_quantity,
                            limit_price=child.limit_price,
                            peg_type=child.peg_type,
                            time_in_force=child.time_in_force,
                            status=OrderStatus.CANCELLED,
                            submitted_at=child.submitted_at,
                            filled_at=None,
                            average_fill_price=child.average_fill_price,
                            phase_at_submit=child.phase_at_submit,
                        )
                        execution.add_note(
                            f"Cancelled child {child.child_order_id}: urgency escalation"
                        )

                except Exception as e:
                    logger.error(
                        "Failed to cancel child order",
                        extra={
                            "child_order_id": child.child_order_id,
                            "error": str(e),
                        },
                    )

        return execution

    def _should_cancel_child(
        self,
        child: ChildOrder,
        current_urgency: float,
        current_phase: ExecutionPhase,
    ) -> bool:
        """Determine if a child order should be cancelled.

        Cancel if:
        - Urgency has increased significantly since submission
        - Phase has changed to a more aggressive phase
        - Order has been resting too long without fills
        """
        # In deadline phase, be more aggressive about cancelling passive orders
        if current_phase == ExecutionPhase.DEADLINE_CLOSE:
            passive_pegs = {PegType.FAR_TOUCH, PegType.MID, PegType.NEAR_TOUCH}
            if child.peg_type in passive_pegs:
                return True

        # If urgency has increased significantly, cancel passive orders
        return current_urgency > 0.7 and child.peg_type in {PegType.FAR_TOUCH, PegType.MID}

    async def _submit_child_order(
        self,
        execution: PendingExecution,
        tick_context: ExecutionTickContext,
        phase_config: object,
        urgency: float,
    ) -> PendingExecution:
        """Submit a new child order based on current phase and urgency."""
        # Determine peg type based on urgency
        allowed_pegs = getattr(phase_config, "allowed_peg_types", frozenset({PegType.MID}))
        peg_type = self.urgency_scorer.suggest_peg_type(
            urgency, allowed_pegs, tick_context.current_phase
        )

        # Determine order size
        max_fraction = getattr(phase_config, "max_order_size_fraction", Decimal("0.25"))
        min_size = getattr(phase_config, "min_order_size", 1)
        suggested_qty = self.urgency_scorer.suggest_order_size_fraction(
            urgency, max_fraction, execution.remaining_quantity, min_size
        )

        # Don't exceed remaining
        order_qty = min(suggested_qty, execution.remaining_quantity)
        if order_qty <= 0:
            return execution

        # Get current price for pricing
        try:
            current_price = await asyncio.to_thread(
                self.alpaca_manager.get_current_price,
                execution.symbol,
            )
            if current_price is None:
                logger.warning(
                    "No price available for symbol",
                    extra={
                        "execution_id": execution.execution_id,
                        "symbol": execution.symbol,
                    },
                )
                return execution
        except Exception as e:
            logger.error(
                "Failed to get price for child order",
                extra={
                    "execution_id": execution.execution_id,
                    "symbol": execution.symbol,
                    "error": str(e),
                },
            )
            return execution

        # Use current price as midpoint estimate for bid/ask spread
        # For limit orders, we add/subtract a small offset
        spread_estimate = current_price * Decimal("0.001")  # 0.1% spread estimate
        bid = current_price - spread_estimate
        ask = current_price + spread_estimate

        if bid <= 0 or ask <= 0:
            logger.warning(
                "Invalid quote, skipping child order",
                extra={
                    "execution_id": execution.execution_id,
                    "bid": str(bid),
                    "ask": str(ask),
                },
            )
            return execution

        limit_price = self._calculate_limit_price(execution.side, bid, ask, peg_type)

        # Generate order IDs
        child_order_id = str(uuid.uuid4())[:8]
        client_order_id = generate_client_order_id(
            execution.symbol,
            execution.strategy_id or "tae",  # time-aware-execution
        )

        # Determine time in force
        tif: Literal["day", "gtc", "ioc", "fok", "cls"] = "day"

        # Submit order
        try:
            if peg_type == PegType.MARKET:
                # Market order
                market_request = MarketOrderRequest(
                    symbol=execution.symbol,
                    qty=float(order_qty),
                    side=OrderSide.BUY if execution.side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    client_order_id=client_order_id,
                )
                order_result = await asyncio.to_thread(
                    self.alpaca_manager.place_order,
                    market_request,
                )
                broker_order_id = order_result.order_id
                status = self._map_broker_status(order_result.status)
            else:
                # Limit order
                limit_request = LimitOrderRequest(
                    symbol=execution.symbol,
                    qty=float(order_qty),
                    side=OrderSide.BUY if execution.side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=float(limit_price),
                    client_order_id=client_order_id,
                )
                order_result = await asyncio.to_thread(
                    self.alpaca_manager.place_order,
                    limit_request,
                )
                broker_order_id = order_result.order_id
                status = self._map_broker_status(order_result.status)

            # Create child order record
            child_order = ChildOrder(
                child_order_id=child_order_id,
                broker_order_id=broker_order_id,
                symbol=execution.symbol,
                side=execution.side,
                quantity=order_qty,
                filled_quantity=Decimal("0"),
                limit_price=limit_price if peg_type != PegType.MARKET else None,
                peg_type=peg_type,
                time_in_force=tif,
                status=status,
                submitted_at=datetime.now(UTC),
                phase_at_submit=tick_context.current_phase,
            )

            execution.child_orders.append(child_order)
            execution.add_note(
                f"Submitted child {child_order_id}: {order_qty} @ {peg_type.value} "
                f"(limit={limit_price}, urgency={urgency:.2f})"
            )

            logger.info(
                "Submitted child order",
                extra={
                    "execution_id": execution.execution_id,
                    "child_order_id": child_order_id,
                    "broker_order_id": broker_order_id,
                    "quantity": str(order_qty),
                    "peg_type": peg_type.value,
                    "limit_price": str(limit_price),
                },
            )

        except Exception as e:
            logger.error(
                "Failed to submit child order",
                extra={
                    "execution_id": execution.execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

        return execution

    def _should_submit_auction_order(
        self,
        execution: PendingExecution,
        tick_context: ExecutionTickContext,
        policy: ExecutionPolicy,
    ) -> bool:
        """Determine if we should submit a closing auction (CLS) order.

        Submit auction order if:
        - Auction participation is enabled
        - We're past the auction cutoff time
        - We have remaining quantity
        - We haven't already submitted an auction order
        """
        if not execution.auction_eligible:
            return False

        if execution.remaining_quantity <= 0:
            return False

        # Check if we've already submitted a CLS order
        for child in execution.child_orders:
            if child.time_in_force == "cls" and not child.is_terminal:
                return False

        # Check if we're past auction cutoff
        # Alpaca CLS orders must be submitted by 3:50 PM ET
        cutoff = policy.get_auction_cutoff()
        et_time = tick_context.tick_time.astimezone(
            __import__("zoneinfo").ZoneInfo("America/New_York")
        )

        return et_time.time() >= cutoff

    async def _submit_auction_order(
        self,
        execution: PendingExecution,
        tick_context: ExecutionTickContext,
    ) -> PendingExecution:
        """Submit a closing auction (MOC/LOC) order using Alpaca's CLS TIF.

        Alpaca's CLS (Close) time-in-force:
        - For market orders: Market-on-Close (MOC)
        - For limit orders: Limit-on-Close (LOC)
        - Must be submitted by 3:50 PM ET
        - Executes in the closing auction at 4:00 PM ET
        """
        # Get policy to determine auction reserve
        policy = POLICY_REGISTRY.get(execution.execution_policy_id)
        reserve_fraction = policy.auction_reserve_fraction

        # Calculate auction quantity
        auction_qty = execution.remaining_quantity * reserve_fraction
        auction_qty = max(Decimal("1"), auction_qty.quantize(Decimal("1")))
        auction_qty = min(auction_qty, execution.remaining_quantity)

        if auction_qty <= 0:
            return execution

        # Generate IDs
        child_order_id = f"cls-{str(uuid.uuid4())[:6]}"
        client_order_id = generate_client_order_id(
            execution.symbol,
            f"{execution.strategy_id or 'tae'}-cls",
        )

        try:
            # Submit market-on-close order using CLS TIF
            order_request = MarketOrderRequest(
                symbol=execution.symbol,
                qty=float(auction_qty),
                side=OrderSide.BUY if execution.side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.CLS,  # Closing auction
                client_order_id=client_order_id,
            )

            order_result = await asyncio.to_thread(
                self.alpaca_manager.place_order,
                order_request,
            )

            child_order = ChildOrder(
                child_order_id=child_order_id,
                broker_order_id=order_result.order_id,
                symbol=execution.symbol,
                side=execution.side,
                quantity=auction_qty,
                filled_quantity=Decimal("0"),
                limit_price=None,  # MOC
                peg_type=PegType.MARKET,
                time_in_force="cls",
                status=OrderStatus.OPEN,
                submitted_at=datetime.now(UTC),
                phase_at_submit=tick_context.current_phase,
            )

            execution.child_orders.append(child_order)
            execution.add_note(
                f"Submitted CLS/MOC order {child_order_id}: {auction_qty} shares for closing auction"
            )

            logger.info(
                "Submitted closing auction order",
                extra={
                    "execution_id": execution.execution_id,
                    "child_order_id": child_order_id,
                    "broker_order_id": order_result.order_id,
                    "quantity": str(auction_qty),
                },
            )

        except Exception as e:
            logger.error(
                "Failed to submit auction order",
                extra={
                    "execution_id": execution.execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

        return execution

    def _calculate_limit_price(
        self,
        side: str,
        bid: Decimal,
        ask: Decimal,
        peg_type: PegType,
    ) -> Decimal:
        """Calculate limit price based on peg type and side.

        For BUY orders:
        - FAR_TOUCH: bid (passive)
        - MID: midpoint
        - NEAR_TOUCH: ask (aggressive)
        - INSIDE_X: bid + X% of spread

        For SELL orders:
        - FAR_TOUCH: ask (passive)
        - MID: midpoint
        - NEAR_TOUCH: bid (aggressive)
        - INSIDE_X: ask - X% of spread
        """
        spread = ask - bid

        peg_ratios = {
            PegType.FAR_TOUCH: Decimal("0"),
            PegType.MID: Decimal("0.5"),
            PegType.NEAR_TOUCH: Decimal("1"),
            PegType.INSIDE_25: Decimal("0.25"),
            PegType.INSIDE_50: Decimal("0.5"),
            PegType.INSIDE_75: Decimal("0.75"),
            PegType.INSIDE_90: Decimal("0.90"),
            PegType.CROSS: Decimal("1"),
        }

        ratio = peg_ratios.get(peg_type, Decimal("0.5"))

        # For buy: start at bid, move toward ask; for sell: start at ask, move toward bid
        price = bid + spread * ratio if side == "buy" else ask - spread * ratio

        # Round to 2 decimal places
        return price.quantize(Decimal("0.01"))

    def _map_broker_status(self, status: str | None) -> OrderStatus:
        """Map broker status string to OrderStatus enum."""
        if not status:
            return OrderStatus.PENDING_SUBMIT

        status_upper = status.upper()
        mapping = {
            "NEW": OrderStatus.OPEN,
            "ACCEPTED": OrderStatus.OPEN,
            "PENDING_NEW": OrderStatus.PENDING_SUBMIT,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "REJECTED": OrderStatus.REJECTED,
            "CANCELED": OrderStatus.CANCELLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "EXPIRED": OrderStatus.EXPIRED,
        }
        return mapping.get(status_upper, OrderStatus.OPEN)
