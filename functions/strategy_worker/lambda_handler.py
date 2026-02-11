"""Business Unit: strategy | Status: current.

Lambda handler for per-strategy execution.

Each strategy worker evaluates its DSL file, calculates its own rebalance
plan, and enqueues trades directly to SQS. No aggregation step required.

Triggered by:
1. Coordinator Lambda (per-strategy mode) - Runs single strategy file
2. EventBridge Schedule (direct invocation for testing)
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from handlers.single_file_signal_handler import SingleFileSignalHandler
from wiring import register_strategy

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Increase recursion limit for deeply nested DSL strategies.
# Some strategies like ftl_starburst_gen2.clj have 288+ levels of nesting
# which exceeds Python's default limit of 1000 when combined with evaluator
# recursion. 10000 provides ample headroom for complex strategies.
sys.setrecursionlimit(10000)

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)

MODULE_NAME = "strategy.lambda_handler"


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle invocation for per-strategy execution.

    Evaluates a single DSL strategy file, calculates its rebalance plan,
    and enqueues trades directly to SQS.

    Args:
        event: Lambda event containing correlation_id, dsl_file, allocation.
        context: Lambda context.

    Returns:
        Response indicating success/failure with trade count.

    """
    correlation_id = event.get("correlation_id", str(uuid.uuid4()))
    dsl_file = event.get("dsl_file", "")
    allocation = Decimal(str(event.get("allocation", "0")))
    debug_mode = event.get("debug_mode", False)

    # Derive strategy_id from dsl_file (e.g., '1-KMLM.clj' -> '1-KMLM')
    strategy_id = Path(dsl_file).stem if dsl_file else ""

    # Validate required fields
    if not dsl_file:
        error_msg = "Missing required field: dsl_file"
        logger.error(error_msg, extra={"correlation_id": correlation_id})
        return {
            "statusCode": 400,
            "body": {
                "status": "error",
                "error": error_msg,
                "correlation_id": correlation_id,
            },
        }

    if allocation <= Decimal("0"):
        error_msg = f"Invalid allocation for {dsl_file}: {allocation}"
        logger.error(
            error_msg,
            extra={
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "allocation": str(allocation),
            },
        )
        return {
            "statusCode": 400,
            "body": {
                "status": "error",
                "error": error_msg,
                "correlation_id": correlation_id,
            },
        }

    logger.info(
        "Strategy worker invoked",
        extra={
            "correlation_id": correlation_id,
            "strategy_id": strategy_id,
            "dsl_file": dsl_file,
            "allocation": str(allocation),
            "debug_mode": debug_mode,
        },
    )

    try:
        # Step 1: Wire dependencies
        container = ApplicationContainer()
        register_strategy(container)

        # Step 2: Evaluate DSL strategy to get target weights
        handler = SingleFileSignalHandler(
            container=container,
            dsl_file=dsl_file,
            debug_mode=debug_mode,
        )

        result = handler.generate_signals(correlation_id)

        if result is None:
            raise ValueError(f"No signals generated for {dsl_file}")

        target_weights = result["target_weights"]
        data_freshness = result.get("data_freshness")

        logger.info(
            "DSL evaluation complete, starting rebalance",
            extra={
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "signal_count": result["signal_count"],
                "symbols": sorted(target_weights.keys()),
            },
        )

        # Step 3: Execute per-strategy rebalance (positions -> plan -> trades)
        rebalancer = container.strategy_rebalancer()
        rebalance_result = rebalancer.execute(
            strategy_id=strategy_id,
            dsl_file=dsl_file,
            allocation=allocation,
            target_weights=target_weights,
            correlation_id=correlation_id,
            data_freshness=data_freshness,
        )

        logger.info(
            "Strategy execution completed",
            extra={
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "trade_count": rebalance_result.trade_count,
                "plan_id": rebalance_result.plan_id,
                "strategy_capital": str(rebalance_result.strategy_capital),
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "trade_count": rebalance_result.trade_count,
                "plan_id": rebalance_result.plan_id,
                "strategy_capital": str(rebalance_result.strategy_capital),
            },
        }

    except Exception as e:
        logger.error(
            "Strategy execution failed",
            extra={
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Publish WorkflowFailed so notifications can fire
        _publish_failure_event(
            correlation_id=correlation_id,
            strategy_id=strategy_id,
            dsl_file=dsl_file,
            error=e,
        )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "error": str(e),
            },
        }


def _publish_failure_event(
    correlation_id: str,
    strategy_id: str,
    dsl_file: str,
    error: Exception,
) -> None:
    """Publish WorkflowFailed event to EventBridge for notification routing."""
    try:
        failure_event = WorkflowFailed(
            event_id=f"workflow-failed-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime.now(UTC),
            source_module="strategy",
            source_component="StrategyWorker",
            workflow_type="strategy_execution",
            failure_reason=str(error),
            failure_step="strategy_execution",
            error_details={
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "exception_type": type(error).__name__,
            },
        )
        publish_to_eventbridge(failure_event)

        logger.info(
            "Published WorkflowFailed event",
            extra={
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
            },
        )
    except Exception as pub_error:
        logger.error(
            "Failed to publish WorkflowFailed event",
            extra={
                "correlation_id": correlation_id,
                "error": str(pub_error),
            },
        )
