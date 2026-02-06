#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Single trade handler for per-trade parallel execution via SQS Standard queue.

Processes TradeMessage events to execute individual trades. Multiple Lambda
invocations process trades concurrently (up to 10 via ReservedConcurrentExecutions),
enabling parallel execution within each phase.

Two-phase ordering (sells before buys) is achieved via enqueue timing:
1. Portfolio Lambda enqueues only SELL trades initially (BUYs stored in DynamoDB)
2. Execution Lambdas process SELLs in parallel
3. When all SELLs complete, the last Lambda enqueues BUY trades
4. BUY trades execute in parallel via fresh Lambda invocations

Note: Despite env var name (EXECUTION_FIFO_QUEUE_URL), we use a Standard queue.
The sequence_number field is preserved for debugging/ordering visibility but does
not provide FIFO guarantees - ordering is controlled by enqueue timing.

This handler is part of the per-trade execution architecture:
- Portfolio Lambda decomposes RebalancePlan into individual TradeMessages
- DynamoDB tracks run state (total_trades, completed_trades, phase)
- When sell_completed == sell_total, this handler triggers BUY phase enqueue
- Notifications Lambda aggregates results when all trades complete
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from core.smart_execution_strategy import ExecutionConfig
from models.execution_result import OrderResult
from services.trade_ledger import TradeLedgerService

