"""Business Unit: trade_aggregator | Status: current.

Lambda handler for Trade Aggregator microservice.

The TradeAggregator collects TradeExecuted events from parallel execution
invocations and emits a single AllTradesCompleted event when all trades
in a run finish. This eliminates race conditions in notifications.

Trigger: EventBridge rule matching TradeExecuted events.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import AllTradesCompleted, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .config import TradeAggregatorSettings
from .services import TradeAggregatorService

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle TradeExecuted events and aggregate trade results.

    This handler:
    1. Extracts trade info from EventBridge event
    2. Checks if all trades in the run have completed
    3. If complete: claims aggregation lock (atomic)
    4. If lock acquired: aggregates results and publishes AllTradesCompleted

    The atomic claim pattern ensures exactly one invocation aggregates,
    eliminating the race condition that plagued the per-trade notification model.

    Args:
        event: EventBridge event containing TradeExecuted
        context: Lambda context

    Returns:
        Response indicating aggregation status.

    """
    # Unwrap EventBridge envelope
    detail = unwrap_eventbridge_event(event)

    # Extract run and trade identifiers from metadata
    metadata = detail.get("metadata", {})
    run_id = metadata.get("run_id", "")
    trade_id = metadata.get("trade_id", "")
    correlation_id = detail.get("correlation_id", "")

    # Skip events without run_id (e.g., legacy or test events)
    if not run_id:
        logger.debug(
            "TradeExecuted event without run_id - skipping aggregation",
            extra={"correlation_id": correlation_id, "trade_id": trade_id},
        )
        return {
            "statusCode": 200,
            "body": {"status": "skipped", "reason": "no_run_id"},
        }

    logger.info(
        "Trade Aggregator received TradeExecuted event",
        extra={
            "run_id": run_id,
            "trade_id": trade_id,
            "correlation_id": correlation_id,
        },
    )

    try:
        # Load settings
        settings = TradeAggregatorSettings.from_environment()

        # Initialize aggregator service
        aggregator_service = TradeAggregatorService(table_name=settings.execution_runs_table_name)

        # Check current completion state
        # Note: Execution Lambda already incremented completed_trades via mark_trade_completed()
        completed, total = aggregator_service.record_trade_completed(run_id, trade_id)

        if total == 0:
            logger.warning(
                "Run not found or has no trades",
                extra={"run_id": run_id, "trade_id": trade_id},
            )
            return {
                "statusCode": 200,
                "body": {"status": "error", "reason": "run_not_found"},
            }

        logger.info(
            "Checked run completion",
            extra={
                "run_id": run_id,
                "completed_trades": completed,
                "total_trades": total,
            },
        )

        # Check if all trades have completed
        if completed < total:
            return {
                "statusCode": 200,
                "body": {
                    "status": "waiting",
                    "run_id": run_id,
                    "completed_trades": completed,
                    "total_trades": total,
                },
            }

        # All trades completed - try to claim aggregation lock
        # This is atomic: only one invocation wins
        if not aggregator_service.try_claim_aggregation(run_id):
            logger.info(
                "Aggregation already claimed by another invocation",
                extra={"run_id": run_id},
            )
            return {
                "statusCode": 200,
                "body": {"status": "already_aggregating", "run_id": run_id},
            }

        # This invocation won the claim - aggregate and emit event
        logger.info(
            "🏁 All trades completed, starting aggregation",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
            },
        )

        # Get run metadata and all trade results
        run_metadata = aggregator_service.get_run_metadata(run_id)
        if not run_metadata:
            raise ValueError(f"Run metadata not found after claiming aggregation: {run_id}")

        trade_results = aggregator_service.get_all_trade_results(run_id)

        # Aggregate trade results
        aggregated_data = aggregator_service.aggregate_trade_results(run_metadata, trade_results)

        # Capture capital deployed percentage
        capital_deployed_pct = _capture_capital_deployed_pct(correlation_id)

        # Build and publish AllTradesCompleted event
        all_trades_event = AllTradesCompleted(
            event_id=f"all-trades-completed-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=run_id,
            timestamp=datetime.now(UTC),
            source_module="trade_aggregator",
            source_component="TradeAggregator",
            run_id=run_id,
            plan_id=run_metadata.get("plan_id", ""),
            total_trades=run_metadata.get("total_trades", 0),
            succeeded_trades=run_metadata.get("succeeded_trades", 0),
            failed_trades=run_metadata.get("failed_trades", 0),
            skipped_trades=run_metadata.get("skipped_trades", 0),
            aggregated_execution_data=aggregated_data,
            capital_deployed_pct=capital_deployed_pct,
            failed_symbols=aggregated_data.get("failed_symbols", []),
        )

        # Publish to EventBridge (triggers Notifications Lambda)
        publish_to_eventbridge(all_trades_event)

        # Mark run as completed
        aggregator_service.mark_run_completed(run_id)

        logger.info(
            "✅ Aggregation completed successfully",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
                "succeeded_trades": run_metadata.get("succeeded_trades", 0),
                "failed_trades": run_metadata.get("failed_trades", 0),
                "event_id": all_trades_event.event_id,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "aggregated",
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
                "event_id": all_trades_event.event_id,
            },
        }

    except Exception as e:
        logger.error(
            "Trade Aggregator failed",
            extra={
                "run_id": run_id,
                "trade_id": trade_id,
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )

        # Try to mark run as failed
        try:
            settings = TradeAggregatorSettings.from_environment()
            aggregator_service = TradeAggregatorService(
                table_name=settings.execution_runs_table_name
            )
            aggregator_service.mark_run_failed(run_id, str(e))
        except Exception as mark_error:
            logger.warning(
                "Failed to mark run as failed",
                extra={"run_id": run_id, "error": str(mark_error)},
            )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=run_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="trade_aggregator",
                source_component="lambda_handler",
                workflow_type="trade_aggregation",
                failure_reason=str(e),
                failure_step="aggregation",
                error_details={
                    "exception_type": type(e).__name__,
                    "run_id": run_id,
                    "trade_id": trade_id,
                },
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "run_id": run_id,
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }


