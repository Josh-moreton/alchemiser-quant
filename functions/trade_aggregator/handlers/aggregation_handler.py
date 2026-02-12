"""Business Unit: trade_aggregator | Status: current.

Handler for TradeExecuted events: checks completion and aggregates results.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from config import TradeAggregatorSettings
from handlers.portfolio_capture import capture_portfolio_state, fetch_pnl_metrics
from service import TradeAggregatorService

from the_alchemiser.shared.events import AllTradesCompleted, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class AggregationHandler:
    """Handles TradeExecuted events, aggregates when all trades complete."""

    def handle(
        self,
        detail: dict[str, Any],
        run_id: str,
        trade_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Handle a single TradeExecuted event.

        Checks run completion, claims aggregation lock, and emits
        AllTradesCompleted if this invocation wins.

        Args:
            detail: Unwrapped EventBridge detail.
            run_id: Execution run identifier.
            trade_id: Trade identifier.
            correlation_id: Workflow correlation identifier.

        Returns:
            Response indicating aggregation status.

        """
        try:
            settings = TradeAggregatorSettings.from_environment()
            aggregator_service = TradeAggregatorService(
                table_name=settings.execution_runs_table_name,
            )

            completed, total = aggregator_service.record_trade_completed(run_id, trade_id)

            if total == 0:
                return self._handle_run_not_found(run_id, trade_id, correlation_id)

            logger.info(
                "Checked run completion",
                extra={
                    "run_id": run_id,
                    "completed_trades": completed,
                    "total_trades": total,
                },
            )

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

            if not aggregator_service.try_claim_aggregation(run_id):
                logger.info(
                    "Aggregation already claimed by another invocation",
                    extra={"run_id": run_id},
                )
                return {
                    "statusCode": 200,
                    "body": {"status": "already_aggregating", "run_id": run_id},
                }

            return self._aggregate_and_publish(
                aggregator_service,
                run_id,
                correlation_id,
                total,
            )

        except Exception as e:
            return self._handle_error(e, run_id, trade_id, correlation_id)

    def _handle_run_not_found(
        self,
        run_id: str,
        trade_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Publish WorkflowFailed for orphaned TradeExecuted events."""
        logger.warning(
            "Run not found or has no trades",
            extra={"run_id": run_id, "trade_id": trade_id},
        )
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=run_id or trade_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="trade_aggregator",
                source_component="AggregationHandler",
                workflow_type="trade_aggregation",
                failure_reason="Run not found or has no trades - orphaned TradeExecuted event",
                failure_step="run_lookup",
                error_details={
                    "exception_type": "RunNotFoundError",
                    "run_id": run_id,
                    "trade_id": trade_id,
                },
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event for run_not_found",
                extra={"error": str(pub_error), "run_id": run_id},
            )
        return {
            "statusCode": 200,
            "body": {"status": "error", "reason": "run_not_found"},
        }

    def _aggregate_and_publish(
        self,
        aggregator_service: TradeAggregatorService,
        run_id: str,
        correlation_id: str,
        total: int,
    ) -> dict[str, Any]:
        """Aggregate trade results and publish AllTradesCompleted."""
        logger.info(
            "All trades completed, starting aggregation",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "total_trades": total,
            },
        )

        run_metadata = aggregator_service.get_run_metadata(run_id)
        if not run_metadata:
            raise ValueError(f"Run metadata not found after claiming aggregation: {run_id}")

        trade_results = aggregator_service.get_all_trade_results(run_id)
        aggregated_data = aggregator_service.aggregate_trade_results(run_metadata, trade_results)

        capital_deployed_pct, portfolio_snapshot = capture_portfolio_state(correlation_id)
        pnl_metrics = fetch_pnl_metrics(correlation_id)

        started_at = run_metadata.get("created_at", "")
        completed_at = datetime.now(UTC).isoformat()

        data_freshness = self._parse_json_field(
            run_metadata.get("data_freshness"),
            "data_freshness",
            run_id,
        )
        strategies_evaluated = run_metadata.get("strategies_evaluated", 0)
        rebalance_plan_summary = (
            self._parse_json_field(
                run_metadata.get("rebalance_plan_summary"),
                "rebalance_plan_summary",
                run_id,
            )
            or []
        )

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
            non_fractionable_skipped_symbols=aggregated_data.get(
                "non_fractionable_skipped_symbols",
                [],
            ),
            started_at=started_at,
            completed_at=completed_at,
            portfolio_snapshot=portfolio_snapshot,
            data_freshness=data_freshness or {},
            pnl_metrics=pnl_metrics,
            strategies_evaluated=strategies_evaluated,
            rebalance_plan_summary=rebalance_plan_summary,
        )

        publish_to_eventbridge(all_trades_event)

        _report_strategy_traded(
            correlation_id=correlation_id,
            run_id=run_id,
            strategy_id=run_metadata.get("strategy_id", ""),
            dsl_file=run_metadata.get("dsl_file", ""),
            all_trades_detail=all_trades_event.model_dump(mode="json"),
        )

        aggregator_service.mark_run_completed(run_id)

        logger.info(
            "Aggregation completed successfully",
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

    def _parse_json_field(
        self,
        raw: str | None,
        field_name: str,
        run_id: str,
    ) -> Any:  # noqa: ANN401
        """Parse a JSON string field from DynamoDB, returning None on failure."""
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse {field_name} from run metadata",
                extra={"run_id": run_id},
            )
            return None

    def _handle_error(
        self,
        error: Exception,
        run_id: str,
        trade_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Handle aggregation failure: mark run failed and publish WorkflowFailed."""
        logger.error(
            "Trade Aggregator failed",
            extra={
                "run_id": run_id,
                "trade_id": trade_id,
                "correlation_id": correlation_id,
                "error": str(error),
            },
            exc_info=True,
        )

        try:
            settings = TradeAggregatorSettings.from_environment()
            service = TradeAggregatorService(table_name=settings.execution_runs_table_name)
            service.mark_run_failed(run_id, str(error))
        except Exception as mark_error:
            logger.warning(
                "Failed to mark run as failed",
                extra={"run_id": run_id, "error": str(mark_error)},
            )

        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=run_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="trade_aggregator",
                source_component="AggregationHandler",
                workflow_type="trade_aggregation",
                failure_reason=str(error),
                failure_step="aggregation",
                error_details={
                    "exception_type": type(error).__name__,
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
                "error": str(error),
            },
        }


