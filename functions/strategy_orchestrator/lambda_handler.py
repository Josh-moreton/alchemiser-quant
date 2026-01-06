"""Business Unit: coordinator_v2 | Status: current.

Lambda handler for Strategy Coordinator microservice.

The Coordinator orchestrates parallel execution of DSL strategy files by:
1. Reading strategy configuration (DSL files and allocations)
2. Optionally adjusting allocations based on current market regime
3. Creating an aggregation session in DynamoDB
4. Invoking Strategy Lambda once per DSL file (async)

This enables horizontal scaling where each strategy file runs in its
own Lambda invocation, with results aggregated by the Aggregator Lambda.
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


def _get_regime_adjusted_allocations(
    base_allocations: dict[str, Decimal],
    table_name: str,
    correlation_id: str,
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    """Get regime-adjusted allocations if regime data is available.

    Args:
        base_allocations: Original allocations from strategy config
        table_name: DynamoDB table name for regime state
        correlation_id: Correlation ID for logging

    Returns:
        Tuple of (adjusted_allocations, regime_info_dict)
        Falls back to base_allocations if regime unavailable

    """
    regime_info: dict[str, Any] = {"enabled": False, "regime": None, "adjusted": False}

    try:
        from the_alchemiser.shared.regime import RegimeWeightAdjuster
        from the_alchemiser.shared.regime.repository import RegimeStateRepository

        # Check if regime is stale (older than 24 hours)
        repo = RegimeStateRepository(table_name=table_name)
        if repo.is_regime_stale(max_age_hours=24):
            logger.warning(
                "Regime state is stale or missing, using base allocations",
                extra={"correlation_id": correlation_id},
            )
            regime_info["stale"] = True
            return base_allocations, regime_info

        # Get current regime
        regime_state = repo.get_current_regime()
        if regime_state is None:
            logger.warning(
                "No regime state found, using base allocations",
                extra={"correlation_id": correlation_id},
            )
            return base_allocations, regime_info

        regime_info["regime"] = regime_state.regime.value
        regime_info["probability"] = str(regime_state.probability)
        regime_info["bull_probability"] = str(regime_state.bull_probability)
        regime_info["timestamp"] = regime_state.timestamp.isoformat()

        # Load weight adjuster with packaged config
        adjuster = RegimeWeightAdjuster.from_packaged_config("regime_weights.json")

        # Compute adjusted allocations
        adjusted = adjuster.compute_adjusted_allocations(base_allocations, regime_state)

        # Log adjustment summary
        summary = adjuster.get_regime_summary(base_allocations, regime_state)
        regime_info["enabled"] = True
        regime_info["adjusted"] = True
        regime_info["adjustment_method"] = summary.get("adjustment_method")

        logger.info(
            "Applied regime-based weight adjustment",
            extra={
                "correlation_id": correlation_id,
                "regime": regime_state.regime.value,
                "probability": str(regime_state.probability),
                "base_total": str(sum(base_allocations.values())),
                "adjusted_total": str(sum(adjusted.values())),
                "changes": summary.get("changes"),
            },
        )

        return adjusted, regime_info

    except ImportError as e:
        logger.warning(
            "Regime module not available, using base allocations",
            extra={"correlation_id": correlation_id, "error": str(e)},
        )
        regime_info["error"] = f"ImportError: {e}"
        return base_allocations, regime_info

    except (RuntimeError, ValueError, KeyError) as e:
        logger.error(
            "Failed to apply regime adjustment, using base allocations",
            extra={"correlation_id": correlation_id, "error": str(e)},
            exc_info=True,
        )
        regime_info["error"] = str(e)
        return base_allocations, regime_info


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

    # Validate correlation_id is non-empty
    if not correlation_id or not correlation_id.strip():
        correlation_id = f"workflow-{uuid.uuid4()}"

    session_id = correlation_id  # Use correlation_id as session_id

    logger.info(
        "Coordinator Lambda invoked - orchestrating parallel strategy execution",
        extra={
            "correlation_id": correlation_id,
            "session_id": session_id,
            "event_source": event.get("source", "schedule"),
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

        # Get DSL files and allocations
        dsl_files = app_settings.strategy.dsl_files
        dsl_allocations = app_settings.strategy.dsl_allocations

        if not dsl_files:
            raise ValueError("No DSL strategy files configured")

        # Build base allocations dict with Decimal for precision
        base_allocations: dict[str, Decimal] = {
            dsl_file: Decimal(str(dsl_allocations.get(dsl_file, 0.0))) for dsl_file in dsl_files
        }

        # Validate base allocations sum to ~1.0 using math.isclose per coding guidelines
        base_total = float(sum(base_allocations.values()))
        if not math.isclose(base_total, 1.0, rel_tol=0.01):
            logger.warning(
                "Base strategy allocations don't sum to 1.0",
                extra={
                    "total_allocation": base_total,
                    "allocations": dsl_allocations,
                },
            )

        # Apply regime-based weight adjustment if enabled
        regime_info: dict[str, Any] = {"enabled": False}
        enable_regime = os.environ.get("ENABLE_REGIME_WEIGHTING", "false").lower() == "true"
        regime_table = os.environ.get("REGIME_STATE_TABLE_NAME", "")

        if enable_regime and regime_table:
            final_allocations, regime_info = _get_regime_adjusted_allocations(
                base_allocations=base_allocations,
                table_name=regime_table,
                correlation_id=correlation_id,
            )
        else:
            final_allocations = base_allocations
            if not enable_regime:
                logger.info(
                    "Regime weighting disabled: ENABLE_REGIME_WEIGHTING is not 'true'",
                    extra={
                        "enable_regime_weighting": enable_regime,
                        "regime_state_table_configured": bool(regime_table),
                    },
                )
            elif not regime_table:
                logger.info(
                    "Regime weighting disabled: REGIME_STATE_TABLE_NAME environment variable not set",
                    extra={
                        "enable_regime_weighting": enable_regime,
                        "regime_state_table_configured": bool(regime_table),
                    },
                )

        # Build strategy configs from final allocations
        strategy_configs: list[tuple[str, Decimal]] = [
            (dsl_file, final_allocations.get(dsl_file, Decimal("0"))) for dsl_file in dsl_files
        ]

        # Log final allocations
        final_total = float(sum(alloc for _, alloc in strategy_configs))
        logger.info(
            "Loaded strategy configuration",
            extra={
                "dsl_files": dsl_files,
                "total_strategies": len(dsl_files),
                "base_total": base_total,
                "final_total": final_total,
                "regime_adjusted": regime_info.get("adjusted", False),
                "regime": regime_info.get("regime"),
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
                "regime_adjustment": {
                    "enabled": regime_info.get("enabled", False),
                    "regime": regime_info.get("regime"),
                    "adjusted": regime_info.get("adjusted", False),
                },
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