from the_alchemiser.shared.constants import EXECUTION_HANDLERS_MODULE
from the_alchemiser.shared.errors import (
    ExecutionManagerError,
    MarketDataError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.events import (
    EventBus,
    TradeExecuted,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.trade_message import TradeMessage
from the_alchemiser.shared.services.execution_run_service import (
    ExecutionRunService,
)

if TYPE_CHECKING:
    from core.executor import Executor

    from the_alchemiser.shared.config.container import ApplicationContainer


class SingleTradeHandler:
    """Event handler for single trade execution from SQS Standard queue.

    Processes individual TradeMessage events. Multiple Lambdas can process
    trades in parallel (up to 10 concurrent via ReservedConcurrentExecutions).
    Each invocation is stateless and idempotent - duplicate messages are detected
    via DynamoDB trade state tracking.

    Two-Phase Parallel Execution:
    1. Portfolio Lambda enqueues SELL trades only (BUYs stored in DynamoDB)
    2. Multiple Lambdas process SELLs in parallel
    3. Each Lambda marks its trade complete in DynamoDB
    4. When all SELLs complete, the last Lambda enqueues BUY trades
    5. BUYs execute in parallel via fresh Lambda invocations

    Workflow per invocation:
    1. Parse TradeMessage from SQS record
    2. Check for duplicate execution (idempotency via DynamoDB)
    3. Mark trade as started in DynamoDB
    4. Execute the trade using Executor
    5. Mark trade as completed/failed in DynamoDB with result
    6. Emit TradeExecuted event for this individual trade
    7. If this was the last SELL, enqueue BUY trades to trigger phase 2

    The Notifications Lambda monitors DynamoDB and aggregates results when
    all trades in a run are complete.
    """

    def __init__(
        self,
        container: ApplicationContainer,
        run_service: ExecutionRunService | None = None,
    ) -> None:
        """Initialize the single trade handler.

        Args:
            container: Application container for dependency injection
            run_service: Optional ExecutionRunService (created if not provided)

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

        # Initialize run service for DynamoDB state tracking
        if run_service:
            self.run_service = run_service
        else:
            table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "ExecutionRunsTable")
            self.run_service = ExecutionRunService(table_name=table_name)

        # Initialize trade ledger service for persisting executed trades
        self.trade_ledger = TradeLedgerService()

        # Track processed idempotency keys for this invocation
        # (in addition to DynamoDB checks for cross-invocation deduplication)
        self._processed_keys: set[str] = set()

    def handle_sqs_record(self, sqs_record: dict[str, Any]) -> dict[str, Any]:
        """Handle a single SQS FIFO record containing a TradeMessage.

        Args:
            sqs_record: SQS record from Lambda event

        Returns:
            Dict with execution result for this trade

        """
        try:
            # Parse TradeMessage from SQS body
            body = sqs_record.get("body", "{}")
            trade_message = TradeMessage.from_sqs_message_body(body)

            self.logger.info(
                f"📥 Received trade message: {trade_message.action} {trade_message.symbol}",
                extra={
                    "run_id": trade_message.run_id,
                    "trade_id": trade_message.trade_id,
                    "symbol": trade_message.symbol,
                    "action": trade_message.action,
                    "phase": trade_message.phase,
                    "sequence_number": trade_message.sequence_number,
                    "correlation_id": trade_message.correlation_id,
                },
            )

            # Check for duplicate execution via idempotency key
            idempotency_key = self._generate_idempotency_key(trade_message)
            if self._is_duplicate_trade(trade_message, idempotency_key):
                self.logger.warning(
                    f"⚠️ Duplicate trade detected (idempotency_key: {idempotency_key}) - skipping",
                    extra={
                        "run_id": trade_message.run_id,
                        "trade_id": trade_message.trade_id,
                        "idempotency_key": idempotency_key,
                    },
                )
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "duplicate_trade",
                    "trade_id": trade_message.trade_id,
                }

            # Execute the trade
            result = self._execute_trade(trade_message)

            return {
                "success": result.get("success", False),
                "trade_id": trade_message.trade_id,
                "symbol": trade_message.symbol,
                "order_id": result.get("order_id"),
                "error": result.get("error"),
            }

        except ValidationError as e:
            self.logger.error(
                f"Validation error processing SQS record: {e}",
                extra={"error_type": "ValidationError", "sqs_record": sqs_record},
            )
            return {"success": False, "error": str(e), "error_type": "ValidationError"}

        except Exception as e:
            self.logger.error(
                f"Unexpected error processing SQS record: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__, "sqs_record": sqs_record},
            )
            return {"success": False, "error": str(e), "error_type": type(e).__name__}

    def _generate_idempotency_key(self, trade_message: TradeMessage) -> str:
        """Generate deterministic idempotency key for trade deduplication.

        Args:
            trade_message: The trade message to generate key for

        Returns:
            16-character hex string hash for deduplication

        """
        key_material = (
            f"{trade_message.run_id}:{trade_message.trade_id}:"
            f"{trade_message.symbol}:{trade_message.action}"
        )
        return hashlib.sha256(key_material.encode()).hexdigest()[:16]

    def _is_duplicate_trade(self, trade_message: TradeMessage, idempotency_key: str) -> bool:
        """Check if trade has already been executed.

        Uses DynamoDB to check trade state across Lambda invocations.

        Args:
            trade_message: The trade message
            idempotency_key: The computed idempotency key

        Returns:
            True if trade has been executed before, False otherwise

        """
        # First check in-memory cache for this invocation
        if idempotency_key in self._processed_keys:
            return True

        # Check DynamoDB for cross-invocation deduplication using efficient GetItem
        try:
            # Direct lookup is O(1) vs O(n) for get_all_trade_results
            trade_result = self.run_service.get_trade_result(
                trade_message.run_id, trade_message.trade_id
            )
            if trade_result is not None:
                # Trade already exists - check if it's completed
                status = trade_result.get("status", "PENDING")
                if status in ("COMPLETED", "FAILED"):
                    self.logger.debug(
                        f"Trade already completed in DynamoDB: {trade_message.trade_id} (status={status})"
                    )
                    return True
                # Trade exists but still PENDING/RUNNING - not a duplicate completion
                self.logger.debug(
                    f"Trade exists but not completed: {trade_message.trade_id} (status={status})"
                )

            return False

        except Exception as e:
            # On error checking duplicates, log warning but proceed
            # (better to risk duplicate detection failure than block execution)
            self.logger.warning(
                f"Error checking for duplicate trade, proceeding: {e}",
                extra={
                    "run_id": trade_message.run_id,
                    "trade_id": trade_message.trade_id,
                    "error": str(e),
                },
            )
            return False

    def _execute_trade(self, trade_message: TradeMessage) -> dict[str, Any]:
        """Execute a single trade from the TradeMessage.

        Args:
            trade_message: The trade message containing trade details

        Returns:
            Dict with execution result

        """
        run_id = trade_message.run_id
        trade_id = trade_message.trade_id
        correlation_id = trade_message.correlation_id

        try:
            # Mark trade as started in DynamoDB
            self.run_service.mark_trade_started(run_id, trade_id)
            self.logger.info(
                f"🚀 Starting trade execution: {trade_message.action} {trade_message.symbol}",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "symbol": trade_message.symbol,
                    "action": trade_message.action,
                    "correlation_id": correlation_id,
                },
            )

            # Check market status before executing
            market_is_open = self._check_market_status(correlation_id)
            if not market_is_open:
                return self._handle_market_closed(trade_message)

            # Check equity circuit breaker for BUY trades
            if trade_message.phase == "BUY":
                breaker_result = self._check_equity_circuit_breaker(trade_message)
                if breaker_result:
                    return breaker_result

            # Execute the trade with retries for SELL phase
            order_result = self._execute_order_with_retries(trade_message, correlation_id)

            # Record successful trade to Trade Ledger DynamoDB
            self._record_trade_to_ledger(order_result, trade_message, correlation_id)

            # Mark trade completed in DynamoDB with execution data
            execution_data = {
                "shares": str(order_result.shares),
                "price": str(order_result.price) if order_result.price else None,
                "trade_amount": str(order_result.trade_amount),
                "order_type": order_result.order_type,
                "filled_at": order_result.filled_at.isoformat() if order_result.filled_at else None,
            }

            completion_result = self.run_service.mark_trade_completed(
                run_id=run_id,
                trade_id=trade_id,
                success=order_result.success,
                order_id=order_result.order_id,
                error_message=order_result.error_message,
                execution_data=execution_data,
                phase=trade_message.phase,  # For phase-specific tracking
                trade_amount=abs(trade_message.trade_amount),  # For SELL phase guard
            )

            # Check if this completes the SELL phase and trigger BUY phase if needed
            self._check_and_trigger_buy_phase(
                run_id=run_id,
                correlation_id=correlation_id,
                completion_result=completion_result,
            )

            # Mark idempotency key as processed
            idempotency_key = self._generate_idempotency_key(trade_message)
            self._processed_keys.add(idempotency_key)

            # Emit TradeExecuted event for this trade
            self._emit_trade_executed_event(
                trade_message=trade_message,
                success=order_result.success,
                order_id=order_result.order_id,
                shares_executed=order_result.shares,
                price=order_result.price,
                error_message=order_result.error_message,
            )

            self.logger.info(
                f"{'✅' if order_result.success else '❌'} Trade execution complete: "
                f"{trade_message.action} {trade_message.symbol}",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "symbol": trade_message.symbol,
                    "action": trade_message.action,
                    "success": order_result.success,
                    "order_id": order_result.order_id,
                    "correlation_id": correlation_id,
                },
            )

            return {
                "success": order_result.success,
                "order_id": order_result.order_id,
                "trade_id": trade_id,
                "shares": str(order_result.shares),
                "price": str(order_result.price) if order_result.price else None,
                "error": order_result.error_message,
            }

        except (ExecutionManagerError, TradingClientError, MarketDataError) as e:
            # Domain-specific execution errors - log descriptively and continue
            self.logger.error(
                f"❌ Trade execution failed for {trade_message.symbol} ({trade_message.phase} phase): {e}",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "symbol": trade_message.symbol,
                    "action": trade_message.action,
                    "phase": trade_message.phase,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "correlation_id": correlation_id,
                    "trade_amount": str(trade_message.trade_amount),
                    "failure_context": "Execution will continue with remaining trades",
                },
            )

            # Mark trade completed (as failure) in DynamoDB - still track phase completion
            completion_result = self.run_service.mark_trade_completed(
                run_id=run_id,
                trade_id=trade_id,
                success=False,
                order_id=None,
                error_message=str(e),
                phase=trade_message.phase,  # For phase-specific tracking
                trade_amount=abs(trade_message.trade_amount),  # For SELL phase guard
            )

            # Check if this completes the SELL phase (even with failures)
            self._check_and_trigger_buy_phase(
                run_id=run_id,
                correlation_id=correlation_id,
                completion_result=completion_result,
            )

            # Emit TradeExecuted event for this failed trade
            self._emit_trade_executed_event(
                trade_message=trade_message,
                success=False,
                order_id=None,
                shares_executed=Decimal("0"),
                price=None,
                error_message=str(e),
            )

            return {
                "success": False,
                "trade_id": trade_id,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        except Exception as e:
            # Unexpected errors - log descriptively with full context
            self.logger.error(
                f"❌ Unexpected error executing trade {trade_message.symbol} ({trade_message.phase} phase): {e}",
                exc_info=True,
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "symbol": trade_message.symbol,
                    "action": trade_message.action,
                    "phase": trade_message.phase,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "correlation_id": correlation_id,
                    "trade_amount": str(trade_message.trade_amount),
                    "failure_context": "Unexpected error - execution will continue with remaining trades",
                },
            )

            # Mark trade completed (as failure) in DynamoDB
            try:
                completion_result = self.run_service.mark_trade_completed(
                    run_id=run_id,
                    trade_id=trade_id,
                    success=False,
                    order_id=None,
                    error_message=f"Unexpected error: {e}",
                    phase=trade_message.phase,  # For phase-specific tracking
                    trade_amount=abs(trade_message.trade_amount),  # For SELL phase guard
                )

                # Check if this completes the SELL phase (even with failures)
                self._check_and_trigger_buy_phase(
                    run_id=run_id,
                    correlation_id=correlation_id,
                    completion_result=completion_result,
                )
            except Exception as db_error:
                self.logger.error(
                    f"Failed to mark trade as failed in DynamoDB: {db_error}",
                    extra={"run_id": run_id, "trade_id": trade_id},
                )

            # Emit TradeExecuted event for this failed trade
            self._emit_trade_executed_event(
                trade_message=trade_message,
                success=False,
                order_id=None,
                shares_executed=Decimal("0"),
                price=None,
                error_message=f"Unexpected error: {e}",
            )

            return {
                "success": False,
                "trade_id": trade_id,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _create_executor(self) -> Executor:
        """Create and configure Executor for trade execution.

        Returns:
            Configured Executor instance

        """
        # Import here to avoid circular imports
        from core.executor import Executor

        alpaca_manager = self.container.infrastructure.alpaca_manager()

        return Executor(
            alpaca_manager=alpaca_manager,
            execution_config=ExecutionConfig(),
        )

    def _check_and_trigger_buy_phase(
        self,
        run_id: str,
        correlation_id: str,
        completion_result: dict[str, Any],
    ) -> None:
        """Check if SELL phase is complete and trigger BUY phase if needed.

        For two-phase execution, when all SELL trades complete (success or failure),
        this method evaluates the BUY phase guard before enqueuing BUY trades.

        BUY Phase Guard: If sell_failed_amount exceeds the configured threshold
        (sell_failure_threshold_usd), the BUY phase is BLOCKED to prevent
        over-deployment and potential margin calls. The run is marked FAILED
        and a WorkflowFailed event is emitted.

        Args:
            run_id: Run identifier.
            correlation_id: Workflow correlation ID.
            completion_result: Result from mark_trade_completed with phase completion info.

        """
        # Check if this is two-phase execution and SELL phase just completed
        current_phase = completion_result.get("current_phase", "ALL")
        sell_phase_complete = completion_result.get("sell_phase_complete", False)
        buy_total = completion_result.get("buy_total", 0)

        # Only trigger BUY phase if:
        # 1. We're in SELL phase (two-phase execution)
        # 2. All SELLs have completed
        # 3. There are BUY trades waiting
        if current_phase != "SELL" or not sell_phase_complete or buy_total == 0:
            return

        # ========================================
        # BUY PHASE GUARD: Check SELL failure threshold
        # ========================================
        sell_failed_amount = completion_result.get("sell_failed_amount", Decimal("0"))
        sell_succeeded_amount = completion_result.get("sell_succeeded_amount", Decimal("0"))

        # Get the failure threshold from ExecutionConfig
        config = ExecutionConfig()
        failure_threshold = config.sell_failure_threshold_usd

        if sell_failed_amount > failure_threshold:
            # CRITICAL: Block BUY phase to prevent over-deployment
            self.logger.critical(
                "🚫 BUY PHASE BLOCKED - SELL failures exceed threshold! "
                f"Failed: ${sell_failed_amount:.2f} > Threshold: ${failure_threshold:.2f}",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "sell_failed_amount": str(sell_failed_amount),
                    "sell_succeeded_amount": str(sell_succeeded_amount),
                    "failure_threshold": str(failure_threshold),
                    "buy_trades_blocked": buy_total,
                    "guard_action": "BUY_PHASE_BLOCKED",
                },
            )

            # Mark run as FAILED (not transitioning to BUY phase)
            self.run_service.update_run_status(run_id, "FAILED")

            # Emit WorkflowFailed event for notifications
            self._emit_buy_phase_blocked_event(
                run_id=run_id,
                correlation_id=correlation_id,
                sell_failed_amount=sell_failed_amount,
                sell_succeeded_amount=sell_succeeded_amount,
                failure_threshold=failure_threshold,
                buy_trades_blocked=buy_total,
            )

            return

        # SELL failures within threshold - proceed with BUY phase
        if sell_failed_amount > Decimal("0"):
            self.logger.warning(
                f"⚠️ SELL phase had failures (${sell_failed_amount:.2f}) but within threshold "
                f"(${failure_threshold:.2f}) - proceeding with BUY phase",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "sell_failed_amount": str(sell_failed_amount),
                    "sell_succeeded_amount": str(sell_succeeded_amount),
                    "failure_threshold": str(failure_threshold),
                },
            )

        self.logger.info(
            "🔄 SELL phase complete - triggering BUY phase",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "sell_completed": completion_result.get("sell_completed", 0),
                "sell_total": completion_result.get("sell_total", 0),
                "sell_failed_amount": str(sell_failed_amount),
                "sell_succeeded_amount": str(sell_succeeded_amount),
                "buy_total": buy_total,
            },
        )

        try:
            # Transition run to BUY phase (idempotent - only one Lambda will succeed)
            transitioned = self.run_service.transition_to_buy_phase(run_id)

            if not transitioned:
                # Another Lambda already triggered the BUY phase
                self.logger.debug(
                    "BUY phase already triggered by another invocation",
                    extra={"run_id": run_id},
                )
                return

            # Get pending BUY trades from DynamoDB
            buy_trades = self.run_service.get_pending_buy_trades(run_id)

            if not buy_trades:
                self.logger.warning(
                    "No BUY trades found to enqueue",
                    extra={"run_id": run_id, "correlation_id": correlation_id},
                )
                return

            # Enqueue BUY trades to SQS
            import boto3

            sqs_client = boto3.client("sqs")
            queue_url = os.environ.get("EXECUTION_FIFO_QUEUE_URL", "")

            if not queue_url:
                self.logger.error(
                    "EXECUTION_FIFO_QUEUE_URL not configured - cannot enqueue BUY trades",
                    extra={"run_id": run_id},
                )
                return

            enqueued_trade_ids = []
            for trade in buy_trades:
                try:
                    sqs_client.send_message(
                        QueueUrl=queue_url,
                        MessageBody=trade["message_body"],
                        MessageDeduplicationId=trade["trade_id"],  # Exactly-once per trade
                        MessageGroupId=trade["symbol"],  # Parallel execution across symbols
                        MessageAttributes={
                            "RunId": {"DataType": "String", "StringValue": run_id},
                            "TradeId": {"DataType": "String", "StringValue": trade["trade_id"]},
                            "Phase": {"DataType": "String", "StringValue": "BUY"},
                        },
                    )
                    enqueued_trade_ids.append(trade["trade_id"])
                except Exception as e:
                    self.logger.error(
                        f"Failed to enqueue BUY trade {trade['trade_id']}: {e}",
                        extra={
                            "run_id": run_id,
                            "trade_id": trade["trade_id"],
                            "error": str(e),
                        },
                    )

            # Mark enqueued trades as PENDING
            if enqueued_trade_ids:
                self.run_service.mark_buy_trades_pending(run_id, enqueued_trade_ids)

            self.logger.info(
                "✅ Enqueued BUY trades for parallel execution",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "buy_enqueued": len(enqueued_trade_ids),
                    "buy_total": buy_total,
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to trigger BUY phase: {e}",
                exc_info=True,
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _check_market_status(self, correlation_id: str) -> bool:
        """Check if market is currently open for trading.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            True if market is open, False otherwise

        """
        try:
            from the_alchemiser.shared.services.market_clock_service import (
                MarketClockService,
            )

            trading_client = self.container.infrastructure.alpaca_manager().trading_client
            market_clock_service = MarketClockService(trading_client)

            is_open = market_clock_service.is_market_open(correlation_id=correlation_id)

            self.logger.debug(
                f"Market status: {'OPEN' if is_open else 'CLOSED'}",
                extra={"correlation_id": correlation_id, "market_is_open": is_open},
            )

            return is_open

        except Exception as e:
            # On error, assume market is open to avoid blocking trades
            self.logger.warning(
                f"Market status check failed - assuming OPEN: {e}",
                extra={"correlation_id": correlation_id, "error_type": type(e).__name__},
            )
            return True

    def _calculate_shares(self, trade_message: TradeMessage) -> Decimal:
        """Calculate shares to trade from trade amount.

        For full liquidations (target_weight = 0), fetches the actual position
        from Alpaca to ensure we sell exactly what we hold, avoiding floating-point
        precision mismatches between calculated and actual positions.

        For ALL sell orders, the calculated quantity is capped to the actual
        position to prevent attempting to sell more shares than held.

        Args:
            trade_message: The trade message

        Returns:
            Number of shares to trade

        Raises:
            MarketDataError: If unable to get price for share calculation

        """
        # CRITICAL: For full liquidations, use actual position from Alpaca
        # This avoids floating-point precision errors between calculated and actual positions
        is_full_liquidation = (
            trade_message.is_full_liquidation or trade_message.target_weight <= Decimal("0")
        )
        if is_full_liquidation and trade_message.action == "SELL":
            try:
                alpaca_manager = self.container.infrastructure.alpaca_manager()
                position = alpaca_manager.get_position(trade_message.symbol)
                if position:
                    actual_qty = getattr(position, "qty", None)
                    if actual_qty and Decimal(str(actual_qty)) > 0:
                        shares = Decimal(str(actual_qty))
                        # Calculate what we would have used for comparison logging
                        calculated_shares = None
                        if trade_message.estimated_price and trade_message.estimated_price > 0:
                            calculated_shares = (
                                abs(trade_message.trade_amount) / trade_message.estimated_price
                            )
                        self.logger.info(
                            "Using actual position for full liquidation",
                            extra={
                                "symbol": trade_message.symbol,
                                "actual_position": str(shares),
                                "calculated_would_be": str(calculated_shares)
                                if calculated_shares
                                else "unknown",
                            },
                        )
                        return shares
            except Exception as e:
                self.logger.warning(
                    f"Failed to fetch position for full liquidation, "
                    f"falling back to calculation: {e}",
                    extra={"symbol": trade_message.symbol},
                )

        # If explicit shares provided, use those
        if trade_message.shares and trade_message.shares > 0:
            shares = trade_message.shares
        # Otherwise calculate from trade_amount and estimated price
        elif trade_message.estimated_price and trade_message.estimated_price > 0:
            shares = abs(trade_message.trade_amount) / trade_message.estimated_price
            shares = shares.quantize(Decimal("0.000001"))
        else:
            # No estimated price provided - fetch current market price
            # This is critical: we must NOT use trade_amount (dollars) as shares
            try:
                alpaca_manager = self.container.infrastructure.alpaca_manager()
                current_price = alpaca_manager.get_current_price(trade_message.symbol)

                if current_price and current_price > 0:
                    shares = abs(trade_message.trade_amount) / Decimal(str(current_price))
                    self.logger.debug(
                        f"Calculated shares from current price: {shares:.6f} "
                        f"(${abs(trade_message.trade_amount):.2f} / ${current_price:.2f})",
                        extra={
                            "symbol": trade_message.symbol,
                            "trade_amount": str(trade_message.trade_amount),
                            "current_price": str(current_price),
                            "shares": str(shares),
                        },
                    )
                    shares = shares.quantize(Decimal("0.000001"))
                else:
                    # Price is None or 0 - this is an error condition
                    raise MarketDataError(
                        f"Unable to get valid price for {trade_message.symbol}: "
                        f"price={current_price}"
                    )

            except MarketDataError:
                raise
            except Exception as e:
                raise MarketDataError(
                    f"Failed to fetch price for {trade_message.symbol} to calculate shares: {e}"
                ) from e

        # SAFETY CAP: For SELL orders, ensure we never try to sell more than
        # we actually hold. This prevents failures when trade_amount/price
        # calculation exceeds the actual position (e.g. due to price changes
        # between planning and execution, or stale position data on retry).
        if trade_message.action == "SELL":
            shares = self._cap_sell_shares_to_position(trade_message, shares)

        return shares

    def _cap_sell_shares_to_position(
        self, trade_message: TradeMessage, calculated_shares: Decimal
    ) -> Decimal:
        """Cap sell shares to actual Alpaca position to prevent overselling.

        Args:
            trade_message: The trade message
            calculated_shares: Shares calculated from trade_amount/price

        Returns:
            Shares capped to actual position, or original if position
            lookup fails (fail-open to preserve existing behaviour).

        """
        try:
            alpaca_manager = self.container.infrastructure.alpaca_manager()
            position = alpaca_manager.get_position(trade_message.symbol)
            if position:
                actual_qty = getattr(position, "qty", None)
                if actual_qty is not None:
                    actual_position = Decimal(str(actual_qty))
                    if calculated_shares > actual_position and actual_position > Decimal("0"):
                        self.logger.warning(
                            "Capping sell shares to actual position",
                            extra={
                                "symbol": trade_message.symbol,
                                "calculated_shares": str(calculated_shares),
                                "actual_position": str(actual_position),
                                "shortfall": str(calculated_shares - actual_position),
                            },
                        )
                        return actual_position
        except Exception as e:
            self.logger.warning(
                f"Failed to fetch position for sell cap, using calculated shares: {e}",
                extra={
                    "symbol": trade_message.symbol,
                    "calculated_shares": str(calculated_shares),
                },
            )
        return calculated_shares

    def _emit_trade_executed_event(
        self,
        trade_message: TradeMessage,
        *,
        success: bool,
        order_id: str | None,
        shares_executed: Decimal,
        price: Decimal | None,
        error_message: str | None,
    ) -> None:
        """Emit TradeExecuted event for a single trade.

        Args:
            trade_message: The original trade message
            success: Whether the trade succeeded
            order_id: Broker order ID if available
            shares_executed: Number of shares executed
            price: Execution price if available
            error_message: Error message if failed

        """
        try:
            event_metadata: dict[str, object] = {
                "execution_mode": "per_trade",
                "run_id": trade_message.run_id,
                "trade_id": trade_message.trade_id,
                "sequence_number": trade_message.sequence_number,
                "phase": trade_message.phase,
            }

            # Single-trade execution data
            execution_data: dict[str, Any] = {
                "plan_id": trade_message.plan_id,
                "trade_id": trade_message.trade_id,
                "symbol": trade_message.symbol,
                "action": trade_message.action,
                "order_id": order_id,
                "shares_executed": str(shares_executed),
                "price": str(price) if price else None,
                "executed_at": datetime.now(UTC).isoformat(),
                "success": success,
                "error_message": error_message,
            }

            event = TradeExecuted(
                correlation_id=trade_message.correlation_id,
                causation_id=trade_message.trade_id,
                event_id=f"trade-executed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="SingleTradeHandler",
                execution_data=execution_data,
                success=success,
                orders_placed=1,
                orders_succeeded=1 if success else 0,
                metadata=event_metadata,
                failure_reason=error_message if not success else None,
                failed_symbols=[trade_message.symbol] if not success else [],
            )

            self.event_bus.publish(event)

            # Publish to EventBridge for Notifications Lambda to receive
            publish_to_eventbridge(event)

            self.logger.info(
                f"📡 Emitted TradeExecuted event for {trade_message.symbol}",
                extra={
                    "run_id": trade_message.run_id,
                    "trade_id": trade_message.trade_id,
                    "success": success,
                },
            )

        except Exception as e:
            # Log but don't fail - trade was already executed
            self.logger.error(
                f"Failed to emit TradeExecuted event: {e}",
                extra={
                    "run_id": trade_message.run_id,
                    "trade_id": trade_message.trade_id,
                    "error_type": type(e).__name__,
                },
            )

    def _emit_buy_phase_blocked_event(
        self,
        run_id: str,
        correlation_id: str,
        sell_failed_amount: Decimal,
        sell_succeeded_amount: Decimal,
        failure_threshold: Decimal,
        buy_trades_blocked: int,
    ) -> None:
        """Emit WorkflowFailed event when BUY phase is blocked due to SELL failures.

        This event triggers notifications to alert operators that the trading
        workflow was halted to prevent over-deployment.

        Args:
            run_id: Execution run identifier.
            correlation_id: Workflow correlation ID.
            sell_failed_amount: Dollar amount of failed SELL trades.
            sell_succeeded_amount: Dollar amount of successful SELL trades.
            failure_threshold: Configured failure threshold.
            buy_trades_blocked: Number of BUY trades that were blocked.

        """
        try:
            event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=run_id,
                event_id=f"buy-phase-blocked-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="SingleTradeHandler",
                workflow_type="TradingExecution",
                failure_reason=(
                    f"BUY phase blocked: SELL failures (${sell_failed_amount:.2f}) "
                    f"exceeded threshold (${failure_threshold:.2f})"
                ),
                failure_step="SELL_PHASE_GUARD",
                error_details={
                    "run_id": run_id,
                    "sell_failed_amount": str(sell_failed_amount),
                    "sell_succeeded_amount": str(sell_succeeded_amount),
                    "failure_threshold": str(failure_threshold),
                    "buy_trades_blocked": buy_trades_blocked,
                    "guard_action": "BUY_PHASE_BLOCKED",
                    "risk_prevented": "Over-deployment and potential margin call",
                },
            )

            self.event_bus.publish(event)

            # Publish to EventBridge for Notifications Lambda to receive
            publish_to_eventbridge(event)

            self.logger.info(
                "📡 Emitted WorkflowFailed event for blocked BUY phase",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "sell_failed_amount": str(sell_failed_amount),
                },
            )

        except Exception as e:
            # Log but don't fail - the run status was already updated
            self.logger.error(
                f"Failed to emit WorkflowFailed event: {e}",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _emit_equity_circuit_breaker_event(
        self,
        run_id: str,
        correlation_id: str,
        trade_message: TradeMessage,
        breaker_details: dict[str, Any],
    ) -> None:
        """Emit WorkflowFailed event when equity circuit breaker is triggered.

        This event triggers notifications to alert operators that the trading
        workflow was halted because cumulative BUY trades would exceed the
        configured equity deployment limit.

        Args:
            run_id: Execution run identifier.
            correlation_id: Workflow correlation ID.
            trade_message: The BUY trade that triggered the circuit breaker.
            breaker_details: Circuit breaker state details from check.

        """
        try:
            cumulative = breaker_details.get("cumulative_buy_succeeded_value", Decimal("0"))
            max_limit = breaker_details.get("max_equity_limit_usd", Decimal("0"))
            proposed = abs(trade_message.trade_amount)

            event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=run_id,
                event_id=f"equity-circuit-breaker-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="SingleTradeHandler",
                workflow_type="TradingExecution",
                failure_reason=(
                    f"Equity circuit breaker triggered: cumulative BUY value "
                    f"(${cumulative:.2f}) + proposed (${proposed:.2f}) "
                    f"would exceed limit (${max_limit:.2f})"
                ),
                failure_step="EQUITY_CIRCUIT_BREAKER",
                error_details={
                    "run_id": run_id,
                    "trade_id": trade_message.trade_id,
                    "symbol": trade_message.symbol,
                    "proposed_buy_value": str(proposed),
                    "cumulative_buy_succeeded_value": str(cumulative),
                    "max_equity_limit_usd": str(max_limit),
                    "new_cumulative_if_executed": str(cumulative + proposed),
                    "overage": str(cumulative + proposed - max_limit),
                    "guard_action": "EQUITY_CIRCUIT_BREAKER_TRIGGERED",
                    "risk_prevented": "Over-deployment beyond configured equity limit",
                },
            )

            self.event_bus.publish(event)

            # Publish to EventBridge for Notifications Lambda to receive
            publish_to_eventbridge(event)

            self.logger.info(
                "📡 Emitted WorkflowFailed event for equity circuit breaker",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "symbol": trade_message.symbol,
                    "cumulative_buy": str(cumulative),
                    "max_limit": str(max_limit),
                },
            )

        except Exception as e:
            # Log but don't fail - the run status was already updated
            self.logger.error(
                f"Failed to emit WorkflowFailed event for equity circuit breaker: {e}",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _handle_market_closed(self, trade_message: TradeMessage) -> dict[str, Any]:
        """Handle market closed scenario by marking trade as skipped.

        Args:
            trade_message: The trade message

        Returns:
            Dict indicating market closed skip

        """
        run_id = trade_message.run_id
        trade_id = trade_message.trade_id
        correlation_id = trade_message.correlation_id

        self.logger.warning(
            f"⚠️ Market is closed - skipping order placement for {trade_message.symbol}",
            extra={
                "run_id": run_id,
                "trade_id": trade_id,
                "correlation_id": correlation_id,
            },
        )

        # Mark trade completed in DynamoDB (skipped due to market closed)
        completion_result = self.run_service.mark_trade_completed(
            run_id=run_id,
            trade_id=trade_id,
            success=True,  # Not a failure, just skipped
            skipped=True,  # Explicitly mark as skipped
            order_id=None,
            error_message="Market closed - order placement skipped",
            phase=trade_message.phase,
            trade_amount=abs(trade_message.trade_amount),
        )

        # Check if this completes the SELL phase and trigger BUY phase if needed
        self._check_and_trigger_buy_phase(
            run_id=run_id,
            correlation_id=correlation_id,
            completion_result=completion_result,
        )

        # Emit TradeExecuted event for this skipped trade
        self._emit_trade_executed_event(
            trade_message=trade_message,
            success=True,
            order_id=None,
            shares_executed=Decimal("0"),
            price=None,
            error_message="Market closed - order placement skipped",
        )

        return {
            "success": True,
            "skipped": True,
            "reason": "market_closed",
            "trade_id": trade_id,
        }

    def _check_equity_circuit_breaker(self, trade_message: TradeMessage) -> dict[str, Any] | None:
        """Check equity circuit breaker for BUY trades.

        Args:
            trade_message: The trade message

        Returns:
            Dict with error if breaker triggered, None if allowed

        """
        run_id = trade_message.run_id
        trade_id = trade_message.trade_id
        correlation_id = trade_message.correlation_id

        allowed, breaker_details = self.run_service.check_equity_circuit_breaker(
            run_id=run_id,
            proposed_buy_value=abs(trade_message.trade_amount),
        )

        if not allowed:
            self.logger.critical(
                f"🚫 EQUITY CIRCUIT BREAKER TRIGGERED - Blocking BUY for {trade_message.symbol}",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "symbol": trade_message.symbol,
                    "proposed_buy_value": str(trade_message.trade_amount),
                    "correlation_id": correlation_id,
                    **{k: str(v) for k, v in breaker_details.items()},
                },
            )

            # Mark trade as failed due to circuit breaker
            self.run_service.mark_trade_completed(
                run_id=run_id,
                trade_id=trade_id,
                success=False,
                order_id=None,
                error_message=(
                    f"Equity circuit breaker: cumulative buys "
                    f"${breaker_details.get('cumulative_buy_succeeded_value', 0)} + "
                    f"proposed ${abs(trade_message.trade_amount):.2f} would exceed "
                    f"limit ${breaker_details.get('max_equity_limit_usd', 0)}"
                ),
                phase=trade_message.phase,
                trade_amount=abs(trade_message.trade_amount),
            )

            # Mark the run as FAILED and emit WorkflowFailed event
            self.run_service.update_run_status(run_id, "FAILED")
            self._emit_equity_circuit_breaker_event(
                run_id=run_id,
                correlation_id=correlation_id,
                trade_message=trade_message,
                breaker_details=breaker_details,
            )

            return {
                "success": False,
                "skipped": False,
                "reason": "equity_circuit_breaker_triggered",
                "trade_id": trade_id,
                "error": "Equity deployment limit exceeded",
            }

        return None

    def _execute_order_with_retries(
        self, trade_message: TradeMessage, correlation_id: str
    ) -> OrderResult:
        """Execute order with retry logic for SELL phase.

        Args:
            trade_message: The trade message
            correlation_id: Correlation ID for traceability

        Returns:
            OrderResult from execution

        """
        run_id = trade_message.run_id
        trade_id = trade_message.trade_id

        executor = self._create_executor()
        config = ExecutionConfig()

        try:
            # Execute via Executor.execute_order
            side = "buy" if trade_message.action == "BUY" else "sell"
            shares = self._calculate_shares(trade_message)

            # Determine if this is a full liquidation (target_weight = 0)
            is_full_liquidation = (
                trade_message.is_full_liquidation or trade_message.target_weight <= Decimal("0")
            )

            # SELL trades get retry logic to handle transient broker errors
            max_attempts = config.max_sell_retries + 1 if trade_message.phase == "SELL" else 1
            retry_delay = config.sell_retry_delay_seconds
            last_error: Exception | None = None
            order_result: OrderResult | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    order_result = asyncio.run(
                        executor.execute_order(
                            symbol=trade_message.symbol,
                            side=side,
                            quantity=shares,
                            correlation_id=correlation_id,
                            is_complete_exit=is_full_liquidation,
                            planned_trade_amount=abs(trade_message.trade_amount),
                            strategy_id=trade_message.strategy_id,
                        )
                    )
                    if order_result.success:
                        break
                    # Retry non-success results for SELLs
                    if attempt < max_attempts:
                        self.logger.warning(
                            f"⚠️ SELL trade attempt {attempt}/{max_attempts} failed for "
                            f"{trade_message.symbol}: {order_result.error_message} - retrying",
                            extra={
                                "run_id": run_id,
                                "trade_id": trade_id,
                                "symbol": trade_message.symbol,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "error_message": order_result.error_message,
                            },
                        )
                        time.sleep(retry_delay)
                    else:
                        break

                except (ExecutionManagerError, TradingClientError, MarketDataError) as e:
                    last_error = e
                    if attempt < max_attempts:
                        self.logger.warning(
                            f"⚠️ SELL trade attempt {attempt}/{max_attempts} raised error for "
                            f"{trade_message.symbol}: {e} - retrying",
                            extra={
                                "run_id": run_id,
                                "trade_id": trade_id,
                                "symbol": trade_message.symbol,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "error_type": type(e).__name__,
                            },
                        )
                        time.sleep(retry_delay)
                    else:
                        raise

            if order_result is None and last_error:
                raise last_error

            if order_result is None:
                raise ExecutionManagerError("order_result must be set after execution loop")

            return order_result

        finally:
            if hasattr(executor, "shutdown"):
                executor.shutdown()

    def _record_trade_to_ledger(
        self,
        order_result: OrderResult,
        trade_message: TradeMessage,
        correlation_id: str,
    ) -> None:
        """Record successful trade to Trade Ledger DynamoDB.

        Args:
            order_result: The order execution result
            trade_message: The trade message
            correlation_id: Correlation ID for traceability

        """
        if not (order_result.success and order_result.order_id):
            return

        try:
            # Extract strategy attribution from TradeMessage metadata
            # This carries the strategy_attribution dict from the original RebalancePlan
            strategy_attribution = None
            if trade_message.metadata:
                strategy_attribution = trade_message.metadata.get("strategy_attribution")

            # Build execution quality metrics from OrderResult
            execution_quality = self._build_execution_quality(order_result)

            self.trade_ledger.record_filled_order(
                order_result=order_result,
                correlation_id=correlation_id,
                rebalance_plan=None,
                quote_at_fill=None,
                strategy_attribution=strategy_attribution,
                execution_quality=execution_quality,
            )

            self.logger.info(
                f"✅ Recorded trade to ledger: {trade_message.symbol}",
                extra={
                    "order_id": order_result.order_id,
                    "symbol": trade_message.symbol,
                    "correlation_id": correlation_id,
                },
            )
        except Exception as ledger_error:
            # Log error but don't fail the trade - execution was successful
            self.logger.error(
                f"Failed to record trade to ledger (trade executed successfully): {ledger_error}",
                exc_info=True,
                extra={
                    "order_id": order_result.order_id,
                    "symbol": trade_message.symbol,
                    "error_type": type(ledger_error).__name__,
                },
            )

    def _build_execution_quality(self, order_result: OrderResult) -> dict[str, Any]:
        """Build execution quality metrics dict from OrderResult.

        Args:
            order_result: Order execution result with slippage fields

        Returns:
            Dict with execution quality metrics for TCA dashboard

        """
        eq: dict[str, Any] = {}

        # Extract slippage metrics from OrderResult (calculated during execution)
        if order_result.expected_price is not None:
            eq["expected_price"] = order_result.expected_price
        if order_result.slippage_bps is not None:
            eq["slippage_bps"] = order_result.slippage_bps
        if order_result.slippage_amount is not None:
            eq["slippage_amount"] = order_result.slippage_amount

        # Calculate time_to_fill_ms if we have timestamps
        if order_result.filled_at and order_result.timestamp:
            time_delta = order_result.filled_at - order_result.timestamp
            eq["time_to_fill_ms"] = int(time_delta.total_seconds() * 1000)

        return eq