def _capture_capital_deployed_pct(correlation_id: str) -> Decimal | None:
    """Capture capital deployed percentage from Alpaca account.

    Called once per run after all trades complete.

    Args:
        correlation_id: Correlation ID for tracing.

    Returns:
        Capital deployed as a percentage (0-100), or None if calculation fails.

    """
    try:
        # Create minimal container for Alpaca access
        container = ApplicationContainer.create_for_notifications("production")
        alpaca_manager = container.infrastructure.alpaca_manager()
        account = alpaca_manager.get_account_object()

        if not account:
            logger.warning(
                "Failed to fetch account for capital deployed calculation",
                extra={"correlation_id": correlation_id},
            )
            return None

        equity = Decimal(str(account.equity))
        long_market_value = (
            Decimal(str(account.long_market_value)) if account.long_market_value else Decimal("0")
        )

        if equity <= 0:
            logger.warning(
                "Account equity is zero or negative",
                extra={"correlation_id": correlation_id, "equity": str(equity)},
            )
            return None

        capital_deployed_pct = (long_market_value / equity) * Decimal("100")

        logger.info(
            f"📊 Capital deployed: {capital_deployed_pct:.2f}% "
            f"(positions: ${long_market_value:,.2f} / equity: ${equity:,.2f})",
            extra={
                "correlation_id": correlation_id,
                "capital_deployed_pct": str(capital_deployed_pct),
                "long_market_value": str(long_market_value),
                "equity": str(equity),
            },
        )

        return capital_deployed_pct.quantize(Decimal("0.01"))

    except Exception as e:
        logger.warning(
            f"Failed to calculate capital deployed percentage: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return None