def _derive_strategy_id(
    strategy_id: str,
    run_id: str,
    all_trades_detail: dict[str, Any],
) -> str:
    """Derive strategy_id from plan metadata if not stored in run."""
    if strategy_id:
        return strategy_id
    metadata = all_trades_detail.get("metadata", {})
    derived = metadata.get("strategy_name", run_id[:8])
    if not derived:
        plan_summary = all_trades_detail.get("rebalance_plan_summary", [])
        if plan_summary:
            derived = f"run-{run_id[:8]}"
    return derived or run_id[:8]


def _report_strategy_traded(
    correlation_id: str,
    run_id: str,
    strategy_id: str,
    dsl_file: str,
    all_trades_detail: dict[str, Any],
) -> None:
    """Report a TRADED strategy to the notification session for consolidated email.

    Non-fatal: if session recording fails, per-strategy emails still work.
    """
    table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
    if not table_name:
        return

    strategy_id = _derive_strategy_id(strategy_id, run_id, all_trades_detail)

    if not dsl_file:
        metadata = all_trades_detail.get("metadata", {})
        dsl_file = metadata.get("dsl_file", "")

    try:
        from the_alchemiser.shared.services.notification_session_service import (
            NotificationSessionService,
            publish_all_strategies_completed,
        )

        session_service = NotificationSessionService(table_name=table_name)
        detail = {**all_trades_detail, "run_id": run_id}

        completed, total = session_service.record_strategy_completion(
            correlation_id=correlation_id,
            strategy_id=strategy_id,
            dsl_file=dsl_file,
            outcome="TRADED",
            detail=detail,
        )

        logger.info(
            "Reported TRADED to notification session",
            extra={
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "run_id": run_id,
                "completed_strategies": completed,
                "total_strategies": total,
            },
        )

        if completed >= total > 0:
            publish_all_strategies_completed(
                correlation_id,
                completed,
                total,
                "TradeAggregator",
            )

    except Exception as e:
        logger.warning(
            "Failed to report TRADED to notification session",
            extra={
                "correlation_id": correlation_id,
                "run_id": run_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
