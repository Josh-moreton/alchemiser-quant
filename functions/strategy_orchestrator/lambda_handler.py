"""Business Unit: coordinator | Status: current.

Lambda handler for Strategy Coordinator microservice.

The Coordinator orchestrates parallel execution of DSL strategy files by:
1. Checking the market calendar to confirm today is a trading day
2. Reading strategy configuration (DSL files and allocations)
3. Invoking Strategy Lambda once per DSL file (async)

Each strategy worker independently evaluates DSL, calculates rebalance,
and enqueues trades. No aggregation session or planner step required.
"""

from __future__ import annotations

import math
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from coordinator_settings import CoordinatorSettings
from strategy_invoker import StrategyInvoker

from the_alchemiser.shared.brokers.alpaca_utils import create_trading_client
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.market_calendar_service import (
    MarketCalendarService,
)

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled invocation to coordinate strategy execution.

    This handler:
    1. Reads DSL strategy configuration
    2. Validates allocations sum to ~1.0
    3. Invokes Strategy Lambda once per file (async parallel)
    4. Returns immediately (each worker executes independently)

    Args:
        event: Lambda event (from EventBridge schedule or direct invoke).
        context: Lambda context.

    Returns:
        Response with correlation_id and invocation count.

    """
    correlation_id = event.get("correlation_id") or f"workflow-{uuid.uuid4()}"
    scheduled_by = event.get("scheduled_by", "direct")

    logger.info(
        "Coordinator invoked - dispatching per-strategy execution",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
            "scheduled_by": scheduled_by,
        },
    )

    try:
        # Load settings
        coordinator_settings = CoordinatorSettings.from_environment()
        app_settings = Settings()

        # ── Market calendar gate ───────────────────────────────────────
        # The Schedule Manager should only trigger us on trading days,
        # but direct/manual invocations bypass that. This is a safety
        # net that aborts early on weekends and market holidays.
        if not _is_trading_day(app_settings, correlation_id):
            logger.warning(
                "Market is closed today - aborting strategy dispatch",
                extra={
                    "correlation_id": correlation_id,
                    "scheduled_by": scheduled_by,
                },
            )

            _publish_market_closed_notification(correlation_id, scheduled_by)

            return {
                "statusCode": 200,
                "body": {
                    "status": "skipped",
                    "correlation_id": correlation_id,
                    "reason": "Market closed today",
                },
            }
        # ───────────────────────────────────────────────────────────────

        if not coordinator_settings.strategy_lambda_function_name:
            raise ValueError("STRATEGY_FUNCTION_NAME environment variable is required")

        # Get DSL files and allocations
        dsl_files = app_settings.strategy.dsl_files
        dsl_allocations = app_settings.strategy.dsl_allocations

        if not dsl_files:
            raise ValueError("No DSL strategy files configured")

        # Build strategy configs list with Decimal for precision
        strategy_configs: list[tuple[str, Decimal]] = [
            (dsl_file, Decimal(str(dsl_allocations.get(dsl_file, 0.0)))) for dsl_file in dsl_files
        ]

        # Validate allocations sum to ~1.0
        total_allocation = float(sum(alloc for _, alloc in strategy_configs))
        if not math.isclose(total_allocation, 1.0, rel_tol=0.01):
            raise ValueError(
                f"Strategy allocations must sum to 1.0, got {total_allocation:.4f}. "
                f"Allocations: {dsl_allocations}"
            )

        logger.info(
            "Loaded strategy configuration",
            extra={
                "correlation_id": correlation_id,
                "dsl_files": dsl_files,
                "total_strategies": len(dsl_files),
                "total_allocation": total_allocation,
            },
        )

        # Create notification session BEFORE dispatching workers.
        # Workers run asynchronously and may complete before we return;
        # the session must already exist so their counter increments
        # land on a valid METADATA row with total_strategies set.
        _create_notification_session(
            correlation_id=correlation_id,
            total_strategies=len(strategy_configs),
            strategy_files=dsl_files,
        )

        # Invoke Strategy Lambda for each file (async parallel)
        invoker = StrategyInvoker(
            function_name=coordinator_settings.strategy_lambda_function_name,
        )

        request_ids = invoker.invoke_all_strategies(
            correlation_id=correlation_id,
            strategy_configs=strategy_configs,
        )

        logger.info(
            "Coordinator completed - strategies dispatched",
            extra={
                "correlation_id": correlation_id,
                "strategies_invoked": len(request_ids),
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "dispatched",
                "correlation_id": correlation_id,
                "strategies_invoked": len(request_ids),
                "strategy_files": dsl_files,
            },
        }

    except Exception as e:
        logger.error(
            "Coordinator failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="coordinator",
                source_component="lambda_handler",
                workflow_type="strategy_coordination",
                failure_reason=str(e),
                failure_step="coordinator_dispatch",
                error_details={"exception_type": type(e).__name__},
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
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }


def _create_notification_session(
    correlation_id: str,
    total_strategies: int,
    strategy_files: list[str],
) -> None:
    """Create a notification session for consolidated email delivery.

    Non-fatal: if session creation fails, strategies fall back to
    per-strategy emails (backward compatible).

    Args:
        correlation_id: Shared workflow correlation ID.
        total_strategies: Number of strategies dispatched.
        strategy_files: List of DSL file names.

    """
    table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
    if not table_name:
        logger.debug("EXECUTION_RUNS_TABLE_NAME not set - skipping notification session")
        return

    try:
        from the_alchemiser.shared.services.notification_session_service import (
            NotificationSessionService,
        )

        session_service = NotificationSessionService(table_name=table_name)
        session_service.create_session(
            correlation_id=correlation_id,
            total_strategies=total_strategies,
            strategy_files=strategy_files,
        )
    except Exception as e:
        logger.warning(
            "Failed to create notification session",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


def _is_trading_day(app_settings: Settings, correlation_id: str) -> bool:
    """Check if today is a trading day using the Alpaca market calendar.

    Uses the MarketCalendarService to query the Alpaca calendar API.
    On failure (API error, missing credentials), defaults to allowing
    execution to avoid blocking production runs.

    Args:
        app_settings: Application settings with Alpaca credentials.
        correlation_id: Correlation ID for tracing.

    Returns:
        True if today is a trading day (or check failed), False if market is closed.

    """
    try:
        alpaca_key = app_settings.alpaca.key
        alpaca_secret = app_settings.alpaca.secret

        if not alpaca_key or not alpaca_secret:
            logger.warning(
                "Alpaca credentials not configured - skipping market calendar check",
                extra={"correlation_id": correlation_id},
            )
            return True

        trading_client = create_trading_client(
            api_key=alpaca_key,
            secret_key=alpaca_secret,
            paper=app_settings.alpaca.endpoint != "https://api.alpaca.markets",
        )
        calendar_service = MarketCalendarService(trading_client)
        is_trading = calendar_service.is_trading_day(correlation_id=correlation_id)

        logger.info(
            "Market calendar check completed",
            extra={
                "correlation_id": correlation_id,
                "is_trading_day": is_trading,
            },
        )
        return is_trading

    except Exception as e:
        # Fail-open: if we cannot check, allow execution rather than silently
        # skipping a real trading day
        logger.warning(
            "Market calendar check failed - assuming trading day (fail-open)",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return True


def _publish_market_closed_notification(
    correlation_id: str,
    scheduled_by: str,
) -> None:
    """Publish a WorkflowFailed event so the Notifications Lambda fires.

    Without this, a market-closed abort would produce zero downstream
    events and the operator would never know the run was skipped.

    Args:
        correlation_id: Workflow correlation ID.
        scheduled_by: How the orchestrator was triggered (schedule_manager / direct).

    """
    try:
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"workflow-skipped-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="coordinator",
            source_component="lambda_handler",
            workflow_type="market_closed_skip",
            failure_reason=(
                f"Strategy execution skipped: market is closed today. Triggered by: {scheduled_by}."
            ),
            failure_step="market_calendar_check",
            error_details={
                "scheduled_by": scheduled_by,
                "skip_type": "market_closed",
            },
        )
        publish_to_eventbridge(failure_event)

        logger.info(
            "Published market-closed notification event",
            extra={"correlation_id": correlation_id},
        )
    except Exception as pub_error:
        logger.error(
            "Failed to publish market-closed notification event",
            extra={
                "correlation_id": correlation_id,
                "error": str(pub_error),
            },
        )
