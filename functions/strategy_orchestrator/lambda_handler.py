"""Business Unit: coordinator_v2 | Status: current.

Lambda handler for Strategy Coordinator microservice.

The Coordinator orchestrates parallel execution of DSL strategy files by:
1. Reading strategy configuration (DSL files and allocations)
2. Creating an aggregation session in DynamoDB
3. Invoking Strategy Lambda once per DSL file (async)

This enables horizontal scaling where each strategy file runs in its
own Lambda invocation, with results aggregated by the Aggregator Lambda.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from coordinator_settings import CoordinatorSettings
from strategy_invoker import StrategyInvoker

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.aggregation_session_service import (
    AggregationSessionService,
)

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled invocation to coordinate strategy execution.

    This handler:
    1. Reads DSL strategy configuration
    2. Creates aggregation session in DynamoDB
    3. Invokes Strategy Lambda once per file (async parallel)
    4. Returns immediately (aggregation happens asynchronously)

    Args:
        event: Lambda event (from EventBridge schedule)
        context: Lambda context

    Returns:
        Response with session_id and invocation count.

    """
    # Generate correlation ID for this workflow
    correlation_id = event.get("correlation_id") or f"workflow-{uuid.uuid4()}"
    session_id = correlation_id  # Use correlation_id as session_id
    scheduled_by = event.get("scheduled_by", "direct")

    logger.info(
        "Coordinator Lambda invoked - orchestrating parallel strategy execution",
        extra={
            "correlation_id": correlation_id,
            "session_id": session_id,
            "event_source": event.get("source", "schedule"),
            "scheduled_by": scheduled_by,
        },
    )

    try:
        # Load settings
        coordinator_settings = CoordinatorSettings.from_environment()
        app_settings = Settings()

        # Validate required environment variables
        if not coordinator_settings.aggregation_table_name:
            raise ValueError(
                "AGGREGATION_TABLE_NAME environment variable is required for multi-node mode"
            )
        if not coordinator_settings.strategy_lambda_function_name:
            raise ValueError(
                "STRATEGY_FUNCTION_NAME environment variable is required for multi-node mode"
            )

        # Get DSL files and base allocations from config
        dsl_files = app_settings.strategy.dsl_files
        base_allocations = app_settings.strategy.dsl_allocations

        if not dsl_files:
            raise ValueError("No DSL strategy files configured")

        # Load live weights from DynamoDB (with fallback to base allocations)
        live_allocations = base_allocations  # Default to base if weights service unavailable

        if coordinator_settings.strategy_weights_table_name:
            try:
                from the_alchemiser.shared.repositories.dynamodb_strategy_weights_repository import (
                    DynamoDBStrategyWeightsRepository,
                )
                from the_alchemiser.shared.services.strategy_weight_service import (
                    StrategyWeightService,
                )

                weights_repo = DynamoDBStrategyWeightsRepository(
                    table_name=coordinator_settings.strategy_weights_table_name
                )
                weight_service = StrategyWeightService(repository=weights_repo)

                # Get current live weights (falls back to base if not initialized)
                live_weights = weight_service.get_current_weights(
                    base_weights=base_allocations, correlation_id=correlation_id
                )

                # Convert Decimal to float for strategy_configs
                live_allocations = {k: float(v) for k, v in live_weights.items()}

                logger.info(
                    "Loaded live strategy weights from DynamoDB",
                    extra={
                        "strategy_count": len(live_allocations),
                        "using_live_weights": True,
                    },
                )
            except Exception as e:
                logger.warning(
                    "Failed to load live weights from DynamoDB, using base weights",
                    extra={"error": str(e)},
                )
                live_allocations = base_allocations
        else:
            logger.info(
                "Strategy weights table not configured, using base weights from config",
                extra={"strategy_count": len(base_allocations)},
            )

        # Build strategy configs list with Decimal for precision
        strategy_configs: list[tuple[str, Decimal]] = [
            (dsl_file, Decimal(str(live_allocations.get(dsl_file, 0.0)))) for dsl_file in dsl_files
        ]

        # Validate allocations sum to ~1.0 using math.isclose per coding guidelines
        # Fail-fast: reject invalid configurations before creating sessions or invoking workers
        total_allocation = float(sum(alloc for _, alloc in strategy_configs))
        if not math.isclose(total_allocation, 1.0, rel_tol=0.01):
            raise ValueError(
                f"Strategy allocations must sum to 1.0, got {total_allocation:.4f}. "
                f"Allocations: {live_allocations}"
            )

        logger.info(
            "Loaded strategy configuration",
            extra={
                "dsl_files": dsl_files,
                "total_strategies": len(dsl_files),
                "total_allocation": total_allocation,
            },
        )

        # Create aggregation session in DynamoDB
        session_service = AggregationSessionService(
            table_name=coordinator_settings.aggregation_table_name
        )

        session = session_service.create_session(
            session_id=session_id,
            correlation_id=correlation_id,
            strategy_configs=strategy_configs,
            timeout_seconds=coordinator_settings.aggregation_timeout_seconds,
        )

        # Invoke Strategy Lambda for each file (async parallel)
        invoker = StrategyInvoker(function_name=coordinator_settings.strategy_lambda_function_name)

        request_ids = invoker.invoke_all_strategies(
            session_id=session_id,
            correlation_id=correlation_id,
            strategy_configs=strategy_configs,
        )

        logger.info(
            "Coordinator completed - strategies dispatched",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "strategies_invoked": len(request_ids),
                "timeout_seconds": coordinator_settings.aggregation_timeout_seconds,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "dispatched",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "strategies_invoked": len(request_ids),
                "strategy_files": dsl_files,
                "timeout_at": session["timeout_at"],
            },
        }

    except Exception as e:
        logger.error(
            "Coordinator Lambda failed",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "error": str(e),
            },
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=session_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="coordinator_v2",
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
                "session_id": session_id,
                "error": str(e),
            },
        }
