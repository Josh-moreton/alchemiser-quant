"""Business Unit: coordinator | Status: current.

Handler for dispatching parallel strategy execution across workers.

Reads strategy configuration (DSL files and allocations), validates
allocation sums, and invokes Strategy Lambda once per DSL file (async).
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
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class DispatchHandler:
    """Orchestrates parallel strategy execution by dispatching to workers."""

    def handle(self, event: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        """Dispatch strategy workers for all configured DSL files.

        Args:
            event: Lambda event (from EventBridge schedule or direct invoke).
            correlation_id: Workflow correlation ID.

        Returns:
            Response with correlation_id and invocation count.

        """
        try:
            return self._dispatch(event, correlation_id)
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
            self._publish_workflow_failed(correlation_id, e)
            return {
                "statusCode": 500,
                "body": {
                    "status": "error",
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            }

    def _dispatch(self, event: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        """Core dispatch logic: load config, validate, invoke workers."""
        coordinator_settings = CoordinatorSettings.from_environment()
        app_settings = Settings()

        if not coordinator_settings.strategy_lambda_function_name:
            raise ValueError("STRATEGY_FUNCTION_NAME environment variable is required")

        dsl_files = app_settings.strategy.dsl_files
        dsl_allocations = app_settings.strategy.dsl_allocations

        if not dsl_files:
            raise ValueError("No DSL strategy files configured")

        strategy_configs: list[tuple[str, Decimal]] = [
            (dsl_file, Decimal(str(dsl_allocations.get(dsl_file, 0.0)))) for dsl_file in dsl_files
        ]

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

        invoker = StrategyInvoker(
            function_name=coordinator_settings.strategy_lambda_function_name,
        )

        request_ids = invoker.invoke_all_strategies(
            correlation_id=correlation_id,
            strategy_configs=strategy_configs,
        )

        self._create_notification_session(
            correlation_id=correlation_id,
            total_strategies=len(strategy_configs),
            strategy_files=dsl_files,
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

    def _create_notification_session(
        self,
        correlation_id: str,
        total_strategies: int,
        strategy_files: list[str],
    ) -> None:
        """Create a notification session for consolidated email delivery.

        Non-fatal: if session creation fails, strategies fall back to
        per-strategy emails (backward compatible).
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

    def _publish_workflow_failed(self, correlation_id: str, error: Exception) -> None:
        """Publish WorkflowFailed event to EventBridge. Non-fatal on failure."""
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="coordinator",
                source_component="DispatchHandler",
                workflow_type="strategy_coordination",
                failure_reason=str(error),
                failure_step="coordinator_dispatch",
                error_details={"exception_type": type(error).__name__},
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )
