#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Single trade handler for per-trade execution via SQS FIFO.

Processes TradeMessage events from SQS FIFO queue to execute individual trades.
Each Lambda invocation handles one trade, enabling AWS-native concurrency while
the FIFO queue guarantees sell-before-buy ordering within a run.

This handler is part of the per-trade execution architecture:
- Portfolio Lambda decomposes RebalancePlan into individual TradeMessages
- TradeMessages are enqueued to SQS FIFO with sequence numbers (SELL: 1000+, BUY: 2000+)
- This handler processes one trade per invocation
- DynamoDB tracks run state (total_trades, completed_trades)
- Notifications Lambda aggregates results when all trades complete
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
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
)
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.trade_message import TradeMessage
from the_alchemiser.shared.services.execution_run_service import (
    ExecutionRunService,
)

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.executor import Executor
    from the_alchemiser.shared.config.container import ApplicationContainer


class SingleTradeHandler:
    """Event handler for single trade execution from SQS FIFO queue.

    Processes individual TradeMessage events to execute trades one at a time.
    Each invocation is stateless and idempotent - duplicate messages are detected
    via DynamoDB trade state tracking.

    Workflow:
    1. Parse TradeMessage from SQS record
    2. Check for duplicate execution (idempotency via DynamoDB)
    3. Mark trade as started in DynamoDB
    4. Execute the trade using Executor
    5. Mark trade as completed/failed in DynamoDB with result
    6. Emit TradeExecuted event for this individual trade

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
                self.logger.warning(
                    f"⚠️ Market is closed - skipping order placement for {trade_message.symbol}",
                    extra={
                        "run_id": run_id,
                        "trade_id": trade_id,
                        "correlation_id": correlation_id,
                    },
                )

                # Mark trade completed in DynamoDB (skipped due to market closed)
                self.run_service.mark_trade_completed(
                    run_id=run_id,
                    trade_id=trade_id,
                    success=True,  # Not a failure, just skipped
                    order_id=None,
                    error_message="Market closed - order placement skipped",
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

            # Create Executor and execute the trade
            executor = self._create_executor()

            try:
                # Execute via Executor.execute_order
                side = "buy" if trade_message.action == "BUY" else "sell"
                shares = self._calculate_shares(trade_message)

                # Determine if this is a full liquidation (target_weight = 0)
                is_full_liquidation = (
                    trade_message.is_full_liquidation or trade_message.target_weight <= Decimal("0")
                )

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

            finally:
                # Cleanup executor resources
                if hasattr(executor, "shutdown"):
                    executor.shutdown()

            # Mark trade completed in DynamoDB with execution data
            execution_data = {
                "shares": str(order_result.shares),
                "price": str(order_result.price) if order_result.price else None,
                "trade_amount": str(order_result.trade_amount),
                "order_type": order_result.order_type,
                "filled_at": order_result.filled_at.isoformat() if order_result.filled_at else None,
            }

            self.run_service.mark_trade_completed(
                run_id=run_id,
                trade_id=trade_id,
                success=order_result.success,
                order_id=order_result.order_id,
                error_message=order_result.error_message,
                execution_data=execution_data,
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
            # Domain-specific execution errors
            self.logger.error(
                f"Trade execution failed for {trade_message.symbol}: {e}",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "error_type": type(e).__name__,
                    "correlation_id": correlation_id,
                },
            )

            # Mark trade completed (as failure) in DynamoDB
            self.run_service.mark_trade_completed(
                run_id=run_id,
                trade_id=trade_id,
                success=False,
                order_id=None,
                error_message=str(e),
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
            # Unexpected errors
            self.logger.error(
                f"Unexpected error executing trade {trade_message.symbol}: {e}",
                exc_info=True,
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "error_type": type(e).__name__,
                    "correlation_id": correlation_id,
                },
            )

            # Mark trade completed (as failure) in DynamoDB
            try:
                self.run_service.mark_trade_completed(
                    run_id=run_id,
                    trade_id=trade_id,
                    success=False,
                    order_id=None,
                    error_message=f"Unexpected error: {e}",
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
        from the_alchemiser.execution_v2.core.executor import Executor

        alpaca_manager = self.container.infrastructure.alpaca_manager()

        return Executor(
            alpaca_manager=alpaca_manager,
            execution_config=ExecutionConfig(),
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
            return trade_message.shares

        # Otherwise calculate from trade_amount and estimated price
        if trade_message.estimated_price and trade_message.estimated_price > 0:
            shares = abs(trade_message.trade_amount) / trade_message.estimated_price
            return shares.quantize(Decimal("0.000001"))

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
                return shares.quantize(Decimal("0.000001"))

            # Price is None or 0 - this is an error condition
            raise MarketDataError(
                f"Unable to get valid price for {trade_message.symbol}: price={current_price}"
            )

        except MarketDataError:
            raise
        except Exception as e:
            raise MarketDataError(
                f"Failed to fetch price for {trade_message.symbol} to calculate shares: {e}"
            ) from e

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
